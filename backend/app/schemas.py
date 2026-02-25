from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Coordinate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float = Field(gt=0)
    page_height: float = Field(gt=0)
    page: int = Field(ge=1)


class SpatialToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    coordinate: Coordinate


class SkillResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    coordinates: Coordinate
    confidence_score: float = Field(ge=0.0, le=1.0)
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    coordinate_weight: float = Field(ge=0.0, le=1.0)
    evidence_snippet: str
    section: Literal["header", "body", "footer"]


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skills: list[SkillResult]
    total_detected: int = Field(ge=0)
    model: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
