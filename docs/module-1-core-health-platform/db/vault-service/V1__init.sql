-- =====================================================================
-- vault-service · database: vault_db · Flyway V1__init.sql
-- Owns: medical records metadata, stored files (upload lifecycle,
--       malware scan state, envelope-encryption metadata).
-- Key hierarchy: Key Vault HSM KEK -> patient_vault_keys (wrapped)
--                -> per-file DEK (wrapped locally, stored on the file row).
-- =====================================================================

CREATE TABLE patient_vault_keys (
    patient_id    uuid         PRIMARY KEY,
    wrapped_key   bytea,                                   -- NULL after crypto-shredding
    kek_key_id    varchar(512) NOT NULL,
    key_version   integer      NOT NULL DEFAULT 1,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    rotated_at    timestamptz,
    destroyed_at  timestamptz,
    CHECK ((destroyed_at IS NULL) = (wrapped_key IS NOT NULL))
);

CREATE TABLE medical_records (
    id                  uuid        PRIMARY KEY,
    patient_id          uuid        NOT NULL,
    record_type         varchar(32) NOT NULL CHECK (record_type IN (
                          'LAB_REPORT','PRESCRIPTION','IMAGING','DISCHARGE_SUMMARY',
                          'CONSULTATION_NOTE','VACCINATION','INSURANCE','OTHER')),
    title_enc           bytea       NOT NULL,
    notes_enc           bytea,
    record_date         date        NOT NULL,
    provider_name_enc   bytea,
    facility_name_enc   bytea,
    tags                text[]      NOT NULL DEFAULT '{}',  -- non-PHI controlled vocabulary only
    sensitivity         varchar(16) NOT NULL DEFAULT 'NORMAL'
                        CHECK (sensitivity IN ('NORMAL','SENSITIVE','RESTRICTED')),
    source              varchar(16) NOT NULL
                        CHECK (source IN ('PATIENT','DOCTOR','FAMILY','NOMINEE','INTEGRATION')),
    created_by          uuid        NOT NULL,
    access_grant_id     uuid,                               -- grant used when created_by <> patient
    status              varchar(16) NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE','ARCHIVED','DELETED')),
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    deleted_at          timestamptz,
    version             bigint      NOT NULL DEFAULT 0,
    CHECK (created_by = patient_id OR access_grant_id IS NOT NULL)
);
CREATE INDEX ix_records_patient_date ON medical_records(patient_id, record_date DESC, id) WHERE deleted_at IS NULL;
CREATE INDEX ix_records_patient_type ON medical_records(patient_id, record_type)         WHERE deleted_at IS NULL;
CREATE INDEX ix_records_tags         ON medical_records USING gin(tags);

CREATE TABLE stored_files (
    id                     uuid         PRIMARY KEY,
    owner_id               uuid         NOT NULL,           -- patient (or doctor for licences); selects key
    record_id              uuid         REFERENCES medical_records(id),
    purpose                varchar(24)  NOT NULL CHECK (purpose IN (
                             'MEDICAL_RECORD','DOCTOR_LICENSE','EMERGENCY_EVIDENCE','AVATAR')),
    uploaded_by            uuid         NOT NULL,
    original_filename_enc  bytea        NOT NULL,
    declared_content_type  varchar(100) NOT NULL,
    detected_content_type  varchar(100),                    -- magic-byte sniffing result
    declared_size_bytes    bigint       NOT NULL CHECK (declared_size_bytes > 0 AND declared_size_bytes <= 104857600),
    size_bytes             bigint,
    declared_sha256        bytea        NOT NULL,
    sha256                 bytea,                           -- of plaintext, verified on ingest
    quarantine_blob_path   varchar(512) NOT NULL,
    blob_container         varchar(63),
    blob_path              varchar(512),
    cipher                 varchar(32)  NOT NULL DEFAULT 'AES256_GCM_HKDF_1MB',  -- Tink StreamingAead
    wrapped_dek            bytea,
    patient_key_version    integer,
    status                 varchar(20)  NOT NULL DEFAULT 'AWAITING_UPLOAD' CHECK (status IN (
                             'AWAITING_UPLOAD','UPLOADED','SCANNING','AVAILABLE','REJECTED','EXPIRED','DELETED')),
    rejection_reason       varchar(64)  CHECK (rejection_reason IN (
                             'MALWARE','TYPE_MISMATCH','SIZE_MISMATCH','HASH_MISMATCH','UNSUPPORTED_TYPE','SCAN_ERROR')),
    upload_expires_at      timestamptz  NOT NULL,
    created_at             timestamptz  NOT NULL DEFAULT now(),
    available_at           timestamptz,
    deleted_at             timestamptz,
    CHECK (purpose <> 'MEDICAL_RECORD' OR record_id IS NOT NULL),
    CHECK (status <> 'AVAILABLE' OR (wrapped_dek IS NOT NULL AND blob_path IS NOT NULL AND sha256 IS NOT NULL))
);
CREATE INDEX ix_files_record        ON stored_files(record_id) WHERE deleted_at IS NULL;
CREATE INDEX ix_files_owner         ON stored_files(owner_id)  WHERE deleted_at IS NULL;
CREATE INDEX ix_files_pending       ON stored_files(upload_expires_at) WHERE status = 'AWAITING_UPLOAD';
CREATE UNIQUE INDEX ux_files_quarantine ON stored_files(quarantine_blob_path);

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
