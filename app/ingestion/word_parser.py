from __future__ import annotations

from dataclasses import dataclass, field

import docx


@dataclass
class ParsedParagraph:
    text: str
    section_heading: str | None  # nearest Heading 1/2 above this paragraph
    style: str                   # original Word style name


class WordParser:
    """
    Reads a .docx file and returns a flat list of paragraphs.
    Each paragraph carries the section heading it belongs to,
    which becomes metadata when the text is later chunked and embedded.
    """

    def parse(self, file_path: str) -> list[ParsedParagraph]:
        doc = docx.Document(file_path)
        paragraphs: list[ParsedParagraph] = []
        current_heading: str | None = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style = para.style.name
            if style.startswith("Heading"):
                current_heading = text
                # Include heading as its own paragraph so it gets embedded too
                paragraphs.append(
                    ParsedParagraph(text=text, section_heading=None, style=style)
                )
            else:
                paragraphs.append(
                    ParsedParagraph(
                        text=text,
                        section_heading=current_heading,
                        style=style,
                    )
                )

        return paragraphs
