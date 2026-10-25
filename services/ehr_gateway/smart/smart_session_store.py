"""
SMART Session Store.
Manages ephemeral OAuth2 state, PKCE code verifiers, and active session tokens.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import uuid


@dataclass
class SMARTSession:
    session_id: str
    launch_id: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    user_id: Optional[str] = None
    auth_code: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=15)
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class SMARTSessionStore:
    """Thread-safe store for SMART OAuth2 state and session exchange."""

    def __init__(self):
        self._sessions_by_id: Dict[str, SMARTSession] = {}
        self._sessions_by_code: Dict[str, str] = {}  # auth_code -> session_id
        self._sessions_by_token: Dict[str, str] = {}  # access_token -> session_id

    def create_session(
        self,
        launch_id: str,
        client_id: str,
        redirect_uri: str,
        scope: str,
        state: str,
        patient_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
        user_id: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
    ) -> SMARTSession:
        session_id = f"smart_sess_{uuid.uuid4().hex}"
        session = SMARTSession(
            session_id=session_id,
            launch_id=launch_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            patient_id=patient_id,
            encounter_id=encounter_id,
            user_id=user_id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        self._sessions_by_id[session_id] = session
        return session

    def issue_auth_code(self, session_id: str) -> str:
        session = self._sessions_by_id.get(session_id)
        if not session or session.is_expired:
            raise ValueError("Invalid or expired session.")
        code = f"auth_code_{uuid.uuid4().hex}"
        session.auth_code = code
        self._sessions_by_code[code] = session_id
        return code

    def get_by_auth_code(self, code: str) -> Optional[SMARTSession]:
        session_id = self._sessions_by_code.get(code)
        if not session_id:
            return None
        return self._sessions_by_id.get(session_id)

    def bind_tokens(self, session_id: str, access_token: str, refresh_token: str):
        session = self._sessions_by_id.get(session_id)
        if session:
            session.access_token = access_token
            session.refresh_token = refresh_token
            self._sessions_by_token[access_token] = session_id

    def get_by_token(self, token: str) -> Optional[SMARTSession]:
        session_id = self._sessions_by_token.get(token)
        if not session_id:
            return None
        return self._sessions_by_id.get(session_id)
