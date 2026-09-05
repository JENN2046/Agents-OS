//! D1 Current Work life-source projection.
//!
//! This module reads the real Goal/Task validation substrate.  It never reads
//! Goal or Task presentation fields, result bodies, activity text, or private
//! Memory material.  A result qualifies only when the complete immutable
//! completion chain and the current `TASK_STATE` pointer agree.

use rusqlite::{Connection, OptionalExtension, params};
use serde_json::{Map, Value, json};

use super::store::{canonical_value_bytes, domain_fingerprint};
use super::{LocalOwnerError, PROFILE_ID};

pub(super) const WORK_ENVELOPE_SCHEMA: &str = "AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1";
pub(super) const WORK_CURRENTNESS_POLICY_ID: &str =
    "AGENTS_OS_WORK_D1_TRANSITION_GOVERNED_CURRENTNESS_V1";
pub(super) const WORK_SOURCE_ID: &str = "RESIDENT_LOCAL_OWNER_GOAL_TASK";
pub(super) const WORK_SOURCE_OWNER: &str = "RESIDENT_VALIDATION_SUBSTRATE";
pub(super) const WORK_CATEGORY: &str = "LAST_VALIDATED_RESULT";

const MAX_SAFE_INTEGER: u64 = 9_007_199_254_740_991;
const LEGACY_WORK_SLOT: &str = "state:presence:work:v1";
const RESERVED_LIFE_SLOT: &str = "state:presence:life:v1";
const LEGACY_WORK_ENVELOPE_SCHEMA: &str = "AGENTS_OS_WORK_D1_FIRST_PROOF_ENVELOPE_V1";

/// Work is a read-only projection of the Goal/Task substrate. Generic MMR
/// callers may neither populate its former slot nor persist an envelope that
/// impersonates this producer under another state id.
pub(super) fn reject_reserved_work_projection_mutation(
    mutation: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let target = mutation
        .get("targetStateId")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::WorkSourceProfileRejected)?;
    let schema = mutation
        .get("components")
        .and_then(Value::as_object)
        .and_then(|components| components.get("content"))
        .and_then(Value::as_object)
        .and_then(|content| content.get("value"))
        .and_then(Value::as_object)
        .and_then(|content| content.get("schema"))
        .and_then(Value::as_str);
    if matches!(target, LEGACY_WORK_SLOT | RESERVED_LIFE_SLOT)
        || matches!(
            schema,
            Some(WORK_ENVELOPE_SCHEMA | LEGACY_WORK_ENVELOPE_SCHEMA)
        )
    {
        return Err(LocalOwnerError::WorkSourceProfileRejected);
    }
    Ok(())
}

pub(super) fn validate_stored_no_work_projection(value: &Value) -> Result<(), LocalOwnerError> {
    let state_id = value
        .get("stateId")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let schema = value
        .get("components")
        .and_then(|components| components.get("content"))
        .and_then(|content| content.get("value"))
        .and_then(|content| content.get("schema"))
        .and_then(Value::as_str);
    if matches!(state_id, LEGACY_WORK_SLOT | RESERVED_LIFE_SLOT)
        || matches!(
            schema,
            Some(WORK_ENVELOPE_SCHEMA | LEGACY_WORK_ENVELOPE_SCHEMA)
        )
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(())
}

pub(super) fn verify_no_stored_work_projection(
    connection: &Connection,
) -> Result<(), LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT canonical_bytes FROM canonical_fact WHERE fact_kind IN ('MMR_STATE_CORE','MMR_CANDIDATE_CORE')",
    )?;
    let rows = statement.query_map([], |row| row.get::<_, Vec<u8>>(0))?;
    for row in rows {
        let value: Value =
            serde_json::from_slice(&row?).map_err(|_| LocalOwnerError::StateCorrupt)?;
        validate_stored_no_work_projection(&value)?;
    }
    Ok(())
}

#[derive(Debug)]
struct AuthorityCut {
    authority_generation: u64,
    epoch_fingerprint: String,
    event_sequence: u64,
    subject_identity_ref: String,
}

#[derive(Debug)]
struct PointerRecord {
    fact_kind: String,
    logical_id: String,
    revision: u64,
    fact_fingerprint: String,
    updated_event_sequence: u64,
    value: Value,
}

#[derive(Debug)]
struct PointerCut {
    digest: String,
    event_sequence: u64,
    records: Vec<PointerRecord>,
}

#[derive(Debug)]
struct ValidatedResult {
    value_ref: String,
    subject_ref: String,
    validation_ref: String,
    fact_revision: u64,
    fact_fingerprint: String,
    event_sequence: u64,
    cut_material: Value,
}

#[derive(Debug)]
struct CompletionGuardRow {
    completion_ref: String,
    task_id: String,
    candidate_id: String,
    validation_set_id: String,
    proof_id: String,
    fingerprint: String,
    event_sequence: u64,
}

