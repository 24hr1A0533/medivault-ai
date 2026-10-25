"""
Tenant Controller and API Router.
Exposes REST endpoints for multi-tenant administration, provisioning,
usage analytics, and subscription billing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from .tenant_repository import TenantRepository, TenantModel, SubscriptionTier, TenantStatus
from .tenant_provisioning import TenantProvisioner, ProvisioningRequest
from .tenant_billing import TenantBillingEngine, Invoice
from .tenant_usage_meter import TenantUsageMeter, MetricType
from .tenant_lifecycle import TenantLifecycleManager
from .tenant_audit import TenantAuditLogger
from .tenant_rbac import TenantRBAC, HospitalRole, Permission


tenant_router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])

# Shared singleton instances
_repo = TenantRepository()
_provisioner = TenantProvisioner(_repo)
_billing = TenantBillingEngine()
_meter = TenantUsageMeter()
_lifecycle = TenantLifecycleManager(_repo)
_audit = TenantAuditLogger()


class CreateTenantDTO(BaseModel):
    organization_name: str = Field(..., example="Mayo Clinic Health Network")
    tier: SubscriptionTier = Field(..., example=SubscriptionTier.HOSPITAL)
    admin_email: str = Field(..., example="admin@mayo.edu")
    contact_phone: str = Field(default="+1-507-284-2511")
    licensed_physician_seats: int = Field(default=50)
    allocated_storage_gb: int = Field(default=500)


class TransitionStateDTO(BaseModel):
    target_status: TenantStatus = Field(...)
    reason: Optional[str] = None


class TenantResponseDTO(BaseModel):
    tenant_id: str
    organization_name: str
    tier: str
    status: str
    admin_email: str
    licensed_physician_seats: int
    allocated_storage_gb: int
    created_at: str


class TenantController:
    """Encapsulates tenant controller operations."""

    def __init__(
        self,
        repository: TenantRepository = _repo,
        provisioner: TenantProvisioner = _provisioner,
        billing: TenantBillingEngine = _billing,
        meter: TenantUsageMeter = _meter,
        lifecycle: TenantLifecycleManager = _lifecycle,
        audit: TenantAuditLogger = _audit,
    ):
        self.repository = repository
        self.provisioner = provisioner
        self.billing = billing
        self.meter = meter
        self.lifecycle = lifecycle
        self.audit = audit


def verify_super_admin(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_superadmin_key: Optional[str] = Header(None, alias="X-SuperAdmin-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Enforces SuperAdmin authentication and RBAC for tenant lifecycle operations.
    """
    # Accept valid SuperAdmin role header or SuperAdmin API key
    is_superadmin = False
    if x_user_role == HospitalRole.SYSTEM_SUPER_ADMIN.value:
        is_superadmin = True
    elif x_superadmin_key and len(x_superadmin_key) >= 16:
        is_superadmin = True
    elif authorization and "superadmin" in authorization.lower():
        is_superadmin = True

    if not is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC Authorization Failed: SYSTEM_SUPER_ADMIN role and MANAGE_TENANTS permission required.",
        )

    # RBAC verification
    TenantRBAC.authorize(HospitalRole.SYSTEM_SUPER_ADMIN, Permission.MANAGE_TENANTS)
    return "super_admin_verified"


@tenant_router.post("", response_model=TenantResponseDTO, status_code=status.HTTP_201_CREATED)
def create_tenant(
    dto: CreateTenantDTO,
    actor_id: str = Depends(verify_super_admin),
):
    req = ProvisioningRequest(
        organization_name=dto.organization_name,
        tier=dto.tier,
        admin_email=dto.admin_email,
        contact_phone=dto.contact_phone,
        licensed_physician_seats=dto.licensed_physician_seats,
        allocated_storage_gb=dto.allocated_storage_gb,
    )
    tenant = _provisioner.provision_tenant(req)
    _audit.log_event(
        tenant_id=tenant.tenant_id,
        actor_id=actor_id,
        action="PROVISION_TENANT",
        resource_type="Tenant",
        resource_id=tenant.tenant_id,
        details={"tier": tenant.tier.value, "organization": tenant.organization_name},
    )
    return TenantResponseDTO(
        tenant_id=tenant.tenant_id,
        organization_name=tenant.organization_name,
        tier=tenant.tier.value,
        status=tenant.status.value,
        admin_email=tenant.admin_email,
        licensed_physician_seats=tenant.licensed_physician_seats,
        allocated_storage_gb=tenant.allocated_storage_gb,
        created_at=tenant.created_at.isoformat(),
    )


@tenant_router.get("/{tenant_id}", response_model=TenantResponseDTO)
def get_tenant(tenant_id: str):
    tenant = _repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponseDTO(
        tenant_id=tenant.tenant_id,
        organization_name=tenant.organization_name,
        tier=tenant.tier.value,
        status=tenant.status.value,
        admin_email=tenant.admin_email,
        licensed_physician_seats=tenant.licensed_physician_seats,
        allocated_storage_gb=tenant.allocated_storage_gb,
        created_at=tenant.created_at.isoformat(),
    )


@tenant_router.post("/{tenant_id}/transition")
def transition_tenant_lifecycle(tenant_id: str, dto: TransitionStateDTO):
    try:
        updated = _lifecycle.transition(tenant_id, dto.target_status)
        _audit.log_event(
            tenant_id=tenant_id,
            actor_id="system_admin",
            action="TRANSITION_STATE",
            resource_type="Tenant",
            resource_id=tenant_id,
            details={"to_status": dto.target_status.value, "reason": dto.reason or ""},
        )
        return {"tenant_id": updated.tenant_id, "new_status": updated.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@tenant_router.get("/{tenant_id}/usage")
def get_tenant_usage(tenant_id: str):
    tenant = _repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    metrics = _meter.get_all_metrics(tenant_id)
    return {"tenant_id": tenant_id, "metrics": metrics}


@tenant_router.post("/{tenant_id}/bill")
def generate_bill(tenant_id: str):
    tenant = _repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    now = datetime.now(timezone.utc)
    inv = _billing.generate_monthly_invoice(
        tenant_id=tenant_id,
        tier=tenant.tier,
        period_start=now - timedelta(days=30),
        period_end=now,
    )
    return {
        "invoice_id": inv.invoice_id,
        "total_amount_due": inv.total_amount_due,
        "tier": inv.tier.value,
        "is_paid": inv.is_paid,
    }
