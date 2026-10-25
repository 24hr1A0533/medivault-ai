"""
HL7 v2.x MDM (Medical Document Management) Message Parser.
Extracts clinical consultation notes, history & physicals, and discharge summaries.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MDMDocument:
    message_control_id: str
    mrn: str
    document_type: str  # e.g., DISCHARGE_SUMMARY, HP_NOTE, CONSULTATION
    document_date: str
    author_name: str
    document_text: str
    raw_segments: Dict[str, List[str]] = field(default_factory=dict)


class HL7MDMParser:
    """Parses MDM_T02 clinical documentation messages."""

    @staticmethod
    def parse(raw_message: str) -> MDMDocument:
        cleaned = raw_message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in cleaned.strip().split("\n") if line.strip()]
        control_id = "UNKNOWN"
        mrn = "UNKNOWN"
        doc_type = "CLINICAL_NOTE"
        doc_date = ""
        author = "STAFF_PHYSICIAN"
        text_lines: List[str] = []
        segments: Dict[str, List[str]] = {}

        for line in lines:
            parts = line.split("|")
            seg = parts[0]
            segments[seg] = parts
            if seg == "MSH":
                control_id = parts[9] if len(parts) > 9 else "UNKNOWN"
            elif seg == "PID":
                mrn = parts[3].split("^")[0] if len(parts) > 3 else "UNKNOWN"
            elif seg == "TXA":
                # TXA-2 Doc Type, TXA-4 Date, TXA-9 Primary Author
                doc_type = parts[2] if len(parts) > 2 else "CLINICAL_NOTE"
                doc_date = parts[4] if len(parts) > 4 else ""
                author = parts[9].replace("^", " ") if len(parts) > 9 else "STAFF_PHYSICIAN"
            elif seg == "OBX":
                # Text content in OBX-5
                if len(parts) > 5:
                    text_lines.append(parts[5].replace("\\.br\\", "\n"))

        return MDMDocument(
            message_control_id=control_id,
            mrn=mrn,
            document_type=doc_type,
            document_date=doc_date,
            author_name=author,
            document_text="\n".join(text_lines),
            raw_segments=segments,
        )