/// Produce a low-disclosure D1 envelope from the canonical Goal/Task tables.
///
/// `expected_source_cut_fingerprint` is an optional optimistic selector.  A
/// mismatch is stale context, never permission to fall back to an older
/// completion.  The function performs no writes and has no clock dependency,
/// so an unchanged logical cut produces byte-for-byte stable output.
pub(super) fn read_current_work_envelope(
    connection: &Connection,
    expected_authority_generation: u64,
    expected_source_cut_fingerprint: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    let authority = read_authority_cut(connection, expected_authority_generation)?;
    let pointer_cut = read_pointer_cut(connection, authority.event_sequence)?;
    let validated = qualifying_last_validated_result(connection, &pointer_cut)?;

    let source_cut_event_sequence = validated
        .as_ref()
        .map_or(pointer_cut.event_sequence, |result| {
            result.event_sequence.max(pointer_cut.event_sequence)
        })
        .max(authority.event_sequence);
    let source_revision = source_cut_event_sequence;
    let source_cut_material = json!({
        "authorityEpochFingerprint": authority.epoch_fingerprint,
        "authorityGeneration": authority.authority_generation,
        "completion": validated.as_ref().map(|result| result.cut_material.clone()),
        "currentPointerSetDigest": pointer_cut.digest,
        "eventSequence": source_cut_event_sequence,
        "sourceId": WORK_SOURCE_ID,
        "sourceOwner": WORK_SOURCE_OWNER,
        "sourceRevision": source_revision,
    });
    let source_cut_fingerprint = format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.work-d1-source-cut.v2",
            &canonical_value_bytes(&source_cut_material)?,
        )
    );
    if expected_source_cut_fingerprint.is_some_and(|expected| expected != source_cut_fingerprint) {
        return Err(LocalOwnerError::PresenceContextStale);
    }

    let last_validated_result = match validated {
        Some(result) => json!({
            "boundedRef": result.value_ref,
            "category": WORK_CATEGORY,
            "categoryState": "PRESENT",
            "domainStatus": "VALIDATED_COMPLETION",
            "factCurrentness": "CURRENT",
            "factFingerprint": result.fact_fingerprint,
            "factRevision": result.fact_revision,
            "reasonCodes": ["VALIDATED_COMPLETION_CURRENT"],
            "subjectRef": result.subject_ref,
            "validationRef": result.validation_ref,
        }),
        None => json!({
            "boundedRef": Value::Null,
            "category": WORK_CATEGORY,
            "categoryState": "ABSENT",
            "domainStatus": "NO_ACCEPTED_COMPLETION",
            "factCurrentness": "CURRENT",
            "factFingerprint": Value::Null,
            "factRevision": Value::Null,
            "reasonCodes": ["CLOSED_WORLD_NO_VALIDATED_RESULT"],
            "subjectRef": Value::Null,
            "validationRef": Value::Null,
        }),
    };
    let facts = json!([
        unknown_work_fact("ACTIVE_COMMITMENT", "NO_EXPLICIT_COMMITMENT_POLICY"),
        unknown_work_fact(
            "CURRENT_FOCUS_PROJECT_TASK",
            "NO_ACCEPTED_FOCUS_CURRENTNESS_POLICY",
        ),
        unknown_work_fact("NEXT_STEP", "NO_EXPLICIT_NEXT_STEP_SOURCE"),
        unknown_work_fact("WAITING_OR_BLOCKER", "NO_EXPLICIT_WAITING_SOURCE"),
        last_validated_result,
    ]);
    let projection_material = json!({
        "authorityGeneration": authority.authority_generation,
        "currentness": "CURRENT",
        "currentnessPolicyId": WORK_CURRENTNESS_POLICY_ID,
        "currentnessReasonCodes": ["SOURCE_CUT_VERIFIED_CURRENT"],
        "facts": facts,
        "observedAtEventSequence": source_cut_event_sequence,
        "schema": WORK_ENVELOPE_SCHEMA,
        "sourceAvailability": "AVAILABLE",
        "sourceCutEventSequence": source_cut_event_sequence,
        "sourceCutFingerprint": source_cut_fingerprint,
        "sourceId": WORK_SOURCE_ID,
        "sourceOwner": WORK_SOURCE_OWNER,
        "sourceRevision": source_revision,
        "subjectIdentityRef": authority.subject_identity_ref,
    });
    let projection_digest = format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.work-d1-projection.v2",
            &canonical_value_bytes(&projection_material)?,
        )
    );
    let mut envelope = projection_material
        .as_object()
        .cloned()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    envelope.insert(
        "projectionDigest".to_owned(),
        Value::String(projection_digest),
    );
    Ok(Value::Object(envelope))
}

