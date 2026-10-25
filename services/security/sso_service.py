"""
Enterprise Single Sign-On (SSO) Service.
Processes SAML 2.0 Assertions and OIDC Tokens from Okta, Azure AD, and PingFederate.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import base64
import json


@dataclass
class SAMLAssertion:
    assertion_id: str
    issuer: str
    subject_email: str
    roles: List[str]
    tenant_id: str
    department: str
    expires_at: datetime


class SSOService:
    """Validates enterprise identity provider assertions."""

    def __init__(self, allowed_issuers: Optional[List[str]] = None):
        self.allowed_issuers = allowed_issuers or [
            "https://login.microsoftonline.com/mayo-clinic/v2.0",
            "https://mayoclinic.okta.com",
            "https://sso.pingfederate.hospital.org",
        ]

    def parse_assertion(
        self,
        assertion_id: str,
        issuer: str,
        email: str,
        roles: List[str],
        tenant_id: str,
        department: str,
    ) -> SAMLAssertion:
        if issuer not in self.allowed_issuers:
            raise ValueError(f"Untrusted Identity Provider Issuer: '{issuer}'")

        return SAMLAssertion(
            assertion_id=assertion_id,
            issuer=issuer,
            subject_email=email,
            roles=roles,
            tenant_id=tenant_id,
            department=department,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
        )
