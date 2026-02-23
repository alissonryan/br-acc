from pydantic import BaseModel

from icarus.models.entity import SourceAttribution


class SearchResult(BaseModel):
    id: str
    type: str
    name: str
    score: float
    document: str | None = None
    properties: dict[str, str | float | int | bool | None]
    sources: list[SourceAttribution]


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    page: int
    size: int
