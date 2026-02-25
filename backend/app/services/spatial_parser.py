from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pdfplumber

from app.schemas import ParsedDocument, WordBox


class CoordinateAwareParser:
    """Extract text with geometry so layout can affect confidence scoring."""

    def parse_pdf(self, pdf_path: str | Path) -> ParsedDocument:
        words: list[WordBox] = []
        ordered_text: list[str] = []

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                page_height = float(page.height or 1.0)
                for word in page.extract_words() or []:
                    token = (word.get("text") or "").strip()
                    if not token:
                        continue

                    top = float(word.get("top", 0.0))
                    section = self._section_from_vertical_position(top, page_height)
                    words.append(
                        WordBox(
                            text=token,
                            x0=float(word.get("x0", 0.0)),
                            x1=float(word.get("x1", 0.0)),
                            top=top,
                            bottom=float(word.get("bottom", top)),
                            section=section,
                        )
                    )
                    ordered_text.append(token)

        return ParsedDocument(words=words, full_text=" ".join(ordered_text))

    @staticmethod
    def _section_from_vertical_position(top: float, page_height: float) -> str:
        y_ratio = top / max(page_height, 1.0)
        if y_ratio <= 0.18:
            return "header"
        if y_ratio >= 0.85:
            return "footer"
        return "body"

    @staticmethod
    def surrounding_context(tokens: Iterable[str], center_index: int, window: int = 50) -> str:
        token_list = list(tokens)
        start = max(0, center_index - window)
        end = min(len(token_list), center_index + window + 1)
        return " ".join(token_list[start:end])
