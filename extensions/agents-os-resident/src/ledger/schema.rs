//! Closed SQLite v1 schema boundary.

use std::collections::BTreeSet;

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use crate::canonical::fingerprint::sha256_hex;

use super::LedgerError;

pub const SCHEMA_VERSION: u64 = 1;
pub const SCHEMA_FINGERPRINT: &str =
    "0c5a61574a891c7cee0559f18c4bc45f70c6f24a91b65e0b826c9fd15e779f48";

/// WP0 declares the future synthetic-test-only v2 migration surface without
/// activating it. `initialize_v1` and `verify_schema` continue to accept only
/// the frozen Phase 5A schema until WP6 implements and tests the migration.
pub const M0B_SCHEMA_V2_TARGET_VERSION: u64 = 2;
pub const M0B_SCHEMA_V2_MIGRATION_STATUS: &str = "WP0_DECLARED_NOT_ACTIVE";
pub const M0B_SCHEMA_V2_NEW_TABLES: [&str; 3] = [
    "home_candidate_revision",
    "home_candidate_head",
    "home_handoff_link",
];
pub const M0B_SCHEMA_V2_NEW_INDEXES: [&str; 3] = [
    "home_candidate_revision_by_subject",
    "home_candidate_revision_by_event",
    "home_handoff_link_by_event",
];
pub const M0B_SCHEMA_V2_NEW_TRIGGERS: [&str; 4] = [
    "home_candidate_revision_no_update",
    "home_candidate_revision_no_delete",
    "home_handoff_link_no_update",
    "home_handoff_link_no_delete",
];

pub fn m0b_schema_v2_migration_sql() -> Option<&'static str> {
    None
}

pub const TABLES: [&str; 18] = [
    "canonical_fact",
    "command_definition",
    "command_envelope",
    "current_fact_pointer",
    "delivery_attempt",
    "delivery_receipt",
    "dispatch_arm",
    "event",
    "first_apply_guard",
    "inbox_command",
    "outbox_claim",
    "outbox_intent",
    "replay_index",
    "resident_authority_epoch",
    "resident_identity",
    "resident_incarnation",
    "schema_metadata",
    "task_completion",
];

pub const TRIGGERS: [&str; 2] = ["canonical_fact_no_delete", "canonical_fact_no_update"];

