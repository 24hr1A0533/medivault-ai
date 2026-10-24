-- =====================================================================
-- access-service · database: access_db · Flyway V1__init.sql
-- Owns: RBAC (roles/permissions/assignments), relationship-based grants
--       (consent, family, guardian, nominee, break-glass), Family Bridge,
--       Emergency Nominee System. Acts as the Policy Decision Point (PDP).
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS citext;

-- ---------------------------------------------------------------- RBAC
CREATE TABLE roles (
    code                 varchar(32)  PRIMARY KEY,
    description          varchar(255) NOT NULL,
    min_assurance_level  smallint     NOT NULL DEFAULT 1 CHECK (min_assurance_level BETWEEN 1 AND 3),
    max_session_minutes  integer,
    is_system            boolean      NOT NULL DEFAULT true
);

CREATE TABLE permissions (
    code         varchar(64)  PRIMARY KEY,
    description  varchar(255) NOT NULL,
    risk_level   varchar(8)   NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL'))
);

CREATE TABLE role_permissions (
    role_code        varchar(32) NOT NULL REFERENCES roles(code) ON DELETE CASCADE,
    permission_code  varchar(64) NOT NULL REFERENCES permissions(code) ON DELETE CASCADE,
    PRIMARY KEY (role_code, permission_code)
);

CREATE TABLE user_roles (
    user_id     uuid        NOT NULL,
    role_code   varchar(32) NOT NULL REFERENCES roles(code),
    granted_by  uuid,
    granted_at  timestamptz NOT NULL DEFAULT now(),
    expires_at  timestamptz,
    PRIMARY KEY (user_id, role_code)
);

-- Four-eyes: privileged role changes require a second approver.
CREATE TABLE role_change_requests (
    id              uuid        PRIMARY KEY,
    target_user_id  uuid        NOT NULL,
    role_code       varchar(32) NOT NULL REFERENCES roles(code),
    change_type     varchar(8)  NOT NULL CHECK (change_type IN ('GRANT','REVOKE')),
    justification   text        NOT NULL,
    requested_by    uuid        NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','APPROVED','REJECTED','EXPIRED')),
    decided_by      uuid,
    decided_at      timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz NOT NULL,
    CHECK (decided_by IS NULL OR decided_by <> requested_by),
    CHECK (requested_by <> target_user_id)
);