fn unknown_work_fact(category: &str, reason: &str) -> Value {
    json!({
        "boundedRef": Value::Null,
        "category": category,
        "categoryState": "UNKNOWN",
        "domainStatus": Value::Null,
        "factCurrentness": "UNKNOWN",
        "factFingerprint": Value::Null,
        "factRevision": Value::Null,
        "reasonCodes": [reason],
        "subjectRef": Value::Null,
        "validationRef": Value::Null,
    })
}

fn read_authority_cut(
    connection: &Connection,
    expected_authority_generation: u64,
) -> Result<AuthorityCut, LocalOwnerError> {
    if expected_authority_generation == 0 || expected_authority_generation > MAX_SAFE_INTEGER {
        return Err(LocalOwnerError::ContinuityAdmissionDenied);
    }
    let expected_identity_fingerprint = domain_fingerprint(
        "agents-os.local-owner.resident-identity.v1",
        PROFILE_ID.as_bytes(),
    );
    let identity_total: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_identity", [], |row| {
            row.get(0)
        })?;
    let identity_matches: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_identity WHERE resident_id=?1 AND identity_revision=1 AND identity_fingerprint=?2",
        params![PROFILE_ID, expected_identity_fingerprint],
        |row| row.get(0),
    )?;
    if identity_total != 1 || identity_matches != 1 {
        return Err(LocalOwnerError::StateCorrupt);
    }

    let row = connection
        .query_row(
            "SELECT authority_epoch,authority_generation,incarnation_id,expected_previous_authority_epoch,previous_epoch_fingerprint,previous_incarnation_id,epoch_fingerprint,created_event_sequence FROM resident_authority_epoch ORDER BY authority_epoch DESC LIMIT 1",
            [],
            |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, Option<i64>>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, String>(6)?,
                    row.get::<_, i64>(7)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let authority_epoch = safe_u64(row.0)?;
    let authority_generation = safe_u64(row.1)?;
    let event_sequence = safe_u64(row.7)?;
    if authority_epoch != authority_generation
        || authority_generation != expected_authority_generation
        || !is_sha256(&row.6)
        || row.3.map(safe_u64).transpose()?
            != authority_epoch
                .checked_sub(1)
                .filter(|_| authority_epoch > 1)
        || (authority_epoch == 1 && (row.4.is_some() || row.5.is_some()))
        || (authority_epoch > 1 && (!row.4.as_deref().is_some_and(is_sha256) || row.5.is_none()))
    {
        return Err(LocalOwnerError::ContinuityAdmissionDenied);
    }

    // The authority payload has additional restore fields after a disaster
    // transition.  Validate its authenticated base fields and fingerprint
    // without copying those fields into the D1 projection.
    let event_bytes: Vec<u8> = connection
        .query_row(
            "SELECT canonical_bytes FROM event WHERE event_sequence=?1",
            [to_i64(event_sequence)?],
            |event| event.get(0),
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let event: Value =
        serde_json::from_slice(&event_bytes).map_err(|_| LocalOwnerError::StateCorrupt)?;
    if canonical_value_bytes(&event)? != event_bytes
        || event["aggregateRef"] != PROFILE_ID
        || event["aggregateRevision"].as_u64() != Some(authority_epoch)
        || event["eventSequence"].as_u64() != Some(event_sequence)
        || !matches!(
            event["eventKind"].as_str(),
            Some("RESIDENT_OWNERSHIP_STARTED" | "RESIDENT_DISASTER_RESTORED")
        )
        || !event["commandFingerprint"].is_null()
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let payload = event
        .get("payload")
        .and_then(Value::as_object)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    if payload.get("residentId").and_then(Value::as_str) != Some(PROFILE_ID)
        || payload.get("authorityEpoch").and_then(Value::as_u64) != Some(authority_epoch)
        || payload.get("authorityGeneration").and_then(Value::as_u64) != Some(authority_generation)
        || payload.get("incarnationId").and_then(Value::as_str) != Some(row.2.as_str())
        || payload.get("createdEventSequence").and_then(Value::as_u64) != Some(event_sequence)
        || payload.get("expectedPreviousAuthorityEpoch")
            != Some(&row.3.map(|value| json!(value)).unwrap_or(Value::Null))
        || payload.get("previousEpochFingerprint")
            != Some(&row.4.clone().map(Value::String).unwrap_or(Value::Null))
        || payload.get("previousIncarnationId")
            != Some(&row.5.clone().map(Value::String).unwrap_or(Value::Null))
        || domain_fingerprint(
            "agents-os.local-owner.authority-epoch.v1",
            &canonical_value_bytes(&Value::Object(payload.clone()))?,
        ) != row.6
    {
        return Err(LocalOwnerError::StateCorrupt);
    }

    Ok(AuthorityCut {
        authority_generation,
        epoch_fingerprint: row.6,
        event_sequence,
        subject_identity_ref: format!("resident:v1:{expected_identity_fingerprint}"),
    })
}

fn read_pointer_cut(
    connection: &Connection,
    authority_event_sequence: u64,
) -> Result<PointerCut, LocalOwnerError> {
    let goal_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM goal", [], |row| row.get(0))?;
    let task_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM task", [], |row| row.get(0))?;
    let mut statement = connection.prepare(
        "SELECT p.fact_kind,p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint,p.pointer_version,p.updated_event_sequence,f.subject_ref,f.subject_revision,f.canonical_bytes,f.fact_fingerprint,f.predecessor_fact_fingerprint,f.created_event_sequence FROM current_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.fact_kind IN ('GOAL_STATE','TASK_STATE') ORDER BY p.fact_kind,p.logical_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, i64>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, i64>(5)?,
            row.get::<_, i64>(6)?,
            row.get::<_, String>(7)?,
            row.get::<_, i64>(8)?,
            row.get::<_, Vec<u8>>(9)?,
            row.get::<_, String>(10)?,
            row.get::<_, Option<String>>(11)?,
            row.get::<_, i64>(12)?,
        ))
    })?;
    let raw_rows = rows.collect::<Result<Vec<_>, _>>()?;
    drop(statement);

    let goal_pointer_count = raw_rows.iter().filter(|row| row.0 == "GOAL_STATE").count();
    let task_pointer_count = raw_rows.iter().filter(|row| row.0 == "TASK_STATE").count();
    if usize::try_from(goal_count).ok() != Some(goal_pointer_count)
        || usize::try_from(task_count).ok() != Some(task_pointer_count)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }

    let mut records = Vec::with_capacity(raw_rows.len());
    let mut digest_rows = Vec::with_capacity(raw_rows.len());
    let mut event_sequence = authority_event_sequence;
    for row in raw_rows {
        let revision = safe_u64(row.2)?;
        let pointer_version = safe_u64(row.5)?;
        let updated_event_sequence = safe_u64(row.6)?;
        let subject_revision = safe_u64(row.8)?;
        let created_event_sequence = safe_u64(row.12)?;
        if revision != pointer_version
            || revision != subject_revision
            || row.1 != row.7
            || row.4 != row.10
            || updated_event_sequence != created_event_sequence
            || row.3 != format!("fact:{}:{}:{revision}", row.0, row.1)
            || !is_sha256(&row.4)
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        let logical_exists: i64 = match row.0.as_str() {
            "GOAL_STATE" => connection.query_row(
                "SELECT EXISTS(SELECT 1 FROM goal WHERE goal_id=?1)",
                [&row.1],
                |value| value.get(0),
            )?,
            "TASK_STATE" => connection.query_row(
                "SELECT EXISTS(SELECT 1 FROM task WHERE task_id=?1)",
                [&row.1],
                |value| value.get(0),
            )?,
            _ => return Err(LocalOwnerError::StateCorrupt),
        };
        let max_revision: i64 = connection.query_row(
            "SELECT COALESCE(MAX(fact_revision),0) FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2",
            params![row.0, row.1],
            |value| value.get(0),
        )?;
        if logical_exists != 1 || safe_u64(max_revision)? != revision {
            return Err(LocalOwnerError::StateCorrupt);
        }
        if revision == 1 {
            if row.11.is_some() {
                return Err(LocalOwnerError::StateCorrupt);
            }
        } else {
            let predecessor: Option<String> = connection
                .query_row(
                    "SELECT fact_fingerprint FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 AND fact_revision=?3",
                    params![row.0, row.1, to_i64(revision - 1)?],
                    |value| value.get(0),
                )
                .optional()?;
            if predecessor.as_deref() != row.11.as_deref() {
                return Err(LocalOwnerError::StateCorrupt);
            }
        }
        let value: Value =
            serde_json::from_slice(&row.9).map_err(|_| LocalOwnerError::StateCorrupt)?;
        if canonical_value_bytes(&value)? != row.9 {
            return Err(LocalOwnerError::StateCorrupt);
        }
        validate_state_value(&row.0, &row.1, &value)?;
        let fingerprint_material = json!({
            "factKind": row.0,
            "logicalId": row.1,
            "predecessorFactFingerprint": row.11,
            "revision": revision,
            "value": value,
        });
        if domain_fingerprint(
            &format!("agents-os.local-owner.fact.{}.v1", row.0),
            &canonical_value_bytes(&fingerprint_material)?,
        ) != row.4
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        validate_fact_event(
            connection,
            created_event_sequence,
            &row.0,
            &row.1,
            revision,
            &row.3,
            &row.4,
        )?;
        event_sequence = event_sequence.max(updated_event_sequence);
        digest_rows.push(json!({
            "factFingerprint": row.4,
            "factKind": row.0,
            "logicalIdDigest": digest_ref(
                "agents-os.local-owner.work-d1-logical-id.v1",
                &row.1,
            ),
            "revision": revision,
            "updatedEventSequence": updated_event_sequence,
        }));
        records.push(PointerRecord {
            fact_kind: row.0,
            logical_id: row.1,
            revision,
            fact_fingerprint: row.4,
            updated_event_sequence,
            value,
        });
    }
    let digest = format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.work-d1-current-pointer-set.v1",
            &canonical_value_bytes(&Value::Array(digest_rows))?,
        )
    );
    Ok(PointerCut {
        digest,
        event_sequence,
        records,
    })
}