/// R2 schema with the exact R3-R6 replacements applied. R6 is the only
/// amendment that authorizes triggers; therefore the inventory is exactly two.
pub const SCHEMA_V1_SQL: &str = r#"
CREATE TABLE schema_metadata (
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1),
  schema_version INTEGER NOT NULL CHECK(schema_version IN (0,1)),
  schema_fingerprint TEXT NOT NULL CHECK(length(schema_fingerprint) = 64)
) STRICT;
CREATE TABLE resident_identity (
  resident_id TEXT PRIMARY KEY,
  identity_revision INTEGER NOT NULL CHECK(identity_revision > 0),
  identity_fingerprint TEXT NOT NULL CHECK(length(identity_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL CHECK(created_event_sequence > 0)
) STRICT;
CREATE TABLE command_definition (
  command_type_id TEXT NOT NULL,
  command_type_revision INTEGER NOT NULL CHECK(command_type_revision > 0),
  schema_fingerprint TEXT NOT NULL CHECK(length(schema_fingerprint) = 64),
  synthetic_only INTEGER NOT NULL CHECK(synthetic_only IN (0,1)),
  PRIMARY KEY(command_type_id, command_type_revision)
) STRICT;
CREATE TABLE inbox_command (
  command_id TEXT PRIMARY KEY,
  request_fingerprint TEXT NOT NULL CHECK(length(request_fingerprint) = 64),
  request_bytes BLOB NOT NULL,
  intake_state TEXT NOT NULL CHECK(intake_state IN ('RECEIVED','COMMITTED','REJECTED','INDETERMINATE')),
  first_event_sequence INTEGER,
  CHECK((intake_state = 'RECEIVED' AND first_event_sequence IS NULL) OR
        (intake_state <> 'RECEIVED' AND first_event_sequence IS NOT NULL))
) STRICT;
CREATE TABLE command_envelope (
  envelope_id TEXT PRIMARY KEY,
  command_id TEXT NOT NULL REFERENCES inbox_command(command_id),
  command_type_id TEXT NOT NULL,
  command_type_revision INTEGER NOT NULL,
  canonical_bytes BLOB NOT NULL,
  envelope_fingerprint TEXT NOT NULL CHECK(length(envelope_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL CHECK(created_event_sequence > 0),
  FOREIGN KEY(command_type_id, command_type_revision)
    REFERENCES command_definition(command_type_id, command_type_revision)
) STRICT;
CREATE TABLE replay_index (
  command_id TEXT PRIMARY KEY REFERENCES inbox_command(command_id),
  request_fingerprint TEXT NOT NULL CHECK(length(request_fingerprint) = 64),
  response_fingerprint TEXT NOT NULL CHECK(length(response_fingerprint) = 64),
  response_bytes BLOB NOT NULL,
  first_event_count INTEGER NOT NULL CHECK(first_event_count >= 0),
  first_external_call_count INTEGER NOT NULL CHECK(first_external_call_count >= 0)
) STRICT;
CREATE TABLE event (
  event_sequence INTEGER PRIMARY KEY CHECK(event_sequence > 0),
  event_id TEXT NOT NULL UNIQUE,
  event_kind TEXT NOT NULL,
  aggregate_ref TEXT NOT NULL,
  aggregate_revision INTEGER NOT NULL CHECK(aggregate_revision > 0),
  command_id TEXT REFERENCES inbox_command(command_id) DEFERRABLE INITIALLY DEFERRED,
  canonical_bytes BLOB NOT NULL,
  event_fingerprint TEXT NOT NULL UNIQUE CHECK(length(event_fingerprint) = 64),
  predecessor_event_fingerprint TEXT CHECK(predecessor_event_fingerprint IS NULL OR length(predecessor_event_fingerprint) = 64),
  UNIQUE(event_id, event_fingerprint),
  UNIQUE(event_sequence, event_id, event_fingerprint, event_kind, aggregate_ref, aggregate_revision)
) STRICT;
CREATE TABLE resident_incarnation (
  incarnation_id TEXT PRIMARY KEY,
  resident_id TEXT NOT NULL REFERENCES resident_identity(resident_id),
  incarnation_revision INTEGER NOT NULL CHECK(incarnation_revision > 0),
  process_nonce_fingerprint TEXT NOT NULL CHECK(length(process_nonce_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL,
  created_event_id TEXT NOT NULL CHECK(created_event_id = 'event:f3-ownership:' || resident_id || ':' || incarnation_revision),
  created_event_fingerprint TEXT NOT NULL CHECK(length(created_event_fingerprint) = 64),
  created_event_kind TEXT NOT NULL CHECK(created_event_kind = 'RESIDENT_OWNERSHIP_STARTED'),
  created_event_aggregate_ref TEXT NOT NULL CHECK(created_event_aggregate_ref = resident_id),
  created_event_aggregate_revision INTEGER NOT NULL CHECK(created_event_aggregate_revision = incarnation_revision),
  UNIQUE(resident_id, incarnation_revision),
  UNIQUE(incarnation_id, resident_id),
  UNIQUE(incarnation_id, resident_id, incarnation_revision),
  FOREIGN KEY(created_event_sequence, created_event_id, created_event_fingerprint, created_event_kind, created_event_aggregate_ref, created_event_aggregate_revision)
    REFERENCES event(event_sequence, event_id, event_fingerprint, event_kind, aggregate_ref, aggregate_revision)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE resident_authority_epoch (
  resident_id TEXT NOT NULL REFERENCES resident_identity(resident_id),
  authority_epoch INTEGER NOT NULL CHECK(authority_epoch > 0),
  epoch_fingerprint TEXT NOT NULL UNIQUE CHECK(length(epoch_fingerprint) = 64),
  expected_previous_authority_epoch INTEGER,
  previous_authority_epoch_fingerprint TEXT,
  authority_generation INTEGER NOT NULL CHECK(authority_generation > 0),
  witness_reservation_ref TEXT NOT NULL,
  witness_reservation_fingerprint TEXT NOT NULL CHECK(length(witness_reservation_fingerprint) = 64),
  incarnation_id TEXT NOT NULL,
  incarnation_revision INTEGER NOT NULL CHECK(incarnation_revision = authority_epoch),
  previous_incarnation_id TEXT,
  restore_decision_ref TEXT,
  restore_decision_fingerprint TEXT,
  ownership_event_sequence INTEGER NOT NULL,
  ownership_event_id TEXT NOT NULL CHECK(ownership_event_id = 'event:f3-ownership:' || resident_id || ':' || authority_epoch),
  ownership_event_fingerprint TEXT NOT NULL CHECK(length(ownership_event_fingerprint) = 64),
  ownership_event_kind TEXT NOT NULL CHECK(ownership_event_kind = 'RESIDENT_OWNERSHIP_STARTED'),
  ownership_event_aggregate_ref TEXT NOT NULL CHECK(ownership_event_aggregate_ref = resident_id),
  ownership_event_aggregate_revision INTEGER NOT NULL CHECK(ownership_event_aggregate_revision = authority_epoch),
  canonical_bytes BLOB NOT NULL,
  PRIMARY KEY(resident_id, authority_epoch),
  UNIQUE(resident_id, authority_epoch, incarnation_id, epoch_fingerprint),
  UNIQUE(resident_id, incarnation_id),
  FOREIGN KEY(incarnation_id, resident_id, incarnation_revision) REFERENCES resident_incarnation(incarnation_id, resident_id, incarnation_revision) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(resident_id, expected_previous_authority_epoch, previous_incarnation_id, previous_authority_epoch_fingerprint)
    REFERENCES resident_authority_epoch(resident_id, authority_epoch, incarnation_id, epoch_fingerprint)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(ownership_event_sequence, ownership_event_id, ownership_event_fingerprint, ownership_event_kind, ownership_event_aggregate_ref, ownership_event_aggregate_revision)
    REFERENCES event(event_sequence, event_id, event_fingerprint, event_kind, aggregate_ref, aggregate_revision)
    DEFERRABLE INITIALLY DEFERRED,
  CHECK((authority_epoch = 1 AND expected_previous_authority_epoch IS NULL AND previous_authority_epoch_fingerprint IS NULL AND previous_incarnation_id IS NULL) OR
        (authority_epoch > 1 AND expected_previous_authority_epoch = authority_epoch - 1 AND length(previous_authority_epoch_fingerprint) = 64 AND previous_incarnation_id IS NOT NULL AND previous_incarnation_id <> incarnation_id)),
  CHECK((restore_decision_ref IS NULL AND restore_decision_fingerprint IS NULL) OR
        (restore_decision_ref IS NOT NULL AND length(restore_decision_fingerprint) = 64))
) STRICT;
CREATE TABLE canonical_fact (
  fact_kind TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  fact_revision INTEGER NOT NULL CHECK(fact_revision > 0),
  fact_ref TEXT NOT NULL,
  subject_ref TEXT NOT NULL,
  subject_revision INTEGER NOT NULL CHECK(subject_revision > 0),
  canonical_bytes BLOB NOT NULL,
  fact_fingerprint TEXT NOT NULL CHECK(length(fact_fingerprint) = 64),
  predecessor_fact_revision INTEGER,
  predecessor_fact_ref TEXT,
  predecessor_fact_fingerprint TEXT,
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  PRIMARY KEY(fact_kind, logical_id, fact_revision),
  UNIQUE(fact_ref, fact_revision),
  UNIQUE(fact_ref, fact_revision, fact_fingerprint),
  UNIQUE(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint),
  UNIQUE(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint, subject_ref, subject_revision),
  CHECK((fact_revision = 1 AND predecessor_fact_revision IS NULL AND predecessor_fact_ref IS NULL AND predecessor_fact_fingerprint IS NULL) OR
        (fact_revision > 1 AND predecessor_fact_revision = fact_revision - 1 AND predecessor_fact_ref IS NOT NULL AND length(predecessor_fact_fingerprint) = 64)),
  FOREIGN KEY(fact_kind, logical_id, predecessor_fact_revision, predecessor_fact_ref, predecessor_fact_fingerprint)
    REFERENCES canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE current_fact_pointer (
  fact_kind TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  current_fact_revision INTEGER NOT NULL CHECK(current_fact_revision > 0),
  current_fact_ref TEXT NOT NULL,
  current_fact_fingerprint TEXT NOT NULL CHECK(length(current_fact_fingerprint) = 64),
  pointer_version INTEGER NOT NULL CHECK(pointer_version > 0),
  updated_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  PRIMARY KEY(fact_kind, logical_id),
  FOREIGN KEY(fact_kind, logical_id, current_fact_revision, current_fact_ref, current_fact_fingerprint)
    REFERENCES canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE outbox_intent (
  intent_id TEXT PRIMARY KEY,
  intent_revision INTEGER NOT NULL CHECK(intent_revision > 0),
  effect_scope_fingerprint TEXT NOT NULL CHECK(length(effect_scope_fingerprint) = 64),
  canonical_bytes BLOB NOT NULL,
  intent_fingerprint TEXT NOT NULL UNIQUE CHECK(length(intent_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence)
) STRICT;
CREATE TABLE outbox_claim (
  claim_id TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES outbox_intent(intent_id),
  claim_epoch INTEGER NOT NULL CHECK(claim_epoch > 0),
  lease_expires_at_utc TEXT NOT NULL CHECK(lease_expires_at_utc GLOB '????-??-??T??:??:??*Z'),
  lease_fact_kind TEXT NOT NULL CHECK(lease_fact_kind = 'OUTBOX_CLAIM_LEASE'),
  lease_fact_logical_id TEXT NOT NULL CHECK(lease_fact_logical_id = intent_id),
  lease_fact_ref TEXT NOT NULL,
  lease_fact_revision INTEGER NOT NULL CHECK(lease_fact_revision > 0),
  lease_fact_fingerprint TEXT NOT NULL CHECK(length(lease_fact_fingerprint) = 64),
  claim_fingerprint TEXT NOT NULL UNIQUE CHECK(length(claim_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(intent_id, claim_epoch),
  UNIQUE(claim_id, intent_id),
  FOREIGN KEY(lease_fact_kind, lease_fact_logical_id, lease_fact_revision, lease_fact_ref, lease_fact_fingerprint)
    REFERENCES canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE delivery_attempt (
  attempt_id TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES outbox_intent(intent_id),
  claim_id TEXT NOT NULL,
  attempt_revision INTEGER NOT NULL CHECK(attempt_revision > 0),
  request_id TEXT NOT NULL,
  request_fingerprint TEXT NOT NULL CHECK(length(request_fingerprint) = 64),
  request_bytes BLOB NOT NULL,
  attempt_fingerprint TEXT NOT NULL UNIQUE CHECK(length(attempt_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(intent_id, attempt_revision),
  UNIQUE(intent_id, attempt_id),
  UNIQUE(attempt_id, intent_id, claim_id),
  UNIQUE(attempt_id, intent_id, claim_id, request_id, request_fingerprint, request_bytes),
  FOREIGN KEY(claim_id, intent_id) REFERENCES outbox_claim(claim_id, intent_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE dispatch_arm (
  arm_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE,
  intent_id TEXT NOT NULL,
  claim_id TEXT NOT NULL,
  attempt_revision INTEGER NOT NULL CHECK(attempt_revision > 0),
  request_id TEXT NOT NULL,
  request_fingerprint TEXT NOT NULL CHECK(length(request_fingerprint) = 64),
  request_bytes BLOB NOT NULL,
  first_event_sequence INTEGER NOT NULL,
  first_event_ref TEXT NOT NULL CHECK(first_event_ref = 'event:f5-dispatch-arm:' || arm_id),
  first_event_fingerprint TEXT NOT NULL CHECK(length(first_event_fingerprint) = 64),
  first_event_kind TEXT NOT NULL CHECK(first_event_kind = 'F5_DISPATCH_ARMED'),
  first_event_aggregate_ref TEXT NOT NULL CHECK(first_event_aggregate_ref = intent_id),
  first_event_aggregate_revision INTEGER NOT NULL CHECK(first_event_aggregate_revision = attempt_revision),
  first_call_authorization_kind TEXT NOT NULL CHECK(first_call_authorization_kind = 'F5_CALL_AUTHORIZATION'),
  first_call_authorization_logical_id TEXT NOT NULL CHECK(first_call_authorization_logical_id = intent_id),
  first_call_authorization_ref TEXT NOT NULL CHECK(first_call_authorization_ref = 'call-auth:' || arm_id),
  first_call_authorization_revision INTEGER NOT NULL CHECK(first_call_authorization_revision > 0),
  first_call_authorization_fingerprint TEXT NOT NULL CHECK(length(first_call_authorization_fingerprint) = 64),
  first_call_authorization_subject_ref TEXT NOT NULL CHECK(first_call_authorization_subject_ref = attempt_id),
  first_call_authorization_subject_revision INTEGER NOT NULL CHECK(first_call_authorization_subject_revision = attempt_revision),
  committed_event_count INTEGER NOT NULL CHECK(committed_event_count = 1),
  committed_call_authorization_count INTEGER NOT NULL CHECK(committed_call_authorization_count = 1),
  arm_fingerprint TEXT NOT NULL UNIQUE CHECK(length(arm_fingerprint) = 64),
  armed_event_sequence INTEGER NOT NULL CHECK(armed_event_sequence = first_event_sequence),
  FOREIGN KEY(attempt_id, intent_id, claim_id, request_id, request_fingerprint, request_bytes)
    REFERENCES delivery_attempt(attempt_id, intent_id, claim_id, request_id, request_fingerprint, request_bytes)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(first_event_sequence, first_event_ref, first_event_fingerprint, first_event_kind, first_event_aggregate_ref, first_event_aggregate_revision)
    REFERENCES event(event_sequence, event_id, event_fingerprint, event_kind, aggregate_ref, aggregate_revision)
    DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(first_call_authorization_kind, first_call_authorization_logical_id, first_call_authorization_revision, first_call_authorization_ref, first_call_authorization_fingerprint, first_call_authorization_subject_ref, first_call_authorization_subject_revision)
    REFERENCES canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint, subject_ref, subject_revision)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE first_apply_guard (
  intent_id TEXT PRIMARY KEY REFERENCES outbox_intent(intent_id),
  winning_attempt_id TEXT NOT NULL UNIQUE,
  winning_claim_id TEXT NOT NULL,
  guard_revision INTEGER NOT NULL CHECK(guard_revision = 1),
  guard_fingerprint TEXT NOT NULL UNIQUE CHECK(length(guard_fingerprint) = 64),
  acquired_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(intent_id, winning_attempt_id, winning_claim_id, guard_fingerprint),
  FOREIGN KEY(winning_attempt_id, intent_id, winning_claim_id)
    REFERENCES delivery_attempt(attempt_id, intent_id, claim_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE delivery_receipt (
  source_id TEXT NOT NULL,
  receipt_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  intent_id TEXT NOT NULL,
  claim_id TEXT NOT NULL,
  receipt_revision INTEGER NOT NULL CHECK(receipt_revision > 0),
  first_apply_guard_fingerprint TEXT NOT NULL,
  receipt_state TEXT NOT NULL CHECK(receipt_state IN ('APPLIED_CURRENT','HISTORY_ONLY','REJECTED','INDETERMINATE','UNKNOWN')),
  canonical_bytes BLOB NOT NULL,
  receipt_fingerprint TEXT NOT NULL UNIQUE CHECK(length(receipt_fingerprint) = 64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  PRIMARY KEY(source_id, receipt_id),
  UNIQUE(source_id, receipt_id, receipt_revision),
  FOREIGN KEY(attempt_id, intent_id, claim_id) REFERENCES delivery_attempt(attempt_id, intent_id, claim_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY(intent_id, attempt_id, claim_id, first_apply_guard_fingerprint)
    REFERENCES first_apply_guard(intent_id, winning_attempt_id, winning_claim_id, guard_fingerprint)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE task_completion (
  task_ref TEXT NOT NULL,
  task_revision INTEGER NOT NULL CHECK(task_revision > 0),
  completion_revision INTEGER NOT NULL CHECK(completion_revision > 0),
  completion_fact_kind TEXT NOT NULL CHECK(completion_fact_kind = 'TASK_COMPLETION'),
  completion_logical_id TEXT NOT NULL,
  completion_fact_revision INTEGER NOT NULL CHECK(completion_fact_revision > 0),
  completion_fact_ref TEXT NOT NULL,
  completion_fact_fingerprint TEXT NOT NULL CHECK(length(completion_fact_fingerprint) = 64),
  completion_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  PRIMARY KEY(task_ref, task_revision, completion_revision),
  CHECK(completion_logical_id = task_ref),
  FOREIGN KEY(completion_fact_kind, completion_logical_id, completion_fact_revision, completion_fact_ref, completion_fact_fingerprint)
    REFERENCES canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, fact_fingerprint)
    DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TRIGGER canonical_fact_no_update
BEFORE UPDATE ON canonical_fact
BEGIN
  SELECT RAISE(ABORT, 'canonical_fact_immutable');
END;
CREATE TRIGGER canonical_fact_no_delete
BEFORE DELETE ON canonical_fact
BEGIN
  SELECT RAISE(ABORT, 'canonical_fact_immutable');
END;
"#;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SchemaSnapshot {
    pub version: u64,
    pub fingerprint: String,
    pub tables: Vec<String>,
    pub triggers: Vec<String>,
}

pub fn initialize_v1(connection: &mut Connection) -> Result<SchemaSnapshot, LedgerError> {
    require_connection_boundary(connection)?;
    let existing: Option<(i64, String)> = connection
        .query_row(
            "SELECT schema_version, schema_fingerprint FROM schema_metadata WHERE singleton_id = 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()
        .or_else(|error| {
            if is_missing_table(&error) {
                Ok(None)
            } else {
                Err(error)
            }
        })?;
    if existing.is_some() {
        return verify_schema(connection);
    }
    let objects: i64 = connection.query_row(
        "SELECT COUNT(*) FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'",
        [],
        |row| row.get(0),
    )?;
    if objects != 0 {
        return Err(LedgerError::SchemaMismatch(
            "nonempty database has no trusted schema_metadata".to_owned(),
        ));
    }

    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    transaction.execute_batch(SCHEMA_V1_SQL)?;
    let actual_fingerprint = inventory_fingerprint(&transaction)?;
    if actual_fingerprint != SCHEMA_FINGERPRINT {
        return Err(LedgerError::SchemaMismatch(
            "created SQLite objects do not match the compiled v1 schema seal".to_owned(),
        ));
    }
    transaction.execute(
        "INSERT INTO schema_metadata(singleton_id, schema_version, schema_fingerprint) VALUES(1, ?1, ?2)",
        params![SCHEMA_VERSION as i64, SCHEMA_FINGERPRINT],
    )?;
    transaction.commit()?;
    verify_schema(connection)
}

pub fn verify_schema(connection: &Connection) -> Result<SchemaSnapshot, LedgerError> {
    require_connection_boundary(connection)?;
    let (version, fingerprint): (i64, String) = connection.query_row(
        "SELECT schema_version, schema_fingerprint FROM schema_metadata WHERE singleton_id = 1",
        [],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    if version != SCHEMA_VERSION as i64
        || fingerprint != SCHEMA_FINGERPRINT
        || inventory_fingerprint(connection)? != SCHEMA_FINGERPRINT
    {
        return Err(LedgerError::SchemaMismatch(
            "schema metadata does not match frozen v1".to_owned(),
        ));
    }
    let extra_metadata: i64 = connection.query_row(
        "SELECT COUNT(*) FROM schema_metadata WHERE singleton_id <> 1",
        [],
        |row| row.get(0),
    )?;
    if extra_metadata != 0 {
        return Err(LedgerError::SchemaMismatch(
            "schema metadata inventory is not singleton".to_owned(),
        ));
    }
    let tables = object_names(connection, "table")?;
    let triggers = object_names(connection, "trigger")?;
    if tables != expected_set(&TABLES) || triggers != expected_set(&TRIGGERS) {
        return Err(LedgerError::SchemaMismatch(
            "SQLite object inventory differs from frozen v1".to_owned(),
        ));
    }
    Ok(SchemaSnapshot {
        version: SCHEMA_VERSION,
        fingerprint,
        tables: tables.into_iter().collect(),
        triggers: triggers.into_iter().collect(),
    })
}

fn require_connection_boundary(connection: &Connection) -> Result<(), LedgerError> {
    let attached: i64 =
        connection.query_row("SELECT COUNT(*) FROM pragma_database_list", [], |row| {
            row.get(0)
        })?;
    let foreign_keys: i64 = connection.query_row("PRAGMA foreign_keys", [], |row| row.get(0))?;
    if attached != 1 || foreign_keys != 1 {
        return Err(LedgerError::SchemaMismatch(
            "schema requires one attached database and foreign_keys=ON".to_owned(),
        ));
    }
    Ok(())
}

fn object_names(connection: &Connection, kind: &str) -> Result<BTreeSet<String>, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT name FROM sqlite_schema WHERE type = ?1 AND name NOT LIKE 'sqlite_%' ORDER BY name",
    )?;
    let rows = statement.query_map([kind], |row| row.get::<_, String>(0))?;
    Ok(rows.collect::<Result<BTreeSet<_>, _>>()?)
}

fn inventory_fingerprint(connection: &Connection) -> Result<String, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
        ))
    })?;
    let mut preimage = Vec::new();
    for row in rows {
        let (kind, name, table, sql) = row?;
        for value in [&kind, &name, &table, &sql] {
            preimage.extend_from_slice(value.len().to_string().as_bytes());
            preimage.push(b':');
            preimage.extend_from_slice(value.as_bytes());
            preimage.push(0);
        }
        *preimage.last_mut().expect("four inventory fields") = b'\n';
    }
    Ok(sha256_hex(&preimage))
}

fn expected_set<const N: usize>(values: &[&str; N]) -> BTreeSet<String> {
    values.iter().map(|value| (*value).to_owned()).collect()
}

fn is_missing_table(error: &rusqlite::Error) -> bool {
    error.to_string().contains("no such table: schema_metadata")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn connection() -> (tempfile::TempDir, Connection) {
        let root = tempfile::tempdir().expect("temporary synthetic root");
        let connection =
            Connection::open(root.path().join("schema-test.sqlite3")).expect("test database");
        connection
            .pragma_update(None, "foreign_keys", "ON")
            .expect("foreign keys");
        (root, connection)
    }

    #[test]
    fn initializes_exact_inventory_and_is_idempotent() {
        let (_root, mut connection) = connection();
        let first = initialize_v1(&mut connection).expect("initialize");
        let second = initialize_v1(&mut connection).expect("verify existing");
        assert_eq!(first, second);
        assert_eq!(first.tables.len(), 18);
        assert_eq!(first.triggers.len(), 2);
    }

    #[test]
    fn refuses_nonempty_unversioned_database() {
        let (_root, mut connection) = connection();
        connection
            .execute("CREATE TABLE attacker(value TEXT) STRICT", [])
            .expect("attacker table");
        assert!(matches!(
            initialize_v1(&mut connection),
            Err(LedgerError::SchemaMismatch(_))
        ));
    }

    #[test]
    fn detects_post_initialization_schema_inventory_drift() {
        let (_root, mut connection) = connection();
        initialize_v1(&mut connection).expect("initialize");
        connection
            .execute("CREATE TABLE unauthorized(value TEXT) STRICT", [])
            .expect("unauthorized table");
        assert!(matches!(
            verify_schema(&connection),
            Err(LedgerError::SchemaMismatch(_))
        ));
    }

    #[test]
    fn canonical_fact_history_rejects_update_and_delete() {
        let (_root, mut connection) = connection();
        initialize_v1(&mut connection).expect("initialize");
        let hash = "0".repeat(64);
        connection
            .execute(
                "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,canonical_bytes,event_fingerprint) VALUES(1,'event:test:1','TEST','logical:test',1,x'7b7d',?1)",
                [&hash],
            )
            .expect("Event");
        connection
            .execute(
                "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence) VALUES('GOAL_SPECIFICATION','logical:test',1,'fact:test:1','subject:test',1,x'7b7d',?1,1)",
                [&hash],
            )
            .expect("fact");
        assert!(connection
            .execute(
                "UPDATE canonical_fact SET canonical_bytes=x'5b5d' WHERE fact_kind='GOAL_SPECIFICATION'",
                [],
            )
            .is_err());
        assert!(
            connection
                .execute(
                    "DELETE FROM canonical_fact WHERE fact_kind='GOAL_SPECIFICATION'",
                    [],
                )
                .is_err()
        );
    }
}
