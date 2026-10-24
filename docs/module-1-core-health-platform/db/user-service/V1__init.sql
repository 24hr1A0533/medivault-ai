-- =====================================================================
-- user-service · database: user_db · Flyway V1__init.sql
-- Owns: user directory (projection of identity accounts + managed
--       dependents without login), patient / doctor / admin profiles.
-- PII columns suffixed _enc are AES-256-GCM ciphertext under the
-- owner's data key (data_keys). Columns suffixed _bidx are HMAC-SHA256
-- blind indexes for exact-match lookup without decrypting.
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS citext;

-- Per-user data key, wrapped by an HSM-backed KEK in Azure Key Vault.
-- Destroying the row (destroyed_at + wrapped_key wiped) = crypto-shredding.
CREATE TABLE data_keys (
    owner_id      uuid         PRIMARY KEY,
    wrapped_key   bytea,                                   -- NULL after shredding
    kek_key_id    varchar(512) NOT NULL,                   -- Key Vault key id incl. version
    key_version   integer      NOT NULL DEFAULT 1,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    rotated_at    timestamptz,
    destroyed_at  timestamptz,
    CHECK ((destroyed_at IS NULL) = (wrapped_key IS NOT NULL))
);

CREATE TABLE users (
    id              uuid         PRIMARY KEY,               -- = identity user_accounts.id
    email           citext       UNIQUE,                    -- NULL for managed dependents
    display_name    varchar(120) NOT NULL,
    user_type       varchar(16)  NOT NULL CHECK (user_type IN ('PATIENT','DOCTOR','ADMIN')),
    status          varchar(24)  NOT NULL
                    CHECK (status IN ('PENDING_VERIFICATION','ACTIVE','SUSPENDED','LOCKED','DEACTIVATED')),
    has_login       boolean      NOT NULL DEFAULT true,     -- false for managed minors
    phone_enc       bytea,
    phone_bidx      bytea        UNIQUE,
    locale          varchar(10)  NOT NULL DEFAULT 'en-IN',
    timezone        varchar(64)  NOT NULL DEFAULT 'Asia/Kolkata',
    avatar_file_id  uuid,                                   -- vault-service stored_files.id
    created_at      timestamptz  NOT NULL DEFAULT now(),
    updated_at      timestamptz  NOT NULL DEFAULT now(),
    deleted_at      timestamptz,
    version         bigint       NOT NULL DEFAULT 0,
    CHECK (has_login = false OR email IS NOT NULL)
);
CREATE INDEX ix_users_type_status ON users(user_type, status) WHERE deleted_at IS NULL;

CREATE TABLE patient_profiles (
    user_id               uuid        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    mrn                   varchar(20) NOT NULL UNIQUE,      -- MediVault record number
    first_name_enc        bytea       NOT NULL,
    last_name_enc         bytea       NOT NULL,
    date_of_birth_enc     bytea       NOT NULL,
    birth_year            smallint    NOT NULL,             -- coarse, for age rules / analytics
    sex                   varchar(16) CHECK (sex IN ('MALE','FEMALE','INTERSEX','UNDISCLOSED')),
    blood_group           varchar(4)  CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
    national_id_type      varchar(16) CHECK (national_id_type IN ('AADHAAR','ABHA','PASSPORT','SSN','OTHER')),
    national_id_enc       bytea,
    national_id_bidx      bytea       UNIQUE,
    address_enc           bytea,
    emergency_summary_enc bytea,                            -- allergies, conditions, meds (JSON, encrypted)
    is_minor              boolean     NOT NULL DEFAULT false,
    managed               boolean     NOT NULL DEFAULT false, -- dependent managed by a guardian
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    version               bigint      NOT NULL DEFAULT 0
);

CREATE TABLE doctor_profiles (
    user_id                  uuid         PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    registration_number      varchar(50)  NOT NULL,
    registration_council     varchar(120) NOT NULL,
    registration_country     char(2)      NOT NULL DEFAULT 'IN',
    specialization           varchar(100) NOT NULL,
    qualifications           jsonb        NOT NULL DEFAULT '[]',
    years_experience         smallint     CHECK (years_experience BETWEEN 0 AND 80),
    affiliations             jsonb        NOT NULL DEFAULT '[]',
    verification_status      varchar(16)  NOT NULL DEFAULT 'PENDING'
                             CHECK (verification_status IN ('PENDING','UNDER_REVIEW','VERIFIED','REJECTED','SUSPENDED')),
    verification_notes       text,
    verified_by              uuid,
    verified_at              timestamptz,
    license_document_file_id uuid,                          -- vault-service stored_files.id
    created_at               timestamptz  NOT NULL DEFAULT now(),
    updated_at               timestamptz  NOT NULL DEFAULT now(),
    version                  bigint       NOT NULL DEFAULT 0,
    UNIQUE (registration_country, registration_council, registration_number),
    CHECK (verified_by IS NULL OR verified_by <> user_id)
);
CREATE INDEX ix_doctor_directory ON doctor_profiles(specialization) WHERE verification_status = 'VERIFIED';

CREATE TABLE admin_profiles (
    user_id       uuid        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    admin_level   varchar(16) NOT NULL
                  CHECK (admin_level IN ('SUPPORT','COMPLIANCE','SECURITY','SUPER_ADMIN')),
    department    varchar(100),
    ip_allowlist  cidr[]      NOT NULL DEFAULT '{}',
    approved_by   uuid        NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CHECK (approved_by <> user_id)
);

CREATE TABLE erasure_requests (
    id            uuid        PRIMARY KEY,
    user_id       uuid        NOT NULL REFERENCES users(id),
    status        varchar(16) NOT NULL DEFAULT 'REQUESTED'
                  CHECK (status IN ('REQUESTED','COOLING_OFF','IN_PROGRESS','COMPLETED','CANCELLED','REJECTED')),
    legal_hold    boolean     NOT NULL DEFAULT false,
    requested_at  timestamptz NOT NULL DEFAULT now(),
    execute_after timestamptz NOT NULL,                     -- cooling-off window
    completed_at  timestamptz
);

CREATE TABLE outbox_events (
    id              uuid         PRIMARY KEY,
    aggregate_type  varchar(64)  NOT NULL,
    aggregate_id    uuid         NOT NULL,
    event_type      varchar(128) NOT NULL,
    topic           varchar(128) NOT NULL,
    payload         jsonb        NOT NULL,
    headers         jsonb        NOT NULL DEFAULT '{}',
    created_at      timestamptz  NOT NULL DEFAULT now(),
    published_at    timestamptz
);
CREATE INDEX ix_outbox_unpublished ON outbox_events(created_at) WHERE published_at IS NULL;
