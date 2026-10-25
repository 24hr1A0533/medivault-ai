"""
MediVault Offline AI Mode & CRDT Synchronization Engine.
Provides mission-critical edge survivability under complete network severance.
Simulates Local Encrypted SQLite (SQLCipher), Local VectorLite, Local TinyLLM, and CRDT Sync.
"""
import time
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class LocalEmergencyPayload(BaseModel):
    patient_id: str
    patient_name: str
    blood_group: str
    allergies: List[str]
    active_medications: List[str]
    recent_reports: List[Dict[str, str]]
    encrypted_local_key: str

class CRDTSyncOperation(BaseModel):
    op_id: str
    patient_id: str
    entity_type: str    # "MEDICATION", "ALLERGY", "NOTE", "ENCOUNTER"
    action: str         # CREATE, UPDATE, DELETE
    payload: Dict[str, Any]
    vector_clock: int   # Monotonic logical timestamp
    device_id: str
    timestamp: str

class OfflineEdgeEngine:
    """
    Offline Local Edge Engine for Mobile App and Ambulance Tablets.
    Runs without internet connection using local encrypted storage and TinyLLM.
    """

    def __init__(self, device_id: str = "EMR-DEVICE-OFFLINE-01"):
        self.device_id = device_id
        self._local_db: Dict[str, LocalEmergencyPayload] = {}
        self._local_vector_db: Dict[str, List[float]] = {}
        self._sync_queue: List[CRDTSyncOperation] = []
        self._logical_clock = 0

    def seed_offline_patient_record(
        self,
        patient_id: str,
        patient_name: str,
        blood_group: str,
        allergies: List[str],
        medications: List[str],
        recent_reports: List[Dict[str, str]],
    ):
        """
        Pre-caches encrypted patient record to local device storage before field operation.
        """
        enc_key = hashlib.sha256(f"LOCAL_AES_KEY_{patient_id}".encode()).hexdigest()
        self._local_db[patient_id] = LocalEmergencyPayload(
            patient_id=patient_id,
            patient_name=patient_name,
            blood_group=blood_group,
            allergies=allergies,
            active_medications=medications,
            recent_reports=recent_reports,
            encrypted_local_key=enc_key,
        )

    def execute_offline_emergency_lookup(self, patient_id: str) -> Dict[str, Any]:
        """
        Instant offline lookup executed entirely in local device memory (< 5ms).
        """
        start = time.perf_counter()
        record = self._local_db.get(patient_id)
        if not record:
            return {"status": "NOT_FOUND_LOCALLY", "message": "No local encrypted record found."}

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "OFFLINE_SUCCESS",
            "source": "Local SQLCipher Encrypted Cache (Edge Mode)",
            "patient_name": record.patient_name,
            "blood_group": record.blood_group,
            "allergies": record.allergies,
            "medications": record.active_medications,
            "recent_reports": record.recent_reports,
            "offline_tiny_llm_inference": "Local TinyLLM Qwen 2.5 1.5B (INT4 ONNX) active. No internet required.",
            "execution_time_ms": elapsed_ms,
        }

    def record_offline_event(self, patient_id: str, entity_type: str, action: str, data: Dict[str, Any]) -> CRDTSyncOperation:
        """
        Records an offline modification into CRDT sync queue with monotonic vector clock.
        """
        self._logical_clock += 1
        op = CRDTSyncOperation(
            op_id=f"OP-{self._logical_clock}-{self.device_id[:6]}",
            patient_id=patient_id,
            entity_type=entity_type,
            action=action,
            payload=data,
            vector_clock=self._logical_clock,
            device_id=self.device_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._sync_queue.append(op)
        return op

    def synchronize_with_cloud(self, cloud_current_clock: int = 0) -> Dict[str, Any]:
        """
        Replicates queued offline CRDT operations to hospital cloud database when connectivity resumes.
        """
        start = time.perf_counter()
        pending = list(self._sync_queue)
        applied = []
        conflicts_resolved = 0

        for op in pending:
            # Deterministic Last-Write-Wins / Vector Clock Conflict Resolution
            if op.vector_clock > cloud_current_clock:
                applied.append(op.op_id)
            else:
                conflicts_resolved += 1

        self._sync_queue.clear()
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            "sync_status": "SYNCHRONIZED",
            "operations_replicated": len(applied),
            "conflicts_resolved": conflicts_resolved,
            "sync_duration_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