-- -------------------------------------------------------- Family Bridge
CREATE TABLE family_groups (
    id          uuid         PRIMARY KEY,
    name        varchar(100) NOT NULL,
    owner_id    uuid         NOT NULL,
    created_at  timestamptz  NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE family_members (
    id            uuid        PRIMARY KEY,
    group_id      uuid        NOT NULL REFERENCES family_groups(id) ON DELETE CASCADE,
    user_id       uuid        NOT NULL,
    relationship  varchar(24) NOT NULL
                  CHECK (relationship IN ('SELF','SPOUSE','PARENT','CHILD','SIBLING','GRANDPARENT','GRANDCHILD','GUARDIAN','CAREGIVER','OTHER')),
    group_role    varchar(16) NOT NULL DEFAULT 'MEMBER' CHECK (group_role IN ('OWNER','ADMIN','MEMBER')),
    status        varchar(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','REMOVED','LEFT')),
    joined_at     timestamptz NOT NULL DEFAULT now(),
    removed_at    timestamptz,
    UNIQUE (group_id, user_id)
);
CREATE INDEX ix_family_members_user ON family_members(user_id) WHERE status = 'ACTIVE';

CREATE TABLE family_invitations (
    id               uuid        PRIMARY KEY,
    group_id         uuid        NOT NULL REFERENCES family_groups(id) ON DELETE CASCADE,
    invited_email    citext,
    invited_phone_bidx bytea,
    relationship     varchar(24) NOT NULL,
    proposed_scopes  text[]      NOT NULL DEFAULT '{}',     -- scopes the inviter offers on THEIR data
    token_hash       bytea       NOT NULL UNIQUE,           -- SHA-256 of single-use invite token
    invited_by       uuid        NOT NULL,
    status           varchar(16) NOT NULL DEFAULT 'PENDING'
                     CHECK (status IN ('PENDING','ACCEPTED','DECLINED','EXPIRED','REVOKED')),
    expires_at       timestamptz NOT NULL,
    accepted_by      uuid,
    accepted_at      timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now(),
    CHECK (invited_email IS NOT NULL OR invited_phone_bidx IS NOT NULL)
);

-- ------------------------------------------------------------- Grants
-- One row = "grantee may perform <scopes> on <patient>'s data".
-- Every PHI access decision resolves to OWNER or exactly one grant.
CREATE TABLE access_grants (
    id              uuid        PRIMARY KEY,
    patient_id      uuid        NOT NULL,
    grantee_type    varchar(16) NOT NULL CHECK (grantee_type IN ('USER','FAMILY_GROUP')),
    grantee_id      uuid        NOT NULL,
    source          varchar(16) NOT NULL
                    CHECK (source IN ('CONSENT','FAMILY','GUARDIAN','NOMINEE','BREAK_GLASS')),
    scopes          text[]      NOT NULL CHECK (cardinality(scopes) > 0),
    record_filter   jsonb       NOT NULL DEFAULT '{}',      -- e.g. {"recordTypes":["LAB_REPORT"],"maxSensitivity":"NORMAL"}
    purpose         varchar(255),
    justification   text,                                   -- mandatory for BREAK_GLASS
    status          varchar(16) NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE','REVOKED','EXPIRED','SUSPENDED')),
    valid_from      timestamptz NOT NULL DEFAULT now(),
    expires_at      timestamptz,
    granted_by      uuid        NOT NULL,
    origin_ref_id   uuid,                                   -- access_request / activation / invitation id
    revoked_at      timestamptz,
    revoked_by      uuid,
    revoke_reason   varchar(255),
    review_status   varchar(16) CHECK (review_status IN ('PENDING','JUSTIFIED','UNJUSTIFIED')),
    reviewed_by     uuid,
    reviewed_at     timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    version         bigint      NOT NULL DEFAULT 0,
    CHECK (source <> 'BREAK_GLASS' OR (justification IS NOT NULL AND expires_at IS NOT NULL AND review_status IS NOT NULL)),
    CHECK (source NOT IN ('BREAK_GLASS','NOMINEE','CONSENT') OR expires_at IS NOT NULL),
    CHECK (expires_at IS NULL OR expires_at > valid_from)
);
CREATE INDEX ix_grants_lookup  ON access_grants(patient_id, grantee_id) WHERE status = 'ACTIVE';
CREATE INDEX ix_grants_grantee ON access_grants(grantee_id)             WHERE status = 'ACTIVE';
CREATE INDEX ix_grants_expiry  ON access_grants(expires_at)             WHERE status = 'ACTIVE';
CREATE INDEX ix_grants_review  ON access_grants(created_at)             WHERE review_status = 'PENDING';

-- Doctor -> patient consent requests.
CREATE TABLE access_requests (
    id                 uuid        PRIMARY KEY,
    patient_id         uuid        NOT NULL,
    requester_id       uuid        NOT NULL,
    requested_scopes   text[]      NOT NULL,
    purpose            varchar(255) NOT NULL,
    requested_minutes  integer     NOT NULL CHECK (requested_minutes BETWEEN 15 AND 525600),
    status             varchar(16) NOT NULL DEFAULT 'PENDING'
                       CHECK (status IN ('PENDING','APPROVED','DENIED','EXPIRED','CANCELLED')),
    decided_at         timestamptz,
    grant_id           uuid        REFERENCES access_grants(id),
    created_at         timestamptz NOT NULL DEFAULT now(),
    expires_at         timestamptz NOT NULL
);
CREATE INDEX ix_access_requests_patient ON access_requests(patient_id, status);

-- ---------------------------------------------- Emergency Nominee System
CREATE TABLE emergency_settings (
    patient_id               uuid        PRIMARY KEY,
    cooldown_minutes         integer     NOT NULL DEFAULT 1440 CHECK (cooldown_minutes BETWEEN 60 AND 10080),
    grant_duration_minutes   integer     NOT NULL DEFAULT 4320 CHECK (grant_duration_minutes BETWEEN 60 AND 20160),
    default_scopes           text[]      NOT NULL DEFAULT '{emergency_card:read,profile:read,records:read}',
    include_sensitive        boolean     NOT NULL DEFAULT false,
    allow_compliance_fast_track boolean  NOT NULL DEFAULT true,
    updated_at               timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE emergency_nominees (
    id                    uuid        PRIMARY KEY,
    patient_id            uuid        NOT NULL,
    nominee_user_id       uuid,                              -- set on acceptance
    nominee_name_enc      bytea       NOT NULL,
    contact_email         citext,
    contact_phone_enc     bytea,
    relationship          varchar(24) NOT NULL,
    priority              smallint    NOT NULL CHECK (priority BETWEEN 1 AND 5),
    scopes_override       text[],                            -- NULL = emergency_settings.default_scopes
    invite_token_hash     bytea       UNIQUE,
    status                varchar(16) NOT NULL DEFAULT 'INVITED'
                          CHECK (status IN ('INVITED','ACTIVE','DECLINED','REVOKED')),
    identity_verified_at  timestamptz,
    accepted_at           timestamptz,
    created_at            timestamptz NOT NULL DEFAULT now(),
    revoked_at            timestamptz,
    CHECK (status <> 'ACTIVE' OR nominee_user_id IS NOT NULL),
    CHECK (nominee_user_id IS NULL OR nominee_user_id <> patient_id)
);
CREATE UNIQUE INDEX ux_nominee_priority ON emergency_nominees(patient_id, priority)
    WHERE status IN ('INVITED','ACTIVE');
CREATE UNIQUE INDEX ux_nominee_user ON emergency_nominees(patient_id, nominee_user_id)
    WHERE status IN ('INVITED','ACTIVE') AND nominee_user_id IS NOT NULL;

CREATE TABLE emergency_activations (
    id                 uuid        PRIMARY KEY,
    patient_id         uuid        NOT NULL,
    nominee_id         uuid        NOT NULL REFERENCES emergency_nominees(id),
    requested_by       uuid        NOT NULL,
    reason             text        NOT NULL,
    evidence_file_id   uuid,                                 -- vault stored_files (EMERGENCY_EVIDENCE)
    status             varchar(20) NOT NULL DEFAULT 'PENDING_COOLDOWN'
                       CHECK (status IN ('PENDING_COOLDOWN','APPROVED','DENIED','EXPIRED','REVOKED','CANCELLED')),
    cooldown_until     timestamptz NOT NULL,
    decided_by         uuid,
    decision_path      varchar(20) CHECK (decision_path IN ('PATIENT','COOLDOWN_ELAPSED','COMPLIANCE_FAST_TRACK')),
    decided_at         timestamptz,
    grant_id           uuid        REFERENCES access_grants(id),
    created_at         timestamptz NOT NULL DEFAULT now(),
    CHECK (status <> 'APPROVED' OR (grant_id IS NOT NULL AND decision_path IS NOT NULL))
);
-- Only one open activation per nominee/patient pair.
CREATE UNIQUE INDEX ux_activation_open ON emergency_activations(patient_id, nominee_id)
    WHERE status IN ('PENDING_COOLDOWN','APPROVED');
CREATE INDEX ix_activation_cooldown ON emergency_activations(cooldown_until) WHERE status = 'PENDING_COOLDOWN';

-- ------------------------------------------------------------- Outbox
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

-- ---------------------------------------------------------- Seed data
INSERT INTO roles (code, description, min_assurance_level, max_session_minutes) VALUES
 ('PATIENT',          'Patient / account holder',                         1, NULL),
 ('DOCTOR',           'Verified medical practitioner',                    2, 720),
 ('ADMIN_SUPPORT',    'Account support (no clinical data)',               3, 480),
 ('ADMIN_COMPLIANCE', 'Compliance: doctor verification, audit, emergency',3, 480),
 ('ADMIN_SECURITY',   'Security operations',                              3, 480),
 ('SUPER_ADMIN',      'Platform administration (no clinical data)',       3, 240);

INSERT INTO permissions (code, description, risk_level) VALUES
 ('profile.own.manage',        'Manage own profile',                           'LOW'),
 ('records.own.manage',        'Manage own medical vault',                     'MEDIUM'),
 ('records.granted.read',      'Read records under an active grant',           'HIGH'),
 ('records.granted.write',     'Add records under an active grant',            'HIGH'),
 ('break_glass.invoke',        'Emergency break-glass access',                 'CRITICAL'),
 ('family.manage',             'Manage family groups and dependents',          'MEDIUM'),
 ('nominee.manage',            'Manage emergency nominees',                    'HIGH'),
 ('emergency.request',         'Request emergency activation as nominee',      'HIGH'),
 ('grants.own.manage',         'Grant / revoke access to own data',            'HIGH'),
 ('doctor.directory.read',     'Search verified doctors',                      'LOW'),
 ('audit.own.read',            'Read access log of own data',                  'LOW'),
 ('admin.users.read',          'Read account metadata (no PHI)',               'MEDIUM'),
 ('admin.users.suspend',       'Suspend / reactivate accounts',                'HIGH'),
 ('admin.mfa.reset.request',   'Request MFA reset for a user',                 'HIGH'),
 ('admin.mfa.reset.approve',   'Approve MFA reset',                            'CRITICAL'),
 ('admin.doctors.verify',      'Verify doctor credentials',                    'HIGH'),
 ('admin.roles.request',       'Request role change',                          'HIGH'),
 ('admin.roles.approve',       'Approve role change',                          'CRITICAL'),
 ('admin.emergency.adjudicate','Fast-track emergency activation with evidence','CRITICAL'),
 ('admin.break_glass.review',  'Review break-glass events',                    'HIGH'),
 ('audit.search',              'Search platform audit log',                    'HIGH'),
 ('audit.export',              'Export audit log',                             'CRITICAL'),
 ('audit.integrity.verify',    'Verify audit hash chain',                      'MEDIUM'),
 ('security.sessions.revoke',  'Revoke any user session',                      'HIGH');

INSERT INTO role_permissions (role_code, permission_code) VALUES
 ('PATIENT','profile.own.manage'), ('PATIENT','records.own.manage'), ('PATIENT','family.manage'),
 ('PATIENT','nominee.manage'), ('PATIENT','emergency.request'), ('PATIENT','grants.own.manage'),
 ('PATIENT','doctor.directory.read'), ('PATIENT','audit.own.read'), ('PATIENT','records.granted.read'),
 ('PATIENT','records.granted.write'),
 ('DOCTOR','profile.own.manage'), ('DOCTOR','records.granted.read'), ('DOCTOR','records.granted.write'),
 ('DOCTOR','break_glass.invoke'), ('DOCTOR','doctor.directory.read'), ('DOCTOR','emergency.request'),
 ('ADMIN_SUPPORT','admin.users.read'), ('ADMIN_SUPPORT','admin.users.suspend'), ('ADMIN_SUPPORT','admin.mfa.reset.request'),
 ('ADMIN_COMPLIANCE','admin.users.read'), ('ADMIN_COMPLIANCE','admin.doctors.verify'),
 ('ADMIN_COMPLIANCE','admin.emergency.adjudicate'), ('ADMIN_COMPLIANCE','admin.break_glass.review'),
 ('ADMIN_COMPLIANCE','audit.search'), ('ADMIN_COMPLIANCE','audit.export'),
 ('ADMIN_SECURITY','admin.users.read'), ('ADMIN_SECURITY','admin.users.suspend'), ('ADMIN_SECURITY','admin.mfa.reset.approve'),
 ('ADMIN_SECURITY','security.sessions.revoke'), ('ADMIN_SECURITY','audit.integrity.verify'), ('ADMIN_SECURITY','admin.roles.approve'),
 ('SUPER_ADMIN','admin.users.read'), ('SUPER_ADMIN','admin.roles.request'), ('SUPER_ADMIN','admin.roles.approve');
