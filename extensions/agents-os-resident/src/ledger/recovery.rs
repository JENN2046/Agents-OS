//! Read-only recovery and integrity observations.

use rusqlite::Connection;
use serde_json::{Value, json};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::reducers::goal_plan::SYNTHETIC_TASK_REFS;

use super::LedgerError;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LedgerCounts {
    pub events: u64,
    pub facts: u64,
    pub pointers: u64,
    pub inbox_commands: u64,
    pub replay_rows: u64,
    pub outbox_intents: u64,
    pub outbox_claims: u64,
    pub delivery_attempts: u64,
    pub dispatch_arms: u64,
    pub delivery_receipts: u64,
    pub first_apply_guards: u64,
    pub task_completions: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IntegratedWitness {
    pub canonical_bytes: Vec<u8>,
    pub root_fingerprint: String,
    pub event_fingerprints: Vec<String>,
    pub synthetic_goal_count: u64,
    pub synthetic_task_count: u64,
    pub mock_effect_count: u64,
    pub external_call_count: u64,
    pub real_occurrence_count: u64,
    pub runtime_usable: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct M0BIntegratedWitness {
    pub canonical_bytes: Vec<u8>,
    pub root_fingerprint: String,
    pub event_fingerprints: Vec<String>,
    pub synthetic_session_observation_count: u64,
    pub synthetic_life_stream_candidate_count: u64,
    pub synthetic_memory_candidate_count: u64,
    pub synthetic_intent_candidate_count: u64,
    pub synthetic_handoff_count: u64,
    pub synthetic_f3_committed_count: u64,
    pub synthetic_f3_rejected_control_count: u64,
    pub synthetic_f3_indeterminate_count: u64,
    pub real_occurrence_count: u64,
    pub runtime_usable: bool,
}

pub fn counts(connection: &Connection) -> Result<LedgerCounts, LedgerError> {
    Ok(LedgerCounts {
        events: count(connection, "event")?,
        facts: count(connection, "canonical_fact")?,
        pointers: count(connection, "current_fact_pointer")?,
        inbox_commands: count(connection, "inbox_command")?,
        replay_rows: count(connection, "replay_index")?,
        outbox_intents: count(connection, "outbox_intent")?,
        outbox_claims: count(connection, "outbox_claim")?,
        delivery_attempts: count(connection, "delivery_attempt")?,
        dispatch_arms: count(connection, "dispatch_arm")?,
        delivery_receipts: count(connection, "delivery_receipt")?,
        first_apply_guards: count(connection, "first_apply_guard")?,
        task_completions: count(connection, "task_completion")?,
    })
}

/// Rebuilds the complete WP7 semantic root from immutable ledger rows.
///
/// This is a read-only test witness.  It neither accepts caller-supplied
/// authority nor writes a projection.  Every canonical byte column is hashed
/// into the root together with its stored identity tuple.
pub fn integrated_witness(connection: &Connection) -> Result<IntegratedWitness, LedgerError> {
    let counts = counts(connection)?;
    if counts.events != 5
        || counts.facts != 7
        || counts.pointers != 7
        || counts.inbox_commands != 4
        || counts.replay_rows != 4
        || counts.outbox_intents != 1
        || counts.outbox_claims != 0
        || counts.delivery_attempts != 0
        || counts.dispatch_arms != 0
        || counts.delivery_receipts != 0
        || counts.first_apply_guards != 0
        || counts.task_completions != 1
    {
        return Err(LedgerError::InvalidInput(
            "ledger does not contain the exact integrated M0-A witness inventory",
        ));
    }

    let mut event_statement = connection.prepare(
        "SELECT event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint FROM event ORDER BY event_sequence",
    )?;
    let events = event_statement
        .query_map([], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, i64>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, Vec<u8>>(6)?,
                row.get::<_, String>(7)?,
                row.get::<_, Option<String>>(8)?,
            ))
        })?
        .collect::<Result<Vec<_>, _>>()?;
    let expected_event_kinds = [
        "RESIDENT_OWNERSHIP_STARTED",
        "F1_SYNTHETIC_GOAL_AND_TASKS_CREATED",
        "F6_SYNTHETIC_VALIDATION_RECORDED",
        "F6_SYNTHETIC_TASK_COMPLETED",
        "F5_SYNTHETIC_OUTBOX_RECORDED",
    ];
    let mut event_fingerprints = Vec::with_capacity(events.len());
    let mut event_rows = Vec::with_capacity(events.len());
    for (
        index,
        (sequence, id, kind, aggregate, revision, command, bytes, fingerprint, predecessor),
    ) in events.into_iter().enumerate()
    {
        require_canonical_runtime_unusable(&bytes)?;
        if sequence != (index + 1) as i64
            || kind != expected_event_kinds[index]
            || sha256_hex(&bytes) != fingerprint
            || (index == 0 && predecessor.is_some())
            || (index > 0
                && predecessor.as_deref() != event_fingerprints.get(index - 1).map(String::as_str))
        {
            return Err(LedgerError::InvalidInput(
                "integrated Event chain is not exact and deterministic",
            ));
        }
        event_fingerprints.push(fingerprint.clone());
        event_rows.push(json!([
            sequence,
            id,
            kind,
            aggregate,
            revision,
            command,
            sha256_hex(&bytes),
            fingerprint,
            predecessor
        ]));
    }

    let fact_rows = canonical_fact_rows(connection)?;
    verify_goal_plan_rows(&fact_rows)?;
    let pointer_rows = string_rows(
        connection,
        "SELECT fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence FROM current_fact_pointer ORDER BY fact_kind,logical_id",
        7,
    )?;
    let envelope_rows = blob_fingerprint_rows(
        connection,
        "SELECT envelope_id,command_id,command_type_id,command_type_revision,canonical_bytes,envelope_fingerprint,created_event_sequence FROM command_envelope ORDER BY envelope_id",
        BlobRowKind::Envelope,
    )?;
    let inbox_rows = inbox_rows(connection)?;
    let (replay_rows, external_call_count) = replay_rows(connection)?;
    let outbox_rows = outbox_rows(connection)?;
    let completion_rows = string_rows(
        connection,
        "SELECT task_ref,task_revision,completion_revision,completion_fact_kind,completion_logical_id,completion_fact_revision,completion_fact_ref,completion_fact_fingerprint,completion_event_sequence FROM task_completion ORDER BY task_ref,task_revision,completion_revision",
        9,
    )?;
    if external_call_count != 0 {
        return Err(LedgerError::InvalidInput(
            "integrated witness contains an external call occurrence",
        ));
    }
    let root_value = json!({
        "command_envelopes": envelope_rows,
        "events": event_rows,
        "facts": fact_rows,
        "inbox": inbox_rows,
        "interface_version": "agents-os.m0a.integrated-witness.v0.1",
        "outbox": outbox_rows,
        "pointers": pointer_rows,
        "replay": replay_rows,
        "runtime_usable": false,
        "task_completions": completion_rows,
        "witness_counts": {
            "external_call_count": 0,
            "mock_effect_count": 1,
            "network_call_count": 0,
            "private_memory_read_count": 0,
            "provider_call_count": 0,
            "real_command_count": 0,
            "real_effect_occurrence_count": 0,
            "real_task_count": 0,
            "runtime_activation_count": 0,
            "sensing_or_recording_count": 0,
            "synthetic_goal_count": 1,
            "synthetic_task_count": 3
        }
    });
    let canonical_bytes = canonicalize_json(
        &serde_json::to_vec(&root_value)
            .map_err(|_| LedgerError::InvalidInput("integrated witness serialization failed"))?,
    )?;
    let root_fingerprint = sha256_hex(&canonical_bytes);
    Ok(IntegratedWitness {
        canonical_bytes,
        root_fingerprint,
        event_fingerprints,
        synthetic_goal_count: 1,
        synthetic_task_count: SYNTHETIC_TASK_REFS.len() as u64,
        mock_effect_count: counts.outbox_intents,
        external_call_count,
        real_occurrence_count: 0,
        runtime_usable: false,
    })
}

