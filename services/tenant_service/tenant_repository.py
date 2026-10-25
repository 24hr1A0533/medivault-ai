"""
Tenant Repository and Data Models.
Implements multi-tenant data storage, PostgreSQL RLS session context management,
and tenant schema configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
import uuid


class SubscriptionTier(str, Enum):
    PATIENT = "PATIENT"
    FAMILY = "FAMILY"
    CLINIC = "CLINIC"
    HOSPITAL = "HOSPITAL"
    ENTERPRISE = "ENTERPRISE"


class TenantStatus(str, Enum):
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


@dataclass
class TenantModel:
    tenant_id: str
    organization_name: str
    tier: SubscriptionTier
    status: TenantStatus = TenantStatus.ACTIVE
    admin_email: str = ""
    contact_phone: str = ""
    kms_key_id: str = ""
    dedicated_db_schema: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, str] = field(default_factory=dict)
    licensed_physician_seats: int = 10
    allocated_storage_gb: int = 100


class TenantRepository:
    """Thread-safe multi-tenant persistence repository."""

    def __init__(self):
        self._tenants: Dict[str, TenantModel] = {}
        self._seed_default_tenants()

    def _seed_default_tenants(self):
        default_hospital = TenantModel(
            tenant_id="mayo-clinic-system",
            organization_name="Mayo Clinic Health Network",
            tier=SubscriptionTier.ENTERPRISE,
            status=TenantStatus.ACTIVE,
            admin_email="cio@mayoclinic.org",
            kms_key_id="arn:aws:kms:us-east-1:123456789012:key/mayo-prod-01",
            dedicated_db_schema="tenant_mayo_clinic",
            licensed_physician_seats=5000,
            allocated_storage_gb=50000,
        )
        self.save(default_hospital)

    def save(self, tenant: TenantModel) -> TenantModel:
        tenant.updated_at = datetime.now(timezone.utc)
        self._tenants[tenant.tenant_id] = tenant
        return tenant

    def get_by_id(self, tenant_id: str) -> Optional[TenantModel]:
        return self._tenants.get(tenant_id)

    def list_all(self, status: Optional[TenantStatus] = None) -> List[TenantModel]:
        if status:
            return [t for t in self._tenants.values() if t.status == status]
        return list(self._tenants.values())

    def delete(self, tenant_id: str) -> bool:
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False

    def build_rls_session_query(self, tenant_id: str) -> str:
        """Returns the PostgreSQL Row-Level Security session set statement."""
        safe_tenant = tenant_id.replace("'", "''")
        return f"SET LOCAL app.current_tenant = '{safe_tenant}';"
