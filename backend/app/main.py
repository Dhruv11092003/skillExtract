from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import AnalyzeResponse, HealthResponse, SkillResult
from app.services.contextual_verifier import ContextualVerifier, coordinate_weight, integrity_score
from app.services.spatial_extractor import SpatialExtractor

app = FastAPI(title=settings.app_name, version=settings.app_version)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = SpatialExtractor()
verifier = ContextualVerifier(settings.semantic_model_name)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_skills: str = Form(default=""),
) -> AnalyzeResponse:
    filename = (resume.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    skills = [s.strip() for s in (job_skills or settings.default_required_skills).split(",") if s.strip()]
    if not skills:
        raise HTTPException(status_code=400, detail="No skills provided for verification.")

    try:
        with NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
            temp_pdf.write(content)
            temp_pdf.flush()
            parsed = extractor.extract(Path(temp_pdf.name))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to parse PDF: {exc}") from exc

    if not parsed.tokens:
        raise HTTPException(status_code=422, detail="No text detected in PDF. Please upload text-based PDF.")

    lowered_tokens = [token.text.lower() for token in parsed.tokens]
    results: list[SkillResult] = []

    for skill in skills:
        skill_key = skill.lower()
        hit_index = next((i for i, token in enumerate(lowered_tokens) if token == skill_key), None)
        if hit_index is None:
            hit_index = next((i for i, token in enumerate(lowered_tokens) if skill_key in token), None)

        if hit_index is None:
            continue

        token = parsed.tokens[hit_index]
        page_width, page_height = parsed.page_sizes.get(token.coordinate.page, (1.0, 1.0))
        section = extractor.classify_section(token.coordinate.y0, page_height)
        snippet = extractor.context(parsed.tokens, hit_index, settings.context_window_size)
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

    results.sort(key=lambda item: item.confidence_score, reverse=True)

    return AnalyzeResponse(
        skills=results,
        total_detected=len(results),
        model=settings.semantic_model_name,
    )
