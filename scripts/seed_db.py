"""
MediVault Enterprise Database & In-Memory Seeder.
Initializes default hospital tenants, FHIR patients, and clinical observations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tenant_service.tenant_repository import TenantRepository, TenantModel, SubscriptionTier, TenantStatus
from services.tenant_service.tenant_provisioning import TenantProvisioner, ProvisioningRequest
from services.ehr_gateway.fhir_server import FHIRServer
from services.ehr_gateway.fhir_mapper import FHIRMapper


def seed_all():
    print("[1/3] Seeding Multi-Tenant Health Systems...")
    repo = TenantRepository()
    provisioner = TenantProvisioner(repo)

    tenants_to_seed = [
        ("Mayo Clinic Health Network", SubscriptionTier.ENTERPRISE, "cio@mayoclinic.org", 5000),
        ("Johns Hopkins Medicine", SubscriptionTier.ENTERPRISE, "it@jhmi.edu", 3500),
        ("Cleveland Clinic", SubscriptionTier.HOSPITAL, "admin@ccf.org", 1200),
        ("Oak Valley Community Practice", SubscriptionTier.CLINIC, "dr.smith@oakvalley.org", 15),
    ]

    for name, tier, email, seats in tenants_to_seed:
        req = ProvisioningRequest(
            organization_name=name,
            tier=tier,
            admin_email=email,
            licensed_physician_seats=seats,
            allocated_storage_gb=seats * 10,
        )
        t = provisioner.provision_tenant(req)
        print(f"  -> Created Tenant: {t.organization_name} (ID: {t.tenant_id}, Tier: {t.tier.value})")

    print("[2/3] Seeding FHIR R4 Clinical Store...")
    fhir = FHIRServer()
    sample_patient = FHIRMapper.patient_to_fhir(
        patient_id="p-1001",
        name="John Alexander Doe",
        gender="male",
        birth_date="1968-04-12",
        mrn="MRN-8920192",
    )
    fhir.save_resource("Patient", sample_patient.id, sample_patient.model_dump())
    print(f"  -> Seeded FHIR Patient: {sample_patient.id} (MRN: MRN-8920192)")

    obs = FHIRMapper.lab_marker_to_fhir_observation(
        patient_id="p-1001",
        marker_name="Fasting Blood Glucose",
        value=104.0,
        unit="mg/dL",
        effective_date="2026-10-24T08:00:00Z",
        loinc_code="2345-7",
    )
    fhir.save_resource("Observation", obs.id, obs.model_dump())
    print(f"  -> Seeded FHIR Observation: Fasting Blood Glucose 104 mg/dL")

    print("[3/3] Database Seeding Complete! System ready for operation.")


if __name__ == "__main__":
    seed_all()
