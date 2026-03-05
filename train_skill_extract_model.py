import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from sklearn.metrics import precision_recall_fscore_support
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from src.dl_models.skill_classifier import SkillExtractModel
from src.pipeline.dataset_builder import build_processed_jsonl, load_jsonl
from src.pipeline.preprocess import SPATIAL_WEIGHTS
from src.semantic_engine.embedding_model import ContextualEmbeddingModel
from src.spatial_engine.coordinate_mapper import integrity_score, section_to_weight

LABEL_TO_ID = {"O": 0, "B-SKILL": 1, "I-SKILL": 2}
SECTION_TO_ID = {"experience": 0, "skills": 1, "projects": 2, "education": 3, "hobbies": 4, "other": 5}


class ResumeDataset(Dataset):
    def __init__(self, records: List[Dict], tokenizer, max_length: int = 256):
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        tokens = rec["tokens"][: self.max_length - 2]
        labels = rec["labels"][: self.max_length - 2]
        sections = rec["section"][: self.max_length - 2]
        bboxes = rec["bbox"][: self.max_length - 2]

        enc = self.tokenizer(tokens, is_split_into_words=True, padding="max_length", truncation=True,
                             max_length=self.max_length, return_tensors="pt")

        seq_len = len(tokens)
        token_labels = [0] + [LABEL_TO_ID.get(x, 0) for x in labels] + [0]
        token_sections = [SECTION_TO_ID["other"]] + [SECTION_TO_ID.get(s, SECTION_TO_ID["other"]) for s in sections] + [SECTION_TO_ID["other"]]
        bbox_vals = [[0, 0, 0, 0]] + bboxes + [[0, 0, 0, 0]]

        pad_len = self.max_length - len(token_labels)
        token_labels += [0] * pad_len
        token_sections += [SECTION_TO_ID["other"]] * pad_len
        bbox_vals += [[0, 0, 0, 0]] * pad_len

        sec = max(set(sections or ["other"]), key=(sections or ["other"]).count)
        section_label = SECTION_TO_ID.get(sec, SECTION_TO_ID["other"])

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(token_labels, dtype=torch.long),
            "section_ids": torch.tensor(token_sections, dtype=torch.long),
            "bbox": torch.tensor(bbox_vals, dtype=torch.float),
            "section_label": torch.tensor(section_label, dtype=torch.long),
        }


def maybe_download_kaggle_dataset(dataset_path: Path):
    if dataset_path.exists() and any(dataset_path.rglob("*.csv")):
        return
    dataset_path.mkdir(parents=True, exist_ok=True)
    try:
        import kagglehub

        dl = kagglehub.dataset_download("snehaanbhawal/resume-dataset")
        src = Path(dl)
        for f in src.rglob("*.csv"):
            target = dataset_path / f.name
            target.write_bytes(f.read_bytes())
        print(f"Downloaded dataset to {dataset_path}")
    except Exception as exc:
        raise RuntimeError(
            "Dataset download failed. Install kagglehub and configure Kaggle credentials, "
            f"or place CSV manually in {dataset_path}. Error: {exc}"
        )


def evaluate(model, dataloader, device, embedder):
    model.eval()
    all_true, all_pred = [], []
    integrity_values = []
    with torch.no_grad():
        for batch in dataloader:
            inputs = {k: v.to(device) for k, v in batch.items() if k in {"input_ids", "attention_mask", "bbox", "section_ids"}}
            out = model(**inputs)
            preds = out["token_predictions"]
            labels = batch["labels"].numpy()
            ids = batch["input_ids"].numpy()

            if isinstance(preds, list):
                pred_np = np.zeros_like(labels)
                for i, seq in enumerate(preds):
                    pred_np[i, : len(seq)] = np.array(seq)
            else:
                pred_np = preds.cpu().numpy()

            all_true.extend(labels.flatten().tolist())
            all_pred.extend(pred_np.flatten().tolist())

            for i in range(labels.shape[0]):
                if 1 in pred_np[i] or 2 in pred_np[i]:
                    section_name = list(SPATIAL_WEIGHTS.keys())[batch["section_label"][i].item()] if batch["section_label"][i].item() < len(SPATIAL_WEIGHTS) else "other"
                    sim = embedder.semantic_similarity("python", " ".join(map(str, ids[i][:20])))
                    integrity_values.append(integrity_score(section_to_weight(section_name), sim))

    precision, recall, f1, _ = precision_recall_fscore_support(all_true, all_pred, average="macro", zero_division=0)
    fp = sum((np.array(all_true) == 0) & (np.array(all_pred) != 0))
    tn = sum((np.array(all_true) == 0) & (np.array(all_pred) == 0))
    fpr = fp / max(fp + tn, 1)
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": float(fpr),
        "integrity_mean": float(np.mean(integrity_values)) if integrity_values else 0.0,
        "integrity_std": float(np.std(integrity_values)) if integrity_values else 0.0,
    }


def main(args):
    dataset_path = Path(args.dataset_path)
    maybe_download_kaggle_dataset(dataset_path)
    processed_path = Path("data/processed/resume_dataset.jsonl")
    build_processed_jsonl(str(dataset_path), str(processed_path), max_samples=args.max_samples)
    records = load_jsonl(str(processed_path))

    split = int(0.8 * len(records))
    train_records, test_records = records[:split], records[split:]

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    train_ds = ResumeDataset(train_records, tokenizer, args.max_length)
    test_ds = ResumeDataset(test_records, tokenizer, args.max_length)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SkillExtractModel(base_model=args.base_model).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        model.train()
        losses = []
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                bbox=batch["bbox"],
                section_ids=batch["section_ids"],
                labels=batch["labels"],
                section_labels=batch["section_label"],
            )
            loss = out["loss"]
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
        print(f"Epoch {epoch + 1}/{args.epochs} loss={np.mean(losses):.4f}")

    embedder = ContextualEmbeddingModel()
    metrics = evaluate(model, test_loader, device, embedder)
    baseline_fpr = 0.25
    metrics["false_skill_detection_reduction_vs_baseline"] = (baseline_fpr - metrics["false_positive_rate"]) / baseline_fpr

    Path("models").mkdir(exist_ok=True)
    torch.save(model.state_dict(), "models/skill_extract_model.pt")
    tokenizer.save_pretrained("models/tokenizer")
    with open("models/training_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", type=str, default="data/raw/resume_dataset")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--max_samples", type=int, default=1200)
    parser.add_argument("--base_model", type=str, default="distilbert-base-uncased")
    main(parser.parse_args())
