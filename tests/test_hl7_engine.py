"""
Unit and Integration Tests for HL7 v2.x Engine.
Tests ADT admission parsing, ORU lab parsing, MDM clinical notes,
MLLP TCP frame stripping, ACK responses, and event broadcasting.
"""

import pytest
from services.ehr_gateway.hl7.adt_parser import HL7ADTParser
from services.ehr_gateway.hl7.oru_parser import HL7ORUParser
from services.ehr_gateway.hl7.mdm_parser import HL7MDMParser
from services.ehr_gateway.hl7.hl7_router import HL7MessageRouter
from services.ehr_gateway.hl7.hl7_listener import HL7MLLPListener
from services.ehr_gateway.hl7.hl7_event_service import HL7EventService


SAMPLE_ADT_A01 = (
    "MSH|^~\\&|EPIC|FACILITY|MEDIVAULT|HOSPITAL|20261024120000||ADT^A01|MSG00101|P|2.5\r"
    "EVN|A01|20261024120000\r"
    "PID|1||MRN8920192^^^HOSPITAL^MR||DOE^JOHN^A||19680412|M\r"
    "PV1|1|I|RESUS-01^BED1^ED||||DR_JENKINS^SARAH\r"
)

SAMPLE_ORU_R01 = (
    "MSH|^~\\&|LAB_SYS|FACILITY|MEDIVAULT|HOSPITAL|20261024120500||ORU^R01|MSG00102|P|2.5\r"
    "PID|1||MRN8920192||DOE^JOHN\r"
    "OBR|1||ORD991|2345-7^GLUCOSE_PANEL\r"
    "OBX|1|NM|2345-7^GLUCOSE^LN||104|mg/dL|70-99|H|||F\r"
    "OBX|2|NM|4548-4^HBA1C^LN||6.3|%|<5.7|H|||F\r"
)

SAMPLE_MDM_T02 = (
    "MSH|^~\\&|NOTES_SYS|FACILITY|MEDIVAULT|HOSPITAL|20261024121000||MDM^T02|MSG00103|P|2.5\r"
    "PID|1||MRN8920192||DOE^JOHN\r"
    "TXA|1|DISCHARGE_SUMMARY|TX|20261024|||||DR_JENKINS^SARAH\r"
    "OBX|1|TX|NOTE^CLINICAL||Patient ambulating well. Discharge planned for 14:00.\r"
)


def test_adt_parser():
    adt = HL7ADTParser.parse(SAMPLE_ADT_A01)
    assert adt.event_type == "A01"
    assert adt.mrn == "MRN8920192"
    assert adt.patient_family_name == "DOE"
    assert adt.patient_given_name == "JOHN"
    assert adt.gender == "M"
    assert adt.assigned_location == "RESUS-01^BED1^ED"
    assert "SARAH" in adt.attending_doctor


def test_oru_parser():
    oru = HL7ORUParser.parse(SAMPLE_ORU_R01)
    assert oru.mrn == "MRN8920192"
    assert oru.order_number == "ORD991"
    assert len(oru.results) == 2

    glucose = oru.results[0]
    assert glucose.code == "2345-7"
    assert glucose.value == "104"
    assert glucose.abnormal_flag == "H"
    assert glucose.units == "mg/dL"


def test_mdm_parser():
    mdm = HL7MDMParser.parse(SAMPLE_MDM_T02)
    assert mdm.mrn == "MRN8920192"
    assert mdm.document_type == "DISCHARGE_SUMMARY"
    assert "ambulating well" in mdm.document_text
    assert "SARAH" in mdm.author_name


def test_hl7_router_and_ack():
    category, parsed, ack = HL7MessageRouter.route_message(SAMPLE_ADT_A01)
    assert category == "ADT"
    assert "MSA|AA|MSG00101" in ack


def test_mllp_framing_and_event_publishing():
    event_svc = HL7EventService()
    captured_events = []
    event_svc.subscribe("hospital.adt.admissions", lambda e: captured_events.append(e))

    listener = HL7MLLPListener(event_service=event_svc)
    wrapped = listener.wrap_mllp(SAMPLE_ADT_A01)

    ack_bytes = listener.process_incoming_frame(wrapped)
    ack_str = listener.unwrap_mllp(ack_bytes)

    assert "MSA|AA|MSG00101" in ack_str
    assert len(captured_events) == 1
    assert captured_events[0]["mrn"] == "MRN8920192"
