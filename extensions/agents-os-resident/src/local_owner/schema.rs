//! Clean local-owner ledger schema. This profile is deliberately separate
//! from the historical synthetic schema and exposes no effect/outbox tables.

use rusqlite::Connection;

use crate::canonical::fingerprint::sha256_hex;

use super::{LocalOwnerError, PACKAGE_VERSION, PROFILE_ID};

pub const F1_ACCEPTANCE_DECISION_SHA256: &str =
    "e49e572055b8e367d38cc70297f5ee144482f4023c62aa46e74de35d999977b2";
pub const F6_ACCEPTANCE_DECISION_SHA256: &str =
    "6bbe48030f6a739d683253f40b4ae122671ac801761eb7a752215c1b84920890";

pub const COMMAND_TYPES: [&str; 10] = [
    "CREATE_GOAL_BUNDLE",
    "START_GOAL",
    "PAUSE_GOAL",
    "RESUME_GOAL",
    "REQUEST_COMPLETION_REVIEW",
    "CLOSE_GOAL_ACHIEVED",
    "START_TASK",
    "PAUSE_TASK",
    "RESUME_TASK",
    "COMPLETE_TASK_MANUALLY",
];

pub const TABLES: [&str; 22] = [
    "canonical_fact",
    "command_record",
    "command_registry",
    "completion_guard",
    "criterion",
    "criterion_decision",
    "current_pointer",
    "event",
    "goal",
    "owner_consent_replay_index",
    "plan_membership",
    "plan_revision",
    "quiescence_proof",
    "resident_authority_epoch",
    "resident_identity",
    "resident_incarnation",
    "result_candidate",
    "runtime_contract_profile",
    "task",
    "validation_attempt",
    "validation_requirement",
    "validation_set",
];

pub const SCHEMA_SQL: &str = r#"
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=0;

CREATE TABLE runtime_contract_profile (
  profile_id TEXT PRIMARY KEY,
  package_version TEXT NOT NULL,
  activation_mode TEXT NOT NULL,
  command_channel_mode TEXT NOT NULL,
  owner_consent_mode TEXT NOT NULL,
  authentication_assurance TEXT NOT NULL,
  f1_acceptance_decision_sha256 TEXT NOT NULL CHECK(length(f1_acceptance_decision_sha256)=64),
  f6_acceptance_decision_sha256 TEXT NOT NULL CHECK(length(f6_acceptance_decision_sha256)=64),
  command_registry_fingerprint TEXT NOT NULL CHECK(length(command_registry_fingerprint)=64),
  schema_fingerprint TEXT NOT NULL CHECK(length(schema_fingerprint)=64),
  runtime_usable INTEGER NOT NULL CHECK(runtime_usable=0),
  provider_enabled INTEGER NOT NULL CHECK(provider_enabled=0),
  memory_enabled INTEGER NOT NULL CHECK(memory_enabled=0),
  external_effects_enabled INTEGER NOT NULL CHECK(external_effects_enabled=0)
) STRICT;

CREATE TABLE command_registry (
  command_type TEXT PRIMARY KEY,
  effect_class TEXT NOT NULL CHECK(effect_class='LEDGER_ONLY'),
  requires_owner_consent INTEGER NOT NULL CHECK(requires_owner_consent=1),
  provider_allowed INTEGER NOT NULL CHECK(provider_allowed=0),
  memory_allowed INTEGER NOT NULL CHECK(memory_allowed=0),
  external_effect_allowed INTEGER NOT NULL CHECK(external_effect_allowed=0)
) STRICT;

CREATE TABLE resident_identity (
  resident_id TEXT PRIMARY KEY,
  identity_revision INTEGER NOT NULL CHECK(identity_revision=1),
  identity_fingerprint TEXT NOT NULL UNIQUE CHECK(length(identity_fingerprint)=64)
) STRICT;

CREATE TABLE event (
  event_sequence INTEGER PRIMARY KEY CHECK(event_sequence>0),
  event_id TEXT NOT NULL UNIQUE,
  event_kind TEXT NOT NULL,
  aggregate_ref TEXT NOT NULL,
  aggregate_revision INTEGER NOT NULL CHECK(aggregate_revision>0),
  command_fingerprint TEXT,
  predecessor_event_fingerprint TEXT,
  canonical_bytes BLOB NOT NULL,
  event_fingerprint TEXT NOT NULL UNIQUE CHECK(length(event_fingerprint)=64)
) STRICT;

