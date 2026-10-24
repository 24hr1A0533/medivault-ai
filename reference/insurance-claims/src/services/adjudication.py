from decimal import Decimal, ROUND_HALF_UP
from models.domain import PolicyDomain, ClaimSubmission, AdjudicationResult, ClaimStatus

class AdjudicationEngine:
    """
    Core adjudication engine calculating coverage, deductibles, copayments, and coinsurance.
    NOTE: Currently lacks database pessimistic locking (SELECT FOR UPDATE) leading to race conditions
    when multiple claims against the same policy are processed concurrently.
    """

    @staticmethod
    def adjudicate(policy: PolicyDomain, submission: ClaimSubmission) -> AdjudicationResult:
        # Step 1: Calculate total eligible covered expenses from itemized bill
        covered_expenses = sum(item.covered_amount for item in submission.items)
        if covered_expenses <= Decimal("0.00"):
            return AdjudicationResult(
                status=ClaimStatus.REJECTED,
                billed_amount=submission.total_bill_amount,
                covered_expenses=Decimal("0.00"),
                deductible_applied=Decimal("0.00"),
                copay_applied=Decimal("0.00"),
                coinsurance_patient_amount=Decimal("0.00"),
                patient_total_responsibility=submission.total_bill_amount,
                insurer_total_payout=Decimal("0.00"),
                remaining_policy_balance=policy.remaining_balance,
                notes="Zero covered expenses found in itemized claim."
            )

        # Step 2: Apply Copayment (patient pays fixed fee upfront)
        copay = min(policy.copay_amount, covered_expenses)
        expenses_after_copay = covered_expenses - copay

        # Step 3: Apply Annual Deductible
        remaining_deductible = max(Decimal("0.00"), policy.annual_deductible - policy.deductible_satisfied)
        deductible_applied = min(remaining_deductible, expenses_after_copay)
        expenses_after_deductible = expenses_after_copay - deductible_applied

        # Step 4: Apply Coinsurance on remaining covered balance
        # e.g., 20% patient, 80% insurer
        coinsurance_patient = (expenses_after_deductible * policy.coinsurance_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        insurer_share = expenses_after_deductible - coinsurance_patient

        # Step 5: Check against remaining annual policy balance
        if insurer_share > policy.remaining_balance:
            insurer_payout = policy.remaining_balance
            exhausted_uncovered = insurer_share - policy.remaining_balance
            patient_total = copay + deductible_applied + coinsurance_patient + exhausted_uncovered + (submission.total_bill_amount - covered_expenses)
            new_remaining_balance = Decimal("0.00")
            notes = "Claim approved but capped at remaining annual policy balance ceiling."
        else:
            insurer_payout = insurer_share
            patient_total = copay + deductible_applied + coinsurance_patient + (submission.total_bill_amount - covered_expenses)
            new_remaining_balance = policy.remaining_balance - insurer_payout
            notes = "Claim successfully adjudicated under policy rules."

        return AdjudicationResult(
            status=ClaimStatus.APPROVED,
            billed_amount=submission.total_bill_amount,
            covered_expenses=covered_expenses,
            deductible_applied=deductible_applied,
            copay_applied=copay,
            coinsurance_patient_amount=coinsurance_patient,
            patient_total_responsibility=patient_total,
            insurer_total_payout=insurer_payout,
            remaining_policy_balance=new_remaining_balance,
            notes=notes
        )
