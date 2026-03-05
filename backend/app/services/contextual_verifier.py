from __future__ import annotations

import math

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


class ContextualVerifier:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def similarity(self, skill: str, snippet: str) -> float:
        if not snippet.strip():
            return 0.0

        if self.model is None:
            return self._fallback_similarity(skill, snippet)

        embeddings = self.model.encode([skill, snippet], normalize_embeddings=True)
        score = float(np.dot(embeddings[0], embeddings[1]))
        return float(max(0.0, min(1.0, (score + 1.0) / 2.0)))

    @staticmethod
    def _fallback_similarity(skill: str, snippet: str) -> float:
        skill_terms = set(skill.lower().split())
        snippet_terms = set(snippet.lower().split())
        if not skill_terms:
            return 0.0
        overlap = len(skill_terms & snippet_terms) / len(skill_terms)
        return max(0.05, min(1.0, overlap))


def coordinate_weight(section: str) -> float:
    mapping = {"header": 1.0, "body": 0.75, "footer": 0.35}
    return mapping.get(section, 0.5)


def integrity_score(coord_weight: float, semantic_similarity: float) -> float:
    score = coord_weight * semantic_similarity
    if math.isnan(score):
        return 0.0
    return max(0.0, min(1.0, score))