CREATE TABLE resident_incarnation (
  incarnation_id TEXT PRIMARY KEY,
  incarnation_revision INTEGER NOT NULL UNIQUE CHECK(incarnation_revision>0),
  process_nonce_commitment TEXT NOT NULL UNIQUE CHECK(length(process_nonce_commitment)=64),
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence)
) STRICT;

CREATE TABLE resident_authority_epoch (
  authority_epoch INTEGER PRIMARY KEY CHECK(authority_epoch>0),
  authority_generation INTEGER NOT NULL UNIQUE CHECK(authority_generation=authority_epoch),
  incarnation_id TEXT NOT NULL UNIQUE REFERENCES resident_incarnation(incarnation_id),
  expected_previous_authority_epoch INTEGER,
  previous_epoch_fingerprint TEXT,
  previous_incarnation_id TEXT,
  epoch_fingerprint TEXT NOT NULL UNIQUE CHECK(length(epoch_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence),
  CHECK(
    (authority_epoch=1 AND expected_previous_authority_epoch IS NULL
      AND previous_epoch_fingerprint IS NULL AND previous_incarnation_id IS NULL)
    OR
    (authority_epoch>1 AND expected_previous_authority_epoch=authority_epoch-1
      AND previous_epoch_fingerprint IS NOT NULL AND previous_incarnation_id IS NOT NULL)
  )
) STRICT;

CREATE TABLE command_record (
  command_fingerprint TEXT PRIMARY KEY CHECK(length(command_fingerprint)=64),
  proposal_fingerprint TEXT NOT NULL UNIQUE CHECK(length(proposal_fingerprint)=64),
  command_type TEXT NOT NULL REFERENCES command_registry(command_type),
  consent_commitment TEXT NOT NULL UNIQUE CHECK(length(consent_commitment)=64),
  canonical_request_bytes BLOB NOT NULL,
  canonical_response_bytes BLOB NOT NULL,
  response_fingerprint TEXT NOT NULL CHECK(length(response_fingerprint)=64),
  first_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence),
  last_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence),
  CHECK(last_event_sequence>=first_event_sequence)
) STRICT;

CREATE TABLE owner_consent_replay_index (
  consent_commitment TEXT PRIMARY KEY CHECK(length(consent_commitment)=64),
  proposal_fingerprint TEXT NOT NULL UNIQUE CHECK(length(proposal_fingerprint)=64),
  command_fingerprint TEXT NOT NULL UNIQUE REFERENCES command_record(command_fingerprint),
  response_fingerprint TEXT NOT NULL CHECK(length(response_fingerprint)=64),
  canonical_response_bytes BLOB NOT NULL
) STRICT;

CREATE TABLE canonical_fact (
  fact_kind TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  fact_revision INTEGER NOT NULL CHECK(fact_revision>0),
  fact_ref TEXT NOT NULL UNIQUE,
  subject_ref TEXT NOT NULL,
  subject_revision INTEGER NOT NULL CHECK(subject_revision>0),
  canonical_bytes BLOB NOT NULL,
  fact_fingerprint TEXT NOT NULL UNIQUE CHECK(length(fact_fingerprint)=64),
  predecessor_fact_fingerprint TEXT,
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence),
  PRIMARY KEY(fact_kind,logical_id,fact_revision)
) STRICT;

CREATE TABLE current_pointer (
  fact_kind TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  current_fact_revision INTEGER NOT NULL CHECK(current_fact_revision>0),
  current_fact_ref TEXT NOT NULL,
  current_fact_fingerprint TEXT NOT NULL CHECK(length(current_fact_fingerprint)=64),
  pointer_version INTEGER NOT NULL CHECK(pointer_version=current_fact_revision),
  updated_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence),
  PRIMARY KEY(fact_kind,logical_id),
  FOREIGN KEY(fact_kind,logical_id,current_fact_revision)
    REFERENCES canonical_fact(fact_kind,logical_id,fact_revision)
) STRICT;

CREATE TABLE goal (
  goal_id TEXT PRIMARY KEY,
  title TEXT NOT NULL CHECK(length(title)>0),
  description TEXT NOT NULL,
  outcome_kind TEXT NOT NULL CHECK(outcome_kind='COMPLETE'),
  created_proposal_fingerprint TEXT NOT NULL CHECK(length(created_proposal_fingerprint)=64)
) STRICT;