/// Rebuilds the complete WP7 M0-B root from the immutable schema-v2 ledger.
///
/// Session branches and the rejected F3 control are deliberately represented
/// only by their fixed low-disclosure case inventory: those paths must write
/// zero canonical rows. The favorable candidate, handoff, committed F3 result
/// and ambiguous/indeterminate F3 result are independently recovered from the
/// ledger. This function is read-only and exposes no runtime entry point.
pub fn m0b_integrated_witness(
    connection: &Connection,
) -> Result<M0BIntegratedWitness, LedgerError> {
    let schema = super::schema::verify_schema(connection)?;
    if schema.version != 2 {
        return Err(LedgerError::SchemaMismatch(
            "M0-B integrated witness requires exact schema v2".to_owned(),
        ));
    }
    let counts = counts(connection)?;
    if counts.events != 6
        || counts.facts != 0
        || counts.pointers != 0
        || counts.inbox_commands != 2
        || counts.replay_rows != 2
        || counts.outbox_intents != 0
        || counts.outbox_claims != 0
        || counts.delivery_attempts != 0
        || counts.dispatch_arms != 0
        || counts.delivery_receipts != 0
        || counts.first_apply_guards != 0
        || counts.task_completions != 0
    {
        return Err(LedgerError::InvalidInput(
            "ledger does not contain the exact integrated M0-B inventory",
        ));
    }

    let (event_rows, event_fingerprints) = m0b_event_rows(connection)?;
    let (candidate_rows, candidate_counts) = m0b_candidate_rows(connection)?;
    if candidate_counts != (1, 1, 1) {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B witness does not contain one candidate of each class",
        ));
    }
    let head_rows = string_rows(
        connection,
        "SELECT candidate_id,semantic_class,current_candidate_revision,current_candidate_ref,current_candidate_fingerprint,pointer_version,updated_event_sequence FROM home_candidate_head ORDER BY candidate_id COLLATE BINARY",
        7,
    )?;
    if head_rows.len() != 3 {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B candidate-head inventory is not exact",
        ));
    }
    let handoff_rows = m0b_handoff_rows(connection)?;
    if handoff_rows.len() != 1 {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B handoff inventory is not exact",
        ));
    }
    let envelope_rows = blob_fingerprint_rows(
        connection,
        "SELECT envelope_id,command_id,command_type_id,command_type_revision,canonical_bytes,envelope_fingerprint,created_event_sequence FROM command_envelope ORDER BY envelope_id",
        BlobRowKind::Envelope,
    )?;
    if envelope_rows.len() != 1
        || envelope_rows[0].get(2).and_then(Value::as_str)
            != Some("M0_SYNTHETIC_SUBMIT_HOME_INTENT")
    {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B witness has an unexpected Command envelope",
        ));
    }
    let inbox_rows = inbox_rows(connection)?;
    let committed = inbox_rows
        .iter()
        .filter(|row| row.get(2).and_then(Value::as_str) == Some("COMMITTED"))
        .count();
    let indeterminate = inbox_rows
        .iter()
        .filter(|row| row.get(2).and_then(Value::as_str) == Some("INDETERMINATE"))
        .count();
    if inbox_rows.len() != 2 || committed != 1 || indeterminate != 1 {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B F3 terminal outcome inventory is not exact",
        ));
    }
    let (replay_rows, external_call_count) = replay_rows(connection)?;
    if replay_rows.len() != 2
        || replay_rows
            .iter()
            .filter_map(|row| row.get(3).and_then(Value::as_i64))
            .sum::<i64>()
            != 1
        || external_call_count != 0
    {
        return Err(LedgerError::InvalidInput(
            "integrated M0-B replay accounting is not exact",
        ));
    }
    let session_branch_rows = m0b_session_branch_rows()?;
    let rejected_control = m0b_rejected_control(connection)?;
    let indeterminate_control = m0b_indeterminate_control(connection)?;

    let root_value = json!({
        "candidate_heads": head_rows,
        "candidate_revisions": candidate_rows,
        "command_envelopes": envelope_rows,
        "events": event_rows,
        "f3_outcome_inventory": [
            ["COMMITTED", "PERSISTED_EXACT_HOME_INTENT", 1],
            ["REJECTED", "ZERO_WRITE_INVALID_HOME_INTENT_CONTROL", rejected_control],
            ["INDETERMINATE", "PERSISTED_ZERO_EVENT_AMBIGUOUS_CONTROL", indeterminate_control]
        ],
        "handoff_links": handoff_rows,
        "inbox": inbox_rows,
        "interface_version": "agents-os.m0b.integrated-witness.v0.1",
        "replay": replay_rows,
        "runtime_usable": false,
        "session_branch_inventory": session_branch_rows,
        "terminal_outcome": "NOT_ACTIVATED",
        "witness_counts": {
            "external_effect_count": 0,
            "formal_memory_write_count": 0,
            "network_call_count": 0,
            "private_memory_read_count": 0,
            "provider_call_count": 0,
            "real_command_count": 0,
            "real_goal_count": 0,
            "real_session_count": 0,
            "real_task_count": 0,
            "runtime_activation_count": 0,
            "sensing_or_recording_count": 0,
            "synthetic_f3_committed_command_count": 1,
            "synthetic_f3_indeterminate_count": 1,
            "synthetic_f3_rejected_control_count": 1,
            "synthetic_handoff_candidate_count": 1,
            "synthetic_intent_candidate_count": 1,
            "synthetic_life_stream_candidate_count": 1,
            "synthetic_memory_candidate_count": 1,
            "synthetic_session_observation_count": 4
        }
    });
    let canonical_bytes = canonicalize_json(
        &serde_json::to_vec(&root_value)
            .map_err(|_| LedgerError::InvalidInput("M0-B witness serialization failed"))?,
    )?;
    Ok(M0BIntegratedWitness {
        root_fingerprint: sha256_hex(&canonical_bytes),
        canonical_bytes,
        event_fingerprints,
        synthetic_session_observation_count: 4,
        synthetic_life_stream_candidate_count: 1,
        synthetic_memory_candidate_count: 1,
        synthetic_intent_candidate_count: 1,
        synthetic_handoff_count: 1,
        synthetic_f3_committed_count: 1,
        synthetic_f3_rejected_control_count: 1,
        synthetic_f3_indeterminate_count: 1,
        real_occurrence_count: 0,
        runtime_usable: false,
    })
}

