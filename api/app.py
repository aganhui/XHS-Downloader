import os

if os.getenv("VERCEL") and not os.getenv("XHS_VOLUME"):
    os.environ["XHS_VOLUME"] = "/tmp/xhs_downloader_volume"

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
app = FastAPI(
    title="XHS-Downloader",
    version=f"{xhs.VERSION_MAJOR}.{xhs.VERSION_MINOR}.{'beta' if xhs.VERSION_BETA else 'stable'}",
)
xhs.setup_routes(app)


@app.on_event("startup")
async def _startup():
    await xhs.__aenter__()


@app.on_event("shutdown")
async def _shutdown():
    await xhs.__aexit__(None, None, None)
