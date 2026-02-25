from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import AnalyzeResponse, HealthResponse, SkillResult
from app.services.contextual_verifier import (
    ContextualVerifier,
    coordinate_weight,
    integrity_score,
)
from app.services.spatial_extractor import SpatialExtractor


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# -------------------- CORS --------------------
origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Services --------------------
extractor = SpatialExtractor()
verifier = ContextualVerifier(settings.semantic_model_name)


# -------------------- Health Check --------------------
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
    )


# -------------------- Helper --------------------
def _persist_upload_bytes(pdf_bytes: bytes) -> Path:
    """
    Persist upload bytes to a closed temp file path.

    Using NamedTemporaryFile(delete=True) can fail on Windows because
    the open handle prevents a second open by pdfplumber.
    mkstemp closes safely and is cross-platform.
    """
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")

    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(pdf_bytes)
    except Exception:
        os.close(fd)
        raise

    return Path(temp_path)


# -------------------- Resume Analyzer --------------------
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_skills: str = Form(default=""),
) -> AnalyzeResponse:

    filename = (resume.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only .pdf files are supported.",
        )

    content = await resume.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty.",
        )

    # Parse required skills
    skills = [
        s.strip()
        for s in (job_skills or settings.default_required_skills).split(",")
        if s.strip()
    ]

    if not skills:
        raise HTTPException(
            status_code=400,
            detail="No skills provided for verification.",
        )

    temp_path: Path | None = None

    try:
        temp_path = _persist_upload_bytes(content)
        parsed = extractor.extract(temp_path)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to parse PDF: {exc}",
        ) from exc

    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    if not parsed.tokens:
        raise HTTPException(
            status_code=422,
            detail="No text detected in PDF. Please upload text-based PDF.",
        )

    lowered_tokens = [token.text.lower() for token in parsed.tokens]
    results: list[SkillResult] = []

    for skill in skills:
        skill_key = skill.lower()

        # Exact match
        hit_index = next(
            (i for i, token in enumerate(lowered_tokens) if token == skill_key),
            None,
        )

        # Partial match fallback
        if hit_index is None:
            hit_index = next(
                (i for i, token in enumerate(lowered_tokens) if skill_key in token),
                None,
            )

        if hit_index is None:
            continue

        token = parsed.tokens[hit_index]

        _, page_height = parsed.page_sizes.get(
            token.coordinate.page,
            (1.0, 1.0),
        )

        section = extractor.classify_section(
            token.coordinate.y0,
            page_height,
        )

        snippet = extractor.context(
            parsed.tokens,
            hit_index,
            settings.context_window_size,
        )

        semantic_similarity = verifier.similarity(skill, snippet)
        c_weight = coordinate_weight(section)
        confidence = integrity_score(c_weight, semantic_similarity)

        results.append(
            SkillResult(
                skill=skill,
                coordinates=token.coordinate,
                confidence_score=confidence,
                semantic_similarity=semantic_similarity,
                coordinate_weight=c_weight,
                evidence_snippet=snippet[:400],
                section=section,
            )
        )

    results.sort(
        key=lambda item: item.confidence_score,
        reverse=True,
    )

    return AnalyzeResponse(
        skills=results,
        total_detected=len(results),
        model=settings.semantic_model_name,
    )