fn qualifying_last_validated_result(
    connection: &Connection,
    pointer_cut: &PointerCut,
) -> Result<Option<ValidatedResult>, LocalOwnerError> {
    let counts = connection.query_row(
        "SELECT (SELECT COUNT(*) FROM completion_guard),(SELECT COUNT(*) FROM result_candidate),(SELECT COUNT(*) FROM validation_requirement),(SELECT COUNT(*) FROM validation_set),(SELECT COUNT(*) FROM validation_attempt),(SELECT COUNT(*) FROM quiescence_proof)",
        [],
        |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, i64>(2)?,
                row.get::<_, i64>(3)?,
                row.get::<_, i64>(4)?,
                row.get::<_, i64>(5)?,
            ))
        },
    )?;
    if counts.0 < 0
        || counts.0 != counts.1
        || counts.0 != counts.2
        || counts.0 != counts.3
        || counts.0 != counts.5
        || counts.4
            != counts
                .0
                .checked_mul(3)
                .ok_or(LocalOwnerError::StateCorrupt)?
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    if counts.0 == 0 {
        return Ok(None);
    }

    let row = connection
        .query_row(
            "SELECT completion_ref,task_id,candidate_id,validation_set_id,quiescence_proof_id,completion_fingerprint,created_event_sequence FROM completion_guard ORDER BY created_event_sequence DESC LIMIT 1",
            [],
            |row| {
                Ok(CompletionGuardRow {
                    completion_ref: row.get(0)?,
                    task_id: row.get(1)?,
                    candidate_id: row.get(2)?,
                    validation_set_id: row.get(3)?,
                    proof_id: row.get(4)?,
                    fingerprint: row.get(5)?,
                    event_sequence: safe_u64_sql(row.get::<_, i64>(6)?)?,
                })
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    validate_completion_chain(connection, pointer_cut, row)
}

fn validate_completion_chain(
    connection: &Connection,
    pointer_cut: &PointerCut,
    guard: CompletionGuardRow,
) -> Result<Option<ValidatedResult>, LocalOwnerError> {
    if !is_sha256(&guard.fingerprint) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let task_pointer = pointer_cut
        .records
        .iter()
        .find(|record| record.fact_kind == "TASK_STATE" && record.logical_id == guard.task_id)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    if task_pointer.value.get("status").and_then(Value::as_str) != Some("DONE")
        || task_pointer
            .value
            .get("completionRef")
            .and_then(Value::as_str)
            != Some(guard.completion_ref.as_str())
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let goal_exists: i64 = connection.query_row(
        "SELECT COUNT(*) FROM task t JOIN goal g ON g.goal_id=t.goal_id WHERE t.task_id=?1",
        [&guard.task_id],
        |row| row.get(0),
    )?;
    if goal_exists != 1 {
        return Err(LocalOwnerError::StateCorrupt);
    }

    let candidate = connection
        .query_row(
            "SELECT task_id,candidate_revision,result_summary_commitment,consent_commitment,candidate_fingerprint,created_event_sequence FROM result_candidate WHERE candidate_id=?1",
            [&guard.candidate_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, i64>(5)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let candidate_event = safe_u64(candidate.5)?;
    if candidate.0 != guard.task_id
        || candidate.1 != 1
        || !is_sha256(&candidate.2)
        || !is_sha256(&candidate.3)
        || !is_sha256(&candidate.4)
        || domain_fingerprint(
            "agents-os.local-owner.result-candidate.v1",
            format!("{}\0{}\0{}", guard.task_id, candidate.2, candidate.3).as_bytes(),
        ) != candidate.4
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let command_fingerprint = validate_payload_event(
        connection,
        candidate_event,
        "RESULT_CANDIDATE_RECORDED",
        &guard.candidate_id,
        1,
        &json!({
            "candidateFingerprint": candidate.4,
            "candidateId": guard.candidate_id,
            "taskId": guard.task_id,
        }),
        None,
    )?;

    let requirement = connection
        .query_row(
            "SELECT requirement_id,task_id,requirement_kind,requirement_revision,requirement_fingerprint,created_event_sequence FROM validation_requirement WHERE candidate_id=?1",
            [&guard.candidate_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, i64>(5)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let requirement_event = safe_u64(requirement.5)?;
    let requirement_value = json!({
        "candidateId": guard.candidate_id,
        "requirementId": requirement.0,
        "requirementKind": "HUMAN_ACCEPTANCE",
        "requirementRevision": 1,
        "taskId": guard.task_id,
    });
    if requirement.1 != guard.task_id
        || requirement.2 != "HUMAN_ACCEPTANCE"
        || requirement.3 != 1
        || !is_sha256(&requirement.4)
        || domain_fingerprint(
            "agents-os.local-owner.validation-requirement.v1",
            &canonical_value_bytes(&requirement_value)?,
        ) != requirement.4
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    validate_payload_event(
        connection,
        requirement_event,
        "VALIDATION_REQUIREMENT_RECORDED",
        &requirement.0,
        1,
        &requirement_value,
        Some(&command_fingerprint),
    )?;

    let validation_set = connection
        .query_row(
            "SELECT task_id,candidate_id,requirement_id,validation_set_revision,current_attempt_id,current_decision,consent_commitment,validation_set_fingerprint,created_event_sequence FROM validation_set WHERE validation_set_id=?1",
            [&guard.validation_set_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, String>(6)?,
                    row.get::<_, String>(7)?,
                    row.get::<_, i64>(8)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let set_event = safe_u64(validation_set.8)?;
    let set_value = json!({
        "candidateId": guard.candidate_id,
        "consentCommitment": candidate.3,
        "currentAttemptId": validation_set.4,
        "currentDecision": "PASSED",
        "requirementId": requirement.0,
        "taskId": guard.task_id,
        "validationSetId": guard.validation_set_id,
        "validationSetRevision": 1,
    });
    if validation_set.0 != guard.task_id
        || validation_set.1 != guard.candidate_id
        || validation_set.2 != requirement.0
        || validation_set.3 != 1
        || validation_set.5 != "PASSED"
        || validation_set.6 != candidate.3
        || !is_sha256(&validation_set.7)
        || domain_fingerprint(
            "agents-os.local-owner.validation-set.v1",
            &canonical_value_bytes(&set_value)?,
        ) != validation_set.7
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    validate_payload_event(
        connection,
        set_event,
        "VALIDATION_SET_RECORDED",
        &guard.validation_set_id,
        1,
        &set_value,
        Some(&command_fingerprint),
    )?;

    let mut statement = connection.prepare(
        "SELECT attempt_id,attempt_ordinal,status,predecessor_attempt_id,evidence_commitment,attempt_fingerprint,created_event_sequence FROM validation_attempt WHERE validation_set_id=?1 ORDER BY attempt_ordinal",
    )?;
    let attempts = statement
        .query_map([&guard.validation_set_id], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Option<String>>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, String>(5)?,
                row.get::<_, i64>(6)?,
            ))
        })?
        .collect::<Result<Vec<_>, _>>()?;
    if attempts.len() != 3 {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let pending_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.pending.v1",
        format!("{}\0{}", guard.validation_set_id, attempts[0].0).as_bytes(),
    );
    let running_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.running.v1",
        format!(
            "{}\0{}\0{}",
            guard.validation_set_id, attempts[1].0, pending_fingerprint
        )
        .as_bytes(),
    );
    let passed_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.passed.v1",
        format!(
            "{}\0{}\0{}\0{}",
            guard.validation_set_id, attempts[2].0, running_fingerprint, candidate.3
        )
        .as_bytes(),
    );
    let expected_attempts = [
        (1_i64, "PENDING", None, None, pending_fingerprint.as_str()),
        (
            2_i64,
            "RUNNING",
            Some(attempts[0].0.as_str()),
            None,
            running_fingerprint.as_str(),
        ),
        (
            3_i64,
            "PASSED",
            Some(attempts[1].0.as_str()),
            Some(candidate.3.as_str()),
            passed_fingerprint.as_str(),
        ),
    ];
    let mut attempt_events = Vec::with_capacity(3);
    for (index, attempt) in attempts.iter().enumerate() {
        let expected = expected_attempts[index];
        if attempt.1 != expected.0
            || attempt.2 != expected.1
            || attempt.3.as_deref() != expected.2
            || attempt.4.as_deref() != expected.3
            || attempt.5 != expected.4
            || !is_sha256(&attempt.5)
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        let attempt_event = safe_u64(attempt.6)?;
        validate_payload_event(
            connection,
            attempt_event,
            &format!("VALIDATION_ATTEMPT_{}", attempt.2),
            &attempt.0,
            safe_u64(attempt.1)?,
            &json!({
                "attemptFingerprint": attempt.5,
                "attemptId": attempt.0,
                "candidateId": guard.candidate_id,
                "predecessorAttemptId": attempt.3,
                "status": attempt.2,
                "taskId": guard.task_id,
                "validationSetId": guard.validation_set_id,
            }),
            Some(&command_fingerprint),
        )?;
        attempt_events.push(attempt_event);
    }
    if validation_set.4 != attempts[2].0 {
        return Err(LocalOwnerError::StateCorrupt);
    }

    let proof = connection
        .query_row(
            "SELECT task_id,run_count,effect_count,outbox_count,control_intent_count,unknown_state_count,proof_fingerprint,created_event_sequence FROM quiescence_proof WHERE proof_id=?1",
            [&guard.proof_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, i64>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, i64>(4)?,
                    row.get::<_, i64>(5)?,
                    row.get::<_, String>(6)?,
                    row.get::<_, i64>(7)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let proof_event = safe_u64(proof.7)?;
    let proof_value = json!({
        "controlIntentCount": 0,
        "effectCount": 0,
        "outboxCount": 0,
        "proofId": guard.proof_id,
        "runCount": 0,
        "taskId": guard.task_id,
        "unknownStateCount": 0,
    });
    if proof.0 != guard.task_id
        || [proof.1, proof.2, proof.3, proof.4, proof.5]
            .iter()
            .any(|value| *value != 0)
        || !is_sha256(&proof.6)
        || domain_fingerprint(
            "agents-os.local-owner.quiescence-proof.v1",
            &canonical_value_bytes(&proof_value)?,
        ) != proof.6
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    validate_payload_event(
        connection,
        proof_event,
        "QUIESCENCE_PROVED",
        &guard.proof_id,
        1,
        &proof_value,
        Some(&command_fingerprint),
    )?;

    let completion_value = json!({
        "candidateId": guard.candidate_id,
        "completionRef": guard.completion_ref,
        "quiescenceProofId": guard.proof_id,
        "taskId": guard.task_id,
        "validationSetId": guard.validation_set_id,
    });
    if domain_fingerprint(
        "agents-os.local-owner.completion-guard.v1",
        &canonical_value_bytes(&completion_value)?,
    ) != guard.fingerprint
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    validate_payload_event(
        connection,
        guard.event_sequence,
        "TASK_COMPLETION_GUARD_RECORDED",
        &guard.completion_ref,
        1,
        &completion_value,
        Some(&command_fingerprint),
    )?;
    let event_order = [
        candidate_event,
        requirement_event,
        set_event,
        attempt_events[0],
        attempt_events[1],
        attempt_events[2],
        proof_event,
        guard.event_sequence,
        task_pointer.updated_event_sequence,
    ];
    if event_order.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(LocalOwnerError::StateCorrupt);
    }

    let value_ref = format!(
        "validation-result:sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.work-d1-value-ref.v1",
            guard.fingerprint.as_bytes(),
        )
    );
    Ok(Some(ValidatedResult {
        value_ref,
        subject_ref: format!(
            "work-subject:v1:{}",
            domain_fingerprint(
                "agents-os.local-owner.work-d1-task-subject.v1",
                guard.task_id.as_bytes(),
            )
        ),
        validation_ref: format!(
            "work-validation:v1:{}",
            domain_fingerprint(
                "agents-os.local-owner.work-d1-validation-ref.v1",
                guard.validation_set_id.as_bytes(),
            )
        ),
        fact_revision: task_pointer.revision,
        fact_fingerprint: format!("sha256:{}", task_pointer.fact_fingerprint),
        event_sequence: task_pointer.updated_event_sequence,
        cut_material: json!({
            "candidateFingerprint": candidate.4,
            "completionFingerprint": guard.fingerprint,
            "completionGuardEventSequence": guard.event_sequence,
            "currentTaskFactFingerprint": task_pointer.fact_fingerprint,
            "currentTaskFactRevision": task_pointer.revision,
            "currentTaskPointerEventSequence": task_pointer.updated_event_sequence,
            "passedAttemptFingerprint": passed_fingerprint,
            "quiescenceProofFingerprint": proof.6,
            "requirementFingerprint": requirement.4,
            "validationSetFingerprint": validation_set.7,
        }),
    }))
}

fn validate_state_value(
    fact_kind: &str,
    logical_id: &str,
    value: &Value,
) -> Result<(), LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::StateCorrupt)?;
    match fact_kind {
        "GOAL_STATE" => {
            exact_keys(object, &["goalId", "outcome", "priorStatus", "status"])?;
            if object.get("goalId").and_then(Value::as_str) != Some(logical_id)
                || !object
                    .get("status")
                    .and_then(Value::as_str)
                    .is_some_and(|status| {
                        matches!(
                            status,
                            "READY" | "ACTIVE" | "PAUSED" | "COMPLETION_REVIEW" | "CLOSED"
                        )
                    })
            {
                return Err(LocalOwnerError::StateCorrupt);
            }
        }
        "TASK_STATE" => {
            let status = object
                .get("status")
                .and_then(Value::as_str)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            if status == "DONE" {
                exact_keys(
                    object,
                    &[
                        "activityContextCommitment",
                        "completionRef",
                        "status",
                        "taskId",
                    ],
                )?;
                if object
                    .get("completionRef")
                    .and_then(Value::as_str)
                    .is_none()
                {
                    return Err(LocalOwnerError::StateCorrupt);
                }
            } else {
                exact_keys(object, &["activityContextCommitment", "status", "taskId"])?;
            }
            if object.get("taskId").and_then(Value::as_str) != Some(logical_id)
                || !matches!(status, "READY" | "ACTIVE" | "PAUSED" | "VERIFYING" | "DONE")
            {
                return Err(LocalOwnerError::StateCorrupt);
            }
        }
        _ => return Err(LocalOwnerError::StateCorrupt),
    }
    Ok(())
}

