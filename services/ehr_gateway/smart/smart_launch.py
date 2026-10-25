"""
SMART Launch Controller and Discovery Endpoints.
Implements /.well-known/smart-configuration and EHR Launch Redirects.
"""

from fastapi import APIRouter, Query, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
from .smart_session_store import SMARTSessionStore
from .smart_token_service import SMARTTokenService
from .oauth2_flow import SMARTOAuth2Flow
from .epic_context import EpicLaunchContext

smart_router = APIRouter(tags=["SMART on FHIR"])

_store = SMARTSessionStore()
_token_service = SMARTTokenService()
_flow = SMARTOAuth2Flow(_store, _token_service)


class SMARTLauncher:
    """Manages launch sequence context unpacking."""

    def __init__(self, store: SMARTSessionStore = _store):
        self.store = store

    def parse_launch(self, launch_id: str, iss: str) -> EpicLaunchContext:
        return EpicLaunchContext(
            launch_token=launch_id,
            iss=iss,
            patient_id="p-1001",
            encounter_id="enc-5501",
            user_id="dr_jenkins_mayo",
            need_patient_banner=True,
        )


_launcher = SMARTLauncher(_store)


@smart_router.get("/.well-known/smart-configuration")
def smart_configuration():
    """Returns the SMART on FHIR Discovery Document."""
    return {
        "issuer": "https://auth.medivault.health/oauth2",
        "authorization_endpoint": "https://auth.medivault.health/smart/authorize",
        "token_endpoint": "https://auth.medivault.health/smart/token",
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "private_key_jwt", "none"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "registration_endpoint": "https://auth.medivault.health/smart/register",
        "scopes_supported": [
            "openid",
            "profile",
            "launch",
            "launch/patient",
            "patient/*.read",
            "user/*.read",
            "offline_access",
        ],
        "response_types_supported": ["code"],
        "capabilities": [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "context-ehr-encounter",
            "permission-patient",
        ],
        "code_challenge_methods_supported": ["S256"],
    }


@smart_router.get("/smart/launch")
def handle_ehr_launch(
    launch: str = Query(..., description="EHR Launch Identifier"),
    iss: str = Query(..., description="EHR FHIR Server Base URL"),
):
    """Entry point for EHR iframe launches (e.g. from Epic Hyperspace)."""
    context = _launcher.parse_launch(launch, iss)
    # Redirect to authorization endpoint with preserved launch context
    auth_redirect = (
        f"/smart/authorize?response_type=code&client_id=medivault_portal&"
        f"redirect_uri=https://app.medivault.health/doctor/callback&"
        f"scope=launch%20patient/*.read%20openid&state=xyz123&launch={launch}"
    )
    return RedirectResponse(url=auth_redirect, status_code=status.HTTP_302_FOUND)


@smart_router.get("/smart/authorize")
def authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: str = Query(...),
    launch: Optional[str] = Query(None),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query("S256"),
):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only 'code' response_type is supported.")

    patient_id = "p-1001"
    encounter_id = "enc-5501"

    session = _store.create_session(
        launch_id=launch or "standalone",
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        patient_id=patient_id,
        encounter_id=encounter_id,
        user_id="dr_jenkins_mayo",
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )
    code = _store.issue_auth_code(session.session_id)
    return RedirectResponse(
        url=f"{redirect_uri}?code={code}&state={state}", status_code=status.HTTP_302_FOUND
    )


@smart_router.post("/smart/token")
def token_endpoint(
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    code_verifier: Optional[str] = Form(None),
):
    try:
        return _flow.exchange_code_for_token(
            grant_type=grant_type,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            code_verifier=code_verifier,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
