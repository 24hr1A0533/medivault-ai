"""
HL7 v2.x ADT (Admission, Discharge, Transfer) Message Parser.
Extracts patient demographics from PID segments and visit details from PV1 segments.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ADTEvent:
    message_control_id: str
    event_type: str  # A01 (Admit), A04 (Registration), A08 (Update), A03 (Discharge)
    mrn: str
    patient_family_name: str
    patient_given_name: str
    date_of_birth: str
    gender: str
    patient_class: str  # I (Inpatient), O (Outpatient), E (Emergency)
    assigned_location: str
    attending_doctor: str
    raw_segments: Dict[str, List[str]] = field(default_factory=dict)


class HL7ADTParser:
    """Parses standard ER7 (pipe-and-hat delimited) ADT messages."""

    @staticmethod
    def parse(raw_message: str) -> ADTEvent:
        cleaned = raw_message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in cleaned.strip().split("\n") if line.strip()]
        segments: Dict[str, List[str]] = {}

        for line in lines:
            parts = line.split("|")
            seg_name = parts[0]
            segments[seg_name] = parts

        msh = segments.get("MSH", [])
        evn = segments.get("EVN", [])
        pid = segments.get("PID", [])
        pv1 = segments.get("PV1", [])

        if not msh:
            raise ValueError("Invalid HL7 message: Missing MSH segment.")

        # In MSH, field index 9 is Message Type (ADT^A01), field index 10 is Message Control ID
        msg_type_field = msh[8] if len(msh) > 8 else "ADT^A01"
        event_type = msg_type_field.split("^")[-1] if "^" in msg_type_field else msg_type_field
        control_id = msh[9] if len(msh) > 9 else "UNKNOWN_ID"

        # PID parsing: PID-3 = MRN, PID-5 = Family^Given, PID-7 = DOB, PID-8 = Gender
        mrn = pid[3].split("^")[0] if len(pid) > 3 else "UNKNOWN_MRN"
        name_parts = pid[5].split("^") if len(pid) > 5 else ["DOE", "JOHN"]
        family_name = name_parts[0] if len(name_parts) > 0 else ""
        given_name = name_parts[1] if len(name_parts) > 1 else ""
        dob = pid[7] if len(pid) > 7 else ""
        gender = pid[8] if len(pid) > 8 else "U"

        # PV1 parsing: PV1-2 = Patient Class, PV1-3 = Assigned Location, PV1-7 = Attending Doctor
        patient_class = pv1[2] if len(pv1) > 2 else "E"
        location = pv1[3] if len(pv1) > 3 else "ROOM-1"
        attending = pv1[7].replace("^", " ") if len(pv1) > 7 else "STAFF_PHYSICIAN"

        return ADTEvent(
            message_control_id=control_id,
            event_type=event_type,
            mrn=mrn,
            patient_family_name=family_name,
            patient_given_name=given_name,
            date_of_birth=dob,
            gender=gender,
            patient_class=patient_class,
            assigned_location=location,
            attending_doctor=attending,
            raw_segments=segments,
        )