fn m0b_session_branch_rows() -> Result<Vec<Value>, LedgerError> {
    let mut rows = Vec::new();
    for choice in [
        "DISCARD",
        "EPHEMERAL_ONLY",
        "PROPOSE_LIFE_STREAM_CANDIDATE",
        "REMAIN_IN_SESSION",
    ] {
        let bytes = canonicalize_json(
            &serde_json::to_vec(&json!({
                "creator_assessment_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "creator_assessment_ref": "assessment:SYNTHETIC_TEST:creator:1",
                "explicit_branch_choice": choice,
                "observation_id": "observation:SYNTHETIC_TEST:wp7",
                "observation_revision": 1,
                "payload_commitment": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "session_ref": "session:SYNTHETIC_TEST:wp7",
                "session_revision": 1,
                "source_subject_fingerprint": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                "source_subject_ref": "subject:SYNTHETIC_TEST:1",
                "source_subject_revision": 1,
                "trusted_event_sequence": 1
            }))
            .map_err(|_| LedgerError::InvalidInput("M0-B branch serialization failed"))?,
        )?;
        let fingerprint = sha256_hex(&bytes);
        if choice == "PROPOSE_LIFE_STREAM_CANDIDATE" {
            let observation = crate::home::session_boundary::decode_synthetic_observation(&bytes)
                .map_err(|_| LedgerError::InvalidInput("M0-B candidate branch is invalid"))?;
            if observation.explicit_branch_choice
                != crate::home::session_boundary::SessionBranchChoice::ProposeLifeStreamCandidate
            {
                return Err(LedgerError::InvalidInput(
                    "M0-B candidate branch result changed",
                ));
            }
            rows.push(json!([choice, fingerprint, "CANDIDATE_BRANCH"]));
        } else {
            let decision = crate::home::session_boundary::reduce_nonpromotion(&bytes)
                .map_err(|_| LedgerError::InvalidInput("M0-B nonpromotion branch is invalid"))?;
            if decision.result != "NO_PROMOTION"
                || decision.reason != choice
                || decision.canonical_writes.total() != 0
                || decision.runtime_usable
            {
                return Err(LedgerError::InvalidInput(
                    "M0-B nonpromotion result changed",
                ));
            }
            rows.push(json!([choice, fingerprint, decision.result]));
        }
    }
    Ok(rows)
}

