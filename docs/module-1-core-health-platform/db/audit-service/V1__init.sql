-- =====================================================================
-- audit-service · database: audit_db (isolated server in prod)
-- Append-only, monthly-partitioned, hash-chained audit log.
-- hash = SHA-256(prev_hash || canonical_json(event))   per chain_id
-- chain_id = Kafka partition of audit.events.v1 (ordered single writer).
-- =====================================================================

CREATE SEQUENCE audit_events_seq AS bigint;

CREATE TABLE audit_events (
    id                  uuid         NOT NULL,              -- producer event id (idempotency)
    occurred_at         timestamptz  NOT NULL,              -- producer time (partition key)
    received_at         timestamptz  NOT NULL DEFAULT now(),
    chain_id            smallint     NOT NULL,
    seq                 bigint       NOT NULL DEFAULT nextval('audit_events_seq'),
    source_service      varchar(32)  NOT NULL,
    category            varchar(24)  NOT NULL CHECK (category IN (
                          'AUTHENTICATION','AUTHORIZATION','PHI_ACCESS','PHI_CHANGE','CONSENT',
                          'EMERGENCY','ADMIN','SECURITY','SYSTEM')),
    action              varchar(64)  NOT NULL,              -- e.g. RECORD_VIEWED, LOGIN_FAILED
    outcome             varchar(16)  NOT NULL CHECK (outcome IN ('SUCCESS','FAILURE','DENIED','ERROR')),
    actor_id            uuid,
    actor_type          varchar(16)  NOT NULL CHECK (actor_type IN ('USER','SERVICE','SYSTEM','ANONYMOUS')),
    actor_roles         text[]       NOT NULL DEFAULT '{}',
    on_behalf_of        uuid,
    subject_patient_id  uuid,
    resource_type       varchar(32),
    resource_id         varchar(64),
    access_basis        varchar(16)  CHECK (access_basis IN (
                          'OWNER','CONSENT','FAMILY','GUARDIAN','NOMINEE','BREAK_GLASS','ADMIN','SYSTEM')),
    grant_id            uuid,
    session_id          uuid,
    ip_address          inet,
    user_agent          varchar(512),
    device_id           varchar(128),
    trace_id            varchar(32),
    details             jsonb        NOT NULL DEFAULT '{}', -- never contains PHI values
    prev_hash           bytea        NOT NULL,
    hash                bytea        NOT NULL,
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

CREATE INDEX ix_audit_patient  ON audit_events(subject_patient_id, occurred_at DESC);
CREATE INDEX ix_audit_actor    ON audit_events(actor_id, occurred_at DESC);
CREATE INDEX ix_audit_category ON audit_events(category, action, occurred_at DESC);
CREATE INDEX ix_audit_chain    ON audit_events(chain_id, seq);

-- Monthly partitions are managed by pg_partman (premake = 3, retention
-- handled by the archive job, never by the application role):
--   SELECT partman.create_parent('public.audit_events','occurred_at','1 month');
CREATE TABLE audit_events_default PARTITION OF audit_events DEFAULT;

-- Current head of each chain; updated in the same transaction as the insert
-- (SELECT ... FOR UPDATE) so the chain is strictly ordered.
CREATE TABLE audit_chain_heads (
    chain_id    smallint    PRIMARY KEY,
    last_seq    bigint      NOT NULL,
    last_hash   bytea       NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Periodic anchors written to immutable (WORM) Blob storage, signed with a
-- Key Vault key, so tampering with the DB is detectable externally.
CREATE TABLE audit_anchors (
    id           bigserial    PRIMARY KEY,
    chain_id     smallint     NOT NULL,
    last_seq     bigint       NOT NULL,
    head_hash    bytea        NOT NULL,
    signature    bytea        NOT NULL,
    blob_uri     varchar(512) NOT NULL,
    anchored_at  timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (chain_id, last_seq)
);

CREATE TABLE audit_export_jobs (
    id             uuid        PRIMARY KEY,
    requested_by   uuid        NOT NULL,
    approved_by    uuid,
    justification  text        NOT NULL,
    filter         jsonb       NOT NULL,
    status         varchar(16) NOT NULL DEFAULT 'PENDING_APPROVAL'
                   CHECK (status IN ('PENDING_APPROVAL','APPROVED','RUNNING','COMPLETED','REJECTED','FAILED')),
    result_blob_uri varchar(512),
    created_at     timestamptz NOT NULL DEFAULT now(),
    completed_at   timestamptz,
    CHECK (approved_by IS NULL OR approved_by <> requested_by)
);

-- ------------------------------------------------------ Immutability
CREATE OR REPLACE FUNCTION audit_block_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_events is append-only (% blocked)', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END $$;

CREATE TRIGGER trg_audit_events_immutable
    BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION audit_block_mutation();

CREATE TRIGGER trg_audit_anchors_immutable
    BEFORE UPDATE OR DELETE ON audit_anchors
    FOR EACH ROW EXECUTE FUNCTION audit_block_mutation();

-- Application role may only INSERT/SELECT. Roles are provisioned by
-- Terraform; grants are applied only if the role exists.
REVOKE UPDATE, DELETE, TRUNCATE ON audit_events, audit_anchors FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_app') THEN
        GRANT SELECT, INSERT ON audit_events, audit_anchors, audit_export_jobs TO audit_app;
        GRANT SELECT, INSERT, UPDATE ON audit_chain_heads TO audit_app;
        GRANT UPDATE (status, approved_by, result_blob_uri, completed_at) ON audit_export_jobs TO audit_app;
        GRANT USAGE ON SEQUENCE audit_events_seq, audit_anchors_id_seq TO audit_app;
    END IF;
END $$;
