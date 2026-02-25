from __future__ import annotations

from typing import Iterable

from app.schemas import RankedSkill, RankingInput


class PatentRankingEngine:
    """Formal ranking implementation: S_final = Σ(Importance × Confidence × SpatialWeight)."""

    @staticmethod
    def rank(entries: Iterable[RankingInput]) -> tuple[list[RankedSkill], float]:
        ranked: list[RankedSkill] = []
        total = 0.0
        for item in entries:
            weighted = item.importance * item.confidence * item.spatial_weight
            total += weighted
            ranked.append(
                RankedSkill(
                    skill=item.skill,
                    importance=item.importance,
                    confidence=item.confidence,
                    spatial_weight=item.spatial_weight,
                    weighted_score=weighted,
                )
            )
        ranked.sort(key=lambda x: x.weighted_score, reverse=True)
        return ranked, total
