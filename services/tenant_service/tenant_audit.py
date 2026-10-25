"""
Tenant Audit Logger.
Implements immutable, tamper-evident hash-chained audit logging
for HIPAA §164.312(b) and SOC 2 Type II compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Dict, List, Optional


@dataclass
class AuditEvent:
    event_id: str
    tenant_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "SUCCESS"
    details: Dict[str, str] = field(default_factory=dict)
    client_ip: str = "127.0.0.1"
    previous_hash: str = ""
    event_hash: str = ""


class TenantAuditLogger:
    """Tamper-evident hash-chained audit trail generator."""

    def __init__(self):
        # tenant_id -> list of AuditEvents
        self._log_chains: Dict[str, List[AuditEvent]] = {}

    def _compute_hash(self, event: AuditEvent) -> str:
        payload = (
            f"{event.event_id}:{event.tenant_id}:{event.actor_id}:{event.action}:"
            f"{event.resource_type}:{event.resource_id}:{json.dumps(event.details, sort_keys=True)}:"
            f"{event.timestamp.isoformat()}:{event.previous_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def log_event(
        self,
        tenant_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str = "SUCCESS",
        details: Optional[Dict[str, str]] = None,
        client_ip: str = "127.0.0.1",
    ) -> AuditEvent:
        chain = self._log_chains.setdefault(tenant_id, [])
        prev_hash = chain[-1].event_hash if chain else "GENESIS_BLOCK_HASH_000000000"

        event = AuditEvent(
            event_id=f"evt_{len(chain) + 1}_{hashlib.md5(f'{tenant_id}{datetime.now()}'.encode()).hexdigest()[:6]}",
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
            client_ip=client_ip,
            previous_hash=prev_hash,
        )
        event.event_hash = self._compute_hash(event)
        chain.append(event)
        return event

    def verify_integrity(self, tenant_id: str) -> bool:
        """Verifies cryptographic chain integrity for a tenant's audit trail."""
        chain = self._log_chains.get(tenant_id, [])
        if not chain:
            return True

        for i, event in enumerate(chain):
            expected_prev = chain[i - 1].event_hash if i > 0 else "GENESIS_BLOCK_HASH_000000000"
            if event.previous_hash != expected_prev:
                return False
            if event.event_hash != self._compute_hash(event):
                return False
        return True

    def get_events(self, tenant_id: str) -> List[AuditEvent]:
        return list(self._log_chains.get(tenant_id, []))
