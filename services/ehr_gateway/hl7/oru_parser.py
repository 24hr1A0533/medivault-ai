"""
HL7 v2.x ORU (Observation Result / Lab Report) Message Parser.
Parses OBR (Observation Request) and OBX (Observation Segment) lines for laboratory panels.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabResultItem:
    set_id: str
    value_type: str  # NM (Numeric), ST (String), TX (Text)
    identifier: str  # e.g., 2345-7^GLUCOSE^LN
    code: str
    name: str
    value: str
    units: str
    reference_range: str
    abnormal_flag: Optional[str] = None  # H (High), L (Low), A (Abnormal), LL (Panic Low), HH (Panic High)
    result_status: str = "F"  # F (Final), P (Preliminary)


@dataclass
class ORUObservation:
    message_control_id: str
    mrn: str
    order_number: str
    universal_service_id: str
    results: List[LabResultItem] = field(default_factory=list)


class HL7ORUParser:
    """Parses ORU_R01 messages into structured lab result items."""

    @staticmethod
    def parse(raw_message: str) -> ORUObservation:
        cleaned = raw_message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in cleaned.strip().split("\n") if line.strip()]
        control_id = "UNKNOWN"
        mrn = "UNKNOWN"
        order_num = "UNKNOWN"
        service_id = "LAB_PANEL"
        items: List[LabResultItem] = []

        for line in lines:
            parts = line.split("|")
            seg = parts[0]
            if seg == "MSH":
                control_id = parts[9] if len(parts) > 9 else "UNKNOWN"
            elif seg == "PID":
                mrn = parts[3].split("^")[0] if len(parts) > 3 else "UNKNOWN"
            elif seg == "OBR":
                order_num = (parts[3] if len(parts) > 3 and parts[3] else parts[2]) if len(parts) > 2 else "UNKNOWN"
                service_id = parts[4] if len(parts) > 4 else "LAB_PANEL"
            elif seg == "OBX":
                # OBX-1 Set ID, OBX-2 Type, OBX-3 Identifier (Code^Name^System), OBX-5 Value,
                # OBX-6 Units, OBX-7 Range, OBX-8 Flag, OBX-11 Status
                set_id = parts[1] if len(parts) > 1 else "1"
                val_type = parts[2] if len(parts) > 2 else "NM"
                raw_code = parts[3] if len(parts) > 3 else "000^TEST^LN"
                code_parts = raw_code.split("^")
                code = code_parts[0] if len(code_parts) > 0 else "000"
                name = code_parts[1] if len(code_parts) > 1 else "TEST"
                val = parts[5] if len(parts) > 5 else "0"
                units = parts[6] if len(parts) > 6 else ""
                ref_range = parts[7] if len(parts) > 7 else ""
                flag = parts[8] if len(parts) > 8 and parts[8] else None
                status = parts[11] if len(parts) > 11 else "F"

                items.append(
                    LabResultItem(
                        set_id=set_id,
                        value_type=val_type,
                        identifier=raw_code,
                        code=code,
                        name=name,
                        value=val,
                        units=units,
                        reference_range=ref_range,
                        abnormal_flag=flag,
                        result_status=status,
                    )
                )

        return ORUObservation(
            message_control_id=control_id,
            mrn=mrn,
            order_number=order_num,
            universal_service_id=service_id,
            results=items,
        )
