"""
HL7 Message Router and ACK Generator.
Dispatches incoming messages to appropriate parsers and constructs MLLP ACK replies.
"""

from typing import Tuple, Any, Dict
from datetime import datetime, timezone
from .adt_parser import HL7ADTParser, ADTEvent
from .oru_parser import HL7ORUParser, ORUObservation
from .mdm_parser import HL7MDMParser, MDMDocument


class HL7MessageRouter:
    """Routes HL7 v2 messages and generates compliant HL7 ACK replies."""

    @staticmethod
    def generate_ack(control_id: str, ack_code: str = "AA", error_text: str = "") -> str:
        """Constructs an HL7 MSA Acknowledgement message."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        msh = f"MSH|^~\\&|MEDIVAULT_HOS|HOSPITAL_SYS|EPIC_EHR|EPIC_FACILITY|{timestamp}||ACK|{control_id}|P|2.5"
        msa = f"MSA|{ack_code}|{control_id}"
        if error_text:
            msa += f"|{error_text}"
        return f"{msh}\r{msa}\r"

    @classmethod
    def route_message(cls, raw_message: str) -> Tuple[str, Any, str]:
        """
        Parses and routes raw message.
        Returns: (message_category, parsed_object, ack_message)
        """
        cleaned = raw_message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in cleaned.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty HL7 message.")

        msh_line = lines[0]
        parts = msh_line.split("|")
        if parts[0] != "MSH":
            raise ValueError("First line must be MSH segment.")

        msg_type_field = parts[8] if len(parts) > 8 else "ADT^A01"
        control_id = parts[9] if len(parts) > 9 else "UNKNOWN_ID"
        category = msg_type_field.split("^")[0]

        try:
            if category == "ADT":
                parsed = HL7ADTParser.parse(raw_message)
            elif category == "ORU":
                parsed = HL7ORUParser.parse(raw_message)
            elif category == "MDM":
                parsed = HL7MDMParser.parse(raw_message)
            else:
                # Default pass-through
                parsed = {"raw": raw_message, "category": category}

            ack = cls.generate_ack(control_id, ack_code="AA")
            return category, parsed, ack
        except Exception as e:
            ack_err = cls.generate_ack(control_id, ack_code="AE", error_text=str(e))
            raise RuntimeError(f"HL7 Routing error: {str(e)}") from e
