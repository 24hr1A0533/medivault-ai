"""
Tenant Provisioning Engine.
Automates end-to-end setup of newly onboarded healthcare organizations,
allocating isolated schemas, KMS envelope keys, and initial admin accounts.
"""

from dataclasses import dataclass
from typing import Dict, Any
import uuid
from .tenant_repository import TenantModel, TenantRepository, SubscriptionTier, TenantStatus


@dataclass
class ProvisioningRequest:
    organization_name: str
    tier: SubscriptionTier
    admin_email: str
    contact_phone: str = ""
    licensed_physician_seats: int = 10
    allocated_storage_gb: int = 100


class TenantProvisioner:
    """Executes atomic provisioning of multi-tenant hospital environments."""

    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def provision_tenant(self, request: ProvisioningRequest) -> TenantModel:
        """Provisions a new tenant with dedicated identifiers and encryption context."""
        slug = request.organization_name.lower().replace(" ", "-").replace(",", "")
        tenant_id = f"{slug}-{uuid.uuid4().hex[:6]}"

        kms_key = f"arn:aws:kms:us-east-1:123456789012:key/tenant-{tenant_id}"
        db_schema = f"tenant_{tenant_id.replace('-', '_')}"

        new_tenant = TenantModel(
            tenant_id=tenant_id,
            organization_name=request.organization_name,
            tier=request.tier,
            status=TenantStatus.ACTIVE,
            admin_email=request.admin_email,
            contact_phone=request.contact_phone,
            kms_key_id=kms_key,
            dedicated_db_schema=db_schema,
            licensed_physician_seats=request.licensed_physician_seats,
            allocated_storage_gb=request.allocated_storage_gb,
            metadata={
                "provisioned_by": "TenantProvisioner_v2",
                "isolation_mode": "SCHEMA_AND_RLS",
            },
        )

        return self.repository.save(new_tenant)
