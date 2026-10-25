"""
SMART Token Service.
Mints signed JWT access tokens containing SMART on FHIR clinical launch scopes
and patient context claims.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import json
import base64
import hashlib
import hmac


class SMARTTokenService:
    """Signs and verifies SMART on FHIR access tokens with HMAC-SHA256."""

    def __init__(self, secret_key: str = "medivault-enterprise-smart-secret-2026"):
        self.secret_key = secret_key

    def _b64_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def _b64_decode(self, s: str) -> bytes:
        padding = "=" * (4 - len(s) % 4)
        return base64.urlsafe_b64decode(s + padding)

    def mint_access_token(
        self,
        client_id: str,
        patient_id: Optional[str],
        encounter_id: Optional[str],
        user_id: Optional[str],
        scope: str = "launch patient/*.read openid fhirUser",
        expires_in_seconds: int = 3600,
    ) -> Dict[str, Any]:
        header = {"alg": "HS256", "typ": "JWT"}
        now = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "iss": "https://auth.medivault.health/oauth2",
            "sub": user_id or f"user_{client_id}",
            "aud": "https://fhir.medivault.health/r4",
            "client_id": client_id,
            "patient": patient_id,
            "encounter": encounter_id,
            "scope": scope,
            "iat": now,
            "exp": now + expires_in_seconds,
        }

        encoded_header = self._b64_encode(json.dumps(header).encode("utf-8"))
        encoded_payload = self._b64_encode(json.dumps(payload).encode("utf-8"))
        signature_base = f"{encoded_header}.{encoded_payload}"
        sig = hmac.new(self.secret_key.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256).digest()
        token = f"{signature_base}.{self._b64_encode(sig)}"

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": expires_in_seconds,
            "scope": scope,
            "patient": patient_id,
            "encounter": encounter_id,
            "need_patient_banner": True,
        }

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts
            signature_base = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                self.secret_key.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256
            ).digest()
            if not hmac.compare_digest(self._b64_decode(sig_b64), expected_sig):
                return None

            payload = json.loads(self._b64_decode(payload_b64).decode("utf-8"))
            if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
                return None
            return payload
        except Exception:
            return None
