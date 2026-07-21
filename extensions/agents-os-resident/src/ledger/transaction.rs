//! Atomic Event, immutable fact, and current-pointer CAS primitives.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use unicode_normalization::UnicodeNormalization;

use crate::canonical::fingerprint::canonical_fingerprint;
use crate::canonical::jcs::canonicalize_json;
use crate::home::candidate::{
    CandidatePredecessor, CandidateSemanticClass, HomeCandidateRevision,
    canonical_candidate_history_fingerprint, validate_materialized_candidate,
};
use crate::home::handoff::{
    HomeIntentHandoffCandidate, owner_commitment_set_fingerprint, trusted_owner_commitments,
    validate_materialized_handoff,
};

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

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HomeHeadExpectation {
    Absent,
    Exact { revision: u64, fingerprint: String },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HomeCommitFault {
    None,
    BeforeBegin,
    AfterCurrentnessRecheck,
    AfterRecordInsert,
    AfterEventInsert,
    AfterHeadCas,
    AfterCommitBeforeResponse,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HomeCommitObservation {
    FirstCommitted,
    ExactReplay,
}

pub fn commit_home_candidate(
    connection: &mut Connection,
    candidate: &HomeCandidateRevision,
    expected: &HomeHeadExpectation,
    fault: HomeCommitFault,
) -> Result<HomeCommitObservation, LedgerError> {
    super::schema::verify_schema(connection).and_then(|snapshot| {
        (snapshot.version == 2).then_some(()).ok_or_else(|| {
            LedgerError::SchemaMismatch("Home candidate writes require exact schema v2".to_owned())
        })
    })?;
    validate_home_candidate(candidate, expected)?;
    if fault == HomeCommitFault::BeforeBegin {
        return Err(LedgerError::InjectedCrash);
    }
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let existing: Option<(Vec<u8>, String)> = transaction
        .query_row(
            "SELECT canonical_bytes,candidate_fingerprint FROM home_candidate_revision WHERE candidate_id=?1 AND candidate_revision=?2",
            params![candidate.candidate_id, as_i64(candidate.candidate_revision)?],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()?;
    if let Some((bytes, fingerprint)) = existing {
        if bytes == candidate.canonical_bytes && fingerprint == candidate.candidate_fingerprint {
            transaction.commit()?;
            return Ok(HomeCommitObservation::ExactReplay);
        }
        return Err(LedgerError::InvalidInput("same Home candidate revision cannot be rewritten"));
    }

    require_expected_home_head(&transaction, candidate, expected)?;
    validate_home_event_head(&transaction, candidate.created_event_sequence)?;

    let predecessor = candidate.predecessor.as_ref();
    transaction.execute(
        "INSERT INTO home_candidate_revision(candidate_id,candidate_revision,candidate_ref,semantic_class,source_subject_ref,source_subject_revision,source_subject_fingerprint,payload_commitment,creator_assessment_ref,creator_assessment_fingerprint,canonical_bytes,candidate_fingerprint,predecessor_candidate_revision,predecessor_candidate_ref,predecessor_candidate_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16)",
        params![candidate.candidate_id,as_i64(candidate.candidate_revision)?,candidate.candidate_ref,candidate.semantic_class.as_str(),candidate.source_subject_ref,as_i64(candidate.source_subject_revision)?,candidate.source_subject_fingerprint,candidate.payload_commitment,candidate.creator_assessment_ref,candidate.creator_assessment_fingerprint,candidate.canonical_bytes,candidate.candidate_fingerprint,predecessor.map(|p|as_i64(p.candidate_revision)).transpose()?,predecessor.map(|p|p.candidate_ref.as_str()),predecessor.map(|p|p.candidate_fingerprint.as_str()),as_i64(candidate.created_event_sequence)?],
    )?;
    if fault == HomeCommitFault::AfterRecordInsert { return Err(LedgerError::InjectedCrash); }
    let event = home_event(
        &transaction,
        candidate.created_event_sequence,
        &format!("event:home-candidate:{}:{}", candidate.candidate_id, candidate.candidate_revision),
        "HOME_CANDIDATE_RECORDED",
        &candidate.candidate_ref,
        candidate.candidate_revision,
    )?;
    insert_home_event(&transaction, &event)?;
    if fault == HomeCommitFault::AfterEventInsert { return Err(LedgerError::InjectedCrash); }
    match expected {
        HomeHeadExpectation::Absent => {
            transaction.execute(
                "INSERT INTO home_candidate_head(candidate_id,semantic_class,current_candidate_revision,current_candidate_ref,current_candidate_fingerprint,pointer_version,updated_event_sequence) VALUES(?1,?2,?3,?4,?5,?3,?6)",
                params![candidate.candidate_id,candidate.semantic_class.as_str(),as_i64(candidate.candidate_revision)?,candidate.candidate_ref,candidate.candidate_fingerprint,as_i64(candidate.created_event_sequence)?],
            )?;
        }
        HomeHeadExpectation::Exact { revision, fingerprint } => {
            let changed = transaction.execute(
                "UPDATE home_candidate_head SET semantic_class=?1,current_candidate_revision=?2,current_candidate_ref=?3,current_candidate_fingerprint=?4,pointer_version=?2,updated_event_sequence=?5 WHERE candidate_id=?6 AND current_candidate_revision=?7 AND current_candidate_fingerprint=?8 AND pointer_version=?7",
                params![candidate.semantic_class.as_str(),as_i64(candidate.candidate_revision)?,candidate.candidate_ref,candidate.candidate_fingerprint,as_i64(candidate.created_event_sequence)?,candidate.candidate_id,as_i64(*revision)?,fingerprint],
            )?;
            if changed != 1 { return Err(LedgerError::StalePointer); }
        }
    }
    if fault == HomeCommitFault::AfterHeadCas { return Err(LedgerError::InjectedCrash); }
    require_no_fk_violations(&transaction)?;
    transaction.commit()?;
    if fault == HomeCommitFault::AfterCommitBeforeResponse { return Err(LedgerError::InjectedCrash); }
    Ok(HomeCommitObservation::FirstCommitted)
}

pub fn commit_home_handoff(
    connection: &mut Connection,
    handoff: &HomeIntentHandoffCandidate,
    intent_candidate_id: &str,
    fault: HomeCommitFault,
) -> Result<HomeCommitObservation, LedgerError> {
    super::schema::verify_schema(connection).and_then(|snapshot| {
        (snapshot.version == 2).then_some(()).ok_or_else(|| {
            LedgerError::SchemaMismatch("Home handoff writes require exact schema v2".to_owned())
        })
    })?;
    validate_home_handoff(handoff, intent_candidate_id)?;
    if fault == HomeCommitFault::BeforeBegin {
        return Err(LedgerError::InjectedCrash);
    }
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let existing: Option<(Vec<u8>, String)> = transaction.query_row(
        "SELECT canonical_bytes,handoff_fingerprint FROM home_handoff_link WHERE handoff_id=?1 AND handoff_revision=?2 AND intent_candidate_id=?3",
        params![handoff.handoff_candidate_id,as_i64(handoff.handoff_candidate_revision)?,intent_candidate_id],
        |row| Ok((row.get(0)?,row.get(1)?)),
    ).optional()?;
    if let Some((bytes,fingerprint))=existing {
        if bytes==handoff.canonical_bytes && fingerprint==handoff.handoff_candidate_fingerprint {
            transaction.commit()?;
            return Ok(HomeCommitObservation::ExactReplay);
        }
        return Err(LedgerError::InvalidInput("same Home handoff revision cannot be rewritten"));
    }
    let head: Option<(i64, String, String)> = transaction.query_row(
        "SELECT current_candidate_revision,current_candidate_ref,current_candidate_fingerprint FROM home_candidate_head WHERE candidate_id=?1 AND semantic_class='INTENT_CANDIDATE'",
        [intent_candidate_id],
        |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?)),
    ).optional()?;
    if head != Some((as_i64(handoff.intent_candidate_revision)?, handoff.intent_candidate_ref.clone(), handoff.intent_candidate_fingerprint.clone())) {
        return Err(LedgerError::StalePointer);
    }
    let history = load_home_candidate_history(&transaction)?;
    if canonical_candidate_history_fingerprint(&history)
        .map_err(|_| LedgerError::InvalidInput("persisted Home candidate history is invalid"))?
        != handoff.canonical_candidate_history_fingerprint
    {
        return Err(LedgerError::StalePointer);
    }
    if fault == HomeCommitFault::AfterCurrentnessRecheck {
        return Err(LedgerError::InjectedCrash);
    }
    let event_sequence = next_home_event_sequence(
        &transaction,
        handoff.minimum_trusted_event_sequence,
    )?;
    transaction.execute(
        "INSERT INTO home_handoff_link(handoff_id,handoff_revision,handoff_ref,intent_candidate_id,intent_candidate_revision,intent_candidate_ref,intent_candidate_fingerprint,owner_commitment_set_fingerprint,canonical_candidate_history_fingerprint,minimum_trusted_event_sequence,canonical_bytes,handoff_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13)",
        params![handoff.handoff_candidate_id,as_i64(handoff.handoff_candidate_revision)?,handoff.handoff_candidate_ref,intent_candidate_id,as_i64(handoff.intent_candidate_revision)?,handoff.intent_candidate_ref,handoff.intent_candidate_fingerprint,handoff.owner_commitment_set_fingerprint,handoff.canonical_candidate_history_fingerprint,as_i64(handoff.minimum_trusted_event_sequence)?,handoff.canonical_bytes,handoff.handoff_candidate_fingerprint,as_i64(event_sequence)?],
    )?;
    if fault == HomeCommitFault::AfterRecordInsert { return Err(LedgerError::InjectedCrash); }
    let event=home_event(&transaction,event_sequence,&format!("event:home-handoff:{}:{}",handoff.handoff_candidate_id,handoff.handoff_candidate_revision),"HOME_HANDOFF_RECORDED",&handoff.handoff_candidate_ref,handoff.handoff_candidate_revision)?;
    insert_home_event(&transaction,&event)?;
    if matches!(fault,HomeCommitFault::AfterEventInsert|HomeCommitFault::AfterHeadCas) { return Err(LedgerError::InjectedCrash); }
    require_no_fk_violations(&transaction)?;
    transaction.commit()?;
    if fault == HomeCommitFault::AfterCommitBeforeResponse { return Err(LedgerError::InjectedCrash); }
    Ok(HomeCommitObservation::FirstCommitted)
}

fn validate_home_candidate(
    candidate: &HomeCandidateRevision,
    expected: &HomeHeadExpectation,
) -> Result<(), LedgerError> {
    validate_materialized_candidate(candidate)
        .map_err(|_| LedgerError::InvalidInput("Home candidate is not exact canonical F7 evidence"))?;
    match (&candidate.predecessor, expected) {
        (None, HomeHeadExpectation::Absent) if candidate.candidate_revision == 1 => Ok(()),
        (
            Some(predecessor),
            HomeHeadExpectation::Exact {
                revision,
                fingerprint,
            },
        ) if candidate.candidate_revision == revision.saturating_add(1)
            && predecessor.candidate_revision == *revision
            && predecessor.candidate_fingerprint == *fingerprint => Ok(()),
        _ => Err(LedgerError::InvalidInput(
            "Home candidate predecessor does not equal expected head",
        )),
    }
}

fn validate_home_handoff(
    handoff: &HomeIntentHandoffCandidate,
    intent_candidate_id: &str,
) -> Result<(), LedgerError> {
    validate_ref(intent_candidate_id)?;
    validate_materialized_handoff(handoff)
        .map_err(|_| LedgerError::InvalidInput("Home handoff is not exact canonical F8 evidence"))?;
    let expected_owner_set = owner_commitment_set_fingerprint(&trusted_owner_commitments())
        .map_err(|_| LedgerError::InvalidInput("trusted owner commitment set is invalid"))?;
    if handoff.owner_commitment_set_fingerprint != expected_owner_set {
        return Err(LedgerError::InvalidInput(
            "Home handoff does not bind the immutable owner commitment set",
        ));
    }
    Ok(())
}

fn require_expected_home_head(
    transaction: &rusqlite::Transaction<'_>,
    candidate: &HomeCandidateRevision,
    expected: &HomeHeadExpectation,
) -> Result<(), LedgerError> {
    let current: Option<(String, i64, String, String, i64)> = transaction
        .query_row(
            "SELECT semantic_class,current_candidate_revision,current_candidate_ref,current_candidate_fingerprint,pointer_version FROM home_candidate_head WHERE candidate_id=?1",
            [&candidate.candidate_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
        )
        .optional()?;
    match (current, expected, candidate.predecessor.as_ref()) {
        (None, HomeHeadExpectation::Absent, None) => Ok(()),
        (
            Some((semantic_class, revision, reference, fingerprint, pointer_version)),
            HomeHeadExpectation::Exact {
                revision: expected_revision,
                fingerprint: expected_fingerprint,
            },
            Some(predecessor),
        ) if semantic_class == candidate.semantic_class.as_str()
            && revision == as_i64(*expected_revision)?
            && pointer_version == as_i64(*expected_revision)?
            && reference == predecessor.candidate_ref
            && fingerprint == *expected_fingerprint
            && predecessor.candidate_fingerprint == *expected_fingerprint => Ok(()),
        _ => Err(LedgerError::StalePointer),
    }
}

fn load_home_candidate_history(
    transaction: &rusqlite::Transaction<'_>,
) -> Result<Vec<HomeCandidateRevision>, LedgerError> {
    let mut statement = transaction.prepare(
        "SELECT candidate_id,candidate_revision,candidate_ref,semantic_class,source_subject_ref,source_subject_revision,source_subject_fingerprint,payload_commitment,creator_assessment_ref,creator_assessment_fingerprint,canonical_bytes,candidate_fingerprint,predecessor_candidate_revision,predecessor_candidate_ref,predecessor_candidate_fingerprint,created_event_sequence FROM home_candidate_revision ORDER BY candidate_id COLLATE BINARY,candidate_revision",
    )?;
    let rows = statement.query_map([], |row| {
        let semantic_class: String = row.get(3)?;
        let predecessor_revision: Option<i64> = row.get(12)?;
        let predecessor_ref: Option<String> = row.get(13)?;
        let predecessor_fingerprint: Option<String> = row.get(14)?;
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, String>(2)?,
            semantic_class,
            row.get::<_, String>(4)?,
            row.get::<_, i64>(5)?,
            row.get::<_, String>(6)?,
            row.get::<_, String>(7)?,
            row.get::<_, String>(8)?,
            row.get::<_, String>(9)?,
            row.get::<_, Vec<u8>>(10)?,
            row.get::<_, String>(11)?,
            predecessor_revision,
            predecessor_ref,
            predecessor_fingerprint,
            row.get::<_, i64>(15)?,
        ))
    })?;
    let mut history = Vec::new();
    for row in rows {
        let (
            candidate_id,
            candidate_revision,
            candidate_ref,
            semantic_class,
            source_subject_ref,
            source_subject_revision,
            source_subject_fingerprint,
            payload_commitment,
            creator_assessment_ref,
            creator_assessment_fingerprint,
            canonical_bytes,
            candidate_fingerprint,
            predecessor_revision,
            predecessor_ref,
            predecessor_fingerprint,
            created_event_sequence,
        ) = row?;
        let semantic_class = match semantic_class.as_str() {
            "LIFE_STREAM_CANDIDATE" => CandidateSemanticClass::LifeStream,
            "MEMORY_CANDIDATE" => CandidateSemanticClass::Memory,
            "INTENT_CANDIDATE" => CandidateSemanticClass::Intent,
            _ => return Err(LedgerError::SchemaMismatch("unknown Home semantic class".to_owned())),
        };
        let predecessor = match (
            predecessor_revision,
            predecessor_ref,
            predecessor_fingerprint,
        ) {
            (None, None, None) => None,
            (Some(revision), Some(reference), Some(fingerprint)) => Some(CandidatePredecessor {
                candidate_revision: from_i64(revision)?,
                candidate_ref: reference,
                candidate_fingerprint: fingerprint,
            }),
            _ => return Err(LedgerError::SchemaMismatch("partial Home predecessor tuple".to_owned())),
        };
        history.push(HomeCandidateRevision {
            candidate_id,
            candidate_revision: from_i64(candidate_revision)?,
            candidate_ref,
            semantic_class,
            source_subject_ref,
            source_subject_revision: from_i64(source_subject_revision)?,
            source_subject_fingerprint,
            payload_commitment,
            creator_assessment_ref,
            creator_assessment_fingerprint,
            predecessor,
            created_event_sequence: from_i64(created_event_sequence)?,
            canonical_bytes,
            candidate_fingerprint,
        });
    }
    Ok(history)
}

