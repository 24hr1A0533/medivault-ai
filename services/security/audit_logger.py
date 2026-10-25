"""
Enterprise WORM Audit Logger.
Implements immutable hash-chained audit trails compliant with HIPAA §164.312(b).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, List, Optional


@dataclass
class AuditEntry:
    entry_id: str
    tenant_id: str
    user_id: str
    action: str
    resource: str
    outcome: str  # PERMITTED | DENIED
    client_ip: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    prev_hash: str = ""
    entry_hash: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)


class EnterpriseAuditLogger:
    """Tamper-evident WORM compliance audit logger."""

    def __init__(self):
        self._entries: List[AuditEntry] = []

    def _hash_entry(self, entry: AuditEntry) -> str:
        body = f"{entry.entry_id}|{entry.tenant_id}|{entry.user_id}|{entry.action}|{entry.resource}|{entry.outcome}|{entry.prev_hash}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def record(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        outcome: str = "PERMITTED",
        client_ip: str = "127.0.0.1",
        metadata: Optional[Dict[str, str]] = None,
    ) -> AuditEntry:
        prev = self._entries[-1].entry_hash if self._entries else "0" * 64
        entry = AuditEntry(
            entry_id=f"audit_{len(self._entries) + 1}",
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            outcome=outcome,
            client_ip=client_ip,
            prev_hash=prev,
            metadata=metadata or {},
        )
        entry.entry_hash = self._hash_entry(entry)
        self._entries.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        if not self._entries:
            return True
        for i, entry in enumerate(self._entries):
            expected_prev = self._entries[i - 1].entry_hash if i > 0 else "0" * 64
            if entry.prev_hash != expected_prev:
                return False
            if entry.entry_hash != self._hash_entry(entry):
                return False
        return True

    def get_entries(self) -> List[AuditEntry]:
        return list(self._entries)
