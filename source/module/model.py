from pydantic import BaseModel


class ExtractParams(BaseModel):
    url: str
    download: bool = False
    index: list[str | int] | None = None
    cookie: str = None
    proxy: str = None
    skip: bool = False


class ExtractData(BaseModel):
    message: str
    params: ExtractParams
    data: dict | None


class SearchParams(BaseModel):
    keyword: str
    require_num: int = 20
    cookie: str | None = None
    proxy: str | None = None
    sort_type_choice: int = 0
    note_type: int = 0
    note_time: int = 0
    note_range: int = 0
    pos_distance: int = 0
    geo: dict | None = None


class SearchData(BaseModel):
    message: str
    params: SearchParams
    data: list[dict] | None