fn validate_home_event_head(
    transaction: &rusqlite::Transaction<'_>,
    sequence: u64,
) -> Result<(), LedgerError> {
    let current: Option<i64> = transaction
        .query_row(
            "SELECT event_sequence FROM event ORDER BY event_sequence DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .optional()?;
    match current {
        Some(value) if sequence > from_i64(value)? => Ok(()),
        _ => Err(LedgerError::InvalidInput(
            "Home Event sequence must be strictly above the exact current head",
        )),
    }
}

fn next_home_event_sequence(
    transaction: &rusqlite::Transaction<'_>,
    minimum_trusted_event_sequence: u64,
) -> Result<u64, LedgerError> {
    let current: i64 = transaction.query_row(
        "SELECT event_sequence FROM event ORDER BY event_sequence DESC LIMIT 1",
        [],
        |row| row.get(0),
    )?;
    from_i64(current)?
        .max(minimum_trusted_event_sequence)
        .checked_add(1)
        .ok_or(LedgerError::InvalidInput("Home Event sequence overflow"))
}

fn home_event(
    transaction: &rusqlite::Transaction<'_>,
    sequence: u64,
    id: &str,
    kind: &str,
    aggregate: &str,
    revision: u64,
) -> Result<EventInput, LedgerError> {
    let predecessor: Option<String> = transaction
        .query_row(
            "SELECT event_fingerprint FROM event ORDER BY event_sequence DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .optional()?;
    let bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "aggregate_ref": aggregate,
            "aggregate_revision": revision,
            "command_id": null,
            "event_id": id,
            "event_kind": kind,
            "event_sequence": sequence,
            "interface_version": "agents-os.m0b-event.v0.1",
            "predecessor_event_fingerprint": predecessor,
            "runtime_usable": false
        }))
        .map_err(|_| LedgerError::InvalidInput("Home Event serialization failed"))?,
    )?;
    Ok(EventInput {
        sequence,
        event_id: id.to_owned(),
        kind: kind.to_owned(),
        aggregate_ref: aggregate.to_owned(),
        aggregate_revision: revision,
        command_id: None,
        fingerprint: canonical_fingerprint(&bytes)?,
        canonical_bytes: bytes,
        predecessor_fingerprint: predecessor,
    })
}

fn insert_home_event(
    transaction: &rusqlite::Transaction<'_>,
    event: &EventInput,
) -> Result<(), LedgerError> {
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint) VALUES(?1,?2,?3,?4,?5,NULL,?6,?7,?8)",
        params![as_i64(event.sequence)?,event.event_id,event.kind,event.aggregate_ref,as_i64(event.aggregate_revision)?,event.canonical_bytes,event.fingerprint,event.predecessor_fingerprint],
    )?;
    Ok(())
}

fn require_no_fk_violations(
    transaction: &rusqlite::Transaction<'_>,
) -> Result<(), LedgerError> {
    let count: i64 = transaction.query_row(
        "SELECT COUNT(*) FROM pragma_foreign_key_check",
        [],
        |row| row.get(0),
    )?;
    if count == 0 {
        Ok(())
    } else {
        Err(LedgerError::SchemaMismatch(
            "Home transaction foreign-key validation failed".to_owned(),
        ))
    }
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

fn from_i64(value: i64) -> Result<u64, LedgerError> {
    u64::try_from(value).map_err(|_| LedgerError::InvalidInput("negative SQLite integer"))
}
