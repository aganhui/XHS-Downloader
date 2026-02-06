import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from quickjs import Context
except Exception as exc:  # pragma: no cover - runtime dependency
    Context = None
    _quickjs_error = exc
else:
    _quickjs_error = None


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _read_js(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"JS file not found: {path}")
    return path.read_text(encoding="utf-8")


def _generate_x_b3_traceid(length: int = 16) -> str:
    return "".join("abcdef0123456789"[math.floor(16 * random.random())] for _ in range(length))


def _trans_cookies(cookie_string: str) -> dict:
    # 清理 Cookie 字符串中的换行符和其他非法字符
    cleaned = cookie_string.replace("\n", "").replace("\r", "").strip()
    if "; " in cleaned:
        return {i.split("=")[0]: "=".join(i.split("=")[1:]) for i in cleaned.split("; ")}
    return {i.split("=")[0]: "=".join(i.split("=")[1:]) for i in cleaned.split(";")}


def _request_headers_template() -> dict:
    return {
        "authority": "edith.xiaohongshu.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.xiaohongshu.com",
        "pragma": "no-cache",
        "referer": "https://www.xiaohongshu.com/",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "x-b3-traceid": "",
        "x-mns": "unload",
        "x-s": "",
        "x-s-common": "",
        "x-t": "",
        "x-xray-traceid": "",
    }


@dataclass(frozen=True)
class _Signer:
    ctx: Any
    get_request_headers_params: Any
    trace_id: Any

    @classmethod
    def load(cls) -> "_Signer":
        if Context is None:
            raise RuntimeError(
                "quickjs unavailable, please install quickjs. "
                f"Original error: {_quickjs_error}"
            )
        ctx = Context()
        ctx.eval(_read_js(ASSETS_DIR / "xhs_xs_xsc_56.js"))
        ctx.eval(_read_js(ASSETS_DIR / "xhs_xray.js"))
        get_request_headers_params = ctx.eval("get_request_headers_params")
        trace_id = ctx.eval("traceId")
        return cls(
            ctx=ctx,
            get_request_headers_params=get_request_headers_params,
            trace_id=trace_id,
        )

    def generate_xs_xs_common(
        self,
        a1: str,
        api: str,
        data: str,
        method: str,
    ) -> tuple[str, str, str]:
        ret = self.get_request_headers_params(api, data, a1, method)
        return ret["xs"], ret["xt"], ret["xs_common"]

    def generate_xray_traceid(self) -> str:
        return self.trace_id()


class XhsSearchClient:
    base_url = "https://edith.xiaohongshu.com"

    def __init__(
        self,
        client,
        cookie: str | None,
        proxy: str | None,
    ):
        self.client = client
        self.cookie = cookie or ""
        self.proxy = proxy
        self.signer = None

    def _get_signer(self) -> _Signer:
        if not self.signer:
            self.signer = _Signer.load()
        return self.signer

    def _generate_headers(
        self,
        cookies_str: str,
        api: str,
        data: dict | str,
        method: str = "POST",
    ) -> tuple[dict, dict, str]:
        cookies = _trans_cookies(cookies_str)
        if "a1" not in cookies:
            raise ValueError("Cookie 缺少 a1")
        raw_data = data
        if isinstance(data, dict):
            raw_data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        signer = self._get_signer()
        xs, xt, xs_common = signer.generate_xs_xs_common(
            cookies["a1"],
            api,
            raw_data or "",
            method,
        )
        headers = _request_headers_template()
        headers["x-s"] = xs
        headers["x-t"] = str(xt)
        headers["x-s-common"] = xs_common
        headers["x-b3-traceid"] = _generate_x_b3_traceid()
        headers["x-xray-traceid"] = signer.generate_xray_traceid()
        return headers, cookies, raw_data or ""

    @staticmethod
    def _build_filters(
        sort_type_choice: int,
        note_type: int,
        note_time: int,
        note_range: int,
        pos_distance: int,
    ) -> list[dict]:
        sort_type = {
            1: "time_descending",
            2: "popularity_descending",
            3: "comment_descending",
            4: "collect_descending",
        }.get(sort_type_choice, "general")
        filter_note_type = {1: "视频笔记", 2: "普通笔记"}.get(note_type, "不限")
        filter_note_time = {1: "一天内", 2: "一周内", 3: "半年内"}.get(note_time, "不限")
        filter_note_range = {1: "已看过", 2: "未看过", 3: "已关注"}.get(note_range, "不限")
        filter_pos_distance = {1: "同城", 2: "附近"}.get(pos_distance, "不限")
        return [
            {"tags": [sort_type], "type": "sort_type"},
            {"tags": [filter_note_type], "type": "filter_note_type"},
            {"tags": [filter_note_time], "type": "filter_note_time"},
            {"tags": [filter_note_range], "type": "filter_note_range"},
            {"tags": [filter_pos_distance], "type": "filter_pos_distance"},
        ]

    async def search_notes(
        self,
        keyword: str,
        require_num: int,
        cookies_str: str | None = None,
        sort_type_choice: int = 0,
        note_type: int = 0,
        note_time: int = 0,
        note_range: int = 0,
        pos_distance: int = 0,
        geo: dict | None = None,
        proxy: str | None = None,
    ) -> list[dict]:
        cookies_str = cookies_str or self.cookie
        if not cookies_str:
            raise ValueError("Cookie 不能为空")
        api = "/api/sns/web/v1/search/notes"
        page = 1
        result: list[dict] = []
        while True:
            data = {
                "keyword": keyword,
                "page": page,
                "page_size": 20,
                "search_id": _generate_x_b3_traceid(21),
                "sort": "general",
                "note_type": 0,
                "ext_flags": [],
                "filters": self._build_filters(
                    sort_type_choice,
                    note_type,
                    note_time,
                    note_range,
                    pos_distance,
                ),
                "geo": json.dumps(geo, separators=(",", ":")) if geo else "",
                "image_formats": ["jpg", "webp", "avif"],
            }
            headers, cookies, payload = self._generate_headers(
                cookies_str,
                api,
                data,
                "POST",
            )
            response = await self.client.post(
                f"{self.base_url}{api}",
                headers=headers,
                content=payload.encode("utf-8"),
                cookies=cookies,
                proxy=proxy or self.proxy,
            )
            response.raise_for_status()
            res_json = response.json()
            if not res_json.get("success"):
                raise RuntimeError(res_json.get("msg") or "搜索请求失败")
            items = res_json.get("data", {}).get("items", [])
            result.extend(items)
            if len(result) >= require_num or not res_json.get("data", {}).get("has_more"):
                break
            page += 1
        return result[:require_num]
