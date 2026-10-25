"""
Multi-Factor Authentication (MFA) Service.
Implements RFC 6238 TOTP (Time-Based One-Time Password) generation and validation.
"""

import hmac
import hashlib
import time
import struct
import base64
from typing import Tuple


class MFAService:
    """RFC 6238 Time-Based One-Time Password engine."""

    @staticmethod
    def generate_secret() -> str:
        """Generates a Base32 encoded 160-bit random secret."""
        return base64.b32encode(hashlib.sha1(str(time.time()).encode()).digest()).decode("utf-8")

    @classmethod
    def generate_totp(cls, secret_base32: str, time_step: int = 30) -> str:
        """Generates a 6-digit TOTP code for the current time step."""
        key = base64.b32decode(secret_base32)
        counter = int(time.time() // time_step)
        counter_bytes = struct.pack(">Q", counter)
        mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = mac[-1] & 0x0F
        binary = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
        token = binary % 1000000
        return f"{token:06d}"

    @classmethod
    def verify_totp(cls, secret_base32: str, candidate_code: str, time_step: int = 30) -> bool:
        """Verifies candidate code with +/- 1 time step skew allowance."""
        key = base64.b32decode(secret_base32)
        current_counter = int(time.time() // time_step)

        for skew in (-1, 0, 1):
            counter_bytes = struct.pack(">Q", current_counter + skew)
            mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            offset = mac[-1] & 0x0F
            binary = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
            token = f"{binary % 1000000:06d}"
            if token == candidate_code:
                return True
        return False
