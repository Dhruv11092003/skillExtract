import argparse
import json

import torch
from transformers import AutoTokenizer

from src.dl_models.skill_classifier import SkillExtractModel
from src.pipeline.preprocess import SPATIAL_WEIGHTS
from src.semantic_engine.embedding_model import ContextualEmbeddingModel
from src.spatial_engine.coordinate_mapper import integrity_score, section_to_weight
from src.spatial_engine.pdf_parser import extract_pdf_tokens

ID_TO_LABEL = {0: "O", 1: "B-SKILL", 2: "I-SKILL"}
ID_TO_SECTION = {0: "experience", 1: "skills", 2: "projects", 3: "education", 4: "hobbies", 5: "other"}


def build_context(tokens, idx, window_size=20):
    left = max(0, idx - window_size)
    right = min(len(tokens), idx + window_size + 1)
    return " ".join(tokens[left:right])


def predict(pdf_path: str, model_path: str = "models/skill_extract_model.pt", tokenizer_path: str = "models/tokenizer"):
    pdf_tokens = extract_pdf_tokens(pdf_path)
    tokens = [t["text"] for t in pdf_tokens]
    bboxes = [t["bbox"] for t in pdf_tokens]

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    model = SkillExtractModel()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    enc = tokenizer(tokens[:254], is_split_into_words=True, return_tensors="pt", truncation=True, max_length=256)
    effective_len = int(enc["attention_mask"][0].sum())
    input_ids = enc["input_ids"]
    attention_mask = enc["attention_mask"]

    bbox_tensor = torch.zeros((1, input_ids.shape[1], 4), dtype=torch.float)
    sec_tensor = torch.full((1, input_ids.shape[1]), 5, dtype=torch.long)

    bbox_slice = bboxes[: max(0, min(len(bboxes), effective_len - 2))]
    if bbox_slice:
        bbox_tensor[0, 1 : 1 + len(bbox_slice)] = torch.tensor(bbox_slice, dtype=torch.float)

    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attention_mask, bbox=bbox_tensor, section_ids=sec_tensor)

    if isinstance(out["token_predictions"], list):
        pred = out["token_predictions"][0]
    else:
        pred = out["token_predictions"][0].tolist()

    section = ID_TO_SECTION[out["section_logits"].argmax(-1).item()]
    embedder = ContextualEmbeddingModel()

    results = []
    for idx, tag in enumerate(pred[1: len(tokens) + 1], start=0):
        if ID_TO_LABEL.get(tag) == "B-SKILL":
            skill = tokens[idx]
            context = build_context(tokens, idx)
            sim = embedder.semantic_similarity(skill, context)
            w = section_to_weight(section)
            results.append(
                {
                    "skill": skill,
                    "section": section,
                    "semantic_similarity": round(sim, 4),
                    "spatial_weight": w,
                    "integrity_score": integrity_score(w, sim),
                    "bounding_box": bboxes[idx] if idx < len(bboxes) else [0, 0, 0, 0],
                    "context_snippet": context,
                }
            )

    return {"skills": results, "integrity_formula": "IntegrityScore = W_spatial × V_semantic"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("resume_pdf", type=str)
    parser.add_argument("--model_path", default="models/skill_extract_model.pt")
    parser.add_argument("--tokenizer_path", default="models/tokenizer")
    args = parser.parse_args()
    print(json.dumps(predict(args.resume_pdf, args.model_path, args.tokenizer_path), indent=2))
