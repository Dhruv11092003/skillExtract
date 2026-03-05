from src.pipeline.preprocess import SPATIAL_WEIGHTS


def section_to_weight(section: str) -> float:
    return SPATIAL_WEIGHTS.get(section.lower(), SPATIAL_WEIGHTS["other"])


def integrity_score(spatial_weight: float, semantic_similarity: float) -> float:
    return round(spatial_weight * semantic_similarity, 4)
