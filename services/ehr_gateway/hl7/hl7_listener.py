"""
HL7 MLLP (Minimal Lower Layer Protocol) Listener.
Implements TCP frame unwrapping (0x0B Start Block, 0x1C 0x0D End Block)
and bidirectional ACK return over port 2575.
"""

import asyncio
from typing import Optional, Callable
from .hl7_router import HL7MessageRouter
from .hl7_event_service import HL7EventService


START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c\x0d"


class HL7MLLPListener:
    """Manages MLLP protocol frame stripping and message routing."""

    def __init__(self, event_service: Optional[HL7EventService] = None):
        self.router = HL7MessageRouter()
        self.event_service = event_service or HL7EventService()
        self.is_running = False

    def wrap_mllp(self, text: str) -> bytes:
        """Encloses HL7 message string in standard MLLP envelope."""
        return START_BLOCK + text.encode("utf-8") + END_BLOCK

    def unwrap_mllp(self, data: bytes) -> str:
        """Strips MLLP header and trailer bytes to return raw HL7 text."""
        cleaned = data
        if cleaned.startswith(START_BLOCK):
            cleaned = cleaned[1:]
        if cleaned.endswith(END_BLOCK):
            cleaned = cleaned[:-2]
        return cleaned.decode("utf-8", errors="replace")

    def process_incoming_frame(self, raw_bytes: bytes) -> bytes:
        """Processes a single incoming MLLP packet and returns MLLP ACK frame."""
        hl7_text = self.unwrap_mllp(raw_bytes)
        category, parsed, ack_text = self.router.route_message(hl7_text)

        # Broadcast via event service
        if category == "ADT":
            self.event_service.publish_adt(parsed)
        elif category == "ORU":
            self.event_service.publish_oru(parsed)
        elif category == "MDM":
            self.event_service.publish_mdm(parsed)

        return self.wrap_mllp(ack_text)
