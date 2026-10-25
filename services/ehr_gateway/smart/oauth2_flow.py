"""
SMART on FHIR OAuth2 Flow Orchestrator.
Validates authorization requests, evaluates PKCE S256 code challenge,
and performs token exchange.
"""

import hashlib
import base64
from typing import Dict, Any, Optional
from .smart_session_store import SMARTSessionStore, SMARTSession
from .smart_token_service import SMARTTokenService


class SMARTOAuth2Flow:
    """Manages the lifecycle of an authorization code exchange."""

    def __init__(self, store: SMARTSessionStore, token_service: SMARTTokenService):
        self.store = store
        self.token_service = token_service

    def verify_pkce(self, code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
        if method == "plain":
            return code_verifier == code_challenge
        elif method == "S256":
            digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
            calculated = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
            return calculated == code_challenge
        return False

    def exchange_code_for_token(
        self,
        grant_type: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        code_verifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        if grant_type != "authorization_code":
            raise ValueError(f"Unsupported grant_type: '{grant_type}'")

        session = self.store.get_by_auth_code(code)
        if not session:
            raise ValueError("Invalid authorization code.")

        if session.client_id != client_id:
            raise ValueError("Client ID mismatch.")

        if session.redirect_uri != redirect_uri:
            raise ValueError("Redirect URI mismatch.")

        if session.code_challenge and code_verifier:
            method = session.code_challenge_method or "S256"
            if not self.verify_pkce(code_verifier, session.code_challenge, method):
                raise ValueError("PKCE verification failed.")

        # Mint token
        token_response = self.token_service.mint_access_token(
            client_id=client_id,
            patient_id=session.patient_id,
            encounter_id=session.encounter_id,
            user_id=session.user_id,
            scope=session.scope,
        )

        refresh_token = f"refresh_{session.session_id}"
        token_response["refresh_token"] = refresh_token
        self.store.bind_tokens(session.session_id, token_response["access_token"], refresh_token)
        return token_response