fn m0b_rejected_control(connection: &Connection) -> Result<Value, LedgerError> {
    let request_bytes: Vec<u8> = connection.query_row(
        "SELECT request_bytes FROM inbox_command WHERE intake_state='COMMITTED'",
        [],
        |row| row.get(0),
    )?;
    let mut value: Value = serde_json::from_slice(&request_bytes)
        .map_err(|_| LedgerError::InvalidInput("M0-B committed request is not JSON"))?;
    let payload = value
        .get_mut("payload")
        .and_then(Value::as_object_mut)
        .and_then(|payload| payload.get_mut("canonical_command"))
        .and_then(Value::as_object_mut)
        .and_then(|command| command.get_mut("command_payload"))
        .and_then(Value::as_object_mut)
        .ok_or(LedgerError::InvalidInput(
            "M0-B committed Home Intent request shape changed",
        ))?;
    payload.insert(
        "raw_content".to_owned(),
        Value::String("fixed-rejection-control".to_owned()),
    );
    let invalid_bytes = canonicalize_json(
        &serde_json::to_vec(&value)
            .map_err(|_| LedgerError::InvalidInput("M0-B rejection serialization failed"))?,
    )?;
    let frame = crate::napi_frame::parse_request(
        &invalid_bytes,
        crate::napi_frame::MethodId::ExecuteCommand,
    )
    .map_err(|_| LedgerError::InvalidInput("M0-B rejected request frame changed"))?;
    if crate::reducers::command_intake::validate_submission(&frame.payload).is_ok() {
        return Err(LedgerError::InvalidInput(
            "M0-B rejected Home Intent control became admissible",
        ));
    }
    Ok(json!([sha256_hex(&invalid_bytes), "INVALID_HOME_INTENT_COMMAND", 0]))
}