CREATE TABLE criterion (
  criterion_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL REFERENCES goal(goal_id),
  criterion_ordinal INTEGER NOT NULL CHECK(criterion_ordinal>0),
  description TEXT NOT NULL CHECK(length(description)>0),
  assessment_kind TEXT NOT NULL CHECK(assessment_kind='HUMAN_JUDGMENT'),
  owner_kind TEXT NOT NULL CHECK(owner_kind='JENN'),
  required INTEGER NOT NULL CHECK(required=1),
  UNIQUE(goal_id,criterion_ordinal)
) STRICT;

CREATE TABLE task (
  task_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL REFERENCES goal(goal_id),
  task_ordinal INTEGER NOT NULL CHECK(task_ordinal>0),
  title TEXT NOT NULL CHECK(length(title)>0),
  description TEXT NOT NULL,
  UNIQUE(goal_id,task_ordinal)
) STRICT;

CREATE TABLE plan_revision (
  plan_id TEXT NOT NULL,
  plan_revision INTEGER NOT NULL CHECK(plan_revision=1),
  goal_id TEXT NOT NULL UNIQUE REFERENCES goal(goal_id),
  plan_fingerprint TEXT NOT NULL UNIQUE CHECK(length(plan_fingerprint)=64),
  PRIMARY KEY(plan_id,plan_revision)
) STRICT;

CREATE TABLE plan_membership (
  plan_id TEXT NOT NULL,
  plan_revision INTEGER NOT NULL,
  criterion_id TEXT NOT NULL REFERENCES criterion(criterion_id),
  task_id TEXT NOT NULL REFERENCES task(task_id),
  selected_route INTEGER NOT NULL CHECK(selected_route IN (0,1)),
  membership_fingerprint TEXT NOT NULL UNIQUE CHECK(length(membership_fingerprint)=64),
  PRIMARY KEY(plan_id,plan_revision,criterion_id,task_id),
  FOREIGN KEY(plan_id,plan_revision) REFERENCES plan_revision(plan_id,plan_revision)
) STRICT;

