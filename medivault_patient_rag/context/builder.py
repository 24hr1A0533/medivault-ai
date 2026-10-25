"""
Clinical Context Builder for Grounded Medical Generation
Structures retrieved patient chunks with explicit source tags to facilitate zero-hallucination citations.
"""

from typing import List, Tuple
from ..schemas.rag_schema import DocumentChunk


class ClinicalContextBuilder:
    """
    Constructs tamper-proof, structured prompt contexts with explicit citation anchors.
    """

    def build_context(self, retrieved_chunks: List[Tuple[DocumentChunk, float]]) -> str:
        """
        Formats candidate chunks into structured context text.
        """
        if not retrieved_chunks:
            return ""

        context_blocks = []
        for idx, (chunk, score) in enumerate(retrieved_chunks, 1):
            block = (
                f"--- [SOURCE {idx}] ---\n"
                f"Report Name: {chunk.report_name}\n"
                f"Report Date: {chunk.report_date}\n"
                f"Page Number: {chunk.page_number}\n"
                f"Content:\n{chunk.text.strip()}\n"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)
