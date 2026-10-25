"""
Page-Aware Clinical Document Chunker
Segments medical reports into semantic passages while preserving essential grounding metadata:
- patient_id (tenant isolation)
- report_name
- report_date
- page_number
"""

import re
import uuid
from typing import List, Dict, Any
from ..schemas.rag_schema import DocumentChunk


class ClinicalDocumentChunker:
    """
    Splits clinical reports into overlapping semantic passages.
    Every chunk retains report name, date, and exact page number for citations.
    """

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_page(
        self,
        page_text: str,
        page_number: int,
        document_id: str,
        patient_id: str,
        report_name: str,
        report_date: str,
        category: str = "LAB_REPORT",
    ) -> List[DocumentChunk]:
        """
        Chunks text from a single page into metadata-rich DocumentChunk objects.
        """
        clean_text = re.sub(r"[ \t]+", " ", page_text.strip())
        if not clean_text:
            return []

        # Split on paragraph boundaries first
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if p.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk_words: List[str] = []
        current_length = 0

        for para in paragraphs:
            words = para.split()
            for word in words:
                current_chunk_words.append(word)
                current_length += len(word) + 1

                if current_length >= self.chunk_size:
                    chunk_str = " ".join(current_chunk_words)
                    chunk_id = f"chk_{uuid.uuid4().hex[:12]}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            patient_id=patient_id,
                            report_name=report_name,
                            report_date=report_date,
                            page_number=page_number,
                            text=chunk_str,
                            category=category,
                        )
                    )
                    # Maintain overlap
                    overlap_words = current_chunk_words[-max(5, self.chunk_overlap // 7):]
                    current_chunk_words = list(overlap_words)
                    current_length = sum(len(w) + 1 for w in current_chunk_words)

        if current_chunk_words:
            chunk_str = " ".join(current_chunk_words)
            chunk_id = f"chk_{uuid.uuid4().hex[:12]}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    patient_id=patient_id,
                    report_name=report_name,
                    report_date=report_date,
                    page_number=page_number,
                    text=chunk_str,
                    category=category,
                )
            )

        return chunks

    def chunk_document(
        self,
        document_id: str,
        patient_id: str,
        report_name: str,
        report_date: str,
        pages: List[Dict[str, Any]],
        category: str = "LAB_REPORT",
    ) -> List[DocumentChunk]:
        """
        Chunks an entire multi-page document across all pages.
        """
        all_chunks: List[DocumentChunk] = []
        for p in pages:
            page_num = p.get("page_number", 1)
            page_text = p.get("text", "")
            page_chunks = self.chunk_page(
                page_text=page_text,
                page_number=page_num,
                document_id=document_id,
                patient_id=patient_id,
                report_name=report_name,
                report_date=report_date,
                category=category,
            )
            all_chunks.extend(page_chunks)
        return all_chunks
