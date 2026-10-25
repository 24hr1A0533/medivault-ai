"""
Unit and Integration Tests for Multi-Tenant SaaS Subsystem.
Tests tenant provisioning, lifecycle state transitions, RBAC permissions,
usage metering, and tamper-evident audit chaining.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.tenant_service.tenant_repository import (
    TenantRepository,
    TenantModel,
    SubscriptionTier,
    TenantStatus,
)
from services.tenant_service.tenant_provisioning import TenantProvisioner, ProvisioningRequest
from services.tenant_service.tenant_lifecycle import TenantLifecycleManager
from services.tenant_service.tenant_rbac import TenantRBAC, HospitalRole, Permission
from services.tenant_service.tenant_billing import TenantBillingEngine
from services.tenant_service.tenant_usage_meter import TenantUsageMeter, MetricType
from services.tenant_service.tenant_audit import TenantAuditLogger


def test_tenant_provisioning_and_isolation():
    repo = TenantRepository()
    provisioner = TenantProvisioner(repo)

    req = ProvisioningRequest(
        organization_name="Johns Hopkins Medicine",
        tier=SubscriptionTier.ENTERPRISE,
        admin_email="admin@jh.edu",
        licensed_physician_seats=2000,
        allocated_storage_gb=10000,
    )
    tenant = provisioner.provision_tenant(req)

    assert tenant.tenant_id.startswith("johns-hopkins-medicine")
    assert tenant.status == TenantStatus.ACTIVE
    assert tenant.dedicated_db_schema.startswith("tenant_johns_hopkins_medicine")
    assert "jh.edu" in tenant.admin_email

    fetched = repo.get_by_id(tenant.tenant_id)
    assert fetched is not None
    assert fetched.organization_name == "Johns Hopkins Medicine"


def test_tenant_lifecycle_transitions():
    repo = TenantRepository()
    provisioner = TenantProvisioner(repo)
    lifecycle = TenantLifecycleManager(repo)

    req = ProvisioningRequest(
        organization_name="Cleveland Clinic",
        tier=SubscriptionTier.HOSPITAL,
        admin_email="cio@ccf.org",
    )
    tenant = provisioner.provision_tenant(req)

    # Active -> Suspended
    suspended = lifecycle.suspend(tenant.tenant_id, reason="Overdue invoice")
    assert suspended.status == TenantStatus.SUSPENDED
    assert suspended.metadata["suspension_reason"] == "Overdue invoice"

    # Suspended -> Active
    reactivated = lifecycle.reactivate(tenant.tenant_id)
    assert reactivated.status == TenantStatus.ACTIVE

    # Active -> Decommissioned
    decommissioned = lifecycle.decommission(tenant.tenant_id)
    assert decommissioned.status == TenantStatus.DECOMMISSIONED

    # Decommissioned is terminal: invalid transition raises error
    with pytest.raises(ValueError):
        lifecycle.reactivate(tenant.tenant_id)


def test_tenant_rbac_enforcement():
    # Attending Physician has clinical orders and emergency break glass
    assert TenantRBAC.has_permission(HospitalRole.ATTENDING_PHYSICIAN, Permission.SIGN_CLINICAL_ORDERS)
    assert TenantRBAC.has_permission(HospitalRole.ATTENDING_PHYSICIAN, Permission.TRIGGER_EMERGENCY_OVERRIDE)

    # Bedside nurse has medication administration
    assert TenantRBAC.has_permission(HospitalRole.BEDSIDE_NURSE, Permission.ADMINISTER_MEDICATION)
    assert not TenantRBAC.has_permission(HospitalRole.BEDSIDE_NURSE, Permission.SIGN_CLINICAL_ORDERS)

    # Patient can only read and query copilot
    assert TenantRBAC.has_permission(HospitalRole.PATIENT, Permission.VIEW_PATIENT_RECORDS)
    assert not TenantRBAC.has_permission(HospitalRole.PATIENT, Permission.ADMINISTER_MEDICATION)

    with pytest.raises(PermissionError):
        TenantRBAC.authorize(HospitalRole.PATIENT, Permission.SIGN_CLINICAL_ORDERS)


def test_tenant_billing_calculation():
    billing = TenantBillingEngine()
    now = datetime.now(timezone.utc)
    inv = billing.generate_monthly_invoice(
        tenant_id="mayo-clinic-system",
        tier=SubscriptionTier.HOSPITAL,
        period_start=now - timedelta(days=30),
        period_end=now,
        extra_seats=20,
        extra_ai_queries=5000,
        extra_storage_gb=100,
    )

    # Base: 12500, Extra seats: 20*50=1000, Extra AI: 5*15=75, Extra storage: 100*0.2=20 -> Total: 13595.0
    assert inv.base_charge == 12500.00
    assert inv.usage_charge == 1095.00
    assert inv.total_amount_due == 13595.00
    assert not inv.is_paid

    assert billing.mark_paid(inv.invoice_id)
    assert inv.is_paid


def test_tenant_usage_metering():
    meter = TenantUsageMeter()
    t_id = "test-tenant-101"

    meter.record_usage(t_id, MetricType.AI_COPILOT_QUERIES, value=15.0)
    meter.record_usage(t_id, MetricType.OCR_DOCUMENTS_PROCESSED, value=4.0)

    assert meter.get_metric_total(t_id, MetricType.AI_COPILOT_QUERIES) == 15.0
    assert meter.get_metric_total(t_id, MetricType.OCR_DOCUMENTS_PROCESSED) == 4.0

    metrics = meter.get_all_metrics(t_id)
    assert metrics[MetricType.AI_COPILOT_QUERIES.value] == 15.0


def test_tenant_audit_hash_chain():
    logger = TenantAuditLogger()
    t_id = "audit-tenant"

    evt1 = logger.log_event(t_id, "user1", "READ_PHI", "Patient", "p-101")
    evt2 = logger.log_event(t_id, "user1", "WRITE_PHI", "Patient", "p-101")
    evt3 = logger.log_event(t_id, "user2", "ADMINISTER_MED", "Med", "m-202")

    assert evt2.previous_hash == evt1.event_hash
    assert evt3.previous_hash == evt2.event_hash
    assert logger.verify_integrity(t_id) is True

    # Tamper test
    evt2.details["tampered"] = "true"
    assert logger.verify_integrity(t_id) is False
