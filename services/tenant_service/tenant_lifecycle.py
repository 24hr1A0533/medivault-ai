"""
Tenant Lifecycle Manager.
Implements the formal state machine governing tenant lifecycle states,
suspensions, maintenance locks, and HIPAA-compliant data decommission.
"""

from enum import Enum
from typing import Set, Dict
from .tenant_repository import TenantRepository, TenantModel, TenantStatus


# Alias for backward compatibility
TenantState = TenantStatus


ALLOWED_TRANSITIONS: Dict[TenantStatus, Set[TenantStatus]] = {
    TenantStatus.PROVISIONING: {TenantStatus.ACTIVE, TenantStatus.DECOMMISSIONED},
    TenantStatus.ACTIVE: {TenantStatus.MAINTENANCE, TenantStatus.SUSPENDED, TenantStatus.DECOMMISSIONED},
    TenantStatus.MAINTENANCE: {TenantStatus.ACTIVE, TenantStatus.SUSPENDED},
    TenantStatus.SUSPENDED: {TenantStatus.ACTIVE, TenantStatus.DECOMMISSIONED},
    TenantStatus.DECOMMISSIONED: set(),  # Terminal state
}


class TenantLifecycleManager:
    """Orchestrates tenant state transitions and validation rules."""

    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def transition(self, tenant_id: str, target_status: TenantStatus) -> TenantModel:
        tenant = self.repository.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' does not exist.")

        allowed = ALLOWED_TRANSITIONS.get(tenant.status, set())
        if target_status not in allowed:
            raise ValueError(
                f"Invalid lifecycle transition from {tenant.status.value} to {target_status.value}."
            )

        tenant.status = target_status
        return self.repository.save(tenant)

    def suspend(self, tenant_id: str, reason: str = "Past due invoice") -> TenantModel:
        tenant = self.transition(tenant_id, TenantStatus.SUSPENDED)
        tenant.metadata["suspension_reason"] = reason
        return self.repository.save(tenant)

    def reactivate(self, tenant_id: str) -> TenantModel:
        return self.transition(tenant_id, TenantStatus.ACTIVE)

    def decommission(self, tenant_id: str) -> TenantModel:
        return self.transition(tenant_id, TenantStatus.DECOMMISSIONED)
