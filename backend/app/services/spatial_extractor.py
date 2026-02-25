from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from app.schemas import Coordinate, SpatialToken


@dataclass
class ParsedDocument:
    tokens: list[SpatialToken]
    page_sizes: dict[int, tuple[float, float]]

    @property
    def full_text(self) -> str:
        return " ".join(t.text for t in self.tokens)


class SpatialExtractor:
    def extract(self, pdf_path: str | Path) -> ParsedDocument:
        tokens: list[SpatialToken] = []
        page_sizes: dict[int, tuple[float, float]] = {}

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                page_width = float(page.width or 1.0)
                page_height = float(page.height or 1.0)
                page_sizes[page_index] = (page_width, page_height)
                for word in page.extract_words() or []:
                    text = (word.get("text") or "").strip()
                    if not text:
                        continue
                    tokens.append(
                        SpatialToken(
                            text=text,
                            coordinate=Coordinate(
                                x0=float(word.get("x0", 0.0)),
                                y0=float(word.get("top", 0.0)),
                                x1=float(word.get("x1", 0.0)),
                                y1=float(word.get("bottom", 0.0)),
                                page_width=page_width,
                                page_height=page_height,
                                page=page_index,
                            ),
                        )
                    )

        return ParsedDocument(tokens=tokens, page_sizes=page_sizes)

    @staticmethod
    def classify_section(y0: float, page_height: float) -> str:
        ratio = y0 / max(page_height, 1.0)
        if ratio <= 0.18:
            return "header"
        if ratio >= 0.84:
            return "footer"
        return "body"

    @staticmethod
    def context(tokens: list[SpatialToken], index: int, window: int) -> str:
        start = max(0, index - window)
        end = min(len(tokens), index + window + 1)
        return " ".join(token.text for token in tokens[start:end])
