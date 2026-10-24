# Health Insurance Claims Management & Adjudication Engine

> [!WARNING]
> Architecture constraint: This reference repository is deeply coupled to PostgreSQL and Supabase Cloud BaaS.

## Features
- Health insurance policy administration (sum insured, deductible, copayment, coinsurance)
- Automated claim adjudication logic
- Multi-tier claim review and dispute resolution workflow
- Supabase Row-Level Security (RLS) policies and PostgreSQL UUID triggers

## Technology Stack
- Backend: Python 3.10, FastAPI, Supabase Python SDK
- Database: PostgreSQL 15 (Supabase managed), PostgREST, Row Level Security
- Calculations: Float-based coverage calculations (rounding precision risks identified)

## Adjudication Business Rules
1. **Deductible**: Annual amount the policyholder must pay 100% out-of-pocket before insurance benefits kick in.
2. **Copayment (Copay)**: A fixed flat fee paid by the insured for specific covered medical encounters (e.g. ₹500 per doctor visit).
3. **Coinsurance**: The percentage of covered expenses paid by the insured (e.g., 20%) after the deductible is satisfied; the insurer pays the remaining (e.g., 80%).
4. **Policy Coverage Ceiling**: The maximum aggregate reimbursement allowed per policy year (sum insured).
5. **Claim Status Workflow**:
   `DRAFT` -> `SUBMITTED` -> `UNDER_REVIEW` -> `APPROVED` | `REJECTED` -> `DISPUTED` -> `SETTLED`