fn validate_payload_event(
    connection: &Connection,
    event_sequence: u64,
    expected_kind: &str,
    expected_aggregate: &str,
    expected_revision: u64,
    expected_payload: &Value,
    expected_command: Option<&str>,
) -> Result<String, LocalOwnerError> {
    let row = connection
        .query_row(
            "SELECT event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint FROM event WHERE event_sequence=?1",
            [to_i64(event_sequence)?],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, Vec<u8>>(6)?,
                    row.get::<_, String>(7)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let command = row.4.ok_or(LocalOwnerError::StateCorrupt)?;
    if row.0 != format!("event:local-owner:{event_sequence}")
        || row.1 != expected_kind
        || row.2 != expected_aggregate
        || safe_u64(row.3)? != expected_revision
        || !is_sha256(&command)
        || expected_command.is_some_and(|expected| expected != command)
        || row.5.as_deref().is_none_or(|value| !is_sha256(value))
        || !is_sha256(&row.7)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let expected = json!({
        "aggregateRef": expected_aggregate,
        "aggregateRevision": expected_revision,
        "commandFingerprint": command,
        "eventKind": expected_kind,
        "eventSequence": event_sequence,
        "payload": expected_payload,
        "predecessorEventFingerprint": row.5,
    });
    let expected_bytes = canonical_value_bytes(&expected)?;
    if expected_bytes != row.6
        || domain_fingerprint("agents-os.local-owner.event.v1", &expected_bytes) != row.7
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(command)
}

fn validate_fact_event(
    connection: &Connection,
    event_sequence: u64,
    fact_kind: &str,
    logical_id: &str,
    revision: u64,
    fact_ref: &str,
    fact_fingerprint: &str,
) -> Result<(), LocalOwnerError> {
    let row = connection
        .query_row(
            "SELECT event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint FROM event WHERE event_sequence=?1",
            [to_i64(event_sequence)?],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, i64>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, Vec<u8>>(6)?,
                    row.get::<_, String>(7)?,
                ))
            },
        )
        .optional()?
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let event_kind = format!("{fact_kind}_ADVANCED");
    let command = row.4.ok_or(LocalOwnerError::StateCorrupt)?;
    if row.0 != format!("event:local-owner:{event_sequence}")
        || row.1 != event_kind
        || row.2 != logical_id
        || safe_u64(row.3)? != revision
        || !is_sha256(&command)
        || row.5.as_deref().is_some_and(|value| !is_sha256(value))
        || !is_sha256(&row.7)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let expected = json!({
        "aggregateRef": logical_id,
        "aggregateRevision": revision,
        "commandFingerprint": command,
        "eventKind": event_kind,
        "eventSequence": event_sequence,
        "factFingerprint": fact_fingerprint,
        "factRef": fact_ref,
        "predecessorEventFingerprint": row.5,
    });
    let expected_bytes = canonical_value_bytes(&expected)?;
    if expected_bytes != row.6
        || domain_fingerprint("agents-os.local-owner.event.v1", &expected_bytes) != row.7
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(())
}

