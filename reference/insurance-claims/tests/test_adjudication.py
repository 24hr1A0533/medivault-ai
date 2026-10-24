import pytest
from decimal import Decimal
from datetime import date
from models.domain import PolicyDomain, ClaimSubmission, ClaimItem, ClaimStatus
from services.adjudication import AdjudicationEngine
from services.state_machine import ClaimStateMachine, InvalidTransitionError

@pytest.fixture
def sample_policy():
    return PolicyDomain(
        id="policy-123",
        policy_number="POL-2024-001",
        provider_name="National Health Assurance",
        policy_holder_id="patient-456",
        sum_insured=Decimal("500000.00"),
        remaining_balance=Decimal("500000.00"),
        annual_deductible=Decimal("10000.00"),
        deductible_satisfied=Decimal("0.00"),
        copay_amount=Decimal("500.00"),
        coinsurance_rate=Decimal("0.20"),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

def test_adjudication_with_deductible_and_coinsurance(sample_policy):
    submission = ClaimSubmission(
        policy_id="policy-123",
        patient_id="patient-456",
        total_bill_amount=Decimal("50000.00"),
        items=[
            ClaimItem(description="Hospital Stay", category="Room", billed_amount=Decimal("30000.00"), covered_amount=Decimal("30000.00")),
            ClaimItem(description="Medicines", category="Pharmacy", billed_amount=Decimal("20000.00"), covered_amount=Decimal("20000.00"))
        ]
    )

    result = AdjudicationEngine.adjudicate(sample_policy, submission)

    assert result.status == ClaimStatus.APPROVED
    assert result.copay_applied == Decimal("500.00")
    assert result.deductible_applied == Decimal("10000.00")
    # Covered 50000 - 500 (copay) = 49500
    # 49500 - 10000 (deductible) = 39500
    # Patient coinsurance (20%) = 7900.00
    # Insurer share (80%) = 31600.00
    assert result.coinsurance_patient_amount == Decimal("7900.00")
    assert result.insurer_total_payout == Decimal("31600.00")
    assert result.patient_total_responsibility == Decimal("18400.00") # 500 + 10000 + 7900
    assert result.remaining_policy_balance == Decimal("468400.00") # 500000 - 31600

def test_invalid_status_transition():
    with pytest.raises(InvalidTransitionError):
        ClaimStateMachine.validate_transition(ClaimStatus.DRAFT, ClaimStatus.APPROVED, user_role="insurance_officer")
