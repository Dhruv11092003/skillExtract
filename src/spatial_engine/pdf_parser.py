from pathlib import Path
from typing import List

import pdfplumber


def extract_pdf_tokens(pdf_path: str) -> List[dict]:
    tokens = []
    with pdfplumber.open(Path(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words() or []
            for w in words:
                tokens.append(
                    {
                        "text": w.get("text", ""),
                        "bbox": [int(w.get("x0", 0)), int(w.get("top", 0)), int(w.get("x1", 0)), int(w.get("bottom", 0))],
                        "page": page_idx,
                    }
                )
    return tokens
