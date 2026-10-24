from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date, datetime
from decimal import Decimal

class ClaimStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    SETTLED = "SETTLED"

class PolicyDomain(BaseModel):
    id: str
    policy_number: str
    provider_name: str
    policy_holder_id: str
    sum_insured: Decimal
    remaining_balance: Decimal
    annual_deductible: Decimal
    deductible_satisfied: Decimal
    copay_amount: Decimal
    coinsurance_rate: Decimal = Field(default=Decimal("0.20"), description="20% patient responsibility")
    start_date: date
    end_date: date

class ClaimItem(BaseModel):
    description: str
    category: str # Consultation, Pharmacy, Lab, Surgery
    billed_amount: Decimal
    covered_amount: Decimal

class ClaimSubmission(BaseModel):
    policy_id: str
    patient_id: str
    total_bill_amount: Decimal
    items: List[ClaimItem]

class AdjudicationResult(BaseModel):
    claim_id: Optional[str] = None
    status: ClaimStatus
    billed_amount: Decimal
    covered_expenses: Decimal
    deductible_applied: Decimal
    copay_applied: Decimal
    coinsurance_patient_amount: Decimal
    patient_total_responsibility: Decimal
    insurer_total_payout: Decimal
    remaining_policy_balance: Decimal
    notes: str