fn m0b_indeterminate_control(connection: &Connection) -> Result<Value, LedgerError> {
    let (request, request_fingerprint, response, response_fingerprint, events, calls):
        (Vec<u8>, String, Vec<u8>, String, i64, i64) = connection.query_row(
        "SELECT i.request_bytes,i.request_fingerprint,r.response_bytes,r.response_fingerprint,r.first_event_count,r.first_external_call_count FROM inbox_command i JOIN replay_index r ON r.command_id=i.command_id WHERE i.command_id='command:SYNTHETIC_TEST:ambiguous-home-intent' AND i.intake_state='INDETERMINATE'",
        [],
        |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?,row.get(3)?,row.get(4)?,row.get(5)?)),
    )?;
    let expected_request = canonicalize_json(
        br#"{"environment":"SYNTHETIC_TEST","interface_version":"agents-os.m0b.f3-ambiguous-control.v0.1","request_id":"command:SYNTHETIC_TEST:ambiguous-home-intent"}"#,
    )?;
    let expected_response = canonicalize_json(
        br#"{"disposition":"INDETERMINATE","external_call_count":0,"runtime_usable":false}"#,
    )?;
    if request != expected_request
        || response != expected_response
        || request_fingerprint != sha256_hex(&request)
        || response_fingerprint != sha256_hex(&response)
        || events != 0
        || calls != 0
    {
        return Err(LedgerError::InvalidInput(
            "M0-B indeterminate F3 control is not exact",
        ));
    }
    Ok(json!([request_fingerprint,response_fingerprint,events,calls]))
}

fn m0b_event_rows(connection: &Connection) -> Result<(Vec<Value>, Vec<String>), LedgerError> {
    let mut statement = connection.prepare(
        "SELECT event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint FROM event ORDER BY event_sequence",
    )?;
    let rows = statement
        .query_map([], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, i64>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, Vec<u8>>(6)?,
                row.get::<_, String>(7)?,
                row.get::<_, Option<String>>(8)?,
            ))
        })?
        .collect::<Result<Vec<_>, _>>()?;
    let expected_kinds = [
        "RESIDENT_OWNERSHIP_STARTED",
        "HOME_CANDIDATE_RECORDED",
        "HOME_CANDIDATE_RECORDED",
        "HOME_CANDIDATE_RECORDED",
        "HOME_HANDOFF_RECORDED",
        "F3_SYNTHETIC_HOME_INTENT_COMMITTED",
    ];
    let mut previous_sequence = 0_i64;
    let mut fingerprints: Vec<String> = Vec::with_capacity(rows.len());
    let mut projected = Vec::with_capacity(rows.len());
    for (index, (sequence, id, kind, aggregate, revision, command, bytes, fingerprint, predecessor))
        in rows.into_iter().enumerate()
    {
        require_canonical_runtime_unusable(&bytes)?;
        if sequence <= previous_sequence
            || kind != expected_kinds[index]
            || sha256_hex(&bytes) != fingerprint
            || (index == 0 && predecessor.is_some())
            || (index > 0
                && predecessor.as_deref() != fingerprints.get(index - 1).map(String::as_str))
        {
            return Err(LedgerError::InvalidInput(
                "integrated M0-B Event chain is not exact",
            ));
        }
        previous_sequence = sequence;
        fingerprints.push(fingerprint.clone());
        projected.push(json!([
            sequence,
            id,
            kind,
            aggregate,
            revision,
            command,
            sha256_hex(&bytes),
            fingerprint,
            predecessor
        ]));
    }
    Ok((projected, fingerprints))
}

