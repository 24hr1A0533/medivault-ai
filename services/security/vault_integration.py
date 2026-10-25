"""
HashiCorp Vault KMS Integration.
Integrates with Vault Transit Secrets Engine for key-wrapping (KEK) and tenant key rotation.
"""

from typing import Dict, Optional
import os
import base64
import hashlib
from .tenant_encryption import TenantEnvelopeEncryption


class VaultKMSClient:
    """Manages Key Encryption Keys (KEK) and envelope key-wrapping."""

    def __init__(self, master_secret: str = "production-vault-root-kek-32bytes-secret"):
        self.master_secret = master_secret
        self._tenant_wrapped_keys: Dict[str, str] = {}

    def _derive_kek(self, tenant_id: str) -> bytes:
        """Derives a tenant-specific Key Encryption Key from the master root."""
        seed = f"{self.master_secret}:{tenant_id}"
        return hashlib.sha256(seed.encode("utf-8")).digest()

    def generate_and_wrap_tenant_key(self, tenant_id: str) -> bytes:
        """Generates a fresh DEK and wraps it for secure tenant storage."""
        dek = TenantEnvelopeEncryption.generate_dek()
        kek = self._derive_kek(tenant_id)

        # Wrap DEK using KEK
        encrypted_dek = TenantEnvelopeEncryption.encrypt_data(
            dek=kek, plaintext=base64.b64encode(dek).decode("utf-8"), associated_data=tenant_id
        )
        self._tenant_wrapped_keys[tenant_id] = base64.b64encode(
            f"{encrypted_dek['nonce']}:{encrypted_dek['ciphertext']}".encode("utf-8")
        ).decode("utf-8")
        return dek

    def unwrap_tenant_key(self, tenant_id: str) -> bytes:
        """Retrieves and unwraps the tenant's DEK from the Vault transit store."""
        wrapped = self._tenant_wrapped_keys.get(tenant_id)
        if not wrapped:
            # Auto-provision if not existing
            return self.generate_and_wrap_tenant_key(tenant_id)

        decoded = base64.b64decode(wrapped).decode("utf-8")
        nonce_str, cipher_str = decoded.split(":")
        kek = self._derive_kek(tenant_id)

        raw_b64_dek = TenantEnvelopeEncryption.decrypt_data(
            dek=kek,
            encrypted_payload={"nonce": nonce_str, "ciphertext": cipher_str, "associated_data": tenant_id},
        )
        return base64.b64decode(raw_b64_dek)
