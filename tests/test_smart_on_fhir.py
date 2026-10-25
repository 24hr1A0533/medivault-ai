"""
Unit and Integration Tests for SMART on FHIR Subsystem.
Tests Epic Hyperspace launch parsing, PKCE validation, OAuth2 token minting, and signature verification.
"""

import pytest
import hashlib
import base64
from services.ehr_gateway.smart.epic_context import EpicLaunchContext
from services.ehr_gateway.smart.smart_session_store import SMARTSessionStore
from services.ehr_gateway.smart.smart_token_service import SMARTTokenService
from services.ehr_gateway.smart.oauth2_flow import SMARTOAuth2Flow


def test_epic_launch_context():
    ctx = EpicLaunchContext(
        launch_token="xyz-epic-launch-987",
        iss="https://epic.hospital.org/interconnect-fhir/api/FHIR/R4",
        patient_id="p-1001",
        encounter_id="enc-5501",
        user_id="dr_jenkins",
    )
    claims = ctx.to_claims()
    assert claims["patient"] == "p-1001"
    assert claims["encounter"] == "enc-5501"
    assert claims["need_patient_banner"] is True


def test_smart_token_minting_and_verification():
    token_svc = SMARTTokenService(secret_key="test-secret-smart-key")
    res = token_svc.mint_access_token(
        client_id="epic_portal_client",
        patient_id="p-1001",
        encounter_id="enc-5501",
        user_id="dr_jenkins",
        scope="launch patient/*.read openid",
    )

    assert "access_token" in res
    assert res["token_type"] == "Bearer"
    assert res["patient"] == "p-1001"

    # Verify signature and expiration
    payload = token_svc.verify_token(res["access_token"])
    assert payload is not None
    assert payload["patient"] == "p-1001"
    assert payload["client_id"] == "epic_portal_client"


def test_smart_oauth2_pkce_flow():
    store = SMARTSessionStore()
    token_svc = SMARTTokenService()
    flow = SMARTOAuth2Flow(store, token_svc)

    # Compute PKCE verifier and challenge
    code_verifier = "a" * 64
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    # Create session
    session = store.create_session(
        launch_id="launch-123",
        client_id="epic_client",
        redirect_uri="https://app.medivault.health/callback",
        scope="launch patient/*.read",
        state="state-abc",
        patient_id="p-1001",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    auth_code = store.issue_auth_code(session.session_id)

    # Exchange with correct PKCE
    tokens = flow.exchange_code_for_token(
        grant_type="authorization_code",
        code=auth_code,
        redirect_uri="https://app.medivault.health/callback",
        client_id="epic_client",
        code_verifier=code_verifier,
    )
    assert tokens["access_token"] is not None
    assert tokens["patient"] == "p-1001"

    # Invalid code verifier test
    session2 = store.create_session(
        launch_id="launch-456",
        client_id="epic_client",
        redirect_uri="https://app.medivault.health/callback",
        scope="launch patient/*.read",
        state="state-xyz",
        code_challenge=code_challenge,
    )
    code2 = store.issue_auth_code(session2.session_id)
    with pytest.raises(ValueError):
        flow.exchange_code_for_token(
            grant_type="authorization_code",
            code=code2,
            redirect_uri="https://app.medivault.health/callback",
            client_id="epic_client",
            code_verifier="wrong_verifier_12345",
        )
