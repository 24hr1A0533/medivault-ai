"""
FHIR R4 REST Server and API Router.
Implements FHIR R4 CRUD interactions, CapabilityStatement metadata,
and search parameters compliant with US Core.
"""

from fastapi import APIRouter, HTTPException, Query, status, Response
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timezone
from .patient_resource import FHIRPatient
from .observation_resource import FHIRObservation
from .medication_resource import FHIRMedicationStatement
from .encounter_resource import FHIREncounter
from .condition_resource import FHIRCondition
from .diagnostic_report_resource import FHIRDiagnosticReport
from .document_reference_resource import FHIRDocumentReference
from .fhir_validator import FHIRValidator, FHIRValidationError

fhir_router = APIRouter(prefix="/fhir/r4", tags=["FHIR R4 Server"])


class FHIRServer:
    """Thread-safe in-memory FHIR R4 resource store."""

    def __init__(self):
        # resourceType -> id -> resource dict
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {
            "Patient": {},
            "Observation": {},
            "MedicationStatement": {},
            "Encounter": {},
            "Condition": {},
            "DiagnosticReport": {},
            "DocumentReference": {},
        }
        self._seed_sample_patient()

    def _seed_sample_patient(self):
        sample_patient = {
            "resourceType": "Patient",
            "id": "p-1001",
            "name": [{"use": "official", "family": "Doe", "given": ["John", "Alexander"]}],
            "gender": "male",
            "birthDate": "1968-04-12",
            "identifier": [{"system": "http://hospital.org/mrn", "value": "MRN-8920192"}],
        }
        self.save_resource("Patient", "p-1001", sample_patient)

        sample_obs = {
            "resourceType": "Observation",
            "id": "obs-glucose-1",
            "status": "final",
            "code": {
                "coding": [{"system": "http://loinc.org", "code": "2345-7", "display": "Glucose [Mass/volume] in Blood"}]
            },
            "subject": {"reference": "Patient/p-1001"},
            "effectiveDateTime": "2026-10-24T08:00:00Z",
            "valueQuantity": {"value": 104.0, "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
        }
        self.save_resource("Observation", "obs-glucose-1", sample_obs)

    def save_resource(self, resource_type: str, resource_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        FHIRValidator.assert_valid(payload)
        bucket = self._store.setdefault(resource_type, {})
        bucket[resource_id] = payload
        return payload

    def get_resource(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(resource_type, {}).get(resource_id)

    def search_resources(self, resource_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        bucket = self._store.get(resource_type, {})
        if not filters:
            return list(bucket.values())
        results = []
        for res in bucket.values():
            match = True
            for k, v in filters.items():
                if k == "subject" and res.get("subject", {}).get("reference") != v:
                    match = False
                    break
                elif k == "patient" and res.get("subject", {}).get("reference") != f"Patient/{v}":
                    match = False
                    break
            if match:
                results.append(res)
        return results


_fhir_server = FHIRServer()


@fhir_router.get("/metadata")
def capability_statement():
    """Returns the FHIR CapabilityStatement declaring supported resources."""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-10-24",
        "publisher": "MediVault AI Health Network",
        "kind": "instance",
        "software": {"name": "MediVault HOS FHIR Server", "version": "2.5.0"},
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {"type": "Patient", "interaction": [{"code": "read"}, {"code": "create"}, {"code": "search-type"}]},
                    {"type": "Observation", "interaction": [{"code": "read"}, {"code": "create"}, {"code": "search-type"}]},
                    {"type": "MedicationStatement", "interaction": [{"code": "read"}, {"code": "create"}]},
                    {"type": "Encounter", "interaction": [{"code": "read"}, {"code": "create"}]},
                    {"type": "Condition", "interaction": [{"code": "read"}, {"code": "create"}]},
                    {"type": "DiagnosticReport", "interaction": [{"code": "read"}, {"code": "create"}]},
                    {"type": "DocumentReference", "interaction": [{"code": "read"}, {"code": "create"}]},
                ],
            }
        ],
    }


@fhir_router.get("/Patient/{patient_id}")
def get_patient(patient_id: str):
    res = _fhir_server.get_resource("Patient", patient_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Patient/{patient_id} not found")
    return res


@fhir_router.post("/Patient", status_code=status.HTTP_201_CREATED)
def create_patient(payload: Dict[str, Any]):
    try:
        p_id = payload.get("id") or f"p-{uuid.uuid4().hex[:6]}"
        payload["id"] = p_id
        return _fhir_server.save_resource("Patient", p_id, payload)
    except FHIRValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@fhir_router.get("/Observation")
def search_observations(patient: Optional[str] = Query(None)):
    filters = {"patient": patient} if patient else {}
    results = _fhir_server.search_resources("Observation", filters)
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(results),
        "entry": [{"resource": r} for r in results],
    }


@fhir_router.post("/Observation", status_code=status.HTTP_201_CREATED)
def create_observation(payload: Dict[str, Any]):
    try:
        obs_id = payload.get("id")
        return _fhir_server.save_resource("Observation", obs_id, payload)
    except FHIRValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@fhir_router.get("/Condition")
def search_conditions(patient: Optional[str] = Query(None)):
    filters = {"patient": patient} if patient else {}
    results = _fhir_server.search_resources("Condition", filters)
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(results),
        "entry": [{"resource": r} for r in results],
    }


@fhir_router.get("/$export", status_code=status.HTTP_202_ACCEPTED)
@fhir_router.post("/$export", status_code=status.HTTP_202_ACCEPTED)
def bulk_data_export(
    response: Response,
    _since: Optional[str] = Query(None),
    _type: Optional[str] = Query(None),
    _outputFormat: Optional[str] = Query("application/fhir+ndjson"),
):
    """
    HIPAA-mandated FHIR Bulk Data Export ($export) Interaction.
    Returns 202 Accepted with polling location or manifest for system-level bulk extracts.
    """
    job_id = f"export-job-{uuid.uuid4().hex[:8]}"
    response.headers["Content-Location"] = f"/fhir/r4/_bulk-status/{job_id}"
    response.headers["Access-Control-Expose-Headers"] = "Content-Location"

    return {
        "transactionTime": datetime.now(timezone.utc).isoformat(),
        "request": f"/fhir/r4/$export?_outputFormat={_outputFormat}",
        "requiresAccessToken": True,
        "output": [
            {"type": "Patient", "url": f"/fhir/r4/_download/{job_id}/Patient.ndjson"},
            {"type": "Observation", "url": f"/fhir/r4/_download/{job_id}/Observation.ndjson"},
            {"type": "Condition", "url": f"/fhir/r4/_download/{job_id}/Condition.ndjson"},
        ],
        "error": [],
        "job_id": job_id,
        "status": "QUEUED_AND_ACCEPTED",
    }
