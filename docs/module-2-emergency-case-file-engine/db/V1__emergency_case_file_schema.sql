-- =====================================================================
-- emergency-case-file-engine · database: emergency_engine_db · Flyway V1__init.sql
-- PostgreSQL 16+ · UUIDv7 primary keys
-- Stores extracted clinical facts, normalized entities (RxNorm, SNOMED, LOINC),
-- temporal timelines, risk alerts, and synthesized emergency snapshots.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ---------------------------------------------------------------------
-- 1. Ingestion & Document Processing Jobs
-- ---------------------------------------------------------------------
CREATE TABLE document_processing_jobs (
    id                     uuid         PRIMARY KEY,
    stored_file_id         uuid         NOT NULL, -- logical ref to vault_db.stored_files.id
    patient_id             uuid         NOT NULL,
    document_type_hint     varchar(32),
    pipeline_version       varchar(32)  NOT NULL DEFAULT 'v2.4.0',
    status                 varchar(24)  NOT NULL DEFAULT 'QUEUED'
                           CHECK (status IN ('QUEUED','PREPROCESSING','OCR_IN_PROGRESS',
                                             'NER_EXTRACTING','NORMALIZING','INDEXED',
                                             'FAILED','RETRY_SCHEDULED')),
    ocr_engine_used        varchar(32)  CHECK (ocr_engine_used IN ('AZURE_DOC_INTEL','PADDLE_OCR','DOCTR','TESSERACT_HYBRID')),
    ocr_confidence_score   numeric(4,3) CHECK (ocr_confidence_score BETWEEN 0.000 AND 1.000),
    page_count             integer      NOT NULL DEFAULT 1,
    processing_time_ms     integer,
    error_code             varchar(64),
    error_message          text,
    created_at             timestamptz  NOT NULL DEFAULT now(),
    updated_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ix_doc_jobs_patient_status ON document_processing_jobs(patient_id, status);
CREATE INDEX ix_doc_jobs_file ON document_processing_jobs(stored_file_id);

-- ---------------------------------------------------------------------
-- 2. Raw Extracted Text & Layout Blocks (Spatial OCR Anchor)
-- ---------------------------------------------------------------------
CREATE TABLE document_ocr_pages (
    id                     uuid         PRIMARY KEY,
    job_id                 uuid         NOT NULL REFERENCES document_processing_jobs(id) ON DELETE CASCADE,
    page_number            integer      NOT NULL,
    width_px               integer      NOT NULL,
    height_px              integer      NOT NULL,
    rotation_deg           integer      NOT NULL DEFAULT 0,
    extracted_text         text         NOT NULL,
    layout_blocks_json     jsonb        NOT NULL DEFAULT '[]', -- bounding boxes, paragraphs, tables, key-values
    created_at             timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (job_id, page_number)
);

-- ---------------------------------------------------------------------
-- 3. Document Classification
-- ---------------------------------------------------------------------
CREATE TABLE classified_documents (
    id                     uuid         PRIMARY KEY,
    job_id                 uuid         NOT NULL REFERENCES document_processing_jobs(id) ON DELETE CASCADE,
    patient_id             uuid         NOT NULL,
    record_date            date         NOT NULL,
    primary_category       varchar(32)  NOT NULL CHECK (primary_category IN (
                             'LAB_REPORT','PRESCRIPTION','CLINICAL_NOTE','DISCHARGE_SUMMARY',
                             'IMAGING_REPORT','PATHOLOGY','IMMUNIZATION','ECG_CARDIOLOGY','OTHER')),
    sub_category           varchar(64),
    classifier_confidence  numeric(4,3) NOT NULL CHECK (classifier_confidence BETWEEN 0.000 AND 1.000),
    detected_facility_enc  bytea,       -- AES-256-GCM
    detected_physician_enc bytea,       -- AES-256-GCM
    contains_critical_flag boolean      NOT NULL DEFAULT false,
    created_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ix_class_doc_patient_date ON classified_documents(patient_id, record_date DESC);

-- ---------------------------------------------------------------------
-- 4. Extracted Clinical Entities (Standardized Terminology)
-- ---------------------------------------------------------------------
CREATE TABLE extracted_clinical_entities (
    id                     uuid         PRIMARY KEY,
    job_id                 uuid         NOT NULL REFERENCES document_processing_jobs(id) ON DELETE CASCADE,
    patient_id             uuid         NOT NULL,
    entity_type            varchar(24)  NOT NULL CHECK (entity_type IN (
                             'ALLERGY','MEDICATION','CONDITION_DIAGNOSIS','LAB_OBSERVATION',
                             'PROCEDURE','VITAL_SIGN','IMPLANT_DEVICE')),
    raw_text               varchar(255) NOT NULL,
    normalized_name        varchar(255) NOT NULL,
    code_system            varchar(24)  NOT NULL CHECK (code_system IN (
                             'RXNORM','SNOMED_CT','LOINC','ICD_10_CM','UCUM','INTERNAL')),
    standard_code          varchar(64)  NOT NULL,
    attributes             jsonb        NOT NULL DEFAULT '{}',
    -- attributes store: dosage, frequency, route, test_value, unit, reference_range, flag (HIGH/LOW/CRITICAL)
    event_timestamp        timestamptz  NOT NULL,
    confidence_score       numeric(4,3) NOT NULL CHECK (confidence_score BETWEEN 0.000 AND 1.000),
    bounding_box           jsonb,       -- {page: 1, x0, y0, x1, y1} for provenance audit
    is_negated             boolean      NOT NULL DEFAULT false, -- clinical assertion: negated vs positive
    is_historical          boolean      NOT NULL DEFAULT false, -- e.g. "past history of appendectomy in 2011"
    created_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ix_entities_patient_type_time ON extracted_clinical_entities(patient_id, entity_type, event_timestamp DESC);
CREATE INDEX ix_entities_standard_code ON extracted_clinical_entities(code_system, standard_code);
CREATE INDEX ix_entities_attrs_gin ON extracted_clinical_entities USING gin(attributes);

-- ---------------------------------------------------------------------
-- 5. Longitudinal Lab Trends (LOINC Normalized Observations)
-- ---------------------------------------------------------------------
CREATE TABLE longitudinal_lab_observations (
    id                     uuid         PRIMARY KEY,
    patient_id             uuid         NOT NULL,
    entity_id              uuid         REFERENCES extracted_clinical_entities(id) ON DELETE SET NULL,
    loinc_code             varchar(32)  NOT NULL,
    test_name              varchar(128) NOT NULL,
    numeric_value          numeric(12,4),
    string_value           varchar(64),
    unit                   varchar(32),
    ref_low                numeric(12,4),
    ref_high               numeric(12,4),
    abnormality_flag       varchar(16)  NOT NULL DEFAULT 'NORMAL'
                           CHECK (abnormality_flag IN ('NORMAL','LOW','HIGH','CRITICAL_LOW','CRITICAL_HIGH','ABNORMAL')),
    observed_at            timestamptz  NOT NULL,
    created_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ix_lab_trends_patient_loinc ON longitudinal_lab_observations(patient_id, loinc_code, observed_at DESC);

-- ---------------------------------------------------------------------
-- 6. Medication Reconciliation & Active Regimen
-- ---------------------------------------------------------------------
CREATE TABLE patient_active_medications (
    id                     uuid         PRIMARY KEY,
    patient_id             uuid         NOT NULL,
    rxnorm_cui             varchar(32)  NOT NULL,
    medication_name        varchar(255) NOT NULL,
    strength               varchar(64),
    form                   varchar(64),
    frequency              varchar(64),
    route                  varchar(32),
    start_date             date,
    last_prescribed_date   date         NOT NULL,
    estimated_end_date     date,
    status                 varchar(16)  NOT NULL DEFAULT 'ACTIVE'
                           CHECK (status IN ('ACTIVE','DISCONTINUED','COMPLETED','UNKNOWN')),
    prescribing_doctor_enc bytea,
    source_entity_id       uuid         REFERENCES extracted_clinical_entities(id),
    updated_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_active_meds_patient_rxnorm ON patient_active_medications(patient_id, rxnorm_cui) WHERE status = 'ACTIVE';

-- ---------------------------------------------------------------------
-- 7. Clinical Risk Warnings & Contraindications
-- ---------------------------------------------------------------------
CREATE TABLE clinical_risk_alerts (
    id                     uuid         PRIMARY KEY,
    patient_id             uuid         NOT NULL,
    alert_level            varchar(16)  NOT NULL CHECK (alert_level IN ('CRITICAL','HIGH','WARNING','INFO')),
    category               varchar(32)  NOT NULL CHECK (category IN (
                             'DRUG_DRUG_INTERACTION','DRUG_ALLERGY_CONTRAINDICATION','ORGAN_RISK',
                             'CRITICAL_LAB_DELTA','BLACK_BOX_WARNING','RED_FLAG_SYMPTOM')),
    title                  varchar(128) NOT NULL,
    description            text         NOT NULL,
    participating_entities jsonb        NOT NULL DEFAULT '[]', -- array of entity IDs and standard codes
    clinical_evidence      text,
    acknowledged           boolean      NOT NULL DEFAULT false,
    acknowledged_by        uuid,
    acknowledged_at        timestamptz,
    created_at             timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ix_alerts_patient_active ON clinical_risk_alerts(patient_id, alert_level, created_at DESC) WHERE NOT acknowledged;

-- ---------------------------------------------------------------------
-- 8. Emergency Case File (Synthesized 6-Month Snapshot Cache)
-- ---------------------------------------------------------------------
CREATE TABLE emergency_case_snapshots (
    id                     uuid         PRIMARY KEY,
    patient_id             uuid         NOT NULL,
    snapshot_version       integer      NOT NULL DEFAULT 1,
    time_window_start      timestamptz  NOT NULL, -- strictly now() - interval '6 months'
    time_window_end        timestamptz  NOT NULL,
    blood_group            varchar(8),
    allergies_summary      jsonb        NOT NULL DEFAULT '[]',
    critical_warnings      jsonb        NOT NULL DEFAULT '[]',
    active_medications     jsonb        NOT NULL DEFAULT '[]',
    critical_history       jsonb        NOT NULL DEFAULT '[]',
    abnormal_lab_trends    jsonb        NOT NULL DEFAULT '[]',
    physician_summary_text text         NOT NULL, -- hallucination-guarded concise medical summary
    timeline_events_count  integer      NOT NULL DEFAULT 0,
    provenance_hash        bytea        NOT NULL, -- cryptographic integrity check of source entities
    generated_at           timestamptz  NOT NULL DEFAULT now(),
    expires_at             timestamptz  NOT NULL, -- TTL max 6 hours or invalidated on new ingest
    is_current             boolean      NOT NULL DEFAULT true
);
CREATE INDEX ix_case_snapshots_patient ON emergency_case_snapshots(patient_id) WHERE is_current = true;

-- ---------------------------------------------------------------------
-- 9. Outbox Pattern for Downstream Sync
-- ---------------------------------------------------------------------
CREATE TABLE emergency_engine_outbox (
    id                     uuid         PRIMARY KEY,
    aggregate_type         varchar(64)  NOT NULL,
    aggregate_id           uuid         NOT NULL,
    event_type             varchar(128) NOT NULL,
    topic                  varchar(128) NOT NULL,
    payload                jsonb        NOT NULL,
    created_at             timestamptz  NOT NULL DEFAULT now(),
    published_at           timestamptz
);
CREATE INDEX ix_emergency_outbox_unpub ON emergency_engine_outbox(created_at) WHERE published_at IS NULL;
