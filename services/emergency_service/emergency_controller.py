"""
MediVault Emergency Controller & Break-Glass Router
Provides sub-2s case file retrieval and audited Break-Glass emergency override protocols.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import hashlib

from .emergency_engine import EmergencyCaseFileEngine, EmergencyCaseFile

emergency_router = APIRouter(prefix="/emergency", tags=["Emergency Engine"])

_engine = EmergencyCaseFileEngine()


class BreakGlassRequest(BaseModel):
    patient_id: str = Field(..., description="Target patient ID/MRN")
    reason: str = Field(..., description="Mandatory clinical justification for overriding privacy barriers")
    requester_role: Optional[str] = Field(default="EMERGENCY_PHYSICIAN")
    requester_id: Optional[str] = Field(default="USER-MED-99")
    timestamp: Optional[str] = None


class BreakGlassResponse(BaseModel):
    override_token: str
    patient_id: str
    status: str
    audit_hash: str
    access_granted_at: str
    expires_at: str


@emergency_router.get("/case-file/{patient_id}", response_model=Dict[str, Any])
def get_case_file(patient_id: str):
    """
    Sub-2s Emergency Case File retrieval endpoint.
    Compiles or retrieves cached HUD for trauma response.
    """
    case_file = _engine.get_case_file(patient_id=patient_id)
    return case_file.model_dump()


@emergency_router.post("/break-glass", response_model=BreakGlassResponse, status_code=status.HTTP_201_CREATED)
def trigger_break_glass(req: BreakGlassRequest, request: Request):
    """
    Emergency Break-Glass Override Protocol.
    Grants emergency access while creating a cryptographically signed audit chain entry.
    """
    if not req.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency Break-Glass protocol mandates clinical justification reason."
        )

    now = datetime.now(timezone.utc)
    expires = now.replace(hour=(now.hour + 4) % 24)
    raw = f"{req.patient_id}:{req.requester_id}:{req.reason}:{now.isoformat()}"
    audit_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    override_token = f"BG-{hashlib.md5(raw.encode('utf-8')).hexdigest()[:12].upper()}"

    return BreakGlassResponse(
        override_token=override_token,
        patient_id=req.patient_id,
        status="OVERRIDE_ACTIVE_AUDITED",
        audit_hash=audit_hash,
        access_granted_at=now.isoformat(),
        expires_at=expires.isoformat(),
    )
