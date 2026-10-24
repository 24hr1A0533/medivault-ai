from models.domain import ClaimStatus

class InvalidTransitionError(Exception):
    pass

class ClaimStateMachine:
    """
    Manages permitted lifecycle transitions for insurance claims.
    """
    ALLOWED_TRANSITIONS = {
        ClaimStatus.DRAFT: [ClaimStatus.SUBMITTED],
        ClaimStatus.SUBMITTED: [ClaimStatus.UNDER_REVIEW, ClaimStatus.REJECTED],
        ClaimStatus.UNDER_REVIEW: [ClaimStatus.APPROVED, ClaimStatus.REJECTED],
        ClaimStatus.REJECTED: [ClaimStatus.DISPUTED],
        ClaimStatus.APPROVED: [ClaimStatus.DISPUTED, ClaimStatus.SETTLED],
        ClaimStatus.DISPUTED: [ClaimStatus.UNDER_REVIEW, ClaimStatus.SETTLED, ClaimStatus.REJECTED],
        ClaimStatus.SETTLED: [] # Terminal state
    }

    @classmethod
    def validate_transition(cls, current_status: ClaimStatus, target_status: ClaimStatus, user_role: str):
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise InvalidTransitionError(f"Cannot transition claim from {current_status} to {target_status}")

        # Authorization guard
        if target_status in [ClaimStatus.UNDER_REVIEW, ClaimStatus.APPROVED, ClaimStatus.REJECTED, ClaimStatus.SETTLED]:
            if user_role not in ['insurance_officer', 'admin']:
                raise PermissionError(f"Role '{user_role}' is not authorized to transition claim to {target_status}")

        if target_status == ClaimStatus.DISPUTED:
            if user_role not in ['patient', 'nominee', 'admin']:
                raise PermissionError("Only patient or authorized nominee can file a dispute")

        return True
