from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ContextualEmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]):
        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def semantic_similarity(self, skill_text: str, context_text: str) -> float:
        skill_emb, context_emb = self.encode([skill_text, context_text])
        return float(cosine_similarity([skill_emb], [context_emb])[0][0])
