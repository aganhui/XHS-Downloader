import os
import warnings
from contextlib import asynccontextmanager

if os.getenv("VERCEL") and not os.getenv("XHS_VOLUME"):
    os.environ["XHS_VOLUME"] = "/tmp/xhs_downloader_volume"

# 抑制来自 uvicorn/websockets 的弃用警告
# 这些警告来自第三方库内部，不影响功能
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*websockets.legacy.*",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*websockets.server.WebSocketServerProtocol.*",
)

from fastapi import FastAPI

from source import Settings, XHS


def _build_settings() -> dict:
    settings = Settings().run()
    work_path = os.getenv("XHS_WORK_PATH")
    if os.getenv("VERCEL") and not work_path:
        work_path = "/tmp/xhs_downloader"
    if work_path:
        settings["work_path"] = work_path
    cookie = os.getenv("XHS_COOKIE")
    if cookie:
        settings["cookie"] = cookie
    proxy = os.getenv("XHS_PROXY")
    if proxy:
        settings["proxy"] = proxy
    return settings


xhs = XHS(**_build_settings())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await xhs.__aenter__()
    yield
    # Shutdown
    await xhs.__aexit__(None, None, None)


app = FastAPI(
    title="XHS-Downloader",
    version=f"{xhs.VERSION_MAJOR}.{xhs.VERSION_MINOR}.{'beta' if xhs.VERSION_BETA else 'stable'}",
    lifespan=lifespan,
)
xhs.setup_routes(app)
