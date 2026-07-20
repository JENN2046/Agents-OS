//! Atomic Event, immutable fact, and current-pointer CAS primitives.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use unicode_normalization::UnicodeNormalization;

use crate::canonical::fingerprint::canonical_fingerprint;
use crate::canonical::jcs::canonicalize_json;

use super::LedgerError;

const FACT_KINDS: [&str; 37] = [
    "ACTOR_IDENTITY_ASSESSMENT",
    "ACTOR_PRINCIPAL_BINDING_ASSESSMENT",
    "ASSIGNMENT_ASSESSMENT",
    "AUTHORITY_CURRENTNESS_ASSESSMENT",
    "CARRY_FORWARD_ROOT",
    "COMMAND_INTAKE_ASSESSMENT",
    "COMPLETION_GUARD_ASSESSMENT",
    "DELEGATION_ASSESSMENT",
    "EFFECT_HANDOFF",
    "F5_CALL_AUTHORIZATION",
    "F3_WITNESS_COMMIT",
    "FENCE_CURRENTNESS_ASSESSMENT",
    "GOAL_SPECIFICATION",
    "HOST_AUTHENTICATION_ASSESSMENT",
    "HOST_WORK_ACCEPTANCE",
    "OUTBOX_CLAIM_LEASE",
    "PLAN_MEMBERSHIP",
    "PLAN_REVISION",
    "PRINCIPAL_ASSESSMENT",
    "RECEIPT_COMPATIBILITY_ASSESSMENT",
    "RECEIPT_CURRENTNESS_ASSESSMENT",
    "RECONCILIATION_DECISION",
    "RESIDENT_CONTINUITY_ASSESSMENT",
    "RESIDENT_LIFECYCLE",
    "RESPONSIBILITY_ASSESSMENT",
    "REVOCATION_PROPAGATION_ASSESSMENT",
    "START_AUTHORITY_CURRENT",
    "SUCCESS_CRITERIA_SET",
    "TASK_COMPLETION",
    "TASK_PERMIT",
    "TASK_STATE_ASSESSMENT",
    "VALIDATION_ATTEMPT_CONTEXT",
    "VALIDATION_CURRENT_DECISION",
    "VALIDATION_EVIDENCE_ASSESSMENT",
    "VALIDATION_REQUIREMENT",
    "VALIDATION_SET",
    "WAIVER_CURRENTNESS_ASSESSMENT",
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FactPredecessor {
    pub revision: u64,
    pub fact_ref: String,
    pub fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CanonicalFactInput {
    pub kind: String,
    pub logical_id: String,
    pub revision: u64,
    pub fact_ref: String,
    pub subject_ref: String,
    pub subject_revision: u64,
    pub canonical_bytes: Vec<u8>,
    pub fingerprint: String,
    pub predecessor: Option<FactPredecessor>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EventInput {
    pub sequence: u64,
    pub event_id: String,
    pub kind: String,
    pub aggregate_ref: String,
    pub aggregate_revision: u64,
    pub command_id: Option<String>,
    pub canonical_bytes: Vec<u8>,
    pub fingerprint: String,
    pub predecessor_fingerprint: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PointerExpectation {
    Absent,
    Exact {
        revision: u64,
        fact_ref: String,
        fingerprint: String,
        pointer_version: u64,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TransactionFault {
    None,
    AfterPointerCasBeforeEvent,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FactAdvanceResult {
    pub fact_revision: u64,
    pub pointer_version: u64,
    pub event_sequence: u64,
}

pub fn advance_fact(
    connection: &mut Connection,
    fact: &CanonicalFactInput,
    expected: &PointerExpectation,
    event: &EventInput,
    fault: TransactionFault,
) -> Result<FactAdvanceResult, LedgerError> {
    validate_fact(fact)?;
    validate_event(event)?;
    if event.aggregate_ref != fact.logical_id || event.aggregate_revision != fact.revision {
        return Err(LedgerError::InvalidInput(
            "Event aggregate must equal the fact logical identity and revision",
        ));
    }
    let expected_revision = match expected {
        PointerExpectation::Absent => 1,
        PointerExpectation::Exact { revision, .. } => revision
            .checked_add(1)
            .ok_or(LedgerError::InvalidInput("fact revision overflow"))?,
    };
    if fact.revision != expected_revision {
        return Err(LedgerError::InvalidInput(
            "fact revision is not contiguous with pointer expectation",
        ));
    }
    match (&fact.predecessor, expected) {
        (None, PointerExpectation::Absent) => {}
        (
            Some(predecessor),
            PointerExpectation::Exact {
                revision,
                fact_ref,
                fingerprint,
                ..
            },
        ) if predecessor.revision == *revision
            && predecessor.fact_ref == *fact_ref
            && predecessor.fingerprint == *fingerprint => {}
        _ => {
            return Err(LedgerError::InvalidInput(
                "fact predecessor does not equal the expected current pointer",
            ));
        }
    }

    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    validate_event_head(&transaction, event)?;
    let predecessor = fact.predecessor.as_ref();
    transaction.execute(
        "INSERT INTO canonical_fact(fact_kind, logical_id, fact_revision, fact_ref, subject_ref, subject_revision, canonical_bytes, fact_fingerprint, predecessor_fact_revision, predecessor_fact_ref, predecessor_fact_fingerprint, created_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)",
        params![
            fact.kind,
            fact.logical_id,
            as_i64(fact.revision)?,
            fact.fact_ref,
            fact.subject_ref,
            as_i64(fact.subject_revision)?,
            fact.canonical_bytes,
            fact.fingerprint,
            predecessor.map(|value| as_i64(value.revision)).transpose()?,
            predecessor.map(|value| value.fact_ref.as_str()),
            predecessor.map(|value| value.fingerprint.as_str()),
            as_i64(event.sequence)?,
        ],
    )?;
    let pointer_version = match expected {
        PointerExpectation::Absent => {
            transaction.execute(
                "INSERT INTO current_fact_pointer(fact_kind, logical_id, current_fact_revision, current_fact_ref, current_fact_fingerprint, pointer_version, updated_event_sequence) VALUES(?1,?2,?3,?4,?5,1,?6)",
                params![fact.kind, fact.logical_id, as_i64(fact.revision)?, fact.fact_ref, fact.fingerprint, as_i64(event.sequence)?],
            )?;
            1
        }
        PointerExpectation::Exact {
            revision,
            fact_ref,
            fingerprint,
            pointer_version,
        } => {
            let next_version = pointer_version
                .checked_add(1)
                .ok_or(LedgerError::InvalidInput("pointer version overflow"))?;
            let changed = transaction.execute(
                "UPDATE current_fact_pointer SET current_fact_revision=?1,current_fact_ref=?2,current_fact_fingerprint=?3,pointer_version=?4,updated_event_sequence=?5 WHERE fact_kind=?6 AND logical_id=?7 AND current_fact_revision=?8 AND current_fact_ref=?9 AND current_fact_fingerprint=?10 AND pointer_version=?11",
                params![as_i64(fact.revision)?, fact.fact_ref, fact.fingerprint, as_i64(next_version)?, as_i64(event.sequence)?, fact.kind, fact.logical_id, as_i64(*revision)?, fact_ref, fingerprint, as_i64(*pointer_version)?],
            )?;
            if changed != 1 {
                return Err(LedgerError::StalePointer);
            }
            next_version
        }
    };
    if fault == TransactionFault::AfterPointerCasBeforeEvent {
        return Err(LedgerError::InjectedCrash);
    }
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![as_i64(event.sequence)?, event.event_id, event.kind, event.aggregate_ref, as_i64(event.aggregate_revision)?, event.command_id, event.canonical_bytes, event.fingerprint, event.predecessor_fingerprint],
    )?;
    let violations: i64 =
        transaction.query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| {
            row.get(0)
        })?;
    if violations != 0 {
        return Err(LedgerError::SchemaMismatch(
            "deferred foreign-key validation failed".to_owned(),
        ));
    }
    transaction.commit()?;
    Ok(FactAdvanceResult {
        fact_revision: fact.revision,
        pointer_version,
        event_sequence: event.sequence,
    })
}

fn validate_event_head(
    transaction: &rusqlite::Transaction<'_>,
    event: &EventInput,
) -> Result<(), LedgerError> {
    let current: Option<(i64, String)> = transaction
        .query_row(
            "SELECT event_sequence,event_fingerprint FROM event ORDER BY event_sequence DESC LIMIT 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()?;
    match current {
        None if event.sequence == 1 && event.predecessor_fingerprint.is_none() => Ok(()),
        Some((sequence, fingerprint)) => {
            let sequence = u64::try_from(sequence)
                .map_err(|_| LedgerError::InvalidInput("negative Event sequence"))?;
            if event.sequence == sequence.saturating_add(1)
                && event.predecessor_fingerprint.as_deref() == Some(fingerprint.as_str())
            {
                Ok(())
            } else {
                Err(LedgerError::InvalidInput(
                    "Event sequence or predecessor fingerprint is not the exact current head",
                ))
            }
        }
        _ => Err(LedgerError::InvalidInput(
            "Event sequence or predecessor fingerprint is not the exact current head",
        )),
    }
}

fn validate_fact(fact: &CanonicalFactInput) -> Result<(), LedgerError> {
    if !FACT_KINDS.contains(&fact.kind.as_str()) {
        return Err(LedgerError::InvalidInput("unknown fact kind"));
    }
    validate_ref(&fact.logical_id)?;
    validate_ref(&fact.fact_ref)?;
    validate_ref(&fact.subject_ref)?;
    if fact.revision == 0 || fact.subject_revision == 0 {
        return Err(LedgerError::InvalidInput("fact revisions must be positive"));
    }
    validate_canonical(&fact.canonical_bytes, &fact.fingerprint)?;
    if let Some(predecessor) = &fact.predecessor {
        validate_ref(&predecessor.fact_ref)?;
        validate_hash(&predecessor.fingerprint)?;
    }
    Ok(())
}

fn validate_event(event: &EventInput) -> Result<(), LedgerError> {
    validate_ref(&event.event_id)?;
    validate_ref(&event.kind)?;
    validate_ref(&event.aggregate_ref)?;
    if event.sequence == 0 || event.aggregate_revision == 0 {
        return Err(LedgerError::InvalidInput("Event numbers must be positive"));
    }
    if let Some(command_id) = &event.command_id {
        validate_ref(command_id)?;
    }
    validate_canonical(&event.canonical_bytes, &event.fingerprint)?;
    if let Some(predecessor) = &event.predecessor_fingerprint {
        validate_hash(predecessor)?;
    }
    Ok(())
}

pub(super) fn validate_canonical(bytes: &[u8], fingerprint: &str) -> Result<(), LedgerError> {
    if canonicalize_json(bytes)? != bytes || canonical_fingerprint(bytes)? != fingerprint {
        return Err(LedgerError::InvalidInput(
            "canonical bytes or fingerprint mismatch",
        ));
    }
    Ok(())
}

pub(crate) fn validate_ref(value: &str) -> Result<(), LedgerError> {
    if value.is_empty() || !value.nfc().eq(value.chars()) {
        return Err(LedgerError::InvalidInput(
            "stable references must be nonempty Unicode NFC strings",
        ));
    }
    Ok(())
}

pub(crate) fn validate_hash(value: &str) -> Result<(), LedgerError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(LedgerError::InvalidInput(
            "fingerprints must be lowercase SHA-256 hex",
        ));
    }
    Ok(())
}

fn as_i64(value: u64) -> Result<i64, LedgerError> {
    i64::try_from(value).map_err(|_| LedgerError::InvalidInput("integer exceeds SQLite i64"))
}
