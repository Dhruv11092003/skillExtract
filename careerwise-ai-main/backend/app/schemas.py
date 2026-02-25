from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class WordBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    x0: float
    x1: float
    top: float
    bottom: float
    section: Literal["header", "body", "footer"]


class ParsedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    words: List[WordBox] = Field(default_factory=list)
    full_text: str = ""


class SkillEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str = Field(min_length=1)
    context_window: str
    semantic_proof_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    section: Literal["header", "body", "footer"]
    spatial_weight: float = Field(ge=0.0, le=1.0)


class RankingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    importance: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    spatial_weight: float = Field(ge=0.0, le=1.0)


class RankedSkill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    importance: float
    confidence: float
    spatial_weight: float
    weighted_score: float


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extracted_skills: List[SkillEvidence]
    ranked_skills: List[RankedSkill]
    total_score: float = Field(ge=0.0)
    notes: Optional[str] = None