fn m0b_candidate_rows(
    connection: &Connection,
) -> Result<(Vec<Value>, (u64, u64, u64)), LedgerError> {
    let mut statement = connection.prepare(
        "SELECT candidate_id,candidate_revision,candidate_ref,semantic_class,source_subject_ref,source_subject_revision,source_subject_fingerprint,payload_commitment,creator_assessment_ref,creator_assessment_fingerprint,canonical_bytes,candidate_fingerprint,predecessor_candidate_revision,predecessor_candidate_ref,predecessor_candidate_fingerprint,created_event_sequence FROM home_candidate_revision ORDER BY candidate_id COLLATE BINARY,candidate_revision",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?, row.get::<_, i64>(1)?, row.get::<_, String>(2)?,
            row.get::<_, String>(3)?, row.get::<_, String>(4)?, row.get::<_, i64>(5)?,
            row.get::<_, String>(6)?, row.get::<_, String>(7)?, row.get::<_, String>(8)?,
            row.get::<_, String>(9)?, row.get::<_, Vec<u8>>(10)?, row.get::<_, String>(11)?,
            row.get::<_, Option<i64>>(12)?, row.get::<_, Option<String>>(13)?,
            row.get::<_, Option<String>>(14)?, row.get::<_, i64>(15)?,
        ))
    })?;
    let mut result = Vec::new();
    let mut counts = (0_u64, 0_u64, 0_u64);
    for row in rows {
        let (id, revision, reference, class, source_ref, source_revision, source_fingerprint,
            payload, assessment_ref, assessment_fingerprint, bytes, fingerprint,
            predecessor_revision, predecessor_ref, predecessor_fingerprint, sequence) = row?;
        let value: Value = serde_json::from_slice(&bytes)
            .map_err(|_| LedgerError::InvalidInput("integrated M0-B candidate is not JSON"))?;
        let expected = json!([
            "agents-os.m0b.home-candidate.v0.1",
            {
                "candidate_id": id,
                "candidate_ref": reference,
                "candidate_revision": revision,
                "created_event_sequence": sequence,
                "creator_assessment_fingerprint": assessment_fingerprint,
                "creator_assessment_ref": assessment_ref,
                "payload_commitment": payload,
                "predecessor_candidate_fingerprint": predecessor_fingerprint,
                "predecessor_candidate_ref": predecessor_ref,
                "predecessor_candidate_revision": predecessor_revision,
                "semantic_class": class,
                "source_subject_fingerprint": source_fingerprint,
                "source_subject_ref": source_ref,
                "source_subject_revision": source_revision
            }
        ]);
        if canonicalize_json(&bytes)? != bytes
            || sha256_hex(&bytes) != fingerprint
            || value != expected
        {
            return Err(LedgerError::InvalidInput(
                "integrated M0-B candidate bytes are not exact",
            ));
        }
        match class.as_str() {
            "LIFE_STREAM_CANDIDATE" => counts.0 += 1,
            "MEMORY_CANDIDATE" => counts.1 += 1,
            "INTENT_CANDIDATE" => counts.2 += 1,
            _ => return Err(LedgerError::InvalidInput("unknown M0-B candidate class")),
        }
        result.push(json!([id,revision,reference,class,source_ref,source_revision,
            source_fingerprint,payload,assessment_ref,assessment_fingerprint,sha256_hex(&bytes),
            fingerprint,predecessor_revision,predecessor_ref,predecessor_fingerprint,sequence]));
    }
    Ok((result, counts))
}

fn m0b_handoff_rows(connection: &Connection) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT handoff_id,handoff_revision,handoff_ref,intent_candidate_id,intent_candidate_revision,intent_candidate_ref,intent_candidate_fingerprint,owner_commitment_set_fingerprint,canonical_candidate_history_fingerprint,minimum_trusted_event_sequence,canonical_bytes,handoff_fingerprint,created_event_sequence FROM home_handoff_link ORDER BY handoff_id,handoff_revision",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?, row.get::<_, i64>(1)?, row.get::<_, String>(2)?,
            row.get::<_, String>(3)?, row.get::<_, i64>(4)?, row.get::<_, String>(5)?,
            row.get::<_, String>(6)?, row.get::<_, String>(7)?, row.get::<_, String>(8)?,
            row.get::<_, i64>(9)?, row.get::<_, Vec<u8>>(10)?, row.get::<_, String>(11)?,
            row.get::<_, i64>(12)?,
        ))
    })?;
    rows.map(|row| {
        let (id, revision, reference, intent_id, intent_revision, intent_ref,
            intent_fingerprint, owner_set, history, minimum, bytes, fingerprint, sequence) = row?;
        let value: Value = serde_json::from_slice(&bytes)
            .map_err(|_| LedgerError::InvalidInput("integrated M0-B handoff is not JSON"))?;
        let expected = json!([
            "agents-os.m0b.home-intent-handoff.v0.1",
            {
                "canonical_candidate_history_fingerprint": history,
                "handoff_candidate_id": id,
                "handoff_candidate_ref": reference,
                "handoff_candidate_revision": revision,
                "intent_candidate_fingerprint": intent_fingerprint,
                "intent_candidate_ref": intent_ref,
                "intent_candidate_revision": intent_revision,
                "minimum_trusted_event_sequence": minimum,
                "owner_commitment_set_fingerprint": owner_set
            }
        ]);
        if canonicalize_json(&bytes)? != bytes
            || sha256_hex(&bytes) != fingerprint
            || value != expected
        {
            return Err(LedgerError::InvalidInput(
                "integrated M0-B handoff bytes are not exact",
            ));
        }
        Ok(json!([id,revision,reference,intent_id,intent_revision,intent_ref,
            intent_fingerprint,owner_set,history,minimum,sha256_hex(&bytes),fingerprint,sequence]))
    }).collect()
}

