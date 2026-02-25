from __future__ import annotations

from typing import Iterable

from app.schemas import SkillEvidence, WordBox

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except Exception:  # pragma: no cover
    torch = None
    AutoModelForSequenceClassification = None
    AutoTokenizer = None


class SemanticVerifier:
    """Cross-encoder style verifier for skill-context grounding."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        if AutoTokenizer and AutoModelForSequenceClassification:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.eval()
            except Exception:
                self.tokenizer = None
                self.model = None

    def semantic_proof(self, skill: str, context: str) -> float:
        if self.tokenizer is None or self.model is None or torch is None:
            return self._fallback_similarity(skill, context)

        with torch.no_grad():
            encoded = self.tokenizer(
                skill,
                context,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            logits = self.model(**encoded).logits
            score = torch.sigmoid(logits.squeeze()).item()
            return float(max(0.0, min(1.0, score)))

    @staticmethod
    def _fallback_similarity(skill: str, context: str) -> float:
        skill_tokens = set(skill.lower().split())
        context_tokens = set(context.lower().split())
        if not skill_tokens:
            return 0.0
        overlap = len(skill_tokens & context_tokens) / len(skill_tokens)
        return float(max(0.05, min(1.0, overlap)))

    def build_evidence(
        self,
        skill: str,
        context: str,
        section: str,
        spatial_weight: float,
    ) -> SkillEvidence:
        semantic_score = self.semantic_proof(skill, context)
        confidence = (semantic_score * 0.7) + (spatial_weight * 0.3)
        return SkillEvidence(
            skill=skill,
            context_window=context,
            semantic_proof_score=semantic_score,
            confidence=confidence,
            reasoning=(
                f"Found {skill} in '{section}' section; verified via semantic "
                f"context: '{context[:150]}...'"
            ),
            section=section,
            spatial_weight=spatial_weight,
        )


def infer_spatial_weight(word: WordBox) -> float:
    mapping = {"header": 1.0, "body": 0.75, "footer": 0.2}
    return mapping.get(word.section, 0.5)