fn exact_keys(object: &Map<String, Value>, expected: &[&str]) -> Result<(), LocalOwnerError> {
    if object.len() != expected.len() || !expected.iter().all(|key| object.contains_key(*key)) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(())
}

fn digest_ref(domain: &str, value: &str) -> String {
    format!("sha256:{}", domain_fingerprint(domain, value.as_bytes()))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn safe_u64(value: i64) -> Result<u64, LocalOwnerError> {
    u64::try_from(value)
        .ok()
        .filter(|value| *value > 0 && *value <= MAX_SAFE_INTEGER)
        .ok_or(LocalOwnerError::StateCorrupt)
}

fn safe_u64_sql(value: i64) -> rusqlite::Result<u64> {
    u64::try_from(value)
        .ok()
        .filter(|value| *value > 0 && *value <= MAX_SAFE_INTEGER)
        .ok_or_else(|| {
            rusqlite::Error::FromSqlConversionFailure(
                0,
                rusqlite::types::Type::Integer,
                Box::new(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "unsafe event sequence",
                )),
            )
        })
}

fn to_i64(value: u64) -> Result<i64, LocalOwnerError> {
    if value == 0 || value > MAX_SAFE_INTEGER {
        return Err(LocalOwnerError::StateCorrupt);
    }
    i64::try_from(value).map_err(|_| LocalOwnerError::StateCorrupt)
}

#[cfg(test)]
#[path = "work_source_tests.rs"]
mod tests;