fn canonical_fact_rows(connection: &Connection) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence FROM canonical_fact ORDER BY fact_kind,logical_id,fact_revision",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, i64>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, i64>(5)?,
            row.get::<_, Vec<u8>>(6)?,
            row.get::<_, String>(7)?,
            row.get::<_, Option<i64>>(8)?,
            row.get::<_, Option<String>>(9)?,
            row.get::<_, Option<String>>(10)?,
            row.get::<_, i64>(11)?,
        ))
    })?;
    rows.map(|row| {
        let (
            kind,
            logical,
            revision,
            fact_ref,
            subject,
            subject_revision,
            bytes,
            fingerprint,
            predecessor_revision,
            predecessor_ref,
            predecessor_fingerprint,
            sequence,
        ) = row?;
        require_canonical_runtime_unusable(&bytes)?;
        Ok(json!([
            kind,
            logical,
            revision,
            fact_ref,
            subject,
            subject_revision,
            sha256_hex(&bytes),
            fingerprint,
            predecessor_revision,
            predecessor_ref,
            predecessor_fingerprint,
            sequence
        ]))
    })
    .collect()
}

fn verify_goal_plan_rows(rows: &[Value]) -> Result<(), LedgerError> {
    let expected = crate::reducers::goal_plan::synthetic_material(1)?;
    for fact in expected.facts {
        let found = rows.iter().any(|row| {
            row.get(0).and_then(Value::as_str) == Some(fact.kind)
                && row.get(1).and_then(Value::as_str) == Some(fact.logical_id)
                && row.get(3).and_then(Value::as_str) == Some(fact.fact_ref)
                && row.get(6).and_then(Value::as_str)
                    == Some(sha256_hex(&fact.canonical_bytes).as_str())
                && row.get(7).and_then(Value::as_str) == Some(fact.fingerprint.as_str())
        });
        if !found {
            return Err(LedgerError::InvalidInput(
                "integrated witness does not contain the exact Goal/Task material",
            ));
        }
    }
    Ok(())
}

fn inbox_rows(connection: &Connection) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence FROM inbox_command ORDER BY command_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Vec<u8>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, Option<i64>>(4)?,
        ))
    })?;
    rows.map(|row| {
        let (command, fingerprint, bytes, state, sequence) = row?;
        if !command.starts_with("command:SYNTHETIC_TEST:")
            || canonicalize_json(&bytes)? != bytes
            || sha256_hex(&bytes) != fingerprint
        {
            return Err(LedgerError::InvalidInput(
                "integrated Inbox row is not exact synthetic canonical input",
            ));
        }
        Ok(json!([command, fingerprint, state, sequence]))
    })
    .collect()
}

fn replay_rows(connection: &Connection) -> Result<(Vec<Value>, u64), LedgerError> {
    let mut statement = connection.prepare(
        "SELECT command_id,request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index ORDER BY command_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, Vec<u8>>(3)?,
            row.get::<_, i64>(4)?,
            row.get::<_, i64>(5)?,
        ))
    })?;
    let mut result = Vec::new();
    let mut calls = 0_u64;
    for row in rows {
        let (command, request, response, bytes, events, external_calls) = row?;
        if canonicalize_json(&bytes)? != bytes || sha256_hex(&bytes) != response {
            return Err(LedgerError::InvalidInput(
                "integrated replay response is not exact canonical bytes",
            ));
        }
        let external_calls = u64::try_from(external_calls)
            .map_err(|_| LedgerError::InvalidInput("negative external call accounting"))?;
        calls = calls
            .checked_add(external_calls)
            .ok_or(LedgerError::InvalidInput(
                "external call accounting overflow",
            ))?;
        result.push(json!([command, request, response, events, external_calls]));
    }
    Ok((result, calls))
}

