from pydantic import BaseModel

from icarus.models.entity import SourceAttribution


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    document_id: str | None = None
    properties: dict[str, str | float | int | bool | None]
    sources: list[SourceAttribution]
    is_pep: bool = False


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: dict[str, str | float | int | bool | None]
    confidence: float = 1.0
    sources: list[SourceAttribution]


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    center_id: str
