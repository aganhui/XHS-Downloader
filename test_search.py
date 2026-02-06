import json
import os
from urllib import request
from urllib.error import HTTPError, URLError


def post_json(url: str, payload: dict, timeout: int = 30) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    url = os.getenv("XHS_BASE_URL", "https://xhs-downloader-nine.vercel.app")
    url = url.rstrip("/") + "/xhs/search"
    cookie = os.getenv("XHS_COOKIE")
    payload = {
        "keyword": "ha24msa",
        "require_num": 20,
        "sort_type_choice": 1,
        "note_type": 0,
        "note_time": 1,
        "note_range": 0,
        "pos_distance": 0,
    }
    if cookie:
        payload["cookie"] = cookie
    try:
        status, body = post_json(url, payload, timeout=60)
        print(f"status={status}")
        print(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"status={exc.code}")
        print(body)
    except URLError as exc:
        print(f"request failed: {exc}")
    except Exception as exc:
        print(f"request failed: {exc}")


if __name__ == "__main__":
    main()