fn outbox_rows(connection: &Connection) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(
        "SELECT intent_id,intent_revision,effect_scope_fingerprint,canonical_bytes,intent_fingerprint,created_event_sequence FROM outbox_intent ORDER BY intent_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, Vec<u8>>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, i64>(5)?,
        ))
    })?;
    rows.map(|row| {
        let (intent, revision, scope, bytes, fingerprint, sequence) = row?;
        let value: Value = serde_json::from_slice(&bytes)
            .map_err(|_| LedgerError::InvalidInput("integrated Outbox row is not JSON"))?;
        if canonicalize_json(&bytes)? != bytes
            || value.get("environment").and_then(Value::as_str) != Some("SYNTHETIC_TEST")
            || value.get("authority_eligible").and_then(Value::as_bool) != Some(false)
            || value.get("completion_blocking").and_then(Value::as_bool) != Some(true)
        {
            return Err(LedgerError::InvalidInput(
                "integrated Outbox row is not the synthetic nonauthority witness",
            ));
        }
        Ok(json!([
            intent,
            revision,
            scope,
            sha256_hex(&bytes),
            fingerprint,
            sequence
        ]))
    })
    .collect()
}

enum BlobRowKind {
    Envelope,
}

fn blob_fingerprint_rows(
    connection: &Connection,
    sql: &str,
    _kind: BlobRowKind,
) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(sql)?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, i64>(3)?,
            row.get::<_, Vec<u8>>(4)?,
            row.get::<_, String>(5)?,
            row.get::<_, i64>(6)?,
        ))
    })?;
    rows.map(|row| {
        let (id, command, command_type, revision, bytes, fingerprint, sequence) = row?;
        if canonicalize_json(&bytes)? != bytes || sha256_hex(&bytes) != fingerprint {
            return Err(LedgerError::InvalidInput(
                "integrated Command envelope bytes are not exact",
            ));
        }
        Ok(json!([
            id,
            command,
            command_type,
            revision,
            fingerprint,
            sequence
        ]))
    })
    .collect()
}

fn string_rows(
    connection: &Connection,
    sql: &str,
    field_count: usize,
) -> Result<Vec<Value>, LedgerError> {
    let mut statement = connection.prepare(sql)?;
    let rows = statement.query_map([], |row| {
        let mut values = Vec::with_capacity(field_count);
        for index in 0..field_count {
            let value = row.get_ref(index)?;
            values.push(match value {
                rusqlite::types::ValueRef::Null => Value::Null,
                rusqlite::types::ValueRef::Integer(value) => json!(value),
                rusqlite::types::ValueRef::Text(value) => {
                    Value::String(String::from_utf8_lossy(value).into_owned())
                }
                _ => {
                    return Err(rusqlite::Error::InvalidColumnType(
                        index,
                        index.to_string(),
                        value.data_type(),
                    ));
                }
            });
        }
        Ok(Value::Array(values))
    })?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

fn require_canonical_runtime_unusable(bytes: &[u8]) -> Result<(), LedgerError> {
    if canonicalize_json(bytes)? != bytes {
        return Err(LedgerError::InvalidInput(
            "integrated canonical bytes are not canonical",
        ));
    }
    let value: Value = serde_json::from_slice(bytes)
        .map_err(|_| LedgerError::InvalidInput("integrated canonical bytes are not JSON"))?;
    if value.get("runtime_usable").and_then(Value::as_bool) != Some(false) {
        return Err(LedgerError::InvalidInput(
            "integrated fact or Event is runtime-usable",
        ));
    }
    if let Some(environment) = value.get("environment")
        && environment.as_str() != Some("SYNTHETIC_TEST")
    {
        return Err(LedgerError::InvalidInput(
            "integrated fact is outside SYNTHETIC_TEST",
        ));
    }
    Ok(())
}

fn count(connection: &Connection, table: &str) -> Result<u64, LedgerError> {
    let sql = format!("SELECT COUNT(*) FROM {table}");
    let value: i64 = connection.query_row(&sql, [], |row| row.get(0))?;
    u64::try_from(value).map_err(|_| LedgerError::InvalidInput("negative SQLite row count"))
}
