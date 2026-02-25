from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.schemas import AnalyzeResponse, RankingInput
from app.services.patent_ranking import PatentRankingEngine
from app.services.spatial_parser import CoordinateAwareParser
from app.services.verifier_engine import SemanticVerifier, infer_spatial_weight

app = FastAPI(title="SkillExtract AI", version="1.0.0")

parser = CoordinateAwareParser()
verifier = SemanticVerifier()
ranker = PatentRankingEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "SkillExtract AI"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_skills: str = Form("Python,FastAPI,React,Django,SQL"),
) -> AnalyzeResponse:
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    requested_skills = [s.strip() for s in job_skills.split(",") if s.strip()]
    if not requested_skills:
        raise HTTPException(status_code=400, detail="Provide at least one job skill.")

    suffix = Path(resume.filename).suffix or ".pdf"
    with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
        tmp.write(await resume.read())
        tmp.flush()
        parsed = parser.parse_pdf(tmp.name)

    tokens = [w.text for w in parsed.words]
    evidences = []
    ranking_inputs = []

    lowered = [t.lower() for t in tokens]
    for skill in requested_skills:
        skill_token = skill.lower()
        if skill_token in lowered:
            idx = lowered.index(skill_token)
            context = parser.surrounding_context(tokens, idx, window=50)
            word = parsed.words[idx]
            spatial_weight = infer_spatial_weight(word)
            evidence = verifier.build_evidence(skill, context, word.section, spatial_weight)
        else:
            context = parsed.full_text[:400]
            evidence = verifier.build_evidence(skill, context, "body", 0.2)

        evidences.append(evidence)
        ranking_inputs.append(
            RankingInput(
                skill=evidence.skill,
                importance=1.0,
                confidence=evidence.confidence,
                spatial_weight=evidence.spatial_weight,
            )
        )

    ranked, total = ranker.rank(ranking_inputs)
    return AnalyzeResponse(
        extracted_skills=evidences,
        ranked_skills=ranked,
        total_score=total,
        notes="TRL-4 prototype with spatial-semantic verification and weighted ranking.",
    )
