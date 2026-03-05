import re
from dataclasses import dataclass
from typing import Dict, List

SECTION_PATTERNS = {
    "experience": re.compile(r"\b(experience|work history|employment)\b", re.I),
    "skills": re.compile(r"\b(skills|technical skills|core competencies)\b", re.I),
    "projects": re.compile(r"\b(projects|project experience)\b", re.I),
    "education": re.compile(r"\b(education|academic)\b", re.I),
    "hobbies": re.compile(r"\b(hobbies|interests|activities)\b", re.I),
}

SPATIAL_WEIGHTS = {
    "experience": 1.0,
    "skills": 0.8,
    "projects": 0.5,
    "education": 0.4,
    "hobbies": 0.2,
    "other": 0.3,
}

DEFAULT_SKILL_LEXICON = {
    "python", "java", "c++", "sql", "pytorch", "tensorflow", "docker", "kubernetes",
    "aws", "azure", "nlp", "machine learning", "deep learning", "transformers", "fastapi",
}


@dataclass
class ResumeSample:
    tokens: List[str]
    sections: List[str]
    labels: List[str]
    bboxes: List[List[int]]


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\b[\w.-]+@[\w.-]+\.\w+\b", " ", text)
    text = re.sub(r"\+?\d[\d\s\-()]{8,}\d", " ", text)
    text = re.sub(r"[^\w\s\n\-+/.:]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_sections(lines: List[str]) -> List[str]:
    current = "other"
    sections = []
    for line in lines:
        for section_name, pattern in SECTION_PATTERNS.items():
            if pattern.search(line):
                current = section_name
                break
        sections.append(current)
    return sections


def tokenize_with_sections(text: str) -> Dict[str, List[str]]:
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    line_sections = detect_sections(lines)
    tokens, sections = [], []
    for line, section in zip(lines, line_sections):
        line_tokens = line.split()
        tokens.extend(line_tokens)
        sections.extend([section] * len(line_tokens))
    return {"tokens": tokens, "sections": sections}


def build_bio_labels(tokens: List[str], skill_lexicon: set | None = None) -> List[str]:
    lex = skill_lexicon or DEFAULT_SKILL_LEXICON
    labels = ["O"] * len(tokens)
    i = 0
    while i < len(tokens):
        matched = False
        for span in (3, 2, 1):
            if i + span > len(tokens):
                continue
            phrase = " ".join(t.lower() for t in tokens[i:i + span])
            if phrase in lex:
                labels[i] = "B-SKILL"
                for j in range(i + 1, i + span):
                    labels[j] = "I-SKILL"
                i += span
                matched = True
                break
        if not matched:
            i += 1
    return labels


def create_dummy_bboxes(tokens: List[str], line_width: int = 1000, line_height: int = 40) -> List[List[int]]:
    bboxes = []
    cursor_x, cursor_y = 0, 0
    for token in tokens:
        token_w = min(180, 20 + 10 * len(token))
        x0, y0 = cursor_x, cursor_y
        x1, y1 = min(line_width, cursor_x + token_w), cursor_y + line_height
        bboxes.append([x0, y0, x1, y1])
        cursor_x += token_w + 10
        if cursor_x > line_width - 200:
            cursor_x = 0
            cursor_y += line_height + 10
    return bboxes


def preprocess_resume(text: str, skill_lexicon: set | None = None) -> ResumeSample:
    cleaned = clean_text(text)
    tokenized = tokenize_with_sections(cleaned)
    labels = build_bio_labels(tokenized["tokens"], skill_lexicon)
    bboxes = create_dummy_bboxes(tokenized["tokens"])
    return ResumeSample(
        tokens=tokenized["tokens"],
        sections=tokenized["sections"],
        labels=labels,
        bboxes=bboxes,
    )
