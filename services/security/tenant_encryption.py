"""
Tenant Envelope Encryption Engine.
Provides AES-256-GCM authenticated envelope encryption (AEAD) with per-tenant data encryption keys (DEKs).
"""

import os
import base64
import json
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TenantEnvelopeEncryption:
    """Encrypts and decrypts PHI using AES-256-GCM authenticated encryption."""

    @staticmethod
    def generate_dek() -> bytes:
        """Generates a 256-bit random data encryption key."""
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt_data(dek: bytes, plaintext: str, associated_data: str) -> Dict[str, str]:
        """Encrypts UTF-8 plaintext with AES-256-GCM."""
        aesgcm = AESGCM(dek)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data.encode("utf-8"))

        return {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "associated_data": associated_data,
        }

    @staticmethod
    def decrypt_data(dek: bytes, encrypted_payload: Dict[str, str]) -> str:
        """Decrypts and authenticates ciphertext with AES-256-GCM."""
        nonce = base64.b64decode(encrypted_payload["nonce"])
        ciphertext = base64.b64decode(encrypted_payload["ciphertext"])
        associated_data = encrypted_payload["associated_data"].encode("utf-8")

        aesgcm = AESGCM(dek)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return decrypted_bytes.decode("utf-8")
