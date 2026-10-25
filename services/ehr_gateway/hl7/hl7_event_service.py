"""
HL7 Event Dispatch Service.
Broadcasts parsed clinical events (ADTs, Lab Observations, Clinical Documents)
to internal Kafka topic handlers and triggers downstream RAG / emergency updates.
"""

from typing import Dict, Any, List, Callable
from collections import defaultdict
import json
from .adt_parser import ADTEvent
from .oru_parser import ORUObservation
from .mdm_parser import MDMDocument


class HL7EventService:
    """Publishes parsed HL7 clinical events to registered topic subscribers."""

    def __init__(self):
        # topic_name -> list of listener callables
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)
        self._event_history: List[Dict[str, Any]] = []

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]):
        self._subscribers[topic].append(handler)

    def publish_adt(self, adt: ADTEvent):
        payload = {
            "topic": "hospital.adt.admissions",
            "event_type": adt.event_type,
            "mrn": adt.mrn,
            "patient_name": f"{adt.patient_family_name}, {adt.patient_given_name}",
            "location": adt.assigned_location,
            "attending": adt.attending_doctor,
        }
        self._dispatch("hospital.adt.admissions", payload)

    def publish_oru(self, oru: ORUObservation):
        payload = {
            "topic": "hospital.lab.results",
            "mrn": oru.mrn,
            "order_number": oru.order_number,
            "test_count": len(oru.results),
            "results": [
                {
                    "code": r.code,
                    "name": r.name,
                    "value": r.value,
                    "units": r.units,
                    "flag": r.abnormal_flag,
                }
                for r in oru.results
            ],
        }
        self._dispatch("hospital.lab.results", payload)

    def publish_mdm(self, mdm: MDMDocument):
        payload = {
            "topic": "hospital.clinical.notes",
            "mrn": mdm.mrn,
            "document_type": mdm.document_type,
            "author": mdm.author_name,
            "length": len(mdm.document_text),
        }
        self._dispatch("hospital.clinical.notes", payload)

    def _dispatch(self, topic: str, payload: Dict[str, Any]):
        self._event_history.append(payload)
        for handler in self._subscribers.get(topic, []):
            try:
                handler(payload)
            except Exception as e:
                # Keep resilient across listeners
                pass

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._event_history)
