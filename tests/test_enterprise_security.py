"""
Unit and Integration Tests for Enterprise Security & Compliance Subsystem.
Tests AES-256-GCM envelope encryption, Vault KMS key wrapping, ABAC decisions,
TOTP MFA verification, and WORM audit chains.
"""

import pytest
import time
from services.security.permissions import SecurityPermission
from services.security.rbac_engine import EnterpriseRBAC
from services.security.abac_engine import EnterpriseABAC, AccessEvaluationContext
from services.security.tenant_encryption import TenantEnvelopeEncryption
from services.security.vault_integration import VaultKMSClient
from services.security.audit_logger import EnterpriseAuditLogger
from services.security.mfa_service import MFAService


def test_tenant_envelope_encryption():
    dek = TenantEnvelopeEncryption.generate_dek()
    plaintext = "Patient John Doe: Confirmed Penicillin Anaphylaxis"
    tenant_context = "tenant-mayo-clinic"

    encrypted = TenantEnvelopeEncryption.encrypt_data(dek, plaintext, tenant_context)
    assert "nonce" in encrypted
    assert "ciphertext" in encrypted

    decrypted = TenantEnvelopeEncryption.decrypt_data(dek, encrypted)
    assert decrypted == plaintext


def test_vault_kms_wrapping():
    vault = VaultKMSClient(master_secret="master-kms-test-secret-32b")
    tenant_id = "mayo-rochester"

    # Wrap and unwrap
    dek = vault.generate_and_wrap_tenant_key(tenant_id)
    retrieved_dek = vault.unwrap_tenant_key(tenant_id)
    assert dek == retrieved_dek

    # Encrypt with unwrapped DEK
    enc = TenantEnvelopeEncryption.encrypt_data(retrieved_dek, "Secret Clinical Data", tenant_id)
    dec = TenantEnvelopeEncryption.decrypt_data(dek, enc)
    assert dec == "Secret Clinical Data"


def test_abac_emergency_break_glass():
    # Emergency break-glass by attending physician in hospital network is permitted
    ctx = AccessEvaluationContext(
        user_id="dr_trauma",
        user_roles=["ATTENDING_PHYSICIAN"],
        user_department="EMERGENCY",
        has_active_shift=True,
        is_hospital_network=True,
        is_emergency_break_glass=True,
    )
    assert EnterpriseABAC.evaluate(ctx) is True


def test_abac_vip_and_department_restrictions():
    # Bedside nurse in Cardiology cannot access Oncology patient unless same department
    nurse_ctx = AccessEvaluationContext(
        user_id="nurse_cardio",
        user_roles=["REGISTERED_NURSE"],
        user_department="CARDIOLOGY",
        patient_department="ONCOLOGY",
        has_active_shift=True,
        is_hospital_network=True,
        is_emergency_break_glass=False,
    )
    assert EnterpriseABAC.evaluate(nurse_ctx) is False

    # VIP record denied to standard resident
    vip_ctx = AccessEvaluationContext(
        user_id="resident_doc",
        user_roles=["RESIDENT_PHYSICIAN"],
        user_department="INTERNAL_MED",
        is_vip=True,
        has_active_shift=True,
    )
    assert EnterpriseABAC.evaluate(vip_ctx) is False

    # VIP permitted to Attending Physician
    vip_md_ctx = AccessEvaluationContext(
        user_id="attending_md",
        user_roles=["ATTENDING_PHYSICIAN"],
        user_department="INTERNAL_MED",
        is_vip=True,
        has_active_shift=True,
    )
    assert EnterpriseABAC.evaluate(vip_md_ctx) is True


def test_totp_mfa_flow():
    secret = MFAService.generate_secret()
    token = MFAService.generate_totp(secret)

    # Valid token passes
    assert MFAService.verify_totp(secret, token) is True
    # Wrong token fails
    assert MFAService.verify_totp(secret, "999999") is False


def test_worm_audit_chain_integrity():
    logger = EnterpriseAuditLogger()
    logger.record("mayo", "dr1", "VIEW_PATIENT", "Patient/p-1001")
    logger.record("mayo", "dr1", "SIGN_ORDER", "Order/ord-55")

    assert logger.verify_integrity() is True
    assert len(logger.get_entries()) == 2
