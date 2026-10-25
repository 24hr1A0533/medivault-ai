"""
Enterprise ABAC Engine (Attribute-Based Access Control).
Implements NIST SP 800-162 evaluation of Subject, Resource, Action, and Environment attributes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .permissions import SecurityPermission, ClinicalScope


@dataclass
class AccessEvaluationContext:
    # Subject Attributes
    user_id: str
    user_roles: List[str]
    user_department: str
    has_active_shift: bool = True

    # Resource Attributes
    resource_type: str = "PatientRecord"
    patient_id: str = ""
    patient_department: str = ""
    is_vip: bool = False
    is_mental_health_restricted: bool = False

    # Action Attributes
    requested_action: SecurityPermission = SecurityPermission.READ_PHI

    # Environment Attributes
    client_ip: str = "127.0.0.1"
    is_hospital_network: bool = True
    is_emergency_break_glass: bool = False
    request_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EnterpriseABAC:
    """NIST SP 800-162 Policy Decision Point (PDP)."""

    @classmethod
    def evaluate(cls, ctx: AccessEvaluationContext) -> bool:
        # Rule 1: Emergency Break-Glass override allows acute access if clinician is in hospital network
        if ctx.is_emergency_break_glass:
            if ctx.is_hospital_network and ("ATTENDING_PHYSICIAN" in ctx.user_roles or "REGISTERED_NURSE" in ctx.user_roles):
                return True

        # Rule 2: VIP patients require explicit Attending Physician or CMO role
        if ctx.is_vip:
            allowed_roles = {"CHIEF_MEDICAL_OFFICER", "ATTENDING_PHYSICIAN"}
            if not any(r in allowed_roles for r in ctx.user_roles):
                return False

        # Rule 3: Highly confidential mental health records require physician or psychologist role
        if ctx.is_mental_health_restricted:
            allowed = {"CHIEF_MEDICAL_OFFICER", "ATTENDING_PHYSICIAN", "PSYCHIATRIST"}
            if not any(r in allowed for r in ctx.user_roles):
                return False

        # Rule 4: Bedside nurses must belong to the same department as the patient
        if "REGISTERED_NURSE" in ctx.user_roles and not ctx.is_emergency_break_glass:
            if ctx.patient_department and ctx.user_department != ctx.patient_department:
                return False

        # Rule 5: User must have an active shift logged
        if not ctx.has_active_shift and "CHIEF_MEDICAL_OFFICER" not in ctx.user_roles:
            return False

        return True