CREATE TABLE result_candidate (
  candidate_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES task(task_id),
  candidate_revision INTEGER NOT NULL CHECK(candidate_revision=1),
  result_summary_commitment TEXT NOT NULL CHECK(length(result_summary_commitment)=64),
  consent_commitment TEXT NOT NULL CHECK(length(consent_commitment)=64),
  candidate_fingerprint TEXT NOT NULL UNIQUE CHECK(length(candidate_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE validation_requirement (
  requirement_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES task(task_id),
  candidate_id TEXT NOT NULL UNIQUE REFERENCES result_candidate(candidate_id),
  requirement_kind TEXT NOT NULL CHECK(requirement_kind='HUMAN_ACCEPTANCE'),
  requirement_revision INTEGER NOT NULL CHECK(requirement_revision=1),
  requirement_fingerprint TEXT NOT NULL UNIQUE CHECK(length(requirement_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE validation_set (
  validation_set_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES task(task_id),
  candidate_id TEXT NOT NULL REFERENCES result_candidate(candidate_id),
  requirement_id TEXT NOT NULL UNIQUE REFERENCES validation_requirement(requirement_id),
  validation_set_revision INTEGER NOT NULL CHECK(validation_set_revision=1),
  current_attempt_id TEXT NOT NULL,
  current_decision TEXT NOT NULL CHECK(current_decision='PASSED'),
  consent_commitment TEXT NOT NULL CHECK(length(consent_commitment)=64),
  validation_set_fingerprint TEXT NOT NULL UNIQUE CHECK(length(validation_set_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(task_id,candidate_id),
  FOREIGN KEY(current_attempt_id) REFERENCES validation_attempt(attempt_id) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE validation_attempt (
  attempt_id TEXT PRIMARY KEY,
  validation_set_id TEXT NOT NULL REFERENCES validation_set(validation_set_id) DEFERRABLE INITIALLY DEFERRED,
  attempt_ordinal INTEGER NOT NULL CHECK(attempt_ordinal BETWEEN 1 AND 3),
  status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','PASSED')),
  predecessor_attempt_id TEXT REFERENCES validation_attempt(attempt_id) DEFERRABLE INITIALLY DEFERRED,
  evidence_commitment TEXT,
  attempt_fingerprint TEXT NOT NULL UNIQUE CHECK(length(attempt_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL UNIQUE REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED,
  UNIQUE(validation_set_id,attempt_ordinal),
  CHECK(
    (attempt_ordinal=1 AND status='PENDING' AND predecessor_attempt_id IS NULL AND evidence_commitment IS NULL)
    OR
    (attempt_ordinal=2 AND status='RUNNING' AND predecessor_attempt_id IS NOT NULL AND evidence_commitment IS NULL)
    OR
    (attempt_ordinal=3 AND status='PASSED' AND predecessor_attempt_id IS NOT NULL
      AND evidence_commitment IS NOT NULL AND length(evidence_commitment)=64)
  )
) STRICT;

CREATE TABLE quiescence_proof (
  proof_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES task(task_id),
  run_count INTEGER NOT NULL CHECK(run_count=0),
  effect_count INTEGER NOT NULL CHECK(effect_count=0),
  outbox_count INTEGER NOT NULL CHECK(outbox_count=0),
  control_intent_count INTEGER NOT NULL CHECK(control_intent_count=0),
  unknown_state_count INTEGER NOT NULL CHECK(unknown_state_count=0),
  proof_fingerprint TEXT NOT NULL UNIQUE CHECK(length(proof_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE completion_guard (
  completion_ref TEXT PRIMARY KEY,
  task_id TEXT NOT NULL UNIQUE REFERENCES task(task_id),
  candidate_id TEXT NOT NULL REFERENCES result_candidate(candidate_id),
  validation_set_id TEXT NOT NULL REFERENCES validation_set(validation_set_id),
  quiescence_proof_id TEXT NOT NULL REFERENCES quiescence_proof(proof_id),
  completion_fingerprint TEXT NOT NULL UNIQUE CHECK(length(completion_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TABLE criterion_decision (
  decision_ref TEXT PRIMARY KEY,
  criterion_id TEXT NOT NULL UNIQUE REFERENCES criterion(criterion_id),
  goal_id TEXT NOT NULL REFERENCES goal(goal_id),
  decision TEXT NOT NULL CHECK(decision='SATISFIED'),
  plan_fingerprint TEXT NOT NULL CHECK(length(plan_fingerprint)=64),
  membership_fingerprint TEXT NOT NULL CHECK(length(membership_fingerprint)=64),
  completion_ref TEXT NOT NULL REFERENCES completion_guard(completion_ref),
  decision_fingerprint TEXT NOT NULL UNIQUE CHECK(length(decision_fingerprint)=64),
  created_event_sequence INTEGER NOT NULL REFERENCES event(event_sequence) DEFERRABLE INITIALLY DEFERRED
) STRICT;

CREATE TRIGGER immutable_event_update BEFORE UPDATE ON event BEGIN SELECT RAISE(ABORT,'immutable event'); END;
CREATE TRIGGER immutable_event_delete BEFORE DELETE ON event BEGIN SELECT RAISE(ABORT,'immutable event'); END;
CREATE TRIGGER immutable_fact_update BEFORE UPDATE ON canonical_fact BEGIN SELECT RAISE(ABORT,'immutable fact'); END;
CREATE TRIGGER immutable_fact_delete BEFORE DELETE ON canonical_fact BEGIN SELECT RAISE(ABORT,'immutable fact'); END;
CREATE TRIGGER immutable_command_update BEFORE UPDATE ON command_record BEGIN SELECT RAISE(ABORT,'immutable command'); END;
CREATE TRIGGER immutable_command_delete BEFORE DELETE ON command_record BEGIN SELECT RAISE(ABORT,'immutable command'); END;
CREATE TRIGGER immutable_replay_update BEFORE UPDATE ON owner_consent_replay_index BEGIN SELECT RAISE(ABORT,'immutable replay'); END;
CREATE TRIGGER immutable_replay_delete BEFORE DELETE ON owner_consent_replay_index BEGIN SELECT RAISE(ABORT,'immutable replay'); END;
CREATE TRIGGER immutable_contract_profile_update BEFORE UPDATE ON runtime_contract_profile BEGIN SELECT RAISE(ABORT,'immutable contract profile'); END;
CREATE TRIGGER immutable_contract_profile_delete BEFORE DELETE ON runtime_contract_profile BEGIN SELECT RAISE(ABORT,'immutable contract profile'); END;
CREATE TRIGGER immutable_command_registry_update BEFORE UPDATE ON command_registry BEGIN SELECT RAISE(ABORT,'immutable command registry'); END;
CREATE TRIGGER immutable_command_registry_delete BEFORE DELETE ON command_registry BEGIN SELECT RAISE(ABORT,'immutable command registry'); END;
CREATE TRIGGER immutable_identity_update BEFORE UPDATE ON resident_identity BEGIN SELECT RAISE(ABORT,'immutable resident identity'); END;
CREATE TRIGGER immutable_identity_delete BEFORE DELETE ON resident_identity BEGIN SELECT RAISE(ABORT,'immutable resident identity'); END;
CREATE TRIGGER immutable_incarnation_update BEFORE UPDATE ON resident_incarnation BEGIN SELECT RAISE(ABORT,'immutable resident incarnation'); END;
CREATE TRIGGER immutable_incarnation_delete BEFORE DELETE ON resident_incarnation BEGIN SELECT RAISE(ABORT,'immutable resident incarnation'); END;
CREATE TRIGGER immutable_epoch_update BEFORE UPDATE ON resident_authority_epoch BEGIN SELECT RAISE(ABORT,'immutable authority epoch'); END;
CREATE TRIGGER immutable_epoch_delete BEFORE DELETE ON resident_authority_epoch BEGIN SELECT RAISE(ABORT,'immutable authority epoch'); END;
CREATE TRIGGER immutable_result_candidate_update BEFORE UPDATE ON result_candidate BEGIN SELECT RAISE(ABORT,'immutable result candidate'); END;
CREATE TRIGGER immutable_result_candidate_delete BEFORE DELETE ON result_candidate BEGIN SELECT RAISE(ABORT,'immutable result candidate'); END;
CREATE TRIGGER immutable_validation_requirement_update BEFORE UPDATE ON validation_requirement BEGIN SELECT RAISE(ABORT,'immutable validation requirement'); END;
CREATE TRIGGER immutable_validation_requirement_delete BEFORE DELETE ON validation_requirement BEGIN SELECT RAISE(ABORT,'immutable validation requirement'); END;
CREATE TRIGGER immutable_validation_set_update BEFORE UPDATE ON validation_set BEGIN SELECT RAISE(ABORT,'immutable validation set'); END;
CREATE TRIGGER immutable_validation_set_delete BEFORE DELETE ON validation_set BEGIN SELECT RAISE(ABORT,'immutable validation set'); END;
CREATE TRIGGER immutable_validation_attempt_update BEFORE UPDATE ON validation_attempt BEGIN SELECT RAISE(ABORT,'immutable validation attempt'); END;
CREATE TRIGGER immutable_validation_attempt_delete BEFORE DELETE ON validation_attempt BEGIN SELECT RAISE(ABORT,'immutable validation attempt'); END;
CREATE TRIGGER immutable_quiescence_update BEFORE UPDATE ON quiescence_proof BEGIN SELECT RAISE(ABORT,'immutable quiescence proof'); END;
CREATE TRIGGER immutable_quiescence_delete BEFORE DELETE ON quiescence_proof BEGIN SELECT RAISE(ABORT,'immutable quiescence proof'); END;
CREATE TRIGGER immutable_completion_update BEFORE UPDATE ON completion_guard BEGIN SELECT RAISE(ABORT,'immutable completion guard'); END;
CREATE TRIGGER immutable_completion_delete BEFORE DELETE ON completion_guard BEGIN SELECT RAISE(ABORT,'immutable completion guard'); END;
CREATE TRIGGER immutable_criterion_decision_update BEFORE UPDATE ON criterion_decision BEGIN SELECT RAISE(ABORT,'immutable criterion decision'); END;
CREATE TRIGGER immutable_criterion_decision_delete BEFORE DELETE ON criterion_decision BEGIN SELECT RAISE(ABORT,'immutable criterion decision'); END;
"#;

fn installed_schema_fingerprint(connection: &Connection) -> Result<String, LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT type,name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL ORDER BY type,name",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
        ))
    })?;
    let mut material = Vec::new();
    for row in rows {
        let (object_type, name, sql) = row?;
        material.extend_from_slice(object_type.as_bytes());
        material.push(0);
        material.extend_from_slice(name.as_bytes());
        material.push(0);
        material.extend_from_slice(sql.as_bytes());
        material.push(b'\n');
    }
    Ok(sha256_hex(&material))
}

pub fn command_registry_fingerprint() -> String {
    let joined = COMMAND_TYPES.join("\n");
    sha256_hex(
        format!("agents-os.local-owner.command-registry.v1\n{joined}").as_bytes(),
    )
}

pub fn initialize_or_verify(connection: &mut Connection) -> Result<(), LocalOwnerError> {
    let table_count: i64 = connection.query_row(
        "SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        [],
        |row| row.get(0),
    )?;
    if table_count == 0 {
        connection.execute_batch(SCHEMA_SQL)?;
        let schema_fingerprint = installed_schema_fingerprint(connection)?;
        let transaction = connection.transaction()?;
        transaction.execute(
            "INSERT INTO runtime_contract_profile(profile_id,package_version,activation_mode,command_channel_mode,owner_consent_mode,authentication_assurance,f1_acceptance_decision_sha256,f6_acceptance_decision_sha256,command_registry_fingerprint,schema_fingerprint,runtime_usable,provider_enabled,memory_enabled,external_effects_enabled) VALUES(?1,?2,'LOCAL_OWNER_SESSION_V1','LOCAL_GOAL_TASK_V1','SPOKEN_CHALLENGE_V1','LOCAL_OWNER_SESSION_ONLY',?3,?4,?5,?6,0,0,0,0)",
            rusqlite::params![
                PROFILE_ID,
                PACKAGE_VERSION,
                F1_ACCEPTANCE_DECISION_SHA256,
                F6_ACCEPTANCE_DECISION_SHA256,
                command_registry_fingerprint(),
                schema_fingerprint
            ],
        )?;
        for command_type in COMMAND_TYPES {
            transaction.execute(
                "INSERT INTO command_registry(command_type,effect_class,requires_owner_consent,provider_allowed,memory_allowed,external_effect_allowed) VALUES(?1,'LEDGER_ONLY',1,0,0,0)",
                [command_type],
            )?;
        }
        transaction.commit()?;
    }
    verify(connection)
}

pub fn verify(connection: &Connection) -> Result<(), LocalOwnerError> {
    let mut names = Vec::new();
    let mut statement = connection.prepare(
        "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name COLLATE BINARY",
    )?;
    let rows = statement.query_map([], |row| row.get::<_, String>(0))?;
    for row in rows {
        names.push(row?);
    }
    if names != TABLES {
        return Err(LocalOwnerError::SchemaMismatch);
    }

    let profile: (String, String, String, String, String, String, String, i64, i64, i64) =
        connection.query_row(
            "SELECT package_version,activation_mode,command_channel_mode,owner_consent_mode,authentication_assurance,f1_acceptance_decision_sha256,f6_acceptance_decision_sha256,runtime_usable,provider_enabled,external_effects_enabled FROM runtime_contract_profile WHERE profile_id=?1",
            [PROFILE_ID],
            |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?,row.get(3)?,row.get(4)?,row.get(5)?,row.get(6)?,row.get(7)?,row.get(8)?,row.get(9)?)),
        )?;
    if profile
        != (
            PACKAGE_VERSION.to_owned(),
            "LOCAL_OWNER_SESSION_V1".to_owned(),
            "LOCAL_GOAL_TASK_V1".to_owned(),
            "SPOKEN_CHALLENGE_V1".to_owned(),
            "LOCAL_OWNER_SESSION_ONLY".to_owned(),
            F1_ACCEPTANCE_DECISION_SHA256.to_owned(),
            F6_ACCEPTANCE_DECISION_SHA256.to_owned(),
            0,
            0,
            0,
        )
    {
        return Err(LocalOwnerError::SchemaMismatch);
    }

    let stored: (String, String, i64) = connection.query_row(
        "SELECT command_registry_fingerprint,schema_fingerprint,memory_enabled FROM runtime_contract_profile WHERE profile_id=?1",
        [PROFILE_ID],
        |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
    )?;
    if stored
        != (
            command_registry_fingerprint(),
            installed_schema_fingerprint(connection)?,
            0,
        )
    {
        return Err(LocalOwnerError::SchemaMismatch);
    }

    let mut registry = Vec::new();
    let mut statement =
        connection.prepare("SELECT command_type FROM command_registry ORDER BY command_type")?;
    let rows = statement.query_map([], |row| row.get::<_, String>(0))?;
    for row in rows {
        registry.push(row?);
    }
    let mut expected: Vec<String> = COMMAND_TYPES.iter().map(|value| (*value).to_owned()).collect();
    expected.sort();
    if registry != expected {
        return Err(LocalOwnerError::SchemaMismatch);
    }

    let fk_error_count: i64 = connection.query_row(
        "SELECT COUNT(*) FROM pragma_foreign_key_check",
        [],
        |row| row.get(0),
    )?;
    if fk_error_count != 0 {
        return Err(LocalOwnerError::SchemaMismatch);
    }
    Ok(())
}
