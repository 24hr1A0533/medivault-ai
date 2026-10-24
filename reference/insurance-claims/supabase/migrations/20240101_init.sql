-- Supabase / PostgreSQL Schema Migration
-- 20240101_init.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- PostgreSQL Custom ENUM types
CREATE TYPE claim_status_enum AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED',
    'DISPUTED',
    'SETTLED'
);

-- Policies table
CREATE TABLE insurance_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    policy_holder_id UUID REFERENCES auth.users(id), -- Supabase auth dependency
    sum_insured NUMERIC(12, 2) NOT NULL,
    remaining_balance NUMERIC(12, 2) NOT NULL,
    annual_deductible NUMERIC(10, 2) NOT NULL DEFAULT 10000.00,
    deductible_satisfied NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    copay_amount NUMERIC(10, 2) NOT NULL DEFAULT 500.00,
    coinsurance_rate NUMERIC(4, 2) NOT NULL DEFAULT 0.20, -- 20% patient share
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Claims table
CREATE TABLE insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    policy_id UUID REFERENCES insurance_policies(id) ON DELETE RESTRICT,
    patient_id UUID NOT NULL,
    status claim_status_enum NOT NULL DEFAULT 'DRAFT',
    total_bill_amount NUMERIC(12, 2) NOT NULL,
    claimed_amount NUMERIC(12, 2) NOT NULL,
    approved_amount NUMERIC(12, 2) DEFAULT 0.00,
    patient_responsibility NUMERIC(12, 2) DEFAULT 0.00,
    insurer_responsibility NUMERIC(12, 2) DEFAULT 0.00,
    adjudication_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Claim documents (PostgreSQL JSONB column)
CREATE TABLE claim_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES insurance_claims(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    storage_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb, -- Postgres specific JSONB
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Claim review audit trail
CREATE TABLE claim_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES insurance_claims(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES auth.users(id),
    previous_status claim_status_enum NOT NULL,
    new_status claim_status_enum NOT NULL,
    remarks TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Supabase Row Level Security (RLS) policies
ALTER TABLE insurance_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance_claims ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Patients can view own policies"
    ON insurance_policies FOR SELECT
    USING (auth.uid() = policy_holder_id);

CREATE POLICY "Patients can view own claims"
    ON insurance_claims FOR SELECT
    USING (auth.uid() = patient_id);

CREATE POLICY "Insurance officers have full access"
    ON insurance_claims FOR ALL
    USING (EXISTS (
        SELECT 1 FROM auth.users WHERE auth.uid() = id AND raw_user_meta_data->>'role' = 'insurance_officer'
    ));
