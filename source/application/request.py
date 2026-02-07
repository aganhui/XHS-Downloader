from typing import TYPE_CHECKING
from urllib.parse import urlparse, parse_qs

from httpx import HTTPError
from httpx import get

from ..module import ERROR, Manager, logging, sleep_time
from ..translation import _

if TYPE_CHECKING:
    from ..module import Manager

__all__ = ["Html"]


class Html:
    def __init__(
        self,
        manager: "Manager",
    ):
        self.print = manager.print
        self.retry = manager.retry
        self.client = manager.request_client
        self.headers = manager.headers
        self.timeout = manager.timeout

    async def request_url(
        self,
        url: str,
        content=True,
        cookie: str = None,
        proxy: str = None,
        **kwargs,
    ) -> str:
        if not url.startswith("http"):
            url = f"https://{url}"
        headers = self.update_cookie(
            cookie,
        )
        # 使用 _NO_RETRY 标记来避免重试
        _NO_RETRY = object()

        async def _do_request():
            try:
                match bool(proxy):
                    case False:
                        response = await self.__request_url_get(
                            url,
                            headers,
                            **kwargs,
                        )
                        await sleep_time()
                        # 检查是否重定向到 404 页面
                        final_url = str(response.url)
                        if "/404" in final_url or "errorCode" in final_url:
                            error_msg = _("请求被重定向到错误页面: {0}").format(final_url)
                            logging(self.print, error_msg, ERROR)
                            # 返回特殊标记，避免重试
                            return _NO_RETRY
                        # 检查重定向后的 URL 是否包含 xsec_token
                        # 如果原始 URL 不包含 token 但重定向后的 URL 包含，说明重定向是正常的
                        if "xsec_token" not in url and "xsec_token" in final_url:
                            # httpx 已经自动跟随重定向，这里只记录日志
                            token = self.extract_xsec_token(final_url)
                            if token:
                                logging(
                                    self.print,
                                    _("检测到重定向，已获取 xsec_token: {0}").format(token[:20] + "..." if len(token) > 20 else token),
                                )
                        response.raise_for_status()
                        return response.text if content else str(response.url)
                    case True:
                        response = await self.__request_url_get_proxy(
                            url,
                            headers,
                            proxy,
                            **kwargs,
                        )
                        await sleep_time()
                        # 检查是否重定向到 404 页面
                        final_url = str(response.url)
                        if "/404" in final_url or "errorCode" in final_url:
                            error_msg = _("请求被重定向到错误页面: {0}").format(final_url)
                            logging(self.print, error_msg, ERROR)
                            # 返回特殊标记，避免重试
                            return _NO_RETRY
                        # 检查重定向后的 URL 是否包含 xsec_token
                        # 如果原始 URL 不包含 token 但重定向后的 URL 包含，说明重定向是正常的
                        if "xsec_token" not in url and "xsec_token" in final_url:
                            # httpx 已经自动跟随重定向，这里只记录日志
                            token = self.extract_xsec_token(final_url)
                            if token:
                                logging(
                                    self.print,
                                    _("检测到重定向，已获取 xsec_token: {0}").format(token[:20] + "..." if len(token) > 20 else token),
                                )
                        response.raise_for_status()
                        return response.text if content else str(response.url)
                    case _:
                        raise ValueError
            except HTTPError as error:
                logging(
                    self.print,
                    _("网络异常，{0} 请求失败: {1}").format(url, repr(error)),
                    ERROR,
                )
                return ""

        # 手动实现重试逻辑，但跳过 _NO_RETRY 标记的情况
        result = await _do_request()
        if result is _NO_RETRY:
            return ""
        if result:
            return result

        # 重试逻辑
        for __ in range(self.retry):
            result = await _do_request()
            if result is _NO_RETRY:
                return ""
            if result:
                return result
        return result or ""

    @staticmethod
    def format_url(url: str) -> str:
        return bytes(url, "utf-8").decode("unicode_escape")

    @staticmethod
    def extract_xsec_token(url: str) -> str | None:
        """
        从 URL 中提取 xsec_token 参数

        Args:
            url: 包含 xsec_token 的 URL

        Returns:
            xsec_token 值，如果不存在则返回 None
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if "xsec_token" in query_params:
                return query_params["xsec_token"][0]
        except Exception:
            pass
        return None

    @staticmethod
    def build_url_with_token(base_url: str, token: str) -> str:
        """
        构建包含 xsec_token 的完整 URL

        Args:
            base_url: 基础 URL（如 https://www.xiaohongshu.com/explore/6986a270000000000e00de24）
            token: xsec_token 值

        Returns:
            包含 xsec_token 的完整 URL
        """
        if "?" in base_url:
            return f"{base_url}&xsec_token={token}"
        return f"{base_url}?xsec_token={token}"

    def update_cookie(
        self,
        cookie: str = None,
    ) -> dict:
        if cookie:
            # 清理 Cookie 字符串中的换行符和其他非法字符
            # HTTP header 值不能包含换行符、回车符等控制字符
            cleaned_cookie = cookie.replace("\n", "").replace("\r", "").strip()
            return self.headers | {"Cookie": cleaned_cookie}
        return self.headers.copy()

    async def __request_url_head(
        self,
        url: str,
        headers: dict,
        **kwargs,
    ):
        return await self.client.head(
            url,
            headers=headers,
            follow_redirects=True,
            **kwargs,
        )

    async def __request_url_head_proxy(
        self,
        url: str,
        headers: dict,
        proxy: str,
        **kwargs,
    ):
        return await self.client.head(
            url,
            headers=headers,
            proxy=proxy,
            follow_redirects=True,
            verify=False,
            timeout=self.timeout,
            **kwargs,
        )

    async def __request_url_get(
        self,
        url: str,
        headers: dict,
        **kwargs,
    ):
        return await self.client.get(
            url,
            headers=headers,
            follow_redirects=True,
            **kwargs,
        )

    async def __request_url_get_proxy(
        self,
        url: str,
        headers: dict,
        proxy: str,
        **kwargs,
    ):
        return get(
            url,
            headers=headers,
            proxy=proxy,
            follow_redirects=True,
            verify=False,
            timeout=self.timeout,
            **kwargs,
        )
