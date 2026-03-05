# SkillExtract: Deep Learning Spatial-Semantic Resume Intelligence

SkillExtract is a deep learning powered spatial-semantic resume intelligence framework for explainable, patent-aligned skill validation.

## Overview

This repository upgrades SkillExtract into a research-grade deep learning system while preserving the deterministic **Spatial-Semantic Integrity Framework**:

\[
\text{IntegrityScore} = W_{spatial} \times V_{semantic}
\]

- **`W_spatial`**: section credibility weight derived from detected resume layout region.
- **`V_semantic`**: cosine similarity between skill embedding and local context embedding.

> **Patent safety statement:** the deterministic scoring mechanism above is the core intellectual property. Deep learning models assist candidate skill detection and section understanding only; verification logic remains deterministic.

## Key Contributions

1. Layout-aware resume understanding (token + coordinates + page-level cues).
2. Transformer-based skill extraction (BIO tagging + section classification).
3. Spatial-semantic deterministic integrity scoring.
4. Explainable validation outputs (bbox + context + score) compatible with X-Ray overlays.
5. Patent-ready hybrid pipeline for reduced false skill detections.

## Deep Learning Architecture

### 1) Layout-Aware Token Encoder
Implemented in `src/dl_models/layout_model.py`:
- text token embeddings from HuggingFace encoder,
- spatial projection from bbox coordinates,
- section embedding fusion with layer normalization.

### 2) Resume Skill Detection Model
Implemented in `src/dl_models/skill_classifier.py`:
- Transformer encoder backbone,
- token classification head for BIO labels,
- section classification head,
- optional CRF decoding (`torchcrf`) fallback supported.

### 3) Contextual Skill Embedding Model
Implemented in `src/semantic_engine/embedding_model.py`:
- SentenceTransformer model: `all-mpnet-base-v2`,
- cosine similarity for semantic verification.

### 4) Integrity Scoring Engine (Patent Component)
Implemented in `src/spatial_engine/coordinate_mapper.py`:
- `V_semantic = cosine(skill_embedding, context_embedding)`
- `IntegrityScore = W_spatial × V_semantic`

Default section weights:
- Experience: `1.0`
- Skills: `0.8`
- Projects: `0.5`
- Education: `0.4`
- Hobbies/Footer: `0.2`
- Other: `0.3`

## Dataset

Primary dataset target:
- Kaggle Resume Dataset: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset

Pipeline output format (`JSONL`):
```json
{
  "tokens": ["..."] ,
  "bbox": [[0,0,10,10]],
  "section": ["experience"],
  "labels": ["B-SKILL"]
}
```

## Project Structure

```text
skillExtract/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── training/
├── inference/
│   └── predict_resume.py
├── src/
│   ├── spatial_engine/
│   │   ├── pdf_parser.py
│   │   └── coordinate_mapper.py
│   ├── semantic_engine/
│   │   └── embedding_model.py
│   ├── dl_models/
│   │   ├── layout_model.py
│   │   └── skill_classifier.py
│   └── pipeline/
│       ├── preprocess.py
│       └── dataset_builder.py
├── train_skill_extract_model.py
├── evaluate_model.py
└── README.md
```

## Training

Single training script (required):

```bash
python train_skill_extract_model.py \
  --dataset_path data/raw/resume_dataset \
  --epochs 10 \
  --batch_size 8
```

Script workflow:
1. Download dataset (if absent).
2. Preprocess resumes (cleaning + section detection + distant BIO supervision).
3. Build processed JSONL dataset.
4. Train hybrid model.
5. Evaluate model.
6. Save artifacts in `models/`.

Saved artifacts:
- `models/skill_extract_model.pt`
- `models/tokenizer/`
- `models/training_metrics.json`

## Evaluation Metrics

`train_skill_extract_model.py` outputs:
- Precision
- Recall
- F1 Score
- False Positive Rate
- Integrity Score Distribution (mean/std)
- False skill detection reduction vs baseline

## Inference

```bash
python inference/predict_resume.py resume.pdf
```

Inference pipeline steps:
1. Parse PDF tokens + bounding boxes.
2. Detect skill candidates.
3. Build local context window.
4. Compute SentenceTransformer embeddings.
5. Apply section-based spatial weight.
6. Compute deterministic integrity score.
7. Return explainable JSON output.

Example output:
```json
{
  "skills": [
    {
      "skill": "Python",
      "section": "experience",
      "semantic_similarity": 0.91,
      "spatial_weight": 1.0,
      "integrity_score": 0.91
    }
  ]
}
```

## Explainability and X-Ray Dashboard Compatibility

The explainability concept remains unchanged:
- backend surfaces bounding boxes,
- context snippets,
- deterministic integrity scores.

Frontend PDF overlays can continue visualizing the same evidence objects, preserving invention-aligned explainable auditability.

## Dependencies

Core stack:
- PyTorch
- HuggingFace Transformers
- SentenceTransformers
- pdfplumber
- FastAPI
- scikit-learn
