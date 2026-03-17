from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import settings
from app.ingestion.word_parser import ParsedParagraph


class TextChunker:
    """
    Splits parsed paragraphs into embeddable LangChain Documents.
    Every chunk carries client_id, source_doc, and section_heading in metadata
    so that vector search can filter by client and cite the source.
    """

    def __init__(self) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(
        self,
        paragraphs: list[ParsedParagraph],
        client_id: str,
        source_doc: str,
    ) -> list[Document]:
        """
        Returns a flat list of LangChain Documents ready to embed and store.
        """
        docs: list[Document] = []
        for para in paragraphs:
            base_metadata = {
                "client_id": client_id,
                "source_doc": source_doc,
                "section_heading": para.section_heading or "",
                "style": para.style,
            }
            chunks = self._splitter.create_documents(
                texts=[para.text],
                metadatas=[base_metadata],
            )
            docs.extend(chunks)
        return docs
