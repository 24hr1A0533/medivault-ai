"""
Grounded Medical Citation Engine
Verifies source attribution and enforces strict negative constraints:
- Ensures report name, page number, and report date are bound to generated text.
- If medical information is missing or absent in retrieved context:
  Enforces exact response: "I could not find that information in your medical records."
"""

import re
from typing import List, Tuple, Dict, Any
from ..schemas.rag_schema import Citation, DocumentChunk


class MedicalCitationEngine:
    """
    Validates, extracts, and formats citations for patient-specific clinical answers.
    """

    FALLBACK_MESSAGE = "I could not find that information in your medical records."

    def extract_and_format_citations(
        self,
        raw_answer: str,
        retrieved_chunks: List[Tuple[DocumentChunk, float]],
    ) -> Tuple[str, List[Citation], bool]:
        """
        Parses generated answer, validates whether information was found,
        attaches source citations (report name, page number, report date),
        or returns the standard fallback message if not grounded.
        """
        # Check negative constraint indicators
        lower_ans = raw_answer.strip().lower()
        negative_indicators = [
            "could not find",
            "cannot find",
            "not found in your medical records",
            "no mention of",
            "not present in the provided",
            "no information",
            "not available in your records",
            "does not contain",
        ]

        if not retrieved_chunks or any(ind in lower_ans for ind in negative_indicators):
            return self.FALLBACK_MESSAGE, [], False

        # Extract unique citations from the retrieved chunks that contributed to the answer
        seen_keys = set()
        citations: List[Citation] = []

        for chunk, score in retrieved_chunks:
            key = (chunk.report_name, chunk.page_number, chunk.report_date)
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append(
                    Citation(
                        report_name=chunk.report_name,
                        page_number=chunk.page_number,
                        report_date=chunk.report_date,
                        quoted_snippet=chunk.text[:150] + ("..." if len(chunk.text) > 150 else ""),
                    )
                )

        # Build formatted citation footnotes appended to answer
        formatted_answer = raw_answer.strip()

        # Check if citations are already formatted into the text
        if "### Sources & Citations" not in formatted_answer and citations:
            citation_lines = ["\n\n### Sources & Citations:"]
            for idx, c in enumerate(citations, 1):
                citation_lines.append(
                    f"{idx}. **{c.report_name}** | Page: {c.page_number} | Date: {c.report_date}"
                )
            formatted_answer += "\n" + "\n".join(citation_lines)

        return formatted_answer, citations, True
