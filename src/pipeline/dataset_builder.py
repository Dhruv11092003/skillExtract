import json
from pathlib import Path
from typing import List

import pandas as pd

from src.pipeline.preprocess import preprocess_resume


def _find_resume_column(df: pd.DataFrame) -> str:
    candidates = ["Resume", "resume", "text", "Text", "cleaned_resume"]
    for col in candidates:
        if col in df.columns:
            return col
    return df.columns[0]


def build_processed_jsonl(dataset_path: str, output_path: str, max_samples: int | None = None) -> Path:
    dataset_path = Path(dataset_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    csv_files = list(dataset_path.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {dataset_path}")

    df = pd.read_csv(csv_files[0])
    resume_col = _find_resume_column(df)
    rows = df[resume_col].dropna().tolist()
    if max_samples:
        rows = rows[:max_samples]

    with output_path.open("w", encoding="utf-8") as f:
        for text in rows:
            sample = preprocess_resume(str(text))
            record = {
                "tokens": sample.tokens,
                "bbox": sample.bboxes,
                "section": sample.sections,
                "labels": sample.labels,
            }
            f.write(json.dumps(record) + "\n")
    return output_path


def load_jsonl(path: str) -> List[dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data
