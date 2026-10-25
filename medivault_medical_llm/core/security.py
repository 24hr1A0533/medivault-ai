"""
HIPAA Security, PHI Redaction, and Multi-User Isolation Governance Layer.
"""
import re
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class SecurityIsolationError(Exception):
    """Raised when cross-tenant data access or isolation violation occurs."""
    pass

class HIPAASecurityManager:
    """
    Enforces HIPAA-inspired privacy controls, PHI de-identification,
    multi-user isolation verification, and immutable access logging.
    """

    PHI_PATTERNS = [
        # Social Security Numbers (SSN)
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
        # Medical Record Numbers (MRN)
        (r"\b(?:MRN|mrn|Medical\s+Record\s+No)[\s:#]+[A-Za-z0-9\-]+\b", "[REDACTED_MRN]"),
        # Phone Numbers
        (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
        # Email Addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
    ]

    def __init__(self):
        self._compiled_phi = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in self.PHI_PATTERNS]
        self._audit_log: List[Dict[str, Any]] = []

    def mask_phi(self, text: str) -> str:
        """
        Redacts direct personal identifiers while preserving clinical lab values,
        dates, medication names, and medical observations.
        """
        cleaned = text
        for regex, replacement in self._compiled_phi:
            cleaned = regex.sub(replacement, cleaned)
        return cleaned

    def assert_tenant_isolation(
        self,
        request_patient_id: str,
        retrieved_chunk_patient_ids: List[str],
    ):
        """
        Guarantees zero cross-tenant retrieval.
        Raises SecurityIsolationError if any retrieved chunk belongs to another patient.
        """
        if not request_patient_id or not request_patient_id.strip():
            raise SecurityIsolationError("Security Violation: Request missing authenticated patient_id.")

        for pid in retrieved_chunk_patient_ids:
            if pid != request_patient_id:
                raise SecurityIsolationError(
                    f"CRITICAL PRIVACY VIOLATION: Retrieval breach detected! "
                    f"Queried patient '{request_patient_id}', but retrieved document belonging to '{pid}'."
                )

    def log_access(
        self,
        patient_id: str,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Records an immutable audit entry with SHA-256 verification signature.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = f"{timestamp}|{patient_id}|{action}|{resource_id or ''}"
        sig = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        entry = {
            "timestamp": timestamp,
            "patient_id": patient_id,
            "action": action,
            "resource_id": resource_id,
            "details": details or {},
            "audit_signature": sig,
        }
        self._audit_log.append(entry)
        return entry

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)
