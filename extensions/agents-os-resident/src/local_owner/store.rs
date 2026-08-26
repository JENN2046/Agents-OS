//! Canonical local-owner mutation/query implementation.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::Read;
use std::time::{SystemTime, UNIX_EPOCH};

use rusqlite::{Connection, OpenFlags, OptionalExtension, Transaction, TransactionBehavior, params};
use serde_json::{Map, Value, json};
use unicode_normalization::UnicodeNormalization;

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;

use super::consent::{
    Challenge, ConsentKind, ConsentParse, consent_commitment, generate_challenge,
    normalize_transcript, parse_transcript,
};
use super::continuity::{ContinuityAnchor, LocalContinuitySnapshot};
use super::schema;
use super::{LocalOwnerError, PROFILE_ID};

pub const DEFAULT_PROPOSAL_TTL_SECONDS: u64 = 300;
const MAX_PROPOSAL_GENERATION_ATTEMPTS: usize = 128;

const MMR_STATE_FACT_KIND: &str = "MMR_STATE_CORE";
const COMMITMENT_FACT_KIND: &str = "MMR_COMMITMENT_CORE";
const EVIDENCE_FACT_KIND: &str = "MMR_EVIDENCE_CORE";
const CANDIDATE_FACT_KIND: &str = "MMR_CANDIDATE_CORE";
const SUMMARY_FACT_KIND: &str = "MMR_SUMMARY_CORE";
const OUTCOME_FACT_KIND: &str = "MMR_OPERATION_OUTCOME";
const COMMITMENT_PROTOCOL: &str = "MMR0_EXPLICIT_COMMITMENT_CORE_V1";
const EVIDENCE_PROTOCOL: &str = "MMR0_EXPLICIT_EVIDENCE_CORE_V1";
const CANDIDATE_PROTOCOL: &str = "MMR0_EXPLICIT_CANDIDATE_CORE_V1";
const SUMMARY_PROTOCOL: &str = "MMR0_EXPLICIT_SUMMARY_CORE_V1";
const OUTCOME_PROTOCOL: &str = "MMR0_OPERATION_OUTCOME_V1";
// P2-H canonical four-way stable logical outcome vocabulary (gate semantic_goal:
// "Bind operation identity and return COMMITTED, DENIED, NOT_COMMITTED_RETRYABLE,
// or BLOCKED_INDETERMINATE deterministically.").
const OUTCOME_COMMITTED: &str = "COMMITTED";
const OUTCOME_DENIED: &str = "DENIED";
const OUTCOME_NOT_COMMITTED_RETRYABLE: &str = "NOT_COMMITTED_RETRYABLE";
const OUTCOME_BLOCKED_INDETERMINATE: &str = "BLOCKED_INDETERMINATE";
// OBS-ACK dispositions recorded at the response boundary (transport/session
// observability, never Memory semantics).
const ACK_DISPOSITION_DELIVERED: &str = "DELIVERED";
const ACK_DISPOSITION_LOST: &str = "LOST";
const COMMITMENT_LIFECYCLE_ACTIVE: &str = "ACTIVE";
const COMMITMENT_LIFECYCLE_FULFILLED: &str = "FULFILLED";
const COMMITMENT_LIFECYCLE_RELEASED: &str = "RELEASED";
const CANDIDATE_STATUS_CANDIDATE: &str = "CANDIDATE";
const CANDIDATE_OUTCOME_EVIDENCE_BACKED: &str = "EVIDENCE_BACKED";
const CANDIDATE_OUTCOME_REVISED: &str = "REVISED";
const CANDIDATE_OUTCOME_REJECTED: &str = "REJECTED";
const EVIDENCE_LIFECYCLE_RECORDED: &str = "P2_F_EVIDENCE_RECORDED";
const SUMMARY_LIFECYCLE_DERIVED: &str = "DERIVED";
const EVIDENCE_AVAILABILITY_AVAILABLE: &str = "AVAILABLE";
const EVIDENCE_AVAILABILITY_UNAVAILABLE: &str = "UNAVAILABLE";
const SUPPORT_STATE_SUPPORTED: &str = "SUPPORTED";
const SUPPORT_STATE_UNSUPPORTED: &str = "UNSUPPORTED";
const SUPPORT_STATE_UNKNOWN: &str = "UNKNOWN";
const COGNITIVE_PROJECTION_SCHEMA: &str = "MMR0_COGNITIVE_PROJECTION_V1";
const COGNITIVE_RESPONSE_CONTRACT: &str = "MMR0_CAV2_STRUCTURED_RESPONSE_V1";
const COGNITIVE_NEGATIVE_RESPONSE_CONTRACT: &str = "MMR0_CAV3_UNKNOWN_RESPONSE_V1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LocalOwnerFault {
    None,
    AfterDomainWrites,
    AfterEvents,
    AfterReplayIndex,
    AfterCommitBeforeResponse,
}

#[derive(Clone, Debug)]
struct MmrOperationRecord {
    operation_id: String,
    operation_fingerprint: String,
    state_id: String,
    fact_fingerprint: String,
    predecessor_fact_fingerprint: Option<String>,
    revision: u64,
}

impl MmrOperationRecord {
    fn as_json(&self) -> Value {
        json!({
            "localTransactionApplied": true,
            "mmrCommittedGuaranteeProven": false,
            "operationFingerprint": self.operation_fingerprint,
            "operationId": self.operation_id,
            "predecessorFactFingerprint": self.predecessor_fact_fingerprint,
            "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF",
            "revision": self.revision,
            "stateId": self.state_id,
            "successorFactFingerprint": self.fact_fingerprint,
        })
    }

    fn as_applied_result(&self) -> Value {
        self.as_json()
    }
}

fn validate_mmr_core_mutation(
    value: &Value,
    plane_required: bool,
) -> Result<&Map<String, Value>, LocalOwnerError> {
    let mutation = require_exact_object(
        value,
        &[
            "components",
            "expectedCurrentFingerprint",
            "mutationType",
            "operationId",
            "targetStateId",
        ],
    )?;
    let components = mutation["components"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    if plane_required {
        require_exact_map_keys(
            components,
            &["authority", "content", "lifecycle", "plane", "provenance", "transition"],
        )?;
    } else {
        require_exact_map_keys(
            components,
            &["authority", "content", "lifecycle", "provenance", "transition"],
        )?;
    }
    let content = require_exact_object(&components["content"], &["value"])?;
    if content["value"].is_null() {
        return Err(LocalOwnerError::InvalidInput);
    }
    let mutation_type = require_string(mutation, "mutationType", 32)?;
    let (subject_ref, mutation_actor_ref) = validate_mmr_provenance(components)?;
    if plane_required {
        validate_mmr_plane_components(
            components,
            require_nonempty_string(mutation, "targetStateId", 200)?,
            &subject_ref,
        )?;
    }
    validate_mmr_mutation_authority(
        components,
        mutation_type,
        require_nonempty_string(mutation, "targetStateId", 200)?,
        &subject_ref,
        &mutation_actor_ref,
    )?;
    let lifecycle = require_exact_object(
        &components["lifecycle"],
        &["epistemicState", "lifecycleState"],
    )?;
    let lifecycle_state = require_string(lifecycle, "lifecycleState", 64)?;
    let lifecycle_valid = match mutation_type {
        "CREATE" => lifecycle_state == "P2_B_CREATED",
        "REVISE" => {
            lifecycle_state == "P2_B_SUCCESSOR"
                || lifecycle_state == "P2_D_ADMITTED_STATUS_TRANSITION"
        }
        "SUPERSEDE" => lifecycle_state == "P2_D_SUPERSEDING",
        "RETIRE" => lifecycle_state == "P2_D_RETIRED",
        "CREATE_COMMITMENT" => lifecycle_state == COMMITMENT_LIFECYCLE_ACTIVE,
        "FULFILL_COMMITMENT" => lifecycle_state == COMMITMENT_LIFECYCLE_FULFILLED,
        "RELEASE_COMMITMENT" => lifecycle_state == COMMITMENT_LIFECYCLE_RELEASED,
        "CREATE_EVIDENCE" => lifecycle_state == EVIDENCE_LIFECYCLE_RECORDED,
        "CREATE_CANDIDATE" => lifecycle_state == CANDIDATE_STATUS_CANDIDATE,
        "CREATE_SUMMARY" => lifecycle_state == SUMMARY_LIFECYCLE_DERIVED,
        "ADD_EVIDENCE" => {
            matches!(
                lifecycle_state,
                "P2_D_EVIDENCE_ADDED"
                    | "EVIDENCE_BACKED"
                    | "REVISED"
                    | "REJECTED"
                    | "CANDIDATE"
            )
        }
        _ => false,
    };
    if require_string(lifecycle, "epistemicState", 64)? != "UNASSESSED" || !lifecycle_valid {
        return Err(LocalOwnerError::InvalidInput);
    }
    let transition = require_exact_object(
        &components["transition"],
        &["predecessorStateFingerprint", "supersedesStateFingerprint"],
    )?;
    match mutation_type {
        "CREATE" | "CREATE_COMMITMENT" | "CREATE_EVIDENCE" | "CREATE_CANDIDATE"
        | "CREATE_SUMMARY" => {
            if !mutation["expectedCurrentFingerprint"].is_null()
                || !transition["predecessorStateFingerprint"].is_null()
                || !transition["supersedesStateFingerprint"].is_null()
            {
                return Err(LocalOwnerError::InvalidInput);
            }
        }
        "REVISE" | "SUPERSEDE" | "ADD_EVIDENCE"
        | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT" => {
            let expected = require_sha256_value(&mutation["expectedCurrentFingerprint"])?;
            if transition["predecessorStateFingerprint"].as_str() != Some(expected)
                || transition["supersedesStateFingerprint"].as_str() != Some(expected)
            {
                return Err(LocalOwnerError::InvalidInput);
            }
        }
        "RETIRE" => {
            let expected = require_sha256_value(&mutation["expectedCurrentFingerprint"])?;
            if transition["predecessorStateFingerprint"].as_str() != Some(expected)
                || !transition["supersedesStateFingerprint"].is_null()
            {
                return Err(LocalOwnerError::InvalidInput);
            }
        }
        _ => return Err(LocalOwnerError::InvalidInput),
    }
    Ok(mutation)
}

fn optional_plane_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
) -> Result<Option<&'a str>, LocalOwnerError> {
    match object.get(key) {
        Some(Value::Null) => Ok(None),
        Some(Value::String(value)) if !value.is_empty() && value.len() <= 300 => Ok(Some(value)),
        _ => Err(LocalOwnerError::MmrSourceScopeEscalation),
    }
}

fn validate_mmr_plane_components(
    components: &Map<String, Value>,
    target_state_id: &str,
    subject_ref: &str,
) -> Result<(), LocalOwnerError> {
    let plane = components
        .get("plane")
        .and_then(Value::as_object)
        .ok_or(LocalOwnerError::MmrSourceScopeEscalation)?;
    require_exact_map_keys(
        plane,
        &[
            "claimScope",
            "controllerRole",
            "interpretationOwnerRef",
            "objectKind",
            "sharedEventStateId",
        ],
    )
    .map_err(|_| LocalOwnerError::MmrSourceScopeEscalation)?;
    let object_kind = require_nonempty_string(plane, "objectKind", 64)
        .map_err(|_| LocalOwnerError::MmrSourceScopeEscalation)?;
    let claim_scope = require_nonempty_string(plane, "claimScope", 64)
        .map_err(|_| LocalOwnerError::MmrSourceScopeEscalation)?;
    let controller_role = require_nonempty_string(plane, "controllerRole", 64)
        .map_err(|_| LocalOwnerError::MmrSourceScopeEscalation)?;
    let interpretation_owner = optional_plane_string(plane, "interpretationOwnerRef")?;
    let shared_event = optional_plane_string(plane, "sharedEventStateId")?;
    let provenance = components["provenance"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let source_type = provenance["source"]["type"]
        .as_str()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    if object_kind == "SUBJECT_INTERPRETATION"
        && shared_event.is_some_and(|value| value == target_state_id)
    {
        return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
    }
    if object_kind == "SUMMARY_STATE"
        && shared_event.is_some_and(|value| value == target_state_id)
    {
        return Err(LocalOwnerError::MmrSummarySelfEvidenceRejected);
    }

    let valid = match object_kind {
        "SCOPED_CLAIM" => {
            controller_role == "NON_CONTROLLER"
                && interpretation_owner.is_none()
                && shared_event.is_none()
                && match claim_scope {
                    "MMR_STATE_CORE" => true,
                    "JENN_PREFERENCE" => {
                        subject_ref == "subject:jenn"
                            && source_type == "JENN_EXPLICIT"
                            && target_state_id.starts_with("state:jenn-preference:")
                    }
                    _ => false,
                }
        }
        "DERIVED_OBSERVATION" => {
            claim_scope == "NOBAO_SELF_OBSERVATION"
                && controller_role == "DERIVED_NON_CONTROLLER"
                && subject_ref == "subject:nobao"
                && source_type == "NOBAO_INFERENCE"
                && interpretation_owner == Some("subject:nobao")
                && shared_event.is_none()
                && target_state_id.starts_with("state:observer:")
        }
        "SHARED_EVENT" => {
            claim_scope == "SHARED_HISTORY"
                && controller_role == "NON_CONTROLLER"
                && subject_ref == "subject:shared-project"
                && interpretation_owner.is_none()
                && shared_event == Some(target_state_id)
                && target_state_id.starts_with("state:shared-event:")
        }
        "SUBJECT_INTERPRETATION" => {
            claim_scope == "SHARED_INTERPRETATION"
                && controller_role == "NON_CONTROLLER"
                && interpretation_owner == Some(subject_ref)
                && shared_event.is_some_and(|value| value != target_state_id)
                && ((subject_ref == "subject:jenn" && source_type == "JENN_EXPLICIT")
                    || (subject_ref == "subject:nobao" && source_type == "NOBAO_INFERENCE"))
                && target_state_id.starts_with("state:interpretation:")
        }
        "DERIVED_STATE" => {
            claim_scope == "DERIVED_STATE"
                && controller_role == "DERIVED_NON_CONTROLLER"
                && subject_ref == "subject:derived"
                && matches!(source_type, "JENN_EXPLICIT" | "SYNTHETIC_TEST")
                && interpretation_owner.is_none()
                && shared_event.is_some_and(|value| value != target_state_id)
                && target_state_id.starts_with("state:derived:")
        }
        "COMMITMENT_STATE" => {
            claim_scope == "COMMITMENT"
                && controller_role == "NON_CONTROLLER"
                && subject_ref == "subject:jenn"
                && source_type == "JENN_EXPLICIT"
                && interpretation_owner.is_none()
                && shared_event.is_none()
                && target_state_id.starts_with("state:commitment:")
        }
        "EVIDENCE_STATE" => {
            claim_scope == "EVIDENCE"
                && controller_role == "NON_CONTROLLER"
                && interpretation_owner.is_none()
                && shared_event.is_none()
                && matches!(
                    (subject_ref, source_type),
                    ("subject:jenn", "JENN_EXPLICIT")
                        | ("subject:synthetic:P2-F", "SYNTHETIC_TEST")
                )
                && target_state_id.starts_with("state:evidence:")
        }
        "CANDIDATE_STATE" => {
            claim_scope == "CANDIDATE"
                && controller_role == "NON_CONTROLLER"
                && interpretation_owner.is_none()
                && shared_event.is_none()
                && matches!(
                    (subject_ref, source_type),
                    ("subject:jenn", "JENN_EXPLICIT")
                        | ("subject:synthetic:P2-F", "SYNTHETIC_TEST")
                )
                && target_state_id.starts_with("state:candidate:")
        }
        "SUMMARY_STATE" => {
            claim_scope == "SUMMARY"
                && controller_role == "NON_CONTROLLER"
                && interpretation_owner.is_none()
                && shared_event.is_some_and(|value| value != target_state_id)
                && matches!(
                    (subject_ref, source_type),
                    ("subject:jenn", "JENN_EXPLICIT")
                        | ("subject:synthetic:P2-F", "SYNTHETIC_TEST")
                )
                && target_state_id.starts_with("state:summary:")
        }
        _ => false,
    };
    if valid {
        Ok(())
    } else {
        Err(LocalOwnerError::MmrSourceScopeEscalation)
    }
}

fn provenance_object<'a>(
    value: &'a Value,
    keys: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    require_exact_map_keys(object, keys).map_err(|_| LocalOwnerError::MmrProvenanceRequired)?;
    Ok(object)
}

fn provenance_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    maximum_bytes: usize,
) -> Result<&'a str, LocalOwnerError> {
    require_nonempty_string(object, key, maximum_bytes)
        .map_err(|_| LocalOwnerError::MmrProvenanceRequired)
}

fn validate_mmr_provenance(
    components: &Map<String, Value>,
) -> Result<(String, String), LocalOwnerError> {
    let provenance = provenance_object(
        components
            .get("provenance")
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?,
        &[
            "interpreter",
            "mutationActor",
            "source",
            "sourceAuthority",
            "subject",
            "supportingBasis",
        ],
    )?;
    let source = provenance_object(&provenance["source"], &["ref", "type"])?;
    let source_ref = provenance_string(source, "ref", 300)?;
    let source_type = provenance_string(source, "type", 64)?;
    let subject = provenance_object(&provenance["subject"], &["ref"])?;
    let subject_ref = provenance_string(subject, "ref", 300)?;
    let interpreter = provenance_object(&provenance["interpreter"], &["ref", "type"])?;
    let interpreter_type = provenance_string(interpreter, "type", 64)?;
    let interpreter_ref = interpreter.get("ref").ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let mutation_actor = provenance_object(&provenance["mutationActor"], &["ref", "type"])?;
    let mutation_actor_type = provenance_string(mutation_actor, "type", 64)?;
    let mutation_actor_ref = provenance_string(mutation_actor, "ref", 300)?;
    let supporting_basis = provenance_object(&provenance["supportingBasis"], &["ref"])?;
    let supporting_basis_ref = provenance_string(supporting_basis, "ref", 300)?;
    let source_authority = provenance_object(
        &provenance["sourceAuthority"],
        &["recordRef", "sourceRef", "sourceType", "supportingBasisRef"],
    )?;
    let record_ref = provenance_string(source_authority, "recordRef", 300)?;
    let asserted_source_ref = provenance_string(source_authority, "sourceRef", 300)?;
    let asserted_source_type = provenance_string(source_authority, "sourceType", 64)?;
    let asserted_basis_ref = provenance_string(source_authority, "supportingBasisRef", 300)?;

    let source_relation_valid = match source_type {
        "JENN_EXPLICIT" => {
            source_ref.starts_with("source:jenn-explicit:")
                && supporting_basis_ref.starts_with("basis:jenn-explicit-statement:")
        }
        "NOBAO_INFERENCE" => {
            source_ref.starts_with("source:nobao-inference:")
                && supporting_basis_ref.starts_with("basis:nobao-inference:")
                && interpreter_type == "NOBAO"
                && interpreter_ref
                    .as_str()
                    .is_some_and(|value| value.starts_with("actor:nobao:"))
        }
        "EXTERNAL_TOOL_RESULT" => {
            source_ref.starts_with("source:external-tool:")
                && supporting_basis_ref.starts_with("basis:external-tool-result:")
        }
        "SYNTHETIC_TEST" => {
            source_ref.starts_with("source:synthetic-test:")
                && supporting_basis_ref.starts_with("basis:synthetic-test:")
                && interpreter_type == "SYNTHETIC_TEST_HARNESS"
        }
        _ => false,
    };
    let interpreter_valid = match interpreter_type {
        "NONE_DIRECT" => interpreter_ref.is_null(),
        "NOBAO" => interpreter_ref
            .as_str()
            .is_some_and(|value| value.starts_with("actor:nobao:")),
        "EXPLICIT_HUMAN_OPERATOR" => interpreter_ref
            .as_str()
            .is_some_and(|value| value.starts_with("actor:human:")),
        "SYNTHETIC_TEST_HARNESS" => interpreter_ref
            .as_str()
            .is_some_and(|value| value.starts_with("actor:synthetic-test-harness:")),
        _ => false,
    };
    let actor_valid = match mutation_actor_type {
        "NOBAO" => mutation_actor_ref.starts_with("actor:nobao:"),
        "EXPLICIT_HUMAN_OPERATOR" => mutation_actor_ref.starts_with("actor:human:"),
        "SYNTHETIC_TEST_HARNESS" => {
            mutation_actor_ref.starts_with("actor:synthetic-test-harness:")
        }
        _ => false,
    };
    if !subject_ref.starts_with("subject:")
        || !record_ref.starts_with("source-authority-record:")
        || !source_relation_valid
        || !interpreter_valid
        || !actor_valid
        || asserted_source_ref != source_ref
        || asserted_source_type != source_type
        || asserted_basis_ref != supporting_basis_ref
    {
        return Err(LocalOwnerError::MmrSourceAuthorityMismatch);
    }
    Ok((subject_ref.to_owned(), mutation_actor_ref.to_owned()))
}

fn authority_object<'a>(
    value: &'a Value,
    keys: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value
        .as_object()
        .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
    require_exact_map_keys(object, keys)
        .map_err(|_| LocalOwnerError::MmrAuthorityScopeDenied)?;
    Ok(object)
}

fn authority_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    maximum_bytes: usize,
) -> Result<&'a str, LocalOwnerError> {
    require_nonempty_string(object, key, maximum_bytes)
        .map_err(|_| LocalOwnerError::MmrAuthorityScopeDenied)
}

fn validate_mmr_mutation_authority(
    components: &Map<String, Value>,
    mutation_type: &str,
    target_state_id: &str,
    subject_ref: &str,
    mutation_actor_ref: &str,
) -> Result<(), LocalOwnerError> {
    let authority = authority_object(
        components
            .get("authority")
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?,
        &["authorityBasisRef", "authorityBasisType", "grant"],
    )?;
    let basis_ref = authority_string(authority, "authorityBasisRef", 300)?;
    let basis_type = authority_string(authority, "authorityBasisType", 64)?;
    let grant = authority_object(
        &authority["grant"],
        &[
            "grantId",
            "granteeActorRef",
            "operation",
            "right",
            "scope",
            "subjectRef",
            "targetStateId",
        ],
    )?;
    let grant_id = authority_string(grant, "grantId", 300)?;
    let grantee = authority_string(grant, "granteeActorRef", 300)?;
    let operation = authority_string(grant, "operation", 64)?;
    let right = authority_string(grant, "right", 64)?;
    let scope = authority_string(grant, "scope", 64)?;
    let grant_subject = authority_string(grant, "subjectRef", 300)?;
    let grant_target = authority_string(grant, "targetStateId", 300)?;
    let plane = components.get("plane").and_then(Value::as_object);
    let plane_kind = plane
        .and_then(|value| value.get("objectKind"))
        .and_then(Value::as_str);
    let claim_scope = plane
        .and_then(|value| value.get("claimScope"))
        .and_then(Value::as_str);

    if basis_type == "OBSERVER_DERIVED_OUTPUT" {
        return Err(LocalOwnerError::MmrObserverControllerPromotion);
    }
    if basis_type == "SUBJECT_INTERPRETATION_AUTHORITY"
        && plane_kind != Some("SUBJECT_INTERPRETATION")
    {
        return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
    }

    let basis_scope_valid = match basis_type {
        "EXPLICIT_OWNER_APPROVED_MUTATION" => {
            basis_ref.starts_with("authority-basis:owner-approved:")
                && matches!(
                    (plane_kind, claim_scope, scope),
                    (None, None, "MMR_STATE_CORE")
                        | (Some("SCOPED_CLAIM"), Some("MMR_STATE_CORE"), "MMR_STATE_CORE")
                        | (Some("SHARED_EVENT"), Some("SHARED_HISTORY"), "SHARED_HISTORY_STATE")
                        | (Some("DERIVED_STATE"), Some("DERIVED_STATE"), "DERIVED_STATE_STATE")
                        | (Some("COMMITMENT_STATE"), Some("COMMITMENT"), "COMMITMENT_STATE")
                        | (Some("EVIDENCE_STATE"), Some("EVIDENCE"), "EVIDENCE_STATE")
                        | (Some("CANDIDATE_STATE"), Some("CANDIDATE"), "CANDIDATE_STATE")
                        | (Some("SUMMARY_STATE"), Some("SUMMARY"), "SUMMARY_STATE")
                )
        }
        "ADMITTED_SYNTHETIC_FIXTURE" => {
            basis_ref.starts_with("authority-basis:synthetic-fixture:")
                && matches!(
                    (plane_kind, claim_scope, scope),
                    (None, None, "MMR_STATE_CORE")
                        | (Some("SCOPED_CLAIM"), Some("MMR_STATE_CORE"), "MMR_STATE_CORE")
                        | (Some("DERIVED_OBSERVATION"), Some("NOBAO_SELF_OBSERVATION"), "DERIVED_OBSERVATION_STATE")
                        | (Some("DERIVED_STATE"), Some("DERIVED_STATE"), "DERIVED_STATE_STATE")
                        | (Some("SHARED_EVENT"), Some("SHARED_HISTORY"), "SHARED_HISTORY_STATE")
                        | (Some("SUBJECT_INTERPRETATION"), Some("SHARED_INTERPRETATION"), "SUBJECT_INTERPRETATION_STATE")
                        | (Some("COMMITMENT_STATE"), Some("COMMITMENT"), "COMMITMENT_STATE")
                        | (Some("EVIDENCE_STATE"), Some("EVIDENCE"), "EVIDENCE_STATE")
                        | (Some("CANDIDATE_STATE"), Some("CANDIDATE"), "CANDIDATE_STATE")
                        | (Some("SUMMARY_STATE"), Some("SUMMARY"), "SUMMARY_STATE")
                )
        }
        "SCOPED_JENN_PREFERENCE" => {
            basis_ref.starts_with("authority-basis:jenn-preference:")
                && scope == "JENN_PREFERENCE_STATE"
                && plane_kind == Some("SCOPED_CLAIM")
                && claim_scope == Some("JENN_PREFERENCE")
                && subject_ref == "subject:jenn"
                && target_state_id.starts_with("state:jenn-preference:")
        }
        "SUBJECT_INTERPRETATION_AUTHORITY" => {
            basis_ref.starts_with("authority-basis:subject-interpretation:")
                && scope == "SUBJECT_INTERPRETATION_STATE"
                && plane_kind == Some("SUBJECT_INTERPRETATION")
                && claim_scope == Some("SHARED_INTERPRETATION")
        }
        "TECHNICAL_REACHABILITY" | "NOBAO_PRIVATE_REFLECTION" => false,
        _ => false,
    };
    if !basis_scope_valid
        || !grant_id.starts_with("grant:")
        || grantee != mutation_actor_ref
        || operation != mutation_type
        || right != "MMR_DURABLE_STATE_MUTATION"
        || grant_subject != subject_ref
        || grant_target != target_state_id
    {
        return Err(LocalOwnerError::MmrAuthorityScopeDenied);
    }
    Ok(())
}

fn require_sha256_value(value: &Value) -> Result<&str, LocalOwnerError> {
    let digest = value.as_str().ok_or(LocalOwnerError::InvalidInput)?;
    if digest.len() == 64
        && digest
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(digest)
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn mmr_consent_kind(mutation_type: &str) -> Result<ConsentKind, LocalOwnerError> {
    match mutation_type {
        "CREATE" | "CREATE_COMMITMENT" | "CREATE_EVIDENCE" | "CREATE_CANDIDATE"
        | "CREATE_SUMMARY" => Ok(ConsentKind::Create),
        "REVISE" | "SUPERSEDE" | "RETIRE" | "ADD_EVIDENCE"
        | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT" => Ok(ConsentKind::Change),
        _ => Err(LocalOwnerError::MmrMutationNotAuthorized),
    }
}

fn require_exact_map_keys(
    object: &Map<String, Value>,
    keys: &[&str],
) -> Result<(), LocalOwnerError> {
    let mut actual: Vec<&str> = object.keys().map(String::as_str).collect();
    let mut expected = keys.to_vec();
    actual.sort();
    expected.sort();
    if actual == expected {
        Ok(())
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn validate_stored_mmr_core_state(value: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        value,
        &[
            "components",
            "localAuthorization",
            "localOutcome",
            "mutationType",
            "operationFingerprint",
            "operationId",
            "protocol",
            "revision",
            "stateId",
        ],
    )?;
    let protocol = require_string(object, "protocol", 64)?;
    if ![
        "MMR0_EXPLICIT_MUTATION_CORE_V2",
        "MMR0_EXPLICIT_MUTATION_CORE_V3",
        "MMR0_EXPLICIT_MUTATION_CORE_V4",
    ]
    .contains(&protocol)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let mutation_type = require_string(object, "mutationType", 32)?;
    if !["CREATE", "REVISE", "SUPERSEDE", "RETIRE", "ADD_EVIDENCE"].contains(&mutation_type) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let revision = require_u64(object, "revision")?;
    if (mutation_type == "CREATE" && revision != 1)
        || (mutation_type != "CREATE" && revision <= 1)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    require_nonempty_string(object, "operationId", 200)?;
    require_nonempty_string(object, "stateId", 200)?;
    let operation_fingerprint = require_string(object, "operationFingerprint", 64)?;
    if operation_fingerprint.len() != 64
        || !operation_fingerprint.bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let authorization = require_exact_object(
        &object["localAuthorization"],
        &[
            "authorityBasisRef",
            "consentCommitment",
            "grantId",
            "mutationActorRef",
            "right",
            "scope",
        ],
    )?;
    let commitment = require_string(authorization, "consentCommitment", 64)?;
    if commitment.len() != 64
        || !commitment.bytes().all(|byte| byte.is_ascii_hexdigit())
        || require_string(authorization, "scope", 64)?
            != match protocol {
                "MMR0_EXPLICIT_MUTATION_CORE_V3" => "P2_C_PLANE_SCOPED_MUTATION_AUTHORITY",
                "MMR0_EXPLICIT_MUTATION_CORE_V4" => {
                    "P2_D_REVISION_SUPERSESSION_DERIVED_STATE_AUTHORITY"
                }
                _ => "P2_B_SCOPED_MUTATION_AUTHORITY",
            }
        || require_string(authorization, "right", 64)? != "MMR_DURABLE_STATE_MUTATION"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let components = object["components"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let authority = components["authority"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let grant = authority["grant"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let provenance = components["provenance"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let actor = provenance["mutationActor"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    if authorization["authorityBasisRef"] != authority["authorityBasisRef"]
        || authorization["grantId"] != grant["grantId"]
        || authorization["mutationActorRef"] != actor["ref"]
    {
        return Err(LocalOwnerError::MmrAuthorityScopeDenied);
    }
    let outcome = require_exact_object(
        &object["localOutcome"],
        &["mmrCommittedGuaranteeProven", "resultCode"],
    )?;
    if outcome["mmrCommittedGuaranteeProven"] != Value::Bool(false)
        || require_string(outcome, "resultCode", 64)?
            != "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let predecessor = &object["components"]["transition"]["predecessorStateFingerprint"];
    let synthetic_mutation = json!({
        "components": object["components"],
        "expectedCurrentFingerprint": predecessor,
        "mutationType": mutation_type,
        "operationId": object["operationId"],
        "targetStateId": object["stateId"],
    });
    match validate_mmr_core_mutation(
        &synthetic_mutation,
        protocol != "MMR0_EXPLICIT_MUTATION_CORE_V2",
    ) {
        Ok(_) => Ok(()),
        Err(LocalOwnerError::MmrProvenanceRequired) => {
            Err(LocalOwnerError::MmrProvenanceRequired)
        }
        Err(LocalOwnerError::MmrSourceAuthorityMismatch) => {
            Err(LocalOwnerError::MmrSourceAuthorityMismatch)
        }
        Err(LocalOwnerError::MmrAuthorityScopeDenied) => {
            Err(LocalOwnerError::MmrAuthorityScopeDenied)
        }
        Err(LocalOwnerError::MmrSourceScopeEscalation) => {
            Err(LocalOwnerError::MmrSourceScopeEscalation)
        }
        Err(LocalOwnerError::MmrObserverControllerPromotion) => {
            Err(LocalOwnerError::MmrObserverControllerPromotion)
        }
        Err(LocalOwnerError::MmrInterpretationPlaneConflict) => {
            Err(LocalOwnerError::MmrInterpretationPlaneConflict)
        }
        Err(_) => Err(LocalOwnerError::StateCorrupt),
    }
}

fn kind_current_metadata(
    connection: &Connection,
    fact_kind: &str,
    state_id: &str,
) -> Result<Option<(u64, String)>, LocalOwnerError> {
    connection
        .query_row(
            "SELECT current_fact_revision,current_fact_fingerprint FROM current_pointer WHERE fact_kind=?1 AND logical_id=?2",
            params![fact_kind, state_id],
            |row| Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?)),
        )
        .optional()?
        .map(|(revision, fingerprint)| Ok((as_u64(revision)?, fingerprint)))
        .transpose()
}

fn mmr_current_metadata(
    connection: &Connection,
    state_id: &str,
) -> Result<Option<(u64, String)>, LocalOwnerError> {
    kind_current_metadata(connection, MMR_STATE_FACT_KIND, state_id)
}

fn commitment_current_metadata(
    connection: &Connection,
    commitment_id: &str,
) -> Result<Option<(u64, String)>, LocalOwnerError> {
    kind_current_metadata(connection, COMMITMENT_FACT_KIND, commitment_id)
}

/// Resolves the durable fact kind that a mutation operates on.  The new P2-F
/// CREATE operations own dedicated fact kinds; ADD_EVIDENCE may attach evidence
/// to an MMR_STATE_CORE fact (P2-D) or drive a Candidate transition (P2-F), so
/// the target kind is resolved from the existing Current pointer, never guessed.
fn mutation_fact_kind(
    connection: &Connection,
    mutation_type: &str,
    target_state_id: &str,
) -> Result<&'static str, LocalOwnerError> {
    let kind = match mutation_type {
        "CREATE_COMMITMENT" | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT" => {
            COMMITMENT_FACT_KIND
        }
        "CREATE_EVIDENCE" => EVIDENCE_FACT_KIND,
        "CREATE_CANDIDATE" => CANDIDATE_FACT_KIND,
        "CREATE_SUMMARY" => SUMMARY_FACT_KIND,
        "ADD_EVIDENCE" => {
            let candidate_exists: bool = connection.query_row(
                "SELECT EXISTS(SELECT 1 FROM current_pointer WHERE fact_kind=?1 AND logical_id=?2)",
                params![CANDIDATE_FACT_KIND, target_state_id],
                |row| row.get(0),
            )?;
            if candidate_exists {
                CANDIDATE_FACT_KIND
            } else {
                MMR_STATE_FACT_KIND
            }
        }
        _ => MMR_STATE_FACT_KIND,
    };
    Ok(kind)
}

fn decode_mmr_fact(
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    let value: Value = serde_json::from_slice(bytes).map_err(|_| LocalOwnerError::StateCorrupt)?;
    validate_stored_mmr_core_state(&value)?;
    if value["stateId"] != state_id || value["revision"] != revision {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let transition_predecessor = value["components"]["transition"]
        ["predecessorStateFingerprint"]
        .as_str();
    if transition_predecessor != predecessor {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let material = canonical_value_bytes(&json!({
        "factKind": "MMR_STATE_CORE",
        "logicalId": state_id,
        "predecessorFactFingerprint": predecessor,
        "revision": revision,
        "value": value,
    }))?;
    let expected = domain_fingerprint("agents-os.local-owner.fact.MMR_STATE_CORE.v1", &material);
    if expected != fingerprint {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(value)
}

/// Verifies the identity relation used to publish MMR Current.  The pointer's
/// stored identity is not authority: the referenced fact is resolved and its
/// identity is recomputed from canonical bytes before the relation is trusted.
fn verify_mmr_current_pointer_integrity(
    connection: &Connection,
) -> Result<(), LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint,p.pointer_version,f.fact_ref,f.subject_ref,f.canonical_bytes,f.fact_fingerprint,f.predecessor_fact_fingerprint FROM current_pointer p LEFT JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.fact_kind='MMR_STATE_CORE' ORDER BY p.logical_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, i64>(4)?,
            row.get::<_, Option<String>>(5)?,
            row.get::<_, Option<String>>(6)?,
            row.get::<_, Option<Vec<u8>>>(7)?,
            row.get::<_, Option<String>>(8)?,
            row.get::<_, Option<String>>(9)?,
        ))
    })?;
    for row in rows {
        let (
            state_id,
            pointer_revision,
            pointer_fact_ref,
            pointer_fingerprint,
            pointer_version,
            fact_ref,
            subject_ref,
            canonical_bytes,
            stored_fingerprint,
            predecessor,
        ) = row?;
        let (Some(fact_ref), Some(subject_ref), Some(canonical_bytes), Some(stored_fingerprint)) =
            (fact_ref, subject_ref, canonical_bytes, stored_fingerprint)
        else {
            return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
        };
        let revision = u64::try_from(pointer_revision)
            .map_err(|_| LocalOwnerError::CurrentPointerIdentityMismatch)?;
        if pointer_version != pointer_revision
            || pointer_fact_ref != fact_ref
            || pointer_fingerprint != stored_fingerprint
            || fact_ref != format!("fact:MMR_STATE_CORE:{state_id}:{revision}")
        {
            return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
        }
        let value = decode_mmr_fact(
            &state_id,
            revision,
            &canonical_bytes,
            &stored_fingerprint,
            predecessor.as_deref(),
        )
        .map_err(|error| match error {
            LocalOwnerError::MmrProvenanceRequired => LocalOwnerError::MmrProvenanceRequired,
            LocalOwnerError::MmrSourceAuthorityMismatch => {
                LocalOwnerError::MmrSourceAuthorityMismatch
            }
            LocalOwnerError::MmrAuthorityScopeDenied => LocalOwnerError::MmrAuthorityScopeDenied,
            LocalOwnerError::MmrSourceScopeEscalation => {
                LocalOwnerError::MmrSourceScopeEscalation
            }
            LocalOwnerError::MmrObserverControllerPromotion => {
                LocalOwnerError::MmrObserverControllerPromotion
            }
            LocalOwnerError::MmrInterpretationPlaneConflict => {
                LocalOwnerError::MmrInterpretationPlaneConflict
            }
            _ => LocalOwnerError::CurrentPointerIdentityMismatch,
        })?;
        if value["stateId"] != state_id
            || value["components"]["provenance"]["subject"]["ref"] != subject_ref
        {
            return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
        }
    }
    Ok(())
}

/// Audits the full MMR_STATE_CORE transition history.  Every revision must be
/// contiguous, its fingerprint must recompute from canonical bytes, its
/// predecessor link must match the prior fact, and its creating event must bind
/// the same fact identity.  Exactly one Current must point at the chain head.
/// Any break is a hard stop: the Runtime must not continue Active on a state
/// whose required transition cannot be audited, and no repair is fabricated.
fn verify_mmr_transition_history_integrity(
    connection: &Connection,
) -> Result<(), LocalOwnerError> {
    let mut state_ids = BTreeSet::new();
    let mut id_statement = connection.prepare(
        "SELECT DISTINCT logical_id FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' ORDER BY logical_id",
    )?;
    let id_rows = id_statement.query_map([], |row| row.get::<_, String>(0))?;
    for id in id_rows {
        state_ids.insert(id?);
    }
    for state_id in state_ids {
        let mut chain = connection.prepare(
            "SELECT fact_revision,fact_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 ORDER BY fact_revision",
        )?;
        let rows = chain.query_map([&state_id], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, Vec<u8>>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, i64>(5)?,
            ))
        })?;
        let mut expected_revision = 1_u64;
        let mut previous_fingerprint: Option<String> = None;
        for row in rows {
            let (revision, fact_ref, bytes, fingerprint, predecessor, event_sequence) = row?;
            let revision = as_u64(revision)?;
            if revision != expected_revision || predecessor != previous_fingerprint {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let value = decode_mmr_fact(
                &state_id,
                revision,
                &bytes,
                &fingerprint,
                predecessor.as_deref(),
            )
            .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            if fact_ref != format!("fact:MMR_STATE_CORE:{state_id}:{revision}")
                || (revision == 1) != (value["mutationType"] == "CREATE")
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let (event_kind, aggregate_revision, command_fingerprint, event_bytes): (
                String,
                i64,
                Option<String>,
                Vec<u8>,
            ) = connection.query_row(
                "SELECT event_kind,aggregate_revision,command_fingerprint,canonical_bytes FROM event WHERE event_sequence=?1",
                [event_sequence],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )?;
            let event_value: Value = serde_json::from_slice(&event_bytes)
                .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            let bound_event = matches!(
                event_kind.as_str(),
                "MMR_STATE_CORE_CREATED"
                    | "MMR_STATE_CORE_SUCCEEDED"
                    | "MMR_STATE_CORE_SUPERSEDED"
                    | "MMR_STATE_CORE_RETIRED"
                    | "MMR_STATE_CORE_EVIDENCE_ADDED"
            );
            if !bound_event
                || as_u64(aggregate_revision)? != revision
                || command_fingerprint.as_deref() != value["operationFingerprint"].as_str()
                || event_value["aggregateRef"] != state_id
                || event_value["aggregateRevision"] != revision
                || event_value["factFingerprint"] != fingerprint
                || event_value["factRef"] != fact_ref
                || event_value["commandFingerprint"] != value["operationFingerprint"]
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            previous_fingerprint = Some(fingerprint);
            expected_revision += 1;
        }
        let head_revision = expected_revision - 1;
        let pointer: Option<(i64, String, String)> = connection
            .query_row(
                "SELECT current_fact_revision,current_fact_ref,current_fact_fingerprint FROM current_pointer WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1",
                [&state_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
            )
            .optional()?;
        match pointer {
            Some((revision, fact_ref, fingerprint)) => {
                if as_u64(revision)? != head_revision
                    || fact_ref
                        != format!("fact:MMR_STATE_CORE:{state_id}:{head_revision}")
                    || previous_fingerprint.as_deref() != Some(fingerprint.as_str())
                {
                    return Err(LocalOwnerError::MmrTransitionHistoryBroken);
                }
            }
            None => return Err(LocalOwnerError::MmrTransitionHistoryBroken),
        }
    }
    Ok(())
}

fn read_kind_current(
    connection: &Connection,
    fact_kind: &str,
    state_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    if fact_kind == MMR_STATE_FACT_KIND {
        verify_mmr_current_pointer_integrity(connection)?;
    } else {
        verify_commitment_pointer_integrity(connection)?;
    }
    let row: Option<(i64, String, String, Vec<u8>, String, Option<String>, i64)> = connection
        .query_row(
            "SELECT f.fact_revision,f.fact_ref,f.subject_ref,f.canonical_bytes,f.fact_fingerprint,f.predecessor_fact_fingerprint,p.pointer_version FROM current_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.fact_kind=?1 AND p.logical_id=?2",
            params![fact_kind, state_id],
            |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?,row.get(3)?,row.get(4)?,row.get(5)?,row.get(6)?)),
        )
        .optional()?;
    let Some((revision, fact_ref, subject_ref, bytes, fingerprint, predecessor, pointer_version)) = row else {
        return Ok(None);
    };
    let revision = as_u64(revision)?;
    if pointer_version != as_i64(revision)? {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let value = decode_kind_fact(
        fact_kind,
        state_id,
        revision,
        &bytes,
        &fingerprint,
        predecessor.as_deref(),
    )?;
    if value["stateId"] != state_id
        || value["components"]["provenance"]["subject"]["ref"] != subject_ref
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    if fact_ref != format!("fact:{fact_kind}:{state_id}:{revision}") {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(Some(json!({
        "factFingerprint": fingerprint,
        "factRef": fact_ref,
        "predecessorFactFingerprint": predecessor,
        "revision": revision,
        "state": value,
    })))
}

fn read_mmr_current(
    connection: &Connection,
    state_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    read_kind_current(connection, MMR_STATE_FACT_KIND, state_id)
}

fn read_commitment_current(
    connection: &Connection,
    commitment_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    read_kind_current(connection, COMMITMENT_FACT_KIND, commitment_id)
}

fn read_mmr_history(
    connection: &Connection,
    state_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT fact_revision,fact_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 ORDER BY fact_revision",
    )?;
    let rows = statement.query_map([state_id], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Vec<u8>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, Option<String>>(4)?,
        ))
    })?;
    let mut history = Vec::new();
    for row in rows {
        let (revision, fact_ref, bytes, fingerprint, predecessor) = row?;
        let revision = as_u64(revision)?;
        let value = decode_mmr_fact(
            state_id,
            revision,
            &bytes,
            &fingerprint,
            predecessor.as_deref(),
        )?;
        if fact_ref != format!("fact:MMR_STATE_CORE:{state_id}:{revision}") {
            return Err(LocalOwnerError::StateCorrupt);
        }
        history.push(json!({
            "factFingerprint": fingerprint,
            "factRef": fact_ref,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "state": value,
        }));
    }
    Ok(history)
}

fn mmr_plane_identity(value: &Value) -> Result<Value, LocalOwnerError> {
    let plane = value["components"]["plane"]
        .as_object()
        .ok_or(LocalOwnerError::MmrInterpretationPlaneConflict)?;
    Ok(json!({
        "claimScope": plane.get("claimScope"),
        "interpretationOwnerRef": plane.get("interpretationOwnerRef"),
        "objectKind": plane.get("objectKind"),
        "sharedEventStateId": plane.get("sharedEventStateId"),
        "subjectRef": value["components"]["provenance"]["subject"]["ref"],
    }))
}

fn validate_mmr_plane_transition(
    connection: &Connection,
    mutation: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let mutation_type = require_string(mutation, "mutationType", 32)?;
    let target_state_id = require_nonempty_string(mutation, "targetStateId", 200)?;
    let components = mutation["components"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let plane = components["plane"]
        .as_object()
        .ok_or(LocalOwnerError::MmrSourceScopeEscalation)?;
    let object_kind = require_nonempty_string(plane, "objectKind", 64)
        .map_err(|_| LocalOwnerError::MmrSourceScopeEscalation)?;

    if object_kind == "SUBJECT_INTERPRETATION" {
        let shared_event_state_id = optional_plane_string(plane, "sharedEventStateId")?
            .ok_or(LocalOwnerError::MmrInterpretationPlaneConflict)?;
        let Some(event) = read_mmr_current(connection, shared_event_state_id)? else {
            return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
        };
        if event["state"]["components"]["plane"]["objectKind"] != "SHARED_EVENT" {
            return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
        }
    }

    if object_kind == "DERIVED_STATE" {
        // A derived state must be bound to an existing non-derived canonical source
        // state. Derivation never grants a source's stronger status.
        let source_state_id = optional_plane_string(plane, "sharedEventStateId")?
            .ok_or(LocalOwnerError::MmrDerivedStateSourceConflict)?;
        let Some(source) = read_mmr_current(connection, source_state_id)? else {
            return Err(LocalOwnerError::MmrDerivedStateSourceConflict);
        };
        if source["state"]["components"]["plane"]["objectKind"] == "DERIVED_STATE" {
            return Err(LocalOwnerError::MmrDerivedStateSourceConflict);
        }
    }

    if object_kind == "SUMMARY_STATE" {
        // B6: a Summary must be bound to an admitted independent evidence fact.
        // It can never cite itself (no circular evidence acceptance) and it can
        // never use another Summary or a Candidate as its supporting evidence.
        let support_ref = optional_plane_string(plane, "sharedEventStateId")?
            .ok_or(LocalOwnerError::MmrSummarySelfEvidenceRejected)?;
        if support_ref == target_state_id {
            return Err(LocalOwnerError::MmrSummarySelfEvidenceRejected);
        }
        let Some(evidence) = read_evidence_current(connection, support_ref)? else {
            return Err(LocalOwnerError::MmrSummarySupportUnresolved);
        };
        if evidence["state"]["components"]["plane"]["objectKind"] != "EVIDENCE_STATE" {
            return Err(LocalOwnerError::MmrSummarySelfEvidenceRejected);
        }
    }

    if matches!(
        mutation_type,
        "REVISE" | "SUPERSEDE" | "RETIRE" | "ADD_EVIDENCE" | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT"
    ) {
        let current = read_kind_current(
            connection,
            mutation_fact_kind(connection, mutation_type, target_state_id)?,
            target_state_id,
        )?
        .ok_or(LocalOwnerError::MmrCurrentConflict)?;
        let current_state = &current["state"];
        if current_state["components"]["plane"]["objectKind"] == "DERIVED_STATE" {
            let candidate_plane = components["plane"]
                .as_object()
                .ok_or(LocalOwnerError::MmrDerivedStateSourceConflict)?;
            let current_plane = current_state["components"]["plane"]
                .as_object()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            if candidate_plane.get("objectKind").and_then(Value::as_str)
                != Some("DERIVED_STATE")
                || candidate_plane.get("claimScope").and_then(Value::as_str)
                    != Some("DERIVED_STATE")
                || candidate_plane.get("controllerRole").and_then(Value::as_str)
                    != Some("DERIVED_NON_CONTROLLER")
                || candidate_plane.get("sharedEventStateId")
                    != current_plane.get("sharedEventStateId")
            {
                return Err(LocalOwnerError::MmrDerivedStateSourceConflict);
            }
        }
        let protocol = current_state["protocol"]
            .as_str()
            .ok_or(LocalOwnerError::StateCorrupt)?;
        if protocol == "MMR0_EXPLICIT_MUTATION_CORE_V2" {
            if object_kind != "SCOPED_CLAIM"
                || plane["claimScope"] != "MMR_STATE_CORE"
                || current_state["components"]["provenance"]["subject"]["ref"]
                    != components["provenance"]["subject"]["ref"]
            {
                return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
            }
        } else {
            let candidate = json!({"components": components});
            if mmr_plane_identity(current_state)? != mmr_plane_identity(&candidate)? {
                return Err(LocalOwnerError::MmrInterpretationPlaneConflict);
            }
        }
    }
    Ok(())
}

/// Enforces derived-state non-inheritance: a derived state cannot change status
/// without a separate admitted status transition, and the admitted status
/// transition lifecycle is reserved for derived states.
fn enforce_mmr_derived_transition(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
    mutation_type: &str,
    target_state_id: &str,
) -> Result<(), LocalOwnerError> {
    let Some(current) = read_kind_current(
        connection,
        mutation_fact_kind(connection, mutation_type, target_state_id)?,
        target_state_id,
    )?
    else {
        return Ok(());
    };
    let derived = current["state"]["components"]["plane"]["objectKind"].as_str()
        == Some("DERIVED_STATE");
    let lifecycle_state = mutation_object["components"]["lifecycle"]["lifecycleState"].as_str();
    if derived {
        match mutation_type {
            "REVISE" if lifecycle_state == Some("P2_D_ADMITTED_STATUS_TRANSITION") => Ok(()),
            _ => Err(LocalOwnerError::MmrDerivedStateStatusChangeRejected),
        }
    } else if mutation_type == "REVISE"
        && lifecycle_state == Some("P2_D_ADMITTED_STATUS_TRANSITION")
    {
        Err(LocalOwnerError::MmrDerivedStateStatusChangeRejected)
    } else {
        Ok(())
    }
}

/// Enforces the explicit commitment lifecycle: a commitment begins ACTIVE and
/// may only reach FULFILLED or RELEASED through an explicit committed
/// transition.  Ended commitments are terminal; recall/projection visibility
/// never changes lifecycle truth.
fn validate_mmr_commitment_transition(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let mutation_type = require_string(mutation_object, "mutationType", 32)?;
    let commitment_id = require_nonempty_string(mutation_object, "targetStateId", 200)?;
    if mutation_type == "CREATE_COMMITMENT" {
        return Ok(());
    }
    let current = read_commitment_current(connection, commitment_id)?
        .ok_or(LocalOwnerError::MmrCommitmentTransitionRejected)?;
    let current_lifecycle = current["state"]["components"]["lifecycle"]["lifecycleState"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    if current_lifecycle != COMMITMENT_LIFECYCLE_ACTIVE {
        return Err(LocalOwnerError::MmrCommitmentTransitionRejected);
    }
    let requested = mutation_object["components"]["lifecycle"]["lifecycleState"].as_str();
    match mutation_type {
        "FULFILL_COMMITMENT" if requested == Some(COMMITMENT_LIFECYCLE_FULFILLED) => Ok(()),
        "RELEASE_COMMITMENT" if requested == Some(COMMITMENT_LIFECYCLE_RELEASED) => Ok(()),
        _ => Err(LocalOwnerError::MmrCommitmentTransitionRejected),
    }
}

fn validate_stored_mmr_commitment_state(value: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        value,
        &[
            "components",
            "localAuthorization",
            "localOutcome",
            "mutationType",
            "operationFingerprint",
            "operationId",
            "protocol",
            "revision",
            "stateId",
        ],
    )?;
    if require_string(object, "protocol", 64)? != COMMITMENT_PROTOCOL {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let mutation_type = require_string(object, "mutationType", 32)?;
    if !["CREATE_COMMITMENT", "FULFILL_COMMITMENT", "RELEASE_COMMITMENT"]
        .contains(&mutation_type)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let revision = require_u64(object, "revision")?;
    if (mutation_type == "CREATE_COMMITMENT" && revision != 1)
        || (mutation_type != "CREATE_COMMITMENT" && revision <= 1)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    require_nonempty_string(object, "operationId", 200)?;
    require_nonempty_string(object, "stateId", 200)?;
    let operation_fingerprint = require_string(object, "operationFingerprint", 64)?;
    if operation_fingerprint.len() != 64
        || !operation_fingerprint.bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let authorization = require_exact_object(
        &object["localAuthorization"],
        &[
            "authorityBasisRef",
            "consentCommitment",
            "grantId",
            "mutationActorRef",
            "right",
            "scope",
        ],
    )?;
    let commitment = require_string(authorization, "consentCommitment", 64)?;
    if commitment.len() != 64
        || !commitment.bytes().all(|byte| byte.is_ascii_hexdigit())
        || require_string(authorization, "scope", 64)? != "P2_E_COMMITMENT_LIFECYCLE_AUTHORITY"
        || require_string(authorization, "right", 64)? != "MMR_DURABLE_STATE_MUTATION"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let components = object["components"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let authority = components["authority"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let grant = authority["grant"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let provenance = components["provenance"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let actor = provenance["mutationActor"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    if authorization["authorityBasisRef"] != authority["authorityBasisRef"]
        || authorization["grantId"] != grant["grantId"]
        || authorization["mutationActorRef"] != actor["ref"]
    {
        return Err(LocalOwnerError::MmrAuthorityScopeDenied);
    }
    let outcome = require_exact_object(
        &object["localOutcome"],
        &["mmrCommittedGuaranteeProven", "resultCode"],
    )?;
    if outcome["mmrCommittedGuaranteeProven"] != Value::Bool(false)
        || require_string(outcome, "resultCode", 64)?
            != "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let predecessor = &object["components"]["transition"]["predecessorStateFingerprint"];
    let synthetic_mutation = json!({
        "components": object["components"],
        "expectedCurrentFingerprint": predecessor,
        "mutationType": mutation_type,
        "operationId": object["operationId"],
        "targetStateId": object["stateId"],
    });
    validate_mmr_core_mutation(&synthetic_mutation, true)
        .map(|_| ())
        .map_err(|_| LocalOwnerError::StateCorrupt)
}

fn decode_mmr_commitment_fact(
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    let value: Value = serde_json::from_slice(bytes).map_err(|_| LocalOwnerError::StateCorrupt)?;
    validate_stored_mmr_commitment_state(&value)?;
    if value["stateId"] != state_id || value["revision"] != revision {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let transition_predecessor = value["components"]["transition"]
        ["predecessorStateFingerprint"]
        .as_str();
    if transition_predecessor != predecessor {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let material = canonical_value_bytes(&json!({
        "factKind": COMMITMENT_FACT_KIND,
        "logicalId": state_id,
        "predecessorFactFingerprint": predecessor,
        "revision": revision,
        "value": value,
    }))?;
    let expected = domain_fingerprint(
        &format!("agents-os.local-owner.fact.{COMMITMENT_FACT_KIND}.v1"),
        &material,
    );
    if expected != fingerprint {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(value)
}

fn decode_kind_fact(
    fact_kind: &str,
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    match fact_kind {
        COMMITMENT_FACT_KIND => {
            decode_mmr_commitment_fact(state_id, revision, bytes, fingerprint, predecessor)
        }
        EVIDENCE_FACT_KIND => {
            decode_mmr_evidence_fact(state_id, revision, bytes, fingerprint, predecessor)
        }
        CANDIDATE_FACT_KIND => {
            decode_mmr_candidate_fact(state_id, revision, bytes, fingerprint, predecessor)
        }
        SUMMARY_FACT_KIND => {
            decode_mmr_summary_fact(state_id, revision, bytes, fingerprint, predecessor)
        }
        _ => decode_mmr_fact(state_id, revision, bytes, fingerprint, predecessor),
    }
}


/// Request-level validator for CREATE_EVIDENCE: the evidence artifact carries an
/// opaque identity, an origin ref, the derivation graph, and artifact
/// availability.  Independence is never derived from names, labels, paths, or
/// text similarity.
fn validate_mmr_evidence_identity(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let _ = connection;
    let _target = require_nonempty_string(mutation_object, "targetStateId", 200)?;
    let content = mutation_object["components"]["content"]["value"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_map_keys(
        content,
        &[
            "artifactAvailability",
            "derivationAncestors",
            "description",
            "originRef",
        ],
    )?;
    require_nonempty_string(content, "description", 4000)?;
    let origin_ref = require_nonempty_string(content, "originRef", 300)?;
    if !origin_ref.starts_with("origin:") {
        return Err(LocalOwnerError::InvalidInput);
    }
    let ancestors = content["derivationAncestors"]
        .as_array()
        .ok_or(LocalOwnerError::InvalidInput)?;
    for ancestor in ancestors {
        let value = ancestor.as_str().ok_or(LocalOwnerError::InvalidInput)?;
        if value.is_empty() || value.len() > 300 {
            return Err(LocalOwnerError::InvalidInput);
        }
    }
    let availability = require_string(content, "artifactAvailability", 16)?;
    if !matches!(
        availability,
        EVIDENCE_AVAILABILITY_AVAILABLE | EVIDENCE_AVAILABILITY_UNAVAILABLE
    ) {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

/// Request-level validator for CREATE_CANDIDATE: status is exactly CANDIDATE;
/// an optional motivating evidence ref must resolve to an admitted evidence
/// fact and never to the Candidate itself.
fn validate_mmr_candidate_creation(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let target = require_nonempty_string(mutation_object, "targetStateId", 200)?;
    let content = mutation_object["components"]["content"]["value"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_map_keys(content, &["description", "motivatingEvidenceRef"])?;
    require_nonempty_string(content, "description", 4000)?;
    if let Some(motivating) = content["motivatingEvidenceRef"].as_str() {
        if motivating == target {
            return Err(LocalOwnerError::MmrCandidateSelfValidationRejected);
        }
        let evidence = read_evidence_current(connection, motivating)?
            .ok_or(LocalOwnerError::MmrEvidenceNotIndependent)?;
        if evidence["state"]["components"]["plane"]["objectKind"] != "EVIDENCE_STATE" {
            return Err(LocalOwnerError::MmrEvidenceNotIndependent);
        }
    }
    Ok(())
}

/// Request-level validator for CREATE_SUMMARY: the supporting evidence
/// reference lives in the SUMMARY_STATE plane and must not be the Summary
/// itself (the plane transition check resolves the evidence fact).
fn validate_mmr_summary_creation(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let _ = connection;
    let target = require_nonempty_string(mutation_object, "targetStateId", 200)?;
    let content = mutation_object["components"]["content"]["value"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_map_keys(content, &["description"])?;
    require_nonempty_string(content, "description", 4000)?;
    let plane = mutation_object["components"]["plane"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let support_ref = optional_plane_string(plane, "sharedEventStateId")?
        .ok_or(LocalOwnerError::MmrSummarySelfEvidenceRejected)?;
    if support_ref == target {
        return Err(LocalOwnerError::MmrSummarySelfEvidenceRejected);
    }
    Ok(())
}

fn read_evidence_current(
    connection: &Connection,
    evidence_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    read_kind_current(connection, EVIDENCE_FACT_KIND, evidence_id)
}

fn read_candidate_current(
    connection: &Connection,
    candidate_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    read_kind_current(connection, CANDIDATE_FACT_KIND, candidate_id)
}

fn read_summary_current(
    connection: &Connection,
    summary_id: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    read_kind_current(connection, SUMMARY_FACT_KIND, summary_id)
}

/// Immutable logical formation time (the created event sequence) of a fact.
/// This is the only time authority for the future-evidence condition; payload
/// timestamps, labels, and counters are never authoritative.
fn kind_formed_event_sequence(
    connection: &Connection,
    fact_kind: &str,
    state_id: &str,
) -> Result<Option<u64>, LocalOwnerError> {
    connection
        .query_row(
            "SELECT f.created_event_sequence FROM current_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.fact_kind=?1 AND p.logical_id=?2",
            params![fact_kind, state_id],
            |row| row.get::<_, i64>(0),
        )
        .optional()?
        .map(|value| Ok(as_u64(value)?))
        .transpose()
}

/// The set of origin identities reachable from an evidence fact through its
/// origin/derivation graph.  This is the only authority used for independence.
fn evidence_origin_chain(value: &Value) -> BTreeSet<String> {
    let mut set = BTreeSet::new();
    if let Some(origin) = value["evidenceIdentity"]["originRef"].as_str() {
        set.insert(origin.to_owned());
    }
    if let Some(ancestors) = value["evidenceIdentity"]["derivationAncestors"].as_array() {
        for ancestor in ancestors {
            if let Some(ancestor) = ancestor.as_str() {
                set.insert(ancestor.to_owned());
            }
        }
    }
    set
}

/// Candidate evidence transition guard: the submitted evidence must be a truly
/// distinct later artifact whose origin/derivation graph does not intersect the
/// Candidate's own origin or its motivating evidence chain.
fn validate_candidate_evidence_independence(
    connection: &Connection,
    candidate: &Value,
    evidence: &Value,
) -> Result<(), LocalOwnerError> {
    let candidate_state = candidate["candidateState"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let candidate_id = candidate["stateId"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let candidate_origin = candidate_state
        .get("originRef")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let evidence_id = evidence["stateId"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;

    // A Candidate can never cite itself as supporting evidence.
    if evidence_id == candidate_id {
        return Err(LocalOwnerError::MmrCandidateSelfValidationRejected);
    }
    let e2_chain = evidence_origin_chain(evidence);
    // Creation reflection / any artifact derived from the Candidate itself.
    if e2_chain.contains(candidate_origin) {
        return Err(LocalOwnerError::MmrCandidateSelfValidationRejected);
    }

    // Independence is judged against the Candidate's motivating evidence chain
    // (the failure event E1).  Any shared origin/derivation identity means the
    // submitted artifact is a copy, summary, rename, relabel, or same-source
    // chain artifact — never independent evidence.
    let mut candidate_chain = BTreeSet::new();
    if let Some(motivating_ref) = candidate_state
        .get("motivatingEvidenceRef")
        .and_then(Value::as_str)
    {
        if let Some(e1) = read_evidence_current(connection, motivating_ref)? {
            candidate_chain = evidence_origin_chain(&e1["state"]);
        }
    }
    if !candidate_chain.is_empty() && e2_chain.intersection(&candidate_chain).next().is_some() {
        return Err(LocalOwnerError::MmrEvidenceNotIndependent);
    }
    Ok(())
}

/// Validates an explicit ADD_EVIDENCE transition against a Candidate target:
/// evidence admission, independence from the origin/derivation graph, the
/// future-evidence condition, and the allowed Candidate outcome vocabulary.
fn validate_mmr_candidate_evidence_transition(
    connection: &Connection,
    mutation_object: &Map<String, Value>,
) -> Result<(), LocalOwnerError> {
    let candidate_id = require_nonempty_string(mutation_object, "targetStateId", 200)?;
    let content = mutation_object["components"]["content"]["value"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let evidence_ref = require_nonempty_string(content, "supportingEvidenceRef", 200)?;
    if evidence_ref == candidate_id {
        return Err(LocalOwnerError::MmrCandidateSelfValidationRejected);
    }
    let lifecycle = mutation_object["components"]["lifecycle"]["lifecycleState"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    if ![
        CANDIDATE_OUTCOME_EVIDENCE_BACKED,
        CANDIDATE_OUTCOME_REVISED,
        CANDIDATE_OUTCOME_REJECTED,
        CANDIDATE_STATUS_CANDIDATE,
    ]
    .contains(&lifecycle)
    {
        return Err(LocalOwnerError::MmrCandidateStatusChangeRejected);
    }
    let current = read_candidate_current(connection, candidate_id)?
        .ok_or(LocalOwnerError::MmrCurrentConflict)?;
    let candidate = &current["state"];
    let evidence = read_evidence_current(connection, evidence_ref)?
        .ok_or(LocalOwnerError::MmrEvidenceNotIndependent)?;
    let evidence = &evidence["state"];
    if evidence["components"]["plane"]["objectKind"] != "EVIDENCE_STATE" {
        return Err(LocalOwnerError::MmrEvidenceNotIndependent);
    }
    validate_candidate_evidence_independence(connection, candidate, evidence)?;
    let e2_formed = kind_formed_event_sequence(connection, EVIDENCE_FACT_KIND, evidence_ref)?;
    let c1_formed = kind_formed_event_sequence(connection, CANDIDATE_FACT_KIND, candidate_id)?;
    match (e2_formed, c1_formed) {
        (Some(e2), Some(c1)) if e2 > c1 => Ok(()),
        _ => Err(LocalOwnerError::MmrFutureEvidenceConditionFailed),
    }
}

/// Common atomic-bundle validation for P2-F stored facts (authorization,
/// outcome, canonical fingerprint fields, and synthetic mutation revalidation).
fn validate_stored_mmr_fact_common(
    object: &Map<String, Value>,
    protocol: &str,
    mutation_types: &[&str],
    revision_ok: fn(u64) -> bool,
) -> Result<(), LocalOwnerError> {
    if require_string(object, "protocol", 64)? != protocol {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let mutation_type = require_string(object, "mutationType", 32)?;
    if !mutation_types.contains(&mutation_type) || !revision_ok(require_u64(object, "revision")?) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    require_nonempty_string(object, "operationId", 200)?;
    require_nonempty_string(object, "stateId", 200)?;
    let operation_fingerprint = require_string(object, "operationFingerprint", 64)?;
    if operation_fingerprint.len() != 64
        || !operation_fingerprint.bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let authorization = require_exact_object(
        &object["localAuthorization"],
        &[
            "authorityBasisRef",
            "consentCommitment",
            "grantId",
            "mutationActorRef",
            "right",
            "scope",
        ],
    )?;
    let commitment = require_string(authorization, "consentCommitment", 64)?;
    if commitment.len() != 64
        || !commitment.bytes().all(|byte| byte.is_ascii_hexdigit())
        || require_string(authorization, "right", 64)? != "MMR_DURABLE_STATE_MUTATION"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let components = object["components"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let authority = components["authority"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let grant = authority["grant"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let provenance = components["provenance"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let actor = provenance["mutationActor"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    if authorization["authorityBasisRef"] != authority["authorityBasisRef"]
        || authorization["grantId"] != grant["grantId"]
        || authorization["mutationActorRef"] != actor["ref"]
    {
        return Err(LocalOwnerError::MmrAuthorityScopeDenied);
    }
    let outcome = require_exact_object(
        &object["localOutcome"],
        &["mmrCommittedGuaranteeProven", "resultCode"],
    )?;
    if outcome["mmrCommittedGuaranteeProven"] != Value::Bool(false)
        || require_string(outcome, "resultCode", 64)? != "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let predecessor = &object["components"]["transition"]["predecessorStateFingerprint"];
    let synthetic_mutation = json!({
        "components": object["components"],
        "expectedCurrentFingerprint": predecessor,
        "mutationType": mutation_type,
        "operationId": object["operationId"],
        "targetStateId": object["stateId"],
    });
    validate_mmr_core_mutation(&synthetic_mutation, true)
        .map(|_| ())
        .map_err(|_| LocalOwnerError::StateCorrupt)
}

fn validate_stored_mmr_evidence_state(value: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        value,
        &[
            "components",
            "evidenceIdentity",
            "localAuthorization",
            "localOutcome",
            "mutationType",
            "operationFingerprint",
            "operationId",
            "protocol",
            "revision",
            "stateId",
        ],
    )?;
    validate_stored_mmr_fact_common(object, EVIDENCE_PROTOCOL, &["CREATE_EVIDENCE"], |revision| {
        revision == 1
    })?;
    let identity = require_exact_object(
        &object["evidenceIdentity"],
        &[
            "artifactAvailability",
            "derivationAncestors",
            "evidenceId",
            "originRef",
        ],
    )?;
    if identity["evidenceId"] != object["stateId"] {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let origin_ref = require_string(identity, "originRef", 300)?;
    if !origin_ref.starts_with("origin:") {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let availability = require_string(identity, "artifactAvailability", 16)?;
    if !matches!(
        availability,
        EVIDENCE_AVAILABILITY_AVAILABLE | EVIDENCE_AVAILABILITY_UNAVAILABLE
    ) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let ancestors = identity["derivationAncestors"]
        .as_array()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    for ancestor in ancestors {
        let value = ancestor.as_str().ok_or(LocalOwnerError::StateCorrupt)?;
        if value.is_empty() || value.len() > 300 {
            return Err(LocalOwnerError::StateCorrupt);
        }
    }
    Ok(())
}

fn validate_stored_mmr_candidate_state(value: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        value,
        &[
            "candidateState",
            "components",
            "localAuthorization",
            "localOutcome",
            "mutationType",
            "operationFingerprint",
            "operationId",
            "protocol",
            "revision",
            "stateId",
        ],
    )?;
    validate_stored_mmr_fact_common(
        object,
        CANDIDATE_PROTOCOL,
        &["CREATE_CANDIDATE", "ADD_EVIDENCE"],
        |revision| revision >= 1,
    )?;
    let candidate = require_exact_object(
        &object["candidateState"],
        &[
            "candidateId",
            "motivatingEvidenceRef",
            "originRef",
            "status",
            "supportingEvidenceFingerprint",
            "supportingEvidenceRef",
        ],
    )?;
    if candidate["candidateId"] != object["stateId"] {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let status = require_string(candidate, "status", 32)?;
    let mutation_type = require_string(object, "mutationType", 32)?;
    let revision = require_u64(object, "revision")?;
    if mutation_type == "CREATE_CANDIDATE" {
        if revision != 1
            || status != CANDIDATE_STATUS_CANDIDATE
            || !candidate["supportingEvidenceRef"].is_null()
            || !candidate["supportingEvidenceFingerprint"].is_null()
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
    } else {
        if revision <= 1
            || !matches!(
                status,
                CANDIDATE_OUTCOME_EVIDENCE_BACKED
                    | CANDIDATE_OUTCOME_REVISED
                    | CANDIDATE_OUTCOME_REJECTED
                    | CANDIDATE_STATUS_CANDIDATE
            )
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        let support_ref = require_nonempty_string(candidate, "supportingEvidenceRef", 200)?;
        let support_fp = require_nonempty_string(candidate, "supportingEvidenceFingerprint", 64)?;
        if support_ref == object["stateId"]
            || support_fp.len() != 64
            || !support_fp.bytes().all(|byte| byte.is_ascii_hexdigit())
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
    }
    let origin_ref = require_string(candidate, "originRef", 300)?;
    if !origin_ref.starts_with("origin:") {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let _ = require_nonempty_string(candidate, "motivatingEvidenceRef", 200);
    Ok(())
}

fn validate_stored_mmr_summary_state(value: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        value,
        &[
            "components",
            "localAuthorization",
            "localOutcome",
            "mutationType",
            "operationFingerprint",
            "operationId",
            "protocol",
            "revision",
            "stateId",
            "summaryState",
        ],
    )?;
    validate_stored_mmr_fact_common(object, SUMMARY_PROTOCOL, &["CREATE_SUMMARY"], |revision| {
        revision == 1
    })?;
    let summary = require_exact_object(
        &object["summaryState"],
        &["status", "summaryId", "supportEvidenceRef"],
    )?;
    if summary["summaryId"] != object["stateId"]
        || require_string(summary, "status", 32)? != SUMMARY_LIFECYCLE_DERIVED
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let support_ref = require_nonempty_string(summary, "supportEvidenceRef", 200)?;
    if support_ref == object["stateId"] {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(())
}

fn decode_mmr_evidence_fact(
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    decode_kind_fact_for(
        EVIDENCE_FACT_KIND,
        EVIDENCE_PROTOCOL,
        state_id,
        revision,
        bytes,
        fingerprint,
        predecessor,
        |value| validate_stored_mmr_evidence_state(value),
    )
}

fn decode_mmr_candidate_fact(
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    decode_kind_fact_for(
        CANDIDATE_FACT_KIND,
        CANDIDATE_PROTOCOL,
        state_id,
        revision,
        bytes,
        fingerprint,
        predecessor,
        |value| validate_stored_mmr_candidate_state(value),
    )
}

fn decode_mmr_summary_fact(
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    decode_kind_fact_for(
        SUMMARY_FACT_KIND,
        SUMMARY_PROTOCOL,
        state_id,
        revision,
        bytes,
        fingerprint,
        predecessor,
        |value| validate_stored_mmr_summary_state(value),
    )
}

fn decode_kind_fact_for(
    fact_kind: &str,
    protocol: &str,
    state_id: &str,
    revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    predecessor: Option<&str>,
    validate: fn(&Value) -> Result<(), LocalOwnerError>,
) -> Result<Value, LocalOwnerError> {
    let value: Value = serde_json::from_slice(bytes).map_err(|_| LocalOwnerError::StateCorrupt)?;
    validate(&value)?;
    if value["stateId"] != state_id || value["revision"] != revision {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let transition_predecessor = value["components"]["transition"]["predecessorStateFingerprint"]
        .as_str();
    if transition_predecessor != predecessor {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let value_object = value.as_object().ok_or(LocalOwnerError::StateCorrupt)?;
    if require_string(value_object, "protocol", 64)? != protocol {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let material = canonical_value_bytes(&json!({
        "factKind": fact_kind,
        "logicalId": state_id,
        "predecessorFactFingerprint": predecessor,
        "revision": revision,
        "value": value,
    }))?;
    let expected = domain_fingerprint(
        &format!("agents-os.local-owner.fact.{fact_kind}.v1"),
        &material,
    );
    if expected != fingerprint {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(value)
}

/// Generic immutable history reader for a fact kind.
fn read_kind_history(
    connection: &Connection,
    fact_kind: &str,
    state_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT fact_revision,fact_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 ORDER BY fact_revision",
    )?;
    let rows = statement.query_map(params![fact_kind, state_id], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Vec<u8>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, Option<String>>(4)?,
        ))
    })?;
    let mut history = Vec::new();
    for row in rows {
        let (revision, fact_ref, bytes, fingerprint, predecessor) = row?;
        let revision = as_u64(revision)?;
        let value = decode_kind_fact(
            fact_kind,
            state_id,
            revision,
            &bytes,
            &fingerprint,
            predecessor.as_deref(),
        )?;
        if fact_ref != format!("fact:{fact_kind}:{state_id}:{revision}") {
            return Err(LocalOwnerError::StateCorrupt);
        }
        history.push(json!({
            "factFingerprint": fingerprint,
            "factRef": fact_ref,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "state": value,
        }));
    }
    Ok(history)
}

fn read_evidence_history(
    connection: &Connection,
    evidence_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    read_kind_history(connection, EVIDENCE_FACT_KIND, evidence_id)
}

fn read_candidate_history(
    connection: &Connection,
    candidate_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    read_kind_history(connection, CANDIDATE_FACT_KIND, candidate_id)
}

fn read_summary_history(
    connection: &Connection,
    summary_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    read_kind_history(connection, SUMMARY_FACT_KIND, summary_id)
}

/// B6 support resolution.  A Summary stays DERIVED; its support state is honest
/// degradation of the evidence lane:
///   SUPPORTED    - reference resolves to an available, traceable evidence fact
///   UNSUPPORTED  - reference resolves but the evidence artifact is unavailable
///   UNKNOWN      - reference is missing/hidden or does not resolve
/// The optional visible-references context models the effective projection:
/// a reference that is not visible cannot support a verifiable claim.
fn resolve_summary_support(
    connection: &Connection,
    summary_id: &str,
    visible_references: Option<&[String]>,
) -> Result<Value, LocalOwnerError> {
    let Some(current) = read_summary_current(connection, summary_id)? else {
        return Err(LocalOwnerError::NotFound);
    };
    let summary = &current["state"];
    let summary_state = summary["summaryState"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let support_ref = summary_state
        .get("supportEvidenceRef")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    if let Some(visible) = visible_references {
        if !visible.iter().any(|value| value == support_ref) {
            return Ok(json!({
                "resolvedEvidence": null,
                "resultCode": "MMR_SUMMARY_REFERENCE_NOT_VISIBLE",
                "summaryId": summary_id,
                "supportEvidenceRef": support_ref,
                "supportState": SUPPORT_STATE_UNKNOWN,
            }));
        }
    }
    let Some(evidence_current) = read_evidence_current(connection, support_ref)? else {
        return Ok(json!({
            "resolvedEvidence": null,
            "resultCode": "MMR_SUMMARY_EVIDENCE_UNRESOLVED",
            "summaryId": summary_id,
            "supportEvidenceRef": support_ref,
            "supportState": SUPPORT_STATE_UNKNOWN,
        }));
    };
    let evidence = &evidence_current["state"];
    let availability = evidence["evidenceIdentity"]["artifactAvailability"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    if availability != EVIDENCE_AVAILABILITY_AVAILABLE {
        return Ok(json!({
            "resolvedEvidence": evidence_current,
            "resultCode": "MMR_SUMMARY_EVIDENCE_UNAVAILABLE",
            "summaryId": summary_id,
            "supportEvidenceRef": support_ref,
            "supportState": SUPPORT_STATE_UNSUPPORTED,
        }));
    }
    Ok(json!({
        "resolvedEvidence": evidence_current,
        "resultCode": "MMR_SUMMARY_SUPPORT_RESOLVED",
        "summaryId": summary_id,
        "supportEvidenceRef": support_ref,
        "supportState": SUPPORT_STATE_SUPPORTED,
    }))
}

/// Full chain audit for a fact kind: contiguous revisions, recomputed
/// fingerprints, predecessor linkage, fact->event binding, and exactly one
/// Current at the chain head.

/// P2-G read-only persistence observability.  The harness inspects the durable
/// state set, Current view, transition history, and recovery-eligibility
/// surface to prove that never-admitted content is absent — without trusting
/// any runtime self-report ("nothing was persisted").
fn persistence_inspect(connection: &Connection) -> Result<Value, LocalOwnerError> {
    let mut fact_statement = connection.prepare(
        "SELECT fact_kind,logical_id,fact_revision,fact_ref,fact_fingerprint,canonical_bytes FROM canonical_fact ORDER BY fact_kind,logical_id,fact_revision",
    )?;
    let fact_rows = fact_statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, i64>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, Vec<u8>>(5)?,
        ))
    })?;
    let mut state_set = Vec::new();
    for row in fact_rows {
        let (fact_kind, state_id, revision, fact_ref, fact_fingerprint, canonical_bytes) = row?;
        state_set.push(json!({
            "contentDigest": sha256_hex(&canonical_bytes),
            "factFingerprint": fact_fingerprint,
            "factKind": fact_kind,
            "factRef": fact_ref,
            "revision": as_u64(revision)?,
            "stateId": state_id,
        }));
    }
    let mut pointer_statement = connection.prepare(
        "SELECT fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint FROM current_pointer ORDER BY fact_kind,logical_id",
    )?;
    let pointer_rows = pointer_statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, i64>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
        ))
    })?;
    let mut current_view = Vec::new();
    for row in pointer_rows {
        let (fact_kind, state_id, revision, fact_ref, fact_fingerprint) = row?;
        current_view.push(json!({
            "currentFactFingerprint": fact_fingerprint,
            "currentFactRef": fact_ref,
            "currentFactRevision": as_u64(revision)?,
            "factKind": fact_kind,
            "stateId": state_id,
        }));
    }
    let mut event_statement = connection.prepare(
        "SELECT event_sequence,event_kind,aggregate_ref,aggregate_revision,event_fingerprint,command_fingerprint FROM event ORDER BY event_sequence",
    )?;
    let event_rows = event_statement.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Option<String>>(2)?,
            row.get::<_, Option<i64>>(3)?,
            row.get::<_, Option<String>>(4)?,
            row.get::<_, Option<String>>(5)?,
        ))
    })?;
    let mut transitions = Vec::new();
    for row in event_rows {
        let (
            sequence,
            kind,
            aggregate_ref,
            aggregate_revision,
            fact_fingerprint,
            command_fingerprint,
        ) = row?;
        transitions.push(json!({
            "aggregateRef": aggregate_ref,
            "aggregateRevision": aggregate_revision,
            "commandFingerprint": command_fingerprint,
            "eventFingerprint": fact_fingerprint,
            "eventKind": kind,
            "eventSequence": as_u64(sequence)?,
        }));
    }
    let snapshot = continuity_snapshot_on(connection)?;
    let recovery_eligibility = json!({
        "authorityAnchors": snapshot
            .authority_anchors
            .iter()
            .map(|anchor| anchor.as_json())
            .collect::<Vec<_>>(),
        "current": snapshot.current.as_ref().map(|anchor| anchor.as_json()),
        "eventFingerprints": snapshot
            .event_fingerprints
            .iter()
            .map(|(sequence, fingerprint)| json!({"eventFingerprint": fingerprint, "eventSequence": sequence}))
            .collect::<Vec<_>>(),
    });
    Ok(json!({
        "currentView": current_view,
        "recoveryEligibility": recovery_eligibility,
        "stateSet": state_set,
        "transitionHistory": transitions,
    }))
}

/// P2-G read-only recall/projection surface.  A test-only plan changes
/// visibility, order, and rank of durable records (and lists retrieved
/// unadmitted content) and produces an effective cognitive projection with
/// ZERO writes: no transaction, no fact, no Current, no lifecycle, no
/// transition, no Memory outcome.
fn recall_projection(connection: &Connection, query: &Value) -> Result<Value, LocalOwnerError> {
    let query = query.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let plan = query
        .get("plan")
        .and_then(Value::as_object)
        .ok_or(LocalOwnerError::InvalidInput)?;
    let items = plan
        .get("items")
        .and_then(Value::as_array)
        .ok_or(LocalOwnerError::InvalidInput)?;
    let mut effective_projection = Vec::new();
    for item in items {
        let item = item.as_object().ok_or(LocalOwnerError::InvalidInput)?;
        let state_id = require_nonempty_string(item, "stateId", 200)?;
        let rank = require_u64(item, "rank")?;
        let visible = item.get("visible").and_then(Value::as_bool).unwrap_or(true);
        let resolved: Option<(String, String, i64, Vec<u8>)> = connection
            .query_row(
                "SELECT p.fact_kind,p.current_fact_fingerprint,p.current_fact_revision,f.canonical_bytes FROM current_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.logical_id=?1 ORDER BY p.fact_kind LIMIT 1",
                params![state_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )
            .optional()?;
        if let Some((fact_kind, fingerprint, revision, canonical_bytes)) = resolved {
            let value: Value =
                serde_json::from_slice(&canonical_bytes).map_err(|_| LocalOwnerError::StateCorrupt)?;
            let components = value
                .get("components")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let provenance = components
                .get("provenance")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let source = provenance
                .get("source")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let subject = provenance
                .get("subject")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let lifecycle = components
                .get("lifecycle")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let authority = components
                .get("authority")
                .and_then(Value::as_object)
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let source_ref = require_nonempty_string(source, "ref", 300)?;
            let source_type = require_nonempty_string(source, "type", 64)?;
            let subject_ref = require_nonempty_string(subject, "ref", 300)?;
            let epistemic_state = require_nonempty_string(lifecycle, "epistemicState", 64)?;
            let lifecycle_state = require_nonempty_string(lifecycle, "lifecycleState", 64)?;
            let authority_basis_ref =
                require_nonempty_string(authority, "authorityBasisRef", 300)?;
            let authority_basis_type =
                require_nonempty_string(authority, "authorityBasisType", 64)?;
            effective_projection.push(json!({
                "admitted": true,
                "authorityBasisRef": authority_basis_ref,
                "authorityBasisType": authority_basis_type,
                "epistemicState": epistemic_state,
                "factKind": fact_kind,
                "factFingerprint": fingerprint,
                "lifecycleState": lifecycle_state,
                "rank": rank,
                "revision": as_u64(revision)?,
                "sourceRef": source_ref,
                "sourceType": source_type,
                "stateId": state_id,
                "subjectRef": subject_ref,
                "visible": visible,
            }));
        } else {
            effective_projection.push(json!({
                "admitted": false,
                "rank": rank,
                "stateId": state_id,
                "visible": visible,
            }));
        }
    }
    let mut retrieved_unadmitted = Vec::new();
    if let Some(retrieved) = plan.get("retrieved").and_then(Value::as_array) {
        for entry in retrieved {
            let entry = entry.as_object().ok_or(LocalOwnerError::InvalidInput)?;
            let label = require_nonempty_string(entry, "label", 300)?;
            let content_digest = require_sha256_value(&entry["contentDigest"])?.to_owned();
            retrieved_unadmitted.push(json!({
                "admitted": false,
                "contentDigest": content_digest,
                "label": label,
            }));
        }
    }
    let transition_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM event", [], |row| row.get(0))?;
    Ok(json!({
        "durableTransitionCount": as_u64(transition_count)?,
        "effectiveProjection": effective_projection,
        "retrievedUnadmitted": retrieved_unadmitted,
    }))
}

/// P6-B bounded cognitive projection for a genuinely fresh Host session.
///
/// The caller supplies only a scenario, a transcript digest, a stable session
/// identity, and a bounded projection plan. The opaque action and its exact
/// source/status are read from canonical Current bytes here. A projection is
/// bound to the latest durable event generation; an old expected generation
/// is rejected before any content can be returned. This function is read-only
/// and intentionally does not select or call a provider/model.
fn cognitive_context_projection(
    connection: &Connection,
    query: &Value,
) -> Result<Value, LocalOwnerError> {
    let query = require_exact_object(
        query,
        &[
            "expectedProjectionGeneration",
            "freshSessionId",
            "projectionPlan",
            "responseContract",
            "scenario",
            "transcriptDigest",
        ],
    )?;
    let fresh_session_id = require_nonempty_string(query, "freshSessionId", 200)?;
    let response_contract = require_nonempty_string(query, "responseContract", 100)?;
    if response_contract != COGNITIVE_RESPONSE_CONTRACT
        && response_contract != COGNITIVE_NEGATIVE_RESPONSE_CONTRACT
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    let scenario = require_nonempty_string(query, "scenario", 512)?;
    let transcript_digest = require_sha256_value(
        query
            .get("transcriptDigest")
            .ok_or(LocalOwnerError::InvalidInput)?,
    )?;
    let projection_plan = query
        .get("projectionPlan")
        .ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_object(projection_plan, &["items", "retrieved"])?;

    let generation: i64 = connection.query_row(
        "SELECT COALESCE(MAX(event_sequence),0) FROM event",
        [],
        |row| row.get(0),
    )?;
    let generation = as_u64(generation)?;
    let expected_generation = match query.get("expectedProjectionGeneration") {
        Some(Value::Null) => None,
        Some(Value::Number(_)) => Some(require_u64(query, "expectedProjectionGeneration")?),
        _ => return Err(LocalOwnerError::InvalidInput),
    };
    if expected_generation.is_some_and(|expected| expected != generation) {
        return Ok(json!({
            "accepted": false,
            "currentProjectionGeneration": generation,
            "expectedProjectionGeneration": expected_generation,
            "freshSessionId": fresh_session_id,
            "resultCode": "STALE_PROJECTION_FAIL_CLOSED",
        }));
    }

    let projection = recall_projection(connection, &json!({"plan": projection_plan}))?;
    let projected_items = projection["effectiveProjection"]
        .as_array()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let mut effective_projection = Vec::new();
    let mut excluded_state_ids = Vec::new();
    for item in projected_items {
        if item["admitted"] != true || item["visible"] != true {
            if let Some(state_id) = item["stateId"].as_str() {
                excluded_state_ids.push(state_id.to_owned());
            }
            continue;
        }
        let state_id = item["stateId"]
            .as_str()
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let current = read_mmr_current(connection, state_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let content_value = current["state"]["components"]["content"]["value"]
            .as_str()
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let rule: Value = serde_json::from_str(content_value)
            .map_err(|_| LocalOwnerError::StateCorrupt)?;
        let rule = require_exact_object(&rule, &["actionToken", "scenario"])
            .map_err(|_| LocalOwnerError::StateCorrupt)?;
        let projected_scenario = require_nonempty_string(rule, "scenario", 512)
            .map_err(|_| LocalOwnerError::StateCorrupt)?;
        if projected_scenario != scenario {
            continue;
        }
        let action_token = require_nonempty_string(rule, "actionToken", 512)
            .map_err(|_| LocalOwnerError::StateCorrupt)?;
        effective_projection.push(json!({
            "actionToken": action_token,
            "admitted": true,
            "admittedStateIdentity": item["factFingerprint"],
            "authorityBasisRef": item["authorityBasisRef"],
            "authorityBasisType": item["authorityBasisType"],
            "epistemicState": item["epistemicState"],
            "lifecycleState": item["lifecycleState"],
            "revision": item["revision"],
            "scenario": projected_scenario,
            "sourceRef": item["sourceRef"],
            "sourceType": item["sourceType"],
            "stateId": state_id,
            "subjectRef": item["subjectRef"],
        }));
    }
    let expected_projection_count =
        usize::from(response_contract == COGNITIVE_RESPONSE_CONTRACT);
    if effective_projection.len() != expected_projection_count {
        return Ok(json!({
            "accepted": false,
            "freshSessionId": fresh_session_id,
            "projectionGeneration": generation,
            "resultCode": if response_contract == COGNITIVE_NEGATIVE_RESPONSE_CONTRACT {
                "NEGATIVE_RULE_APPEARED_IN_PROJECTION"
            } else {
                "CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE"
            },
        }));
    }

    let projection_value = json!({
        "effectiveProjection": effective_projection,
        "excludedStateIds": excluded_state_ids,
        "freshSessionId": fresh_session_id,
        "projectionGeneration": generation,
        "schema": COGNITIVE_PROJECTION_SCHEMA,
        "transcriptDigest": transcript_digest,
    });
    let projection_identity = format!(
        "sha256:{}",
        sha256_hex(&canonical_value_bytes(&projection_value)?)
    );
    Ok(json!({
        "accepted": true,
        "durableTransitionCount": projection["durableTransitionCount"],
        "freshSessionId": fresh_session_id,
        "projection": projection_value,
        "projectionGeneration": generation,
        "projectionIdentity": projection_identity,
        "resultCode": if response_contract == COGNITIVE_NEGATIVE_RESPONSE_CONTRACT {
            "MMR_COGNITIVE_PROJECTION_EMPTY_OK"
        } else {
            "MMR_COGNITIVE_PROJECTION_FRESH_OK"
        },
    }))
}

/// P2-H: defensively extracts the authority basis reference/type from a raw
/// mutation for outcome-journal records written before full semantic
/// validation (prepare-time denials and the indeterminate-window journal).
fn mutation_authority_basis(mutation: &Value) -> (Option<String>, Option<String>) {
    let authority = mutation
        .get("components")
        .and_then(|components| components.get("authority"))
        .and_then(Value::as_object);
    let basis_ref = authority
        .and_then(|value| value.get("authorityBasisRef"))
        .and_then(Value::as_str)
        .map(str::to_owned);
    let basis_type = authority
        .and_then(|value| value.get("authorityBasisType"))
        .and_then(Value::as_str)
        .map(str::to_owned);
    (basis_ref, basis_type)
}

fn verify_kind_chain_integrity(
    connection: &Connection,
    fact_kind: &str,
    event_kinds: &[&str],
) -> Result<(), LocalOwnerError> {
    let mut state_ids = BTreeSet::new();
    let mut id_statement = connection.prepare(
        "SELECT DISTINCT logical_id FROM canonical_fact WHERE fact_kind=?1 ORDER BY logical_id",
    )?;
    let id_rows = id_statement.query_map([fact_kind], |row| row.get::<_, String>(0))?;
    for id in id_rows {
        state_ids.insert(id?);
    }
    let mut pointer_ids = BTreeSet::new();
    let mut pointer_statement = connection.prepare(
        "SELECT logical_id FROM current_pointer WHERE fact_kind=?1 ORDER BY logical_id",
    )?;
    let pointer_rows = pointer_statement.query_map([fact_kind], |row| row.get::<_, String>(0))?;
    for id in pointer_rows {
        pointer_ids.insert(id?);
    }
    if state_ids != pointer_ids {
        return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
    }
    for state_id in state_ids {
        let mut chain = connection.prepare(
            "SELECT fact_revision,fact_ref,subject_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 ORDER BY fact_revision",
        )?;
        let rows = chain.query_map(params![fact_kind, &state_id], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Vec<u8>>(3)?,
                row.get::<_, String>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, i64>(6)?,
            ))
        })?;
        let mut expected_revision = 1_u64;
        let mut previous_fingerprint: Option<String> = None;
        for row in rows {
            let (revision, fact_ref, subject_ref, bytes, fingerprint, predecessor, event_sequence) =
                row?;
            let revision = as_u64(revision)?;
            if revision != expected_revision || predecessor != previous_fingerprint {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let value = decode_kind_fact(
                fact_kind,
                &state_id,
                revision,
                &bytes,
                &fingerprint,
                predecessor.as_deref(),
            )
            .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            let create_mutation = value["mutationType"].as_str();
            if fact_ref != format!("fact:{fact_kind}:{state_id}:{revision}")
                || value["stateId"] != state_id
                || value["components"]["provenance"]["subject"]["ref"] != subject_ref
                || (revision == 1)
                    != matches!(
                        create_mutation,
                        Some("CREATE_EVIDENCE" | "CREATE_CANDIDATE" | "CREATE_SUMMARY")
                    )
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let (event_kind, aggregate_revision, command_fingerprint, event_bytes): (
                String,
                i64,
                Option<String>,
                Vec<u8>,
            ) = connection.query_row(
                "SELECT event_kind,aggregate_revision,command_fingerprint,canonical_bytes FROM event WHERE event_sequence=?1",
                [event_sequence],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )?;
            let event_value: Value = serde_json::from_slice(&event_bytes)
                .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            if !event_kinds.contains(&event_kind.as_str())
                || as_u64(aggregate_revision)? != revision
                || command_fingerprint.as_deref() != value["operationFingerprint"].as_str()
                || event_value["aggregateRef"] != state_id
                || event_value["aggregateRevision"] != revision
                || event_value["factFingerprint"] != fingerprint
                || event_value["factRef"] != fact_ref
                || event_value["commandFingerprint"] != value["operationFingerprint"]
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            previous_fingerprint = Some(fingerprint);
            expected_revision += 1;
        }
        let head_revision = expected_revision - 1;
        let pointer: Option<(i64, String, String, i64)> = connection
            .query_row(
                "SELECT current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version FROM current_pointer WHERE fact_kind=?1 AND logical_id=?2",
                params![fact_kind, &state_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )
            .optional()?;
        match pointer {
            Some((revision, fact_ref, fingerprint, pointer_version)) => {
                if as_u64(revision)? != head_revision
                    || pointer_version != revision
                    || fact_ref != format!("fact:{fact_kind}:{state_id}:{head_revision}")
                    || previous_fingerprint.as_deref() != Some(fingerprint.as_str())
                {
                    return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
                }
            }
            None => return Err(LocalOwnerError::CurrentPointerIdentityMismatch),
        }
    }
    Ok(())
}

fn verify_p2f_kind_integrity(connection: &Connection) -> Result<(), LocalOwnerError> {
    verify_kind_chain_integrity(connection, EVIDENCE_FACT_KIND, &["MMR_EVIDENCE_CORE_CREATED"])?;
    verify_kind_chain_integrity(
        connection,
        CANDIDATE_FACT_KIND,
        &["MMR_CANDIDATE_CORE_CREATED", "MMR_CANDIDATE_CORE_EVIDENCE_ADDED"],
    )?;
    verify_kind_chain_integrity(connection, SUMMARY_FACT_KIND, &["MMR_SUMMARY_CORE_CREATED"])?;
    Ok(())
}


/// Verifies the identity relation used to publish commitment Current.  The
/// pointer's stored identity is not authority: the referenced fact is resolved
/// and its identity is recomputed from canonical bytes before it is trusted.
fn verify_commitment_pointer_integrity(connection: &Connection) -> Result<(), LocalOwnerError> {
    let mut commitment_ids = BTreeSet::new();
    let mut id_statement = connection.prepare(
        "SELECT DISTINCT logical_id FROM canonical_fact WHERE fact_kind=?1 ORDER BY logical_id",
    )?;
    let id_rows = id_statement.query_map([COMMITMENT_FACT_KIND], |row| row.get::<_, String>(0))?;
    for id in id_rows {
        commitment_ids.insert(id?);
    }
    let mut pointer_ids = BTreeSet::new();
    let mut pointer_statement = connection.prepare(
        "SELECT logical_id FROM current_pointer WHERE fact_kind=?1 ORDER BY logical_id",
    )?;
    let pointer_rows = pointer_statement.query_map([COMMITMENT_FACT_KIND], |row| {
        row.get::<_, String>(0)
    })?;
    for id in pointer_rows {
        pointer_ids.insert(id?);
    }
    if commitment_ids != pointer_ids {
        return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
    }
    for commitment_id in commitment_ids {
        let mut chain = connection.prepare(
            "SELECT fact_revision,fact_ref,subject_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 ORDER BY fact_revision",
        )?;
        let rows = chain.query_map(params![COMMITMENT_FACT_KIND, &commitment_id], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Vec<u8>>(3)?,
                row.get::<_, String>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, i64>(6)?,
            ))
        })?;
        let mut expected_revision = 1_u64;
        let mut previous_fingerprint: Option<String> = None;
        for row in rows {
            let (
                revision,
                fact_ref,
                subject_ref,
                bytes,
                fingerprint,
                predecessor,
                event_sequence,
            ) = row?;
            let revision = as_u64(revision)?;
            if revision != expected_revision || predecessor != previous_fingerprint {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let value = decode_mmr_commitment_fact(
                &commitment_id,
                revision,
                &bytes,
                &fingerprint,
                predecessor.as_deref(),
            )
            .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            if fact_ref != format!("fact:{COMMITMENT_FACT_KIND}:{commitment_id}:{revision}")
                || value["stateId"] != commitment_id
                || value["components"]["provenance"]["subject"]["ref"] != subject_ref
                || (revision == 1) != (value["mutationType"] == "CREATE_COMMITMENT")
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            let (event_kind, aggregate_revision, command_fingerprint, event_bytes): (
                String,
                i64,
                Option<String>,
                Vec<u8>,
            ) = connection.query_row(
                "SELECT event_kind,aggregate_revision,command_fingerprint,canonical_bytes FROM event WHERE event_sequence=?1",
                [event_sequence],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )?;
            let event_value: Value = serde_json::from_slice(&event_bytes)
                .map_err(|_| LocalOwnerError::MmrTransitionHistoryBroken)?;
            let bound_event = matches!(
                event_kind.as_str(),
                "MMR_COMMITMENT_CORE_CREATED"
                    | "MMR_COMMITMENT_CORE_FULFILLED"
                    | "MMR_COMMITMENT_CORE_RELEASED"
            );
            if !bound_event
                || as_u64(aggregate_revision)? != revision
                || command_fingerprint.as_deref() != value["operationFingerprint"].as_str()
                || event_value["aggregateRef"] != commitment_id
                || event_value["aggregateRevision"] != revision
                || event_value["factFingerprint"] != fingerprint
                || event_value["factRef"] != fact_ref
                || event_value["commandFingerprint"] != value["operationFingerprint"]
            {
                return Err(LocalOwnerError::MmrTransitionHistoryBroken);
            }
            previous_fingerprint = Some(fingerprint);
            expected_revision += 1;
        }
        let head_revision = expected_revision - 1;
        let pointer: Option<(i64, String, String, i64)> = connection
            .query_row(
                "SELECT current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version FROM current_pointer WHERE fact_kind=?1 AND logical_id=?2",
                params![COMMITMENT_FACT_KIND, &commitment_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )
            .optional()?;
        match pointer {
            Some((revision, fact_ref, fingerprint, pointer_version)) => {
                if as_u64(revision)? != head_revision
                    || pointer_version != revision
                    || fact_ref
                        != format!("fact:{COMMITMENT_FACT_KIND}:{commitment_id}:{head_revision}")
                    || previous_fingerprint.as_deref() != Some(fingerprint.as_str())
                {
                    return Err(LocalOwnerError::CurrentPointerIdentityMismatch);
                }
            }
            None => return Err(LocalOwnerError::CurrentPointerIdentityMismatch),
        }
    }
    Ok(())
}

fn read_commitment_history(
    connection: &Connection,
    commitment_id: &str,
) -> Result<Vec<Value>, LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT fact_revision,fact_ref,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 ORDER BY fact_revision",
    )?;
    let rows = statement.query_map(params![COMMITMENT_FACT_KIND, commitment_id], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Vec<u8>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, Option<String>>(4)?,
        ))
    })?;
    let mut history = Vec::new();
    for row in rows {
        let (revision, fact_ref, bytes, fingerprint, predecessor) = row?;
        let revision = as_u64(revision)?;
        let value = decode_mmr_commitment_fact(
            commitment_id,
            revision,
            &bytes,
            &fingerprint,
            predecessor.as_deref(),
        )?;
        if fact_ref != format!("fact:{COMMITMENT_FACT_KIND}:{commitment_id}:{revision}") {
            return Err(LocalOwnerError::StateCorrupt);
        }
        history.push(json!({
            "factFingerprint": fingerprint,
            "factRef": fact_ref,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "state": value,
        }));
    }
    Ok(history)
}

fn validate_observer_control_request(
    connection: &Connection,
    query: &Value,
) -> Result<Value, LocalOwnerError> {
    let query = require_exact_object(query, &["observerStateId", "requestedCapability"])?;
    let observer_state_id = require_nonempty_string(query, "observerStateId", 200)?;
    let capability = require_nonempty_string(query, "requestedCapability", 64)?;
    if ![
        "ALTER_IDENTITY",
        "ALTER_GOAL",
        "GRANT_PERMISSION",
        "MUTATION_AUTHORITY",
        "ALTER_COMMITMENT",
        "CONTROLLER_ROUTING",
    ]
    .contains(&capability)
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    let observer = read_mmr_current(connection, observer_state_id)?
        .ok_or(LocalOwnerError::NotFound)?;
    if observer["state"]["components"]["plane"]["objectKind"] != "DERIVED_OBSERVATION"
        || observer["state"]["components"]["plane"]["controllerRole"]
            != "DERIVED_NON_CONTROLLER"
    {
        return Err(LocalOwnerError::MmrObserverControllerPromotion);
    }
    Ok(json!({
        "accepted": false,
        "controllerChanged": false,
        "durableTransition": false,
        "observerStateId": observer_state_id,
        "requestedCapability": capability,
        "resultCode": "MMR_OBSERVER_TO_CONTROLLER_PROMOTION",
    }))
}

fn validate_cognitive_plane_binding(
    connection: &Connection,
    query: &Value,
) -> Result<Value, LocalOwnerError> {
    let query = require_exact_object(
        query,
        &[
            "authorityEpoch",
            "canonicalResidentId",
            "contentFingerprint",
            "epochFingerprint",
            "incarnationId",
            "memoryNamespace",
            "planeId",
            "presentationName",
        ],
    )?;
    let plane_id = require_nonempty_string(query, "planeId", 200)?;
    let resident_id = require_nonempty_string(query, "canonicalResidentId", 300)?;
    let incarnation_id = require_nonempty_string(query, "incarnationId", 300)?;
    let epoch_fingerprint = require_sha256_value(&query["epochFingerprint"])?;
    let authority_epoch = require_u64(query, "authorityEpoch")?;
    require_nonempty_string(query, "presentationName", 200)?;
    require_nonempty_string(query, "memoryNamespace", 300)?;
    require_sha256_value(&query["contentFingerprint"])?;
    let snapshot = continuity_snapshot_on(connection)?;
    let anchor = snapshot.current.ok_or(LocalOwnerError::StateCorrupt)?;
    let exact = resident_id == anchor.resident_id
        && incarnation_id == anchor.incarnation_id
        && authority_epoch == anchor.authority_epoch
        && epoch_fingerprint == anchor.epoch_fingerprint;
    Ok(if exact {
        json!({
            "accepted": true,
            "canonicalResidentId": resident_id,
            "identityBindingExact": true,
            "mergedContinuityCriticalState": false,
            "planeId": plane_id,
            "resultCode": "MMR_COGNITIVE_PLANE_BINDING_ELIGIBLE",
        })
    } else {
        json!({
            "accepted": false,
            "identityBindingExact": false,
            "mergedContinuityCriticalState": false,
            "planeId": plane_id,
            "resultCode": "MMR_IDENTITY_PLANE_MISMATCH",
        })
    })
}

fn mmr_operation_record(
    connection: &Connection,
    operation_id: &str,
) -> Result<Option<MmrOperationRecord>, LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT logical_id,fact_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' ORDER BY logical_id,fact_revision",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, Vec<u8>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, Option<String>>(4)?,
        ))
    })?;
    let mut found = None;
    for row in rows {
        let (state_id, revision, bytes, fact_fingerprint, predecessor) = row?;
        let revision = as_u64(revision)?;
        let value = decode_mmr_fact(
            &state_id,
            revision,
            &bytes,
            &fact_fingerprint,
            predecessor.as_deref(),
        )?;
        if value["operationId"] == operation_id {
            if found.is_some() {
                return Err(LocalOwnerError::StateCorrupt);
            }
            found = Some(MmrOperationRecord {
                operation_id: operation_id.to_owned(),
                operation_fingerprint: value["operationFingerprint"]
                    .as_str()
                    .ok_or(LocalOwnerError::StateCorrupt)?
                    .to_owned(),
                state_id,
                fact_fingerprint,
                predecessor_fact_fingerprint: predecessor,
                revision,
            });
        }
    }
    Ok(found)
}

#[derive(Clone, Debug)]
struct MmrOperationOutcomeRecord {
    operation_id: String,
    operation_fingerprint: String,
    state_id: String,
    authority_basis_ref: Option<String>,
    authority_basis_type: Option<String>,
    cutpoint_fact_fingerprint: Option<String>,
    operation_outcome: String,
    transition_fact_fingerprint: Option<String>,
}

impl MmrOperationOutcomeRecord {
    fn as_json(&self) -> Value {
        json!({
            "authorityBasisRef": self.authority_basis_ref,
            "authorityBasisType": self.authority_basis_type,
            "cutpointFactFingerprint": self.cutpoint_fact_fingerprint,
            "operationFingerprint": self.operation_fingerprint,
            "operationId": self.operation_id,
            "operationOutcome": self.operation_outcome,
            "targetStateId": self.state_id,
            "transitionFactFingerprint": self.transition_fact_fingerprint,
        })
    }
}

/// Looks up a committed MMR_STATE_CORE / MMR_COMMITMENT_CORE operation by
/// operation identity and derives its immutable COMMITTED outcome.
fn mmr_committed_operation_outcome(
    connection: &Connection,
    operation_id: &str,
) -> Result<Option<MmrOperationOutcomeRecord>, LocalOwnerError> {
    let row: Option<(String, String, i64, String, String, String, Option<String>)> = connection
        .query_row(
            "SELECT fact_kind,logical_id,fact_revision,json_extract(CAST(canonical_bytes AS TEXT),'$.operationFingerprint'),json_extract(CAST(canonical_bytes AS TEXT),'$.components.authority.authorityBasisRef'),json_extract(CAST(canonical_bytes AS TEXT),'$.components.authority.authorityBasisType'),predecessor_fact_fingerprint FROM canonical_fact WHERE json_extract(CAST(canonical_bytes AS TEXT),'$.operationId')=?1 AND fact_kind IN ('MMR_STATE_CORE','MMR_COMMITMENT_CORE','MMR_EVIDENCE_CORE','MMR_CANDIDATE_CORE','MMR_SUMMARY_CORE') ORDER BY fact_kind,fact_revision",
            [operation_id],
            |row| {
                Ok((
                    row.get(0)?,
                    row.get(1)?,
                    row.get(2)?,
                    row.get(3)?,
                    row.get(4)?,
                    row.get(5)?,
                    row.get(6)?,
                ))
            },
        )
        .optional()?;
    let Some((fact_kind, state_id, revision, operation_fingerprint, basis_ref, basis_type, predecessor)) = row else {
        return Ok(None);
    };
    let revision = as_u64(revision)?;
    let (bytes, fact_fingerprint): (Vec<u8>, String) = connection.query_row(
        "SELECT canonical_bytes,fact_fingerprint FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 AND fact_revision=?3",
        params![fact_kind, state_id, as_i64(revision)?],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    decode_kind_fact(
        &fact_kind,
        &state_id,
        revision,
        &bytes,
        &fact_fingerprint,
        predecessor.as_deref(),
    )?;
    Ok(Some(MmrOperationOutcomeRecord {
        operation_id: operation_id.to_owned(),
        operation_fingerprint,
        state_id,
        authority_basis_ref: Some(basis_ref),
        authority_basis_type: Some(basis_type),
        cutpoint_fact_fingerprint: predecessor,
        operation_outcome: "COMMITTED".to_owned(),
        transition_fact_fingerprint: Some(fact_fingerprint),
    }))
}

/// Durable operation outcome: first the immutable outcome journal, then any
/// committed MMR core fact.  Once decided, an operation identity can never be
/// re-decided under a later authority.
fn mmr_operation_outcome(
    connection: &Connection,
    operation_id: &str,
) -> Result<Option<MmrOperationOutcomeRecord>, LocalOwnerError> {
    let row: Option<(String, Option<String>, Option<String>, Option<String>, Option<String>, String, Option<String>)> =
        connection
            .query_row(
                "SELECT logical_id,json_extract(CAST(canonical_bytes AS TEXT),'$.operationFingerprint'),json_extract(CAST(canonical_bytes AS TEXT),'$.authorityBasisRef'),json_extract(CAST(canonical_bytes AS TEXT),'$.authorityBasisType'),json_extract(CAST(canonical_bytes AS TEXT),'$.cutpointFactFingerprint'),json_extract(CAST(canonical_bytes AS TEXT),'$.operationOutcome'),json_extract(CAST(canonical_bytes AS TEXT),'$.transitionFactFingerprint') FROM canonical_fact WHERE fact_kind=?1 AND logical_id=?2 AND fact_revision=1",
                params![OUTCOME_FACT_KIND, operation_id],
                |row| {
                    Ok((
                        row.get(0)?,
                        row.get(1)?,
                        row.get(2)?,
                        row.get(3)?,
                        row.get(4)?,
                        row.get(5)?,
                        row.get(6)?,
                    ))
                },
            )
            .optional()?;
    if let Some((state_id, fingerprint, basis_ref, basis_type, cutpoint, outcome, transition)) = row {
        let Some(fingerprint) = fingerprint else {
            return Err(LocalOwnerError::StateCorrupt);
        };
        return Ok(Some(MmrOperationOutcomeRecord {
            operation_id: operation_id.to_owned(),
            operation_fingerprint: fingerprint,
            state_id,
            authority_basis_ref: basis_ref,
            authority_basis_type: basis_type,
            cutpoint_fact_fingerprint: cutpoint,
            operation_outcome: outcome,
            transition_fact_fingerprint: transition,
        }));
    }
    mmr_committed_operation_outcome(connection, operation_id)
}

/// Records an immutable operation outcome in the same single-writer
/// transaction as the operation that produced it.
fn journal_operation_outcome(
    transaction: &Transaction<'_>,
    next_sequence: &mut u64,
    operation_id: &str,
    operation_fingerprint: &str,
    authority_basis_ref: Option<&str>,
    authority_basis_type: Option<&str>,
    cutpoint_fact_fingerprint: Option<&str>,
    operation_outcome: &str,
    transition_fact_fingerprint: Option<&str>,
) -> Result<(), LocalOwnerError> {
    let value = json!({
        "authorityBasisRef": authority_basis_ref,
        "authorityBasisType": authority_basis_type,
        "cutpointFactFingerprint": cutpoint_fact_fingerprint,
        "operationFingerprint": operation_fingerprint,
        "operationId": operation_id,
        "operationOutcome": operation_outcome,
        "protocol": OUTCOME_PROTOCOL,
        "transitionFactFingerprint": transition_fact_fingerprint,
    });
    let canonical_bytes = canonical_value_bytes(&value)?;
    let fingerprint_material = canonical_value_bytes(&json!({
        "factKind": OUTCOME_FACT_KIND,
        "logicalId": operation_id,
        "predecessorFactFingerprint": Value::Null,
        "revision": 1,
        "value": value,
    }))?;
    let fact_fingerprint = domain_fingerprint(
        &format!("agents-os.local-owner.fact.{OUTCOME_FACT_KIND}.v1"),
        &fingerprint_material,
    );
    let fact_ref = format!("fact:{OUTCOME_FACT_KIND}:{operation_id}:1");
    let event_sequence = *next_sequence;
    let previous_event_fingerprint = latest_event_fingerprint(transaction)?;
    let event_value = json!({
        "aggregateRef": operation_id,
        "aggregateRevision": 1,
        "commandFingerprint": operation_fingerprint,
        "eventKind": "MMR_OPERATION_OUTCOME_RECORDED",
        "eventSequence": event_sequence,
        "factFingerprint": fact_fingerprint,
        "factRef": fact_ref,
        "operationOutcome": operation_outcome,
        "predecessorEventFingerprint": previous_event_fingerprint,
    });
    let event_bytes = canonical_value_bytes(&event_value)?;
    let event_fingerprint = domain_fingerprint("agents-os.local-owner.event.v1", &event_bytes);
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![
            as_i64(event_sequence)?,
            format!("event:local-owner:{event_sequence}"),
            "MMR_OPERATION_OUTCOME_RECORDED",
            operation_id,
            1_i64,
            operation_fingerprint,
            previous_event_fingerprint,
            event_bytes,
            event_fingerprint
        ],
    )?;
    transaction.execute(
        "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence) VALUES(?1,?2,1,?3,?4,1,?5,?6,NULL,?7)",
        params![
            OUTCOME_FACT_KIND,
            operation_id,
            fact_ref,
            "subject:runtime-outcome",
            canonical_bytes,
            fact_fingerprint,
            as_i64(event_sequence)?
        ],
    )?;
    *next_sequence += 1;
    Ok(())
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MmrCoreFault {
    None,
    AfterAuthorityBeforeTransaction,
    AfterFirstCandidateComponent,
    AfterAllCandidateComponents,
    AfterAtomicPublication,
    AfterTransactionBeforeResponse,
}

#[derive(Clone, Debug)]
struct PendingProposal {
    attachment_generation: u64,
    proposal_fingerprint: String,
    command_fingerprint: String,
    command_type: String,
    canonical_request_bytes: Vec<u8>,
    request: Value,
    state_binding: Value,
    consent_kind: ConsentKind,
    challenge: Challenge,
    expires_at_unix_ms: u64,
    failed_attempts: u8,
}

#[derive(Clone, Debug)]
struct PendingMmrProposal {
    attachment_generation: u64,
    operation_id: String,
    operation_fingerprint: String,
    mutation_type: String,
    target_state_id: String,
    request: Value,
    challenge: Challenge,
    expires_at_unix_ms: u64,
    failed_attempts: u8,
}

#[derive(Debug)]
struct MutationCommit {
    first_event_sequence: u64,
    last_event_sequence: u64,
    result: Value,
}

pub struct LocalOwnerStore {
    connection: Connection,
    pending: Option<PendingProposal>,
    pending_mmr: BTreeMap<String, PendingMmrProposal>,
    // P2-H OBS-ACK: read-only caller-visible acknowledgement disposition per
    // operation identity (DELIVERED / LOST). Session/transport surface only.
    ack_trace: BTreeMap<String, String>,
}

impl LocalOwnerStore {
    pub fn open_admitted(
        database_path: &std::path::Path,
        process_nonce: Option<&[u8]>,
        initialize_genesis: bool,
    ) -> Result<Self, LocalOwnerError> {
        let flags = OpenFlags::SQLITE_OPEN_READ_WRITE
            | OpenFlags::SQLITE_OPEN_NO_MUTEX
            | if initialize_genesis {
                OpenFlags::SQLITE_OPEN_CREATE
            } else {
                OpenFlags::empty()
            };
        let mut connection = Connection::open_with_flags(database_path, flags)?;
        connection.busy_timeout(std::time::Duration::ZERO)?;
        connection.pragma_update(None, "foreign_keys", "ON")?;
        connection.pragma_update(None, "journal_mode", "DELETE")?;
        connection.pragma_update(None, "synchronous", "FULL")?;
        if initialize_genesis {
            let table_count: i64 = connection.query_row(
                "SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                [],
                |row| row.get(0),
            )?;
            if table_count != 0 {
                return Err(LocalOwnerError::ContinuityLineageConflict);
            }
            schema::initialize_or_verify(&mut connection)?;
            append_authority_epoch(
                &mut connection,
                process_nonce.ok_or(LocalOwnerError::RandomnessUnavailable)?,
            )?;
        } else {
            if process_nonce.is_some() {
                return Err(LocalOwnerError::InvalidInput);
            }
            schema::verify(&connection)?;
        }
        verify_event_and_epoch_chains(&connection)?;
        schema::verify(&connection)?;
        verify_mmr_current_pointer_integrity(&connection)?;
        verify_mmr_transition_history_integrity(&connection)?;
        verify_commitment_pointer_integrity(&connection)?;
        verify_p2f_kind_integrity(&connection)?;
        Ok(Self {
            connection,
            pending: None,
            pending_mmr: BTreeMap::new(),
            ack_trace: BTreeMap::new(),
        })
    }

    pub fn health(&self) -> Result<Value, LocalOwnerError> {
        schema::verify(&self.connection)?;
        verify_event_and_epoch_chains(&self.connection)?;
        verify_mmr_current_pointer_integrity(&self.connection)?;
        verify_mmr_transition_history_integrity(&self.connection)?;
        verify_commitment_pointer_integrity(&self.connection)?;
        verify_p2f_kind_integrity(&self.connection)?;
        let snapshot = continuity_snapshot_on(&self.connection)?;
        let anchor = snapshot.current.ok_or(LocalOwnerError::StateCorrupt)?;
        Ok(json!({
            "authorityEpoch": anchor.authority_epoch,
            "continuityAnchor": anchor.as_json(),
            "incarnationId": anchor.incarnation_id,
            "ledgerThreadAlive": true,
            "lockHeld": true,
        }))
    }

    pub fn invalidate(&mut self, attachment_generation: u64) -> Value {
        if self
            .pending
            .as_ref()
            .is_some_and(|value| value.attachment_generation == attachment_generation)
        {
            self.pending = None;
        }
        json!({
            "invalidated": true,
            "resultCode": "PENDING_PROPOSAL_INVALIDATED"
        })
    }

    pub fn restore(&mut self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = input.as_object().ok_or(LocalOwnerError::InvalidInput)?;
        require_allowed_keys(
            object,
            &[
                "checkpointIdentity",
                "gap",
                "lineageAuthority",
                "protectionOutcome",
                "restoredFrom",
            ],
            &["exclusionConstraints", "projectionStates", "requestedClaim", "restoreMode"],
        )?;
        let checkpoint_identity = require_nonempty_string(object, "checkpointIdentity", 300)?;
        let restored_from = require_nonempty_string(object, "restoredFrom", 300)?;
        let lineage_authority = require_nonempty_string(object, "lineageAuthority", 300)?;
        let protection_outcome = require_string(object, "protectionOutcome", 32)?;
        if protection_outcome != "PROTECTED" || lineage_authority.starts_with("local:") {
            return Err(LocalOwnerError::ContinuityAdmissionDenied);
        }
        let gap = object
            .get("gap")
            .ok_or(LocalOwnerError::InvalidInput)?
            .as_object()
            .ok_or(LocalOwnerError::InvalidInput)?;
        require_allowed_keys(gap, &["known", "possible", "claim"], &[])?;
        let known = gap
            .get("known")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;
        let possible = gap
            .get("possible")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;
        let claim = require_nonempty_string(gap, "claim", 300)?;
        if !known && !possible {
            return Err(LocalOwnerError::InvalidInput);
        }
        if restored_from != checkpoint_identity {
            return Err(LocalOwnerError::InvalidInput);
        }

        let requested_claim = optional_string(object, "requestedClaim", 64)?.unwrap_or("NONE");
        if requested_claim == "ERASE" {
            return Ok(json!({
                "accepted": false,
                "resultCode": "STRONG_CLAIM_REFUSED",
                "resurrectionRisk": true,
                "durableTransition": false,
            }));
        }
        if requested_claim != "NONE"
            && requested_claim != "LOGICAL_REMOVAL"
            && requested_claim != "PROTECTED_EXCLUSION"
        {
            return Err(LocalOwnerError::InvalidInput);
        }
        let restore_mode = optional_string(object, "restoreMode", 32)?.unwrap_or("SUCCESSOR");
        if restore_mode != "SUCCESSOR" && restore_mode != "DIRECT" {
            return Err(LocalOwnerError::InvalidInput);
        }
        let projection_states = parse_projection_states(object.get("projectionStates"))?;
        let exclusion_constraints = parse_exclusion_constraints(object.get("exclusionConstraints"))?;
        if restore_mode == "DIRECT"
            && exclusion_constraints
                .iter()
                .any(|constraint| constraint["strength"] == "PROTECTED_EXCLUSION")
        {
            return Ok(json!({
                "accepted": false,
                "checkpointDisposition": "QUARANTINED",
                "currentProjection": [],
                "resultCode": "DIRECT_RESTORE_BLOCKED_PROTECTED_EXCLUSION",
                "durableTransition": false,
            }));
        }

        let mut nonce = vec![0_u8; 32];
        File::open("/dev/urandom")
            .and_then(|mut file| file.read_exact(&mut nonce))
            .map_err(|_| LocalOwnerError::RandomnessUnavailable)?;
        append_disaster_restore_epoch(
            &mut self.connection,
            &nonce,
            checkpoint_identity,
            restored_from,
            known,
            possible,
            claim,
            lineage_authority,
            projection_states,
            exclusion_constraints,
        )
    }

    pub fn attempt_replica_activation(&self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(
            input,
            &[
                "activationAuthority",
                "basis",
                "lineageRelation",
                "replicaId",
                "replicaRole",
            ],
        )?;
        let replica_id = require_nonempty_string(object, "replicaId", 300)?;
        let replica_role = require_nonempty_string(object, "replicaRole", 64)?;
        let lineage_relation = require_nonempty_string(object, "lineageRelation", 64)?;
        let basis = require_nonempty_string(object, "basis", 300)?;
        let authority = object
            .get("activationAuthority")
            .and_then(Value::as_object)
            .ok_or(LocalOwnerError::InvalidInput)?;
        require_exact_object_value(authority, &["authorityRef", "decision"])?;
        let authority_ref = require_nonempty_string(authority, "authorityRef", 300)?;
        let decision = require_string(authority, "decision", 32)?;
        if replica_role != "RECOVERY_REPLICA" && replica_role != "SECOND_HOME" && replica_role != "COPIED_HOME" {
            return Err(LocalOwnerError::InvalidInput);
        }
        Ok(json!({
            "accepted": false,
            "canonicalHomeRelation": lineage_relation,
            "currentGrantValid": false,
            "durableTransition": false,
            "mutationAllowed": false,
            "observedBasis": basis,
            "observedAuthorityDecision": decision,
            "observedAuthorityRef": authority_ref,
            "reason": "REPLICA_MATERIAL_IS_NOT_ACTIVATION_AUTHORITY",
            "replicaId": replica_id,
            "replicaRole": replica_role,
            "resultCode": "REPLICA_ACTIVATION_DENIED",
        }))
    }

    pub fn evaluate_removal_claim(&self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(
            input,
            &[
                "claim",
                "continuityAuthority",
                "currentProjectionPresent",
                "grantValid",
                "historicalStatePresent",
                "incarnationId",
                "protectedCopyPresent",
                "stableIdentity",
            ],
        )?;
        let claim = require_nonempty_string(object, "claim", 64)?;
        let continuity_authority = require_nonempty_string(object, "continuityAuthority", 300)?;
        let incarnation_id = require_nonempty_string(object, "incarnationId", 300)?;
        let stable_identity = require_nonempty_string(object, "stableIdentity", 300)?;
        let current_projection_present = object
            .get("currentProjectionPresent")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;
        let grant_valid = object
            .get("grantValid")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;
        let historical_state_present = object
            .get("historicalStatePresent")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;
        let protected_copy_present = object
            .get("protectedCopyPresent")
            .and_then(Value::as_bool)
            .ok_or(LocalOwnerError::InvalidInput)?;

        let unsupported_claim = matches!(claim, "REMOVE" | "ERASE" | "RETIRE");
        let downgraded = unsupported_claim && !current_projection_present;
        let continuity_denied = continuity_authority.starts_with("local:");
        let cpk7_blocked = claim == "CPK7" && current_projection_present;
        let effective_claim = if continuity_denied {
            "NONE"
        } else if cpk7_blocked {
            "PROTECTED_EXCLUSION"
        } else if downgraded {
            "NOT_IN_CURRENT_PROJECTION"
        } else {
            "NONE"
        };
        let result_code = if continuity_denied {
            "CONTINUITY_SELF_AUTHORITY_DENIED"
        } else if cpk7_blocked {
            "CPK7_PROTECTED_EXCLUSION_QUARANTINED"
        } else if downgraded {
            "REMOVAL_CLAIM_DOWNGRADED"
        } else {
            "REMOVAL_CLAIM_REFUSED"
        };

        Ok(json!({
            "accepted": false,
            "claim": claim,
            "continuityAuthority": continuity_authority,
            "currentProjectionPresent": current_projection_present,
            "durableTransition": false,
            "effectiveClaim": effective_claim,
            "grantValid": grant_valid && !continuity_denied,
            "historicalStatePresent": historical_state_present,
            "incarnationId": incarnation_id,
            "mutationAllowed": false,
            "protectedCopyDisclosed": protected_copy_present,
            "quarantined": cpk7_blocked,
            "resultCode": result_code,
            "stableIdentity": stable_identity,
        }))
    }

    pub fn prepare_mmr_mutation(
        &mut self,
        input: &Value,
    ) -> Result<Value, LocalOwnerError> {
        verify_mmr_current_pointer_integrity(&self.connection)?;
        let object = require_exact_object(input, &["attachmentGeneration", "request"])?;
        let generation = require_u64(object, "attachmentGeneration")?;
        if generation == 0 {
            return Err(LocalOwnerError::InvalidInput);
        }
        let request = object.get("request").ok_or(LocalOwnerError::InvalidInput)?;
        let request_object = require_exact_object(request, &["mutation", "operation"])?;
        if require_string(request_object, "operation", 64)? != "PROPOSE_MMR_MUTATION_CORE" {
            return Err(LocalOwnerError::InvalidInput);
        }
        let mutation = request_object
            .get("mutation")
            .ok_or(LocalOwnerError::InvalidInput)?;

        // P2-H: bind the logical operation identity (operation_id + operation
        // intent digest over the canonical request) BEFORE semantic validation,
        // so an already-decided identity deterministically returns its original
        // durable outcome and can never be re-evaluated under a later authority,
        // payload, cutpoint, or consent. Same identity + same digest = same
        // logical operation (original outcome returned). Same identity +
        // different digest = HARD CONFLICT / immutable outcome (A3-V2/V3/V4).
        let operation_id = mutation
            .as_object()
            .ok_or(LocalOwnerError::InvalidInput)
            .and_then(|object| require_nonempty_string(object, "operationId", 200))?;
        let canonical_request_bytes = canonical_value_bytes(request)?;
        let operation_fingerprint = domain_fingerprint(
            "agents-os.local-owner.mmr-operation-core.v1",
            &canonical_request_bytes,
        );
        if let Some(existing) = mmr_operation_outcome(&self.connection, operation_id)? {
            return Ok(if existing.operation_fingerprint == operation_fingerprint {
                json!({
                    "accepted": false,
                    "operationFingerprint": operation_fingerprint,
                    "operationId": operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": if existing.operation_outcome == OUTCOME_COMMITTED {
                        "OPERATION_ALREADY_APPLIED_LOCALLY"
                    } else {
                        "MMR_OPERATION_OUTCOME_IMMUTABLE"
                    },
                    "targetStateId": existing.state_id,
                })
            } else {
                json!({
                    "accepted": false,
                    "operationId": operation_id,
                    "resultCode": "MMR_OPERATION_ID_CONFLICT",
                })
            });
        }

        // P2-B invariant: a determinate authority denial is a rejection with
        // ZERO durable writes (no state, no transition, no outcome journal).
        // A denied identity that reaches a journaled DENIED outcome is the
        // P2-E current-conflict path, which the identity-first dedup below and
        // the immutable outcome journal make non-retroactive (A3-V3).
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        let mutation_type = require_string(mutation_object, "mutationType", 32)?;
        let target_state_id = require_nonempty_string(mutation_object, "targetStateId", 200)?;
        if ![
            "CREATE",
            "REVISE",
            "SUPERSEDE",
            "RETIRE",
            "ADD_EVIDENCE",
            "CREATE_COMMITMENT",
            "FULFILL_COMMITMENT",
            "RELEASE_COMMITMENT",
            "CREATE_EVIDENCE",
            "CREATE_CANDIDATE",
            "CREATE_SUMMARY",
        ]
        .contains(&mutation_type)
        {
            return Err(LocalOwnerError::InvalidInput);
        }
        let expected_current = mutation_object["expectedCurrentFingerprint"].as_str();
        let current_metadata = kind_current_metadata(
            &self.connection,
            mutation_fact_kind(&self.connection, mutation_type, target_state_id)?,
            target_state_id,
        )?;
        let match_ok = match (mutation_type, &current_metadata) {
            (
                "CREATE" | "CREATE_COMMITMENT" | "CREATE_EVIDENCE" | "CREATE_CANDIDATE"
                | "CREATE_SUMMARY",
                None,
            ) if expected_current.is_none() => true,
            (
                "REVISE" | "SUPERSEDE" | "RETIRE" | "ADD_EVIDENCE"
                | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT",
                Some((_, current)),
            ) if expected_current == Some(current.as_str()) => true,
            (
                "REVISE" | "SUPERSEDE" | "RETIRE" | "ADD_EVIDENCE"
                | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT",
                None,
            ) => false,
            _ => false,
        };
        if !match_ok {
            let cutpoint = current_metadata
                .as_ref()
                .map(|(_, fingerprint)| fingerprint.as_str());
            self.journal_denied_outcome(
                operation_id,
                &operation_fingerprint,
                mutation_object,
                cutpoint,
            )?;
            return Ok(json!({
                "accepted": false,
                "operationId": operation_id,
                "operationOutcome": OUTCOME_DENIED,
                "resultCode": if current_metadata.is_none() {
                    "MMR_PREDECESSOR_NOT_FOUND"
                } else {
                    "MMR_CURRENT_CONFLICT"
                },
                "targetStateId": target_state_id,
            }));
        }
        validate_mmr_plane_transition(&self.connection, mutation_object)?;
        enforce_mmr_derived_transition(
            &self.connection,
            mutation_object,
            mutation_type,
            target_state_id,
        )?;
        if matches!(
            mutation_type,
            "CREATE_COMMITMENT" | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT"
        ) {
            validate_mmr_commitment_transition(&self.connection, mutation_object)?;
        }
        match mutation_type {
            "CREATE_EVIDENCE" => validate_mmr_evidence_identity(&self.connection, mutation_object)?,
            "CREATE_CANDIDATE" => validate_mmr_candidate_creation(&self.connection, mutation_object)?,
            "CREATE_SUMMARY" => validate_mmr_summary_creation(&self.connection, mutation_object)?,
            "ADD_EVIDENCE" => {
                if mutation_fact_kind(&self.connection, mutation_type, target_state_id)?
                    == CANDIDATE_FACT_KIND
                {
                    validate_mmr_candidate_evidence_transition(
                        &self.connection,
                        mutation_object,
                    )?;
                }
            }
            _ => {}
        }
        let consent_kind = mmr_consent_kind(mutation_type)?;
        let challenge = self.unique_mmr_challenge(consent_kind)?;
        let prompt = challenge.prompt(consent_kind);
        let replaced = self
            .pending_mmr
            .insert(
                operation_id.to_owned(),
                PendingMmrProposal {
                    attachment_generation: generation,
                    operation_id: operation_id.to_owned(),
                    operation_fingerprint: operation_fingerprint.clone(),
                    mutation_type: mutation_type.to_owned(),
                    target_state_id: target_state_id.to_owned(),
                    request: request.clone(),
                    challenge,
                    expires_at_unix_ms: unix_ms()?
                        + DEFAULT_PROPOSAL_TTL_SECONDS * 1000,
                    failed_attempts: 0,
                },
            )
            .is_some();
        Ok(json!({
            "accepted": true,
            "authenticationAssurance": "LOCAL_OWNER_SESSION_ONLY",
            "consentPrompt": prompt,
            "expiresInSeconds": DEFAULT_PROPOSAL_TTL_SECONDS,
            "mutationType": mutation_type,
            "operationFingerprint": operation_fingerprint,
            "operationId": operation_id,
            "ownerConsentAuthorityScope": "P2_A_LOCAL_MUTATION_ELIGIBILITY_ONLY",
            "ownerConsentMode": "SPOKEN_CHALLENGE_V1",
            "replacedSameOperationProposal": replaced,
            "resultCode": "MMR_MUTATION_CORE_PROPOSAL_PREPARED",
            "targetStateId": target_state_id,
        }))
    }

    pub fn submit_mmr_consent(
        &mut self,
        input: &Value,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(
            input,
            &["attachmentGeneration", "ingress", "operationId", "transcript"],
        )?;
        let generation = require_u64(object, "attachmentGeneration")?;
        let operation_id = require_nonempty_string(object, "operationId", 200)?;
        let ingress = require_string(object, "ingress", 64)?;
        let transcript = require_string(object, "transcript", 4096)?;
        if generation == 0
            || !["TYPED_TEXT", "FINAL_VOICE_TRANSCRIPT", "PARTIAL_VOICE_TRANSCRIPT"]
                .contains(&ingress)
        {
            return Err(LocalOwnerError::InvalidInput);
        }
        if ingress == "PARTIAL_VOICE_TRANSCRIPT" {
            return Ok(json!({"accepted": false, "resultCode": "PARTIAL_TRANSCRIPT_REJECTED"}));
        }
        let Some(mut pending) = self.pending_mmr.remove(operation_id) else {
            return Ok(json!({"accepted": false, "resultCode": "NO_PENDING_MMR_MUTATION"}));
        };
        if pending.attachment_generation != generation {
            return Ok(json!({"accepted": false, "resultCode": "ATTACHMENT_GENERATION_MISMATCH"}));
        }
        if unix_ms()? > pending.expires_at_unix_ms {
            return Ok(json!({"accepted": false, "resultCode": "PROPOSAL_EXPIRED"}));
        }
        let consent_kind = mmr_consent_kind(&pending.mutation_type)?;
        match parse_transcript(transcript, consent_kind, &pending.challenge) {
            ConsentParse::Cancel => Ok(json!({"accepted": false, "resultCode": "PROPOSAL_CANCELLED"})),
            ConsentParse::Reject => {
                pending.failed_attempts += 1;
                if pending.failed_attempts >= 3 {
                    Ok(json!({"accepted": false, "attemptsRemaining": 0, "resultCode": "PROPOSAL_INVALIDATED"}))
                } else {
                    let attempts_remaining = 3 - pending.failed_attempts;
                    self.pending_mmr.insert(operation_id.to_owned(), pending);
                    Ok(json!({"accepted": false, "attemptsRemaining": attempts_remaining, "resultCode": "CONSENT_REJECTED"}))
                }
            }
            ConsentParse::Approve => {
                let consent = consent_commitment(transcript);
                match self.commit_mmr_mutation(&pending, &consent, fault) {
                    Ok(result) => {
                        // P2-H OBS-ACK: record the acknowledgement disposition
                        // at the response boundary (session/transport surface).
                        self.ack_trace.insert(
                            pending.operation_id.clone(),
                            ACK_DISPOSITION_DELIVERED.to_owned(),
                        );
                        Ok(json!({
                            "accepted": true,
                            "result": result,
                            "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF",
                        }))
                    }
                    Err(LocalOwnerError::ResponseLostAfterCommit) => {
                        // P2-H OBS-ACK: durable commit succeeded but the
                        // acknowledgement was lost before reaching the caller
                        // (A3-V1 ack-loss window).
                        self.ack_trace.insert(
                            pending.operation_id.clone(),
                            ACK_DISPOSITION_LOST.to_owned(),
                        );
                        Err(LocalOwnerError::ResponseLostAfterCommit)
                    }
                    Err(LocalOwnerError::InjectedCrash) => {
                        // P2-H: a crash at a provably-not-committed cutpoint
                        // (before atomic publication) means the attempt did not
                        // commit; the stable outcome class is
                        // NOT_COMMITTED_RETRYABLE and retry of the same logical
                        // operation is safe. AfterAtomicPublication is not
                        // provably-not-committed: it is journaled
                        // BLOCKED_INDETERMINATE and never reported retryable.
                        if fault != MmrCoreFault::AfterAtomicPublication {
                            self.ack_trace.insert(
                                pending.operation_id.clone(),
                                OUTCOME_NOT_COMMITTED_RETRYABLE.to_owned(),
                            );
                        }
                        Err(LocalOwnerError::InjectedCrash)
                    }
                    Err(LocalOwnerError::MmrCurrentConflict) => {
                        let mutation_object = validate_mmr_core_mutation(
                            &pending.request["mutation"],
                            true,
                        )?;
                        let cutpoint = kind_current_metadata(
                            &self.connection,
                            mutation_fact_kind(
                                &self.connection,
                                &pending.mutation_type,
                                &pending.target_state_id,
                            )?,
                            &pending.target_state_id,
                        )?
                        .map(|(_, fingerprint)| fingerprint);
                        self.journal_denied_outcome(
                            &pending.operation_id,
                            &pending.operation_fingerprint,
                            mutation_object,
                            cutpoint.as_deref(),
                        )?;
                        Err(LocalOwnerError::MmrCurrentConflict)
                    }
                    Err(error) => Err(error),
                }
            }
        }
    }

    /// Writes an immutable DENIED outcome journal record for a determinate
    /// operation denial (stale/conflicting cutpoint or missing predecessor).
    /// This is the durable audit trail that later authority cannot rewrite.
    fn journal_denied_outcome(
        &mut self,
        operation_id: &str,
        operation_fingerprint: &str,
        mutation_object: &Map<String, Value>,
        cutpoint_fact_fingerprint: Option<&str>,
    ) -> Result<(), LocalOwnerError> {
        let authority = mutation_object["components"]["authority"]
            .as_object()
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
        let basis_ref = authority["authorityBasisRef"]
            .as_str()
            .unwrap_or("authority-basis:unresolved");
        let basis_type = authority["authorityBasisType"]
            .as_str()
            .unwrap_or("UNRESOLVED");
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mut next_sequence = next_event_sequence(&transaction)?;
        journal_operation_outcome(
            &transaction,
            &mut next_sequence,
            operation_id,
            operation_fingerprint,
            Some(basis_ref),
            Some(basis_type),
            cutpoint_fact_fingerprint,
            "DENIED",
            None,
        )?;
        transaction.commit()?;
        Ok(())
    }

    /// P2-H: durably records BLOCKED_INDETERMINATE for an operation that entered
    /// the atomic-publication window and whose commit state cannot be safely
    /// determined. A retry of the same identity must then return the original
    /// BLOCKED_INDETERMINATE and must never blind re-execute (A3-V4). Idempotent.
    fn journal_indeterminate_outcome(
        &mut self,
        operation_id: &str,
        operation_fingerprint: &str,
        mutation: &Value,
    ) -> Result<(), LocalOwnerError> {
        if mmr_operation_outcome(&self.connection, operation_id)?.is_some() {
            return Ok(());
        }
        let (basis_ref, basis_type) = mutation_authority_basis(mutation);
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mut next_sequence = next_event_sequence(&transaction)?;
        journal_operation_outcome(
            &transaction,
            &mut next_sequence,
            operation_id,
            operation_fingerprint,
            basis_ref.as_deref(),
            basis_type.as_deref(),
            None,
            OUTCOME_BLOCKED_INDETERMINATE,
            None,
        )?;
        transaction.commit()?;
        Ok(())
    }

    pub fn query_mmr_core(&self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(input, &["operation", "query"])?;
        let query = object.get("query").ok_or(LocalOwnerError::InvalidInput)?;
        match require_string(object, "operation", 64)? {
            "QUERY_MMR_CURRENT_CORE" => {
                let query = require_exact_object(query, &["stateId"])?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                match read_mmr_current(&self.connection, state_id)? {
                    Some(current) => Ok(json!({
                        "accepted": true,
                        "current": current,
                        "history": read_mmr_history(&self.connection, state_id)?,
                        "resultCode": "MMR_CURRENT_CORE_QUERY_OK",
                    })),
                    None => Ok(json!({"accepted": true, "current": null, "history": [], "resultCode": "MMR_CURRENT_CORE_QUERY_OK"})),
                }
            }
            "QUERY_MMR_OPERATION_CORE" => {
                let query = require_exact_object(query, &["operationId"])?;
                let operation_id = require_nonempty_string(query, "operationId", 200)?;
                let outcome = mmr_operation_outcome(&self.connection, operation_id)?;
                let committed = mmr_operation_record(&self.connection, operation_id)?;
                Ok(json!({
                    "accepted": true,
                    "operation": committed.as_ref().map(|record| record.as_json()),
                    "operationOutcome": outcome.as_ref().map(|record| record.operation_outcome.clone()),
                    "outcome": outcome.as_ref().map(|record| record.as_json()),
                    "resultCode": "MMR_OPERATION_CORE_QUERY_OK",
                }))
            }
            "QUERY_MMR_COMMITMENT_CORE" => {
                let query = require_exact_object(query, &["stateId"])?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                match read_commitment_current(&self.connection, state_id)? {
                    Some(current) => Ok(json!({
                        "accepted": true,
                        "current": current,
                        "history": read_commitment_history(&self.connection, state_id)?,
                        "resultCode": "MMR_COMMITMENT_CORE_QUERY_OK",
                    })),
                    None => Ok(json!({"accepted": true, "current": null, "history": [], "resultCode": "MMR_COMMITMENT_CORE_QUERY_OK"})),
                }
            }
            "QUERY_MMR_EVIDENCE_CORE" => {
                let query = require_exact_object(query, &["stateId"])?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                match read_evidence_current(&self.connection, state_id)? {
                    Some(current) => Ok(json!({
                        "accepted": true,
                        "current": current,
                        "history": read_evidence_history(&self.connection, state_id)?,
                        "resultCode": "MMR_EVIDENCE_CORE_QUERY_OK",
                    })),
                    None => Ok(json!({"accepted": true, "current": null, "history": [], "resultCode": "MMR_EVIDENCE_CORE_QUERY_OK"})),
                }
            }
            "QUERY_MMR_CANDIDATE_CORE" => {
                let query = require_exact_object(query, &["stateId"])?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                match read_candidate_current(&self.connection, state_id)? {
                    Some(current) => Ok(json!({
                        "accepted": true,
                        "current": current,
                        "history": read_candidate_history(&self.connection, state_id)?,
                        "resultCode": "MMR_CANDIDATE_CORE_QUERY_OK",
                    })),
                    None => Ok(json!({"accepted": true, "current": null, "history": [], "resultCode": "MMR_CANDIDATE_CORE_QUERY_OK"})),
                }
            }
            "QUERY_MMR_SUMMARY_CORE" => {
                let query = require_exact_object(query, &["stateId"])?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                match read_summary_current(&self.connection, state_id)? {
                    Some(current) => Ok(json!({
                        "accepted": true,
                        "current": current,
                        "history": read_summary_history(&self.connection, state_id)?,
                        "resultCode": "MMR_SUMMARY_CORE_QUERY_OK",
                    })),
                    None => Ok(json!({"accepted": true, "current": null, "history": [], "resultCode": "MMR_SUMMARY_CORE_QUERY_OK"})),
                }
            }
            "QUERY_MMR_SUMMARY_SUPPORT" => {
                let query = query.as_object().ok_or(LocalOwnerError::InvalidInput)?;
                let state_id = require_nonempty_string(query, "stateId", 200)?;
                let visible_references = match query.get("visibleReferences") {
                    Some(Value::Null) | None => None,
                    Some(Value::Array(values)) => {
                        let mut refs = Vec::new();
                        for value in values {
                            refs.push(
                                value
                                    .as_str()
                                    .ok_or(LocalOwnerError::InvalidInput)?
                                    .to_owned(),
                            );
                        }
                        Some(refs)
                    }
                    Some(_) => return Err(LocalOwnerError::InvalidInput),
                };
                Ok(json!({
                    "accepted": true,
                    "support": resolve_summary_support(
                        &self.connection,
                        state_id,
                        visible_references.as_deref(),
                    )?,
                    "resultCode": "MMR_SUMMARY_SUPPORT_QUERY_OK",
                }))
            }
            "QUERY_MMR_PERSISTENCE_INSPECT" => {
                Ok(json!({
                    "accepted": true,
                    "inspect": persistence_inspect(&self.connection)?,
                    "resultCode": "MMR_PERSISTENCE_INSPECT_OK",
                }))
            }
            "QUERY_MMR_RECALL_PROJECTION" => {
                Ok(json!({
                    "accepted": true,
                    "projection": recall_projection(&self.connection, query)?,
                    "resultCode": "MMR_RECALL_PROJECTION_READ_ONLY_OK",
                }))
            }
            "QUERY_MMR_COGNITIVE_CONTEXT" => {
                cognitive_context_projection(&self.connection, query)
            }
            "QUERY_MMR_ACK_TRACE" => {
                // P2-H OBS-ACK: read-only acknowledgement disposition per
                // operation identity (DELIVERED / LOST). Distinguishes the
                // durable mutation outcome from whether the caller received the
                // acknowledgement. Session/transport surface, never Memory.
                let trace = self
                    .ack_trace
                    .iter()
                    .map(|(operation_id, disposition)| {
                        json!({
                            "ackDisposition": disposition,
                            "operationId": operation_id,
                        })
                    })
                    .collect::<Vec<_>>();
                Ok(json!({
                    "accepted": true,
                    "ackTrace": trace,
                    "resultCode": "MMR_ACK_TRACE_READ_ONLY_OK",
                }))
            }
            "VALIDATE_MMR_OBSERVER_CONTROL_REQUEST" => {
                validate_observer_control_request(&self.connection, query)
            }
            "VALIDATE_MMR_COGNITIVE_PLANE_BINDING" => {
                validate_cognitive_plane_binding(&self.connection, query)
            }
            _ => Err(LocalOwnerError::InvalidInput),
        }
    }

    pub fn prepare_proposal(&mut self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(input, &["attachmentGeneration", "request"])?;
        let generation = require_u64(object, "attachmentGeneration")?;
        if generation == 0 {
            return Err(LocalOwnerError::InvalidInput);
        }
        let request = object.get("request").ok_or(LocalOwnerError::InvalidInput)?;
        let request_object = require_exact_object(request, &["mutation", "operation"])?;
        let operation = require_string(request_object, "operation", 64)?;
        if !["PROPOSE_GOAL_MUTATION", "PROPOSE_TASK_MUTATION"].contains(&operation) {
            return Err(LocalOwnerError::InvalidInput);
        }
        let mutation = request_object
            .get("mutation")
            .ok_or(LocalOwnerError::InvalidInput)?;
        let mutation_object = require_exact_object(mutation, &["mutationType", "payload"])?;
        let command_type = require_string(mutation_object, "mutationType", 64)?.to_owned();
        validate_operation_command_pair(operation, &command_type)?;
        validate_mutation_payload(
            &self.connection,
            &command_type,
            mutation_object
                .get("payload")
                .ok_or(LocalOwnerError::InvalidInput)?,
        )?;
        let payload = mutation_object
            .get("payload")
            .ok_or(LocalOwnerError::InvalidInput)?;
        validate_transition_preconditions(&self.connection, &command_type, payload)?;
        let state_binding = state_binding_for(&self.connection, &command_type, payload)?;

        let canonical_request_bytes = canonical_value_bytes(&json!({
            "request": request,
            "stateBinding": state_binding,
        }))?;
        let proposal_fingerprint = domain_fingerprint(
            "agents-os.local-owner.proposal.v1",
            &canonical_request_bytes,
        );
        let command_fingerprint = domain_fingerprint(
            "agents-os.local-owner.command.v1",
            &canonical_request_bytes,
        );
        if self
            .connection
            .query_row(
                "SELECT 1 FROM command_record WHERE proposal_fingerprint=?1",
                [&proposal_fingerprint],
                |_| Ok(()),
            )
            .optional()?
            .is_some()
        {
            return Ok(json!({
                "accepted": false,
                "resultCode": "PROPOSAL_ALREADY_COMMITTED",
                "proposalFingerprint": proposal_fingerprint,
            }));
        }

        let consent_kind = consent_kind_for(&command_type);
        let now = unix_ms()?;
        let replaced_commitment = self.pending.as_ref().map(|pending| {
            consent_commitment(&pending.challenge.prompt(pending.consent_kind))
        });
        let challenge =
            self.unique_challenge(consent_kind, replaced_commitment.as_deref())?;
        let replaced = self.pending.take().is_some();
        let prompt = challenge.prompt(consent_kind);
        self.pending = Some(PendingProposal {
            attachment_generation: generation,
            proposal_fingerprint: proposal_fingerprint.clone(),
            command_fingerprint,
            command_type: command_type.clone(),
            canonical_request_bytes,
            request: request.clone(),
            state_binding,
            consent_kind,
            challenge,
            expires_at_unix_ms: now + DEFAULT_PROPOSAL_TTL_SECONDS * 1000,
            failed_attempts: 0,
        });
        Ok(json!({
            "accepted": true,
            "authenticationAssurance": "LOCAL_OWNER_SESSION_ONLY",
            "consentPrompt": prompt,
            "expiresInSeconds": DEFAULT_PROPOSAL_TTL_SECONDS,
            "mutationType": command_type,
            "ownerConsentMode": "SPOKEN_CHALLENGE_V1",
            "proposalFingerprint": proposal_fingerprint,
            "replacedPendingProposal": replaced,
            "resultCode": "PROPOSAL_PREPARED",
        }))
    }

    pub fn submit_consent(
        &mut self,
        input: &Value,
        fault: LocalOwnerFault,
    ) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(
            input,
            &["attachmentGeneration", "ingress", "transcript"],
        )?;
        let generation = require_u64(object, "attachmentGeneration")?;
        if generation == 0 {
            return Err(LocalOwnerError::InvalidInput);
        }
        let ingress = require_string(object, "ingress", 64)?;
        let transcript = require_string(object, "transcript", 4096)?;
        if ![
            "TYPED_TEXT",
            "FINAL_VOICE_TRANSCRIPT",
            "PARTIAL_VOICE_TRANSCRIPT",
        ]
        .contains(&ingress)
        {
            return Err(LocalOwnerError::InvalidInput);
        }
        if ingress == "PARTIAL_VOICE_TRANSCRIPT" {
            return Ok(json!({
                "accepted": false,
                "resultCode": "PARTIAL_TRANSCRIPT_REJECTED"
            }));
        }

        let commitment = consent_commitment(transcript);
        if let Some(response) = replay_response(&self.connection, &commitment)? {
            self.pending = None;
            return Ok(json!({
                "accepted": true,
                "result": response,
                "resultCode": "REPLAYED_COMMITTED"
            }));
        }

        let Some(mut pending) = self.pending.take() else {
            return Ok(json!({
                "accepted": false,
                "resultCode": "NO_PENDING_PROPOSAL"
            }));
        };
        if pending.attachment_generation != generation {
            return Ok(json!({
                "accepted": false,
                "resultCode": "ATTACHMENT_GENERATION_MISMATCH"
            }));
        }
        if unix_ms()? > pending.expires_at_unix_ms {
            return Ok(json!({
                "accepted": false,
                "resultCode": "PROPOSAL_EXPIRED"
            }));
        }

        match parse_transcript(transcript, pending.consent_kind, &pending.challenge) {
            ConsentParse::Cancel => Ok(json!({
                "accepted": false,
                "resultCode": "PROPOSAL_CANCELLED"
            })),
            ConsentParse::Reject => {
                pending.failed_attempts += 1;
                if pending.failed_attempts >= 3 {
                    Ok(json!({
                        "accepted": false,
                        "attemptsRemaining": 0,
                        "resultCode": "PROPOSAL_INVALIDATED"
                    }))
                } else {
                    let attempts_remaining = 3 - pending.failed_attempts;
                    self.pending = Some(pending);
                    Ok(json!({
                        "accepted": false,
                        "attemptsRemaining": attempts_remaining,
                        "resultCode": "CONSENT_REJECTED"
                    }))
                }
            }
            ConsentParse::Approve => {
                let result = self.commit_pending(&pending, &commitment, fault)?;
                Ok(json!({
                    "accepted": true,
                    "result": result,
                    "resultCode": "COMMITTED"
                }))
            }
        }
    }

    pub fn query(&self, input: &Value) -> Result<Value, LocalOwnerError> {
        let object = require_exact_object(input, &["attachmentGeneration", "request"])?;
        let generation = require_u64(object, "attachmentGeneration")?;
        if generation == 0 {
            return Err(LocalOwnerError::InvalidInput);
        }
        let request = object.get("request").ok_or(LocalOwnerError::InvalidInput)?;
        let request_object = require_exact_object(request, &["operation", "query"])?;
        let operation = require_string(request_object, "operation", 64)?;
        let query = request_object
            .get("query")
            .ok_or(LocalOwnerError::InvalidInput)?;
        match operation {
            "QUERY_GOALS" => query_goals(&self.connection, query),
            "QUERY_TASKS" => query_tasks(&self.connection, query),
            _ => Err(LocalOwnerError::InvalidInput),
        }
    }

    fn unique_challenge(
        &self,
        kind: ConsentKind,
        excluded_commitment: Option<&str>,
    ) -> Result<Challenge, LocalOwnerError> {
        for _ in 0..MAX_PROPOSAL_GENERATION_ATTEMPTS {
            let challenge = generate_challenge()?;
            let commitment = consent_commitment(&challenge.prompt(kind));
            if excluded_commitment == Some(commitment.as_str()) {
                continue;
            }
            let exists = self
                .connection
                .query_row(
                    "SELECT 1 FROM owner_consent_replay_index WHERE consent_commitment=?1",
                    [&commitment],
                    |_| Ok(()),
                )
                .optional()?
                .is_some();
            if !exists {
                return Ok(challenge);
            }
        }
        Err(LocalOwnerError::RandomnessUnavailable)
    }

    fn unique_mmr_challenge(
        &self,
        consent_kind: ConsentKind,
    ) -> Result<Challenge, LocalOwnerError> {
        for _ in 0..MAX_PROPOSAL_GENERATION_ATTEMPTS {
            let challenge = generate_challenge()?;
            let commitment = consent_commitment(&challenge.prompt(consent_kind));
            let collides_with_pending = self.pending_mmr.values().any(|pending| {
                mmr_consent_kind(&pending.mutation_type)
                    .map(|kind| consent_commitment(&pending.challenge.prompt(kind)) == commitment)
                    .unwrap_or(true)
            });
            if !collides_with_pending {
                return Ok(challenge);
            }
        }
        Err(LocalOwnerError::RandomnessUnavailable)
    }

    fn commit_pending(
        &mut self,
        pending: &PendingProposal,
        commitment: &str,
        fault: LocalOwnerFault,
    ) -> Result<Value, LocalOwnerError> {
        if let Some(response) = replay_response(&self.connection, commitment)? {
            return Ok(response);
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let command_type = pending.command_type.as_str();
        let payload = pending.request["mutation"]["payload"].clone();
        validate_transition_preconditions(&transaction, command_type, &payload)?;
        if state_binding_for(&transaction, command_type, &payload)? != pending.state_binding {
            return Err(LocalOwnerError::TransitionRejected);
        }
        let commit = match command_type {
            "CREATE_GOAL_BUNDLE" => commit_create_goal_bundle(
                &transaction,
                pending,
                &payload,
                commitment,
            )?,
            "START_GOAL" | "PAUSE_GOAL" | "RESUME_GOAL"
            | "REQUEST_COMPLETION_REVIEW" | "CLOSE_GOAL_ACHIEVED" => {
                commit_goal_transition(&transaction, pending, &payload, commitment)?
            }
            "START_TASK" | "PAUSE_TASK" | "RESUME_TASK" => {
                commit_task_transition(&transaction, pending, &payload, commitment)?
            }
            "COMPLETE_TASK_MANUALLY" => {
                commit_manual_completion(&transaction, pending, &payload, commitment)?
            }
            _ => return Err(LocalOwnerError::InvalidInput),
        };
        if fault == LocalOwnerFault::AfterDomainWrites {
            return Err(LocalOwnerError::InjectedCrash);
        }
        verify_transaction_state(&transaction)?;
        if fault == LocalOwnerFault::AfterEvents {
            return Err(LocalOwnerError::InjectedCrash);
        }

        let canonical_response_bytes = canonical_value_bytes(&commit.result)?;
        let response_fingerprint = domain_fingerprint(
            "agents-os.local-owner.response.v1",
            &canonical_response_bytes,
        );
        transaction.execute(
            "INSERT INTO command_record(command_fingerprint,proposal_fingerprint,command_type,consent_commitment,canonical_request_bytes,canonical_response_bytes,response_fingerprint,first_event_sequence,last_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
            params![
                pending.command_fingerprint,
                pending.proposal_fingerprint,
                pending.command_type,
                commitment,
                pending.canonical_request_bytes,
                canonical_response_bytes,
                response_fingerprint,
                as_i64(commit.first_event_sequence)?,
                as_i64(commit.last_event_sequence)?
            ],
        )?;
        transaction.execute(
            "INSERT INTO owner_consent_replay_index(consent_commitment,proposal_fingerprint,command_fingerprint,response_fingerprint,canonical_response_bytes) VALUES(?1,?2,?3,?4,?5)",
            params![
                commitment,
                pending.proposal_fingerprint,
                pending.command_fingerprint,
                response_fingerprint,
                canonical_response_bytes
            ],
        )?;
        if fault == LocalOwnerFault::AfterReplayIndex {
            return Err(LocalOwnerError::InjectedCrash);
        }
        verify_transaction_state(&transaction)?;
        transaction.commit()?;
        if fault == LocalOwnerFault::AfterCommitBeforeResponse {
            return Err(LocalOwnerError::ResponseLostAfterCommit);
        }
        Ok(commit.result)
    }

    fn commit_mmr_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_record(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(existing.as_applied_result())
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        // P2-H defense in depth: an already-decided logical operation (DENIED /
        // BLOCKED_INDETERMINATE, or COMMITTED outside the record scan) must
        // never mutate again, even if a pending proposal reached commit.
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": if existing.operation_outcome == OUTCOME_COMMITTED {
                        "OPERATION_ALREADY_APPLIED_LOCALLY"
                    } else {
                        "MMR_OPERATION_OUTCOME_IMMUTABLE"
                    },
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        if matches!(
            pending.mutation_type.as_str(),
            "CREATE_COMMITMENT" | "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT"
        ) {
            return self.commit_commitment_mutation(pending, consent_commitment_value, fault);
        }
        match pending.mutation_type.as_str() {
            "CREATE_EVIDENCE" => {
                return self.commit_evidence_mutation(pending, consent_commitment_value, fault)
            }
            "CREATE_CANDIDATE" => {
                return self.commit_candidate_creation_mutation(
                    pending,
                    consent_commitment_value,
                    fault,
                )
            }
            "CREATE_SUMMARY" => {
                return self.commit_summary_mutation(pending, consent_commitment_value, fault)
            }
            "ADD_EVIDENCE"
                if mutation_fact_kind(
                    &self.connection,
                    &pending.mutation_type,
                    &pending.target_state_id,
                )? == CANDIDATE_FACT_KIND =>
            {
                return self.commit_candidate_evidence_mutation(
                    pending,
                    consent_commitment_value,
                    fault,
                )
            }
            _ => {}
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        let mutation_type = require_string(mutation_object, "mutationType", 32)?;
        if mutation_type != pending.mutation_type
            || ![
                "CREATE",
                "REVISE",
                "SUPERSEDE",
                "RETIRE",
                "ADD_EVIDENCE",
                "CREATE_COMMITMENT",
                "FULFILL_COMMITMENT",
                "RELEASE_COMMITMENT",
            ]
            .contains(&mutation_type)
        {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current = mmr_current_metadata(&transaction, &pending.target_state_id)?;
        let expected_current = mutation_object["expectedCurrentFingerprint"].as_str();
        let (revision, predecessor) = match (mutation_type, current) {
            ("CREATE", None) if expected_current.is_none() => (1_u64, None),
            ("REVISE" | "SUPERSEDE" | "RETIRE" | "ADD_EVIDENCE", Some((current_revision, current_fingerprint)))
                if expected_current == Some(current_fingerprint.as_str()) =>
            {
                (
                    current_revision
                        .checked_add(1)
                        .ok_or(LocalOwnerError::StateCorrupt)?,
                    Some(current_fingerprint),
                )
            }
            _ => return Err(LocalOwnerError::MmrCurrentConflict),
        };
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        enforce_mmr_derived_transition(
            &transaction,
            mutation_object,
            mutation_type,
            &pending.target_state_id,
        )?;
        let components = mutation_object["components"].clone();
        let authority = components["authority"]
            .as_object()
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
        let grant = authority["grant"]
            .as_object()
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
        let provenance = components["provenance"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let mutation_actor = provenance["mutationActor"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let authority_basis_ref = authority["authorityBasisRef"].clone();
        let grant_id = grant["grantId"].clone();
        let mutation_actor_ref = mutation_actor["ref"].clone();
        let next_sequence = next_event_sequence(&transaction)?;
        let previous_event_fingerprint = latest_event_fingerprint(&transaction)?;
        let state_value = json!({
            "components": components,
            "localAuthorization": {
                "authorityBasisRef": authority_basis_ref,
                "consentCommitment": consent_commitment_value,
                "grantId": grant_id,
                "mutationActorRef": mutation_actor_ref,
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_D_REVISION_SUPERSESSION_DERIVED_STATE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": mutation_type,
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": "MMR0_EXPLICIT_MUTATION_CORE_V4",
            "revision": revision,
            "stateId": pending.target_state_id,
        });
        validate_stored_mmr_core_state(&state_value)?;
        let canonical_state_bytes = canonical_value_bytes(&state_value)?;
        let fact_fingerprint_material = canonical_value_bytes(&json!({
            "factKind": "MMR_STATE_CORE",
            "logicalId": pending.target_state_id,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "value": state_value,
        }))?;
        let fact_fingerprint = domain_fingerprint(
            "agents-os.local-owner.fact.MMR_STATE_CORE.v1",
            &fact_fingerprint_material,
        );
        let fact_ref = format!(
            "fact:MMR_STATE_CORE:{}:{revision}",
            pending.target_state_id
        );
        let event_kind = match (revision == 1, mutation_type) {
            (true, _) => "MMR_STATE_CORE_CREATED",
            (false, "SUPERSEDE") => "MMR_STATE_CORE_SUPERSEDED",
            (false, "RETIRE") => "MMR_STATE_CORE_RETIRED",
            (false, "ADD_EVIDENCE") => "MMR_STATE_CORE_EVIDENCE_ADDED",
            (false, _) => "MMR_STATE_CORE_SUCCEEDED",
        };
        let event_value = json!({
            "aggregateRef": pending.target_state_id,
            "aggregateRevision": revision,
            "commandFingerprint": pending.operation_fingerprint,
            "eventKind": event_kind,
            "eventSequence": next_sequence,
            "factFingerprint": fact_fingerprint,
            "factRef": fact_ref,
            "predecessorEventFingerprint": previous_event_fingerprint,
        });
        let event_bytes = canonical_value_bytes(&event_value)?;
        let event_fingerprint = domain_fingerprint(
            "agents-os.local-owner.event.v1",
            &event_bytes,
        );
        transaction.execute(
            "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
            params![
                as_i64(next_sequence)?,
                format!("event:local-owner:{next_sequence}"),
                event_kind,
                pending.target_state_id,
                as_i64(revision)?,
                pending.operation_fingerprint,
                previous_event_fingerprint,
                event_bytes,
                event_fingerprint,
            ],
        )?;
        if fault == MmrCoreFault::AfterFirstCandidateComponent {
            return Err(LocalOwnerError::InjectedCrash);
        }
        let provenance = &mutation_object["components"]["provenance"];
        let provenance = provenance
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let subject = provenance["subject"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let subject_ref = provenance_string(subject, "ref", 200)?;
        transaction.execute(
            "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence) VALUES('MMR_STATE_CORE',?1,?2,?3,?4,?2,?5,?6,?7,?8)",
            params![
                pending.target_state_id,
                as_i64(revision)?,
                fact_ref,
                subject_ref,
                canonical_state_bytes,
                fact_fingerprint,
                predecessor,
                as_i64(next_sequence)?,
            ],
        )?;
        if fault == MmrCoreFault::AfterAllCandidateComponents {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if revision == 1 {
            transaction.execute(
                "INSERT INTO current_pointer(fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence) VALUES('MMR_STATE_CORE',?1,1,?2,?3,1,?4)",
                params![pending.target_state_id, fact_ref, fact_fingerprint, as_i64(next_sequence)?],
            )?;
        } else {
            let predecessor = predecessor
                .as_deref()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let updated = transaction.execute(
                "UPDATE current_pointer SET current_fact_revision=?1,current_fact_ref=?2,current_fact_fingerprint=?3,pointer_version=?1,updated_event_sequence=?4 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?5 AND current_fact_revision=?6 AND current_fact_fingerprint=?7 AND pointer_version=?6",
                params![
                    as_i64(revision)?,
                    fact_ref,
                    fact_fingerprint,
                    as_i64(next_sequence)?,
                    pending.target_state_id,
                    as_i64(revision - 1)?,
                    predecessor,
                ],
            )?;
            if updated != 1 {
                return Err(LocalOwnerError::MmrCurrentConflict);
            }
        }
        if fault == MmrCoreFault::AfterAtomicPublication {
            // P2-H A3-V4: the mutation entered the dangerous commit window and
            // its commit state cannot be safely determined. Roll back the
            // atomic bundle, durably journal BLOCKED_INDETERMINATE, then crash.
            drop(transaction);
            self.journal_indeterminate_outcome(
                &pending.operation_id,
                &pending.operation_fingerprint,
                &pending.request["mutation"],
            )?;
            return Err(LocalOwnerError::InjectedCrash);
        }
        verify_transaction_state(&transaction)?;
        let visible = read_mmr_current(&transaction, &pending.target_state_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        if visible["factFingerprint"] != fact_fingerprint {
            return Err(LocalOwnerError::StateCorrupt);
        }
        transaction.commit()?;
        if fault == MmrCoreFault::AfterTransactionBeforeResponse {
            return Err(LocalOwnerError::ResponseLostAfterCommit);
        }
        Ok(json!({
            "localTransactionApplied": true,
            "mmrCommittedGuaranteeProven": false,
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "predecessorFactFingerprint": predecessor,
            "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF",
            "revision": revision,
            "stateId": pending.target_state_id,
            "successorFactFingerprint": fact_fingerprint,
        }))
    }

    fn commit_commitment_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": "OPERATION_ALREADY_APPLIED_LOCALLY",
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        let mutation_type = require_string(mutation_object, "mutationType", 32)?;
        if mutation_type != pending.mutation_type
            || !["CREATE_COMMITMENT", "FULFILL_COMMITMENT", "RELEASE_COMMITMENT"]
                .contains(&mutation_type)
        {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current = commitment_current_metadata(&transaction, &pending.target_state_id)?;
        let expected_current = mutation_object["expectedCurrentFingerprint"].as_str();
        let (revision, predecessor) = match (mutation_type, current) {
            ("CREATE_COMMITMENT", None) if expected_current.is_none() => (1_u64, None),
            (
                "FULFILL_COMMITMENT" | "RELEASE_COMMITMENT",
                Some((current_revision, current_fingerprint)),
            ) if expected_current == Some(current_fingerprint.as_str()) =>
            {
                (
                    current_revision
                        .checked_add(1)
                        .ok_or(LocalOwnerError::StateCorrupt)?,
                    Some(current_fingerprint),
                )
            }
            _ => return Err(LocalOwnerError::MmrCurrentConflict),
        };
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        validate_mmr_commitment_transition(&transaction, mutation_object)?;
        let components = mutation_object["components"].clone();
        let authority = components["authority"]
            .as_object()
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
        let grant = authority["grant"]
            .as_object()
            .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
        let provenance = components["provenance"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let mutation_actor = provenance["mutationActor"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let authority_basis_ref = authority["authorityBasisRef"].clone();
        let grant_id = grant["grantId"].clone();
        let mutation_actor_ref = mutation_actor["ref"].clone();
        let mut next_sequence = next_event_sequence(&transaction)?;
        let previous_event_fingerprint = latest_event_fingerprint(&transaction)?;
        let state_value = json!({
            "components": components,
            "localAuthorization": {
                "authorityBasisRef": authority_basis_ref,
                "consentCommitment": consent_commitment_value,
                "grantId": grant_id,
                "mutationActorRef": mutation_actor_ref,
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_E_COMMITMENT_LIFECYCLE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": mutation_type,
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": COMMITMENT_PROTOCOL,
            "revision": revision,
            "stateId": pending.target_state_id,
        });
        validate_stored_mmr_commitment_state(&state_value)?;
        let canonical_state_bytes = canonical_value_bytes(&state_value)?;
        let fact_fingerprint_material = canonical_value_bytes(&json!({
            "factKind": COMMITMENT_FACT_KIND,
            "logicalId": pending.target_state_id,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "value": state_value,
        }))?;
        let fact_fingerprint = domain_fingerprint(
            &format!("agents-os.local-owner.fact.{COMMITMENT_FACT_KIND}.v1"),
            &fact_fingerprint_material,
        );
        let fact_ref = format!(
            "fact:{COMMITMENT_FACT_KIND}:{}:{revision}",
            pending.target_state_id
        );
        let event_kind = match mutation_type {
            "CREATE_COMMITMENT" => "MMR_COMMITMENT_CORE_CREATED",
            "FULFILL_COMMITMENT" => "MMR_COMMITMENT_CORE_FULFILLED",
            "RELEASE_COMMITMENT" => "MMR_COMMITMENT_CORE_RELEASED",
            _ => return Err(LocalOwnerError::MmrMutationNotAuthorized),
        };
        let event_value = json!({
            "aggregateRef": pending.target_state_id,
            "aggregateRevision": revision,
            "commandFingerprint": pending.operation_fingerprint,
            "eventKind": event_kind,
            "eventSequence": next_sequence,
            "factFingerprint": fact_fingerprint,
            "factRef": fact_ref,
            "predecessorEventFingerprint": previous_event_fingerprint,
        });
        let event_bytes = canonical_value_bytes(&event_value)?;
        let event_fingerprint = domain_fingerprint(
            "agents-os.local-owner.event.v1",
            &event_bytes,
        );
        transaction.execute(
            "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
            params![
                as_i64(next_sequence)?,
                format!("event:local-owner:{next_sequence}"),
                event_kind,
                pending.target_state_id,
                as_i64(revision)?,
                pending.operation_fingerprint,
                previous_event_fingerprint,
                event_bytes,
                event_fingerprint,
            ],
        )?;
        next_sequence += 1;
        let provenance_value = &mutation_object["components"]["provenance"];
        let provenance_object = provenance_value
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let subject = provenance_object["subject"]
            .as_object()
            .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
        let subject_ref = provenance_string(subject, "ref", 200)?;
        transaction.execute(
            "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?3,?6,?7,?8,?9)",
            params![
                COMMITMENT_FACT_KIND,
                pending.target_state_id,
                as_i64(revision)?,
                fact_ref,
                subject_ref,
                canonical_state_bytes,
                fact_fingerprint,
                predecessor,
                as_i64(next_sequence - 1)?,
            ],
        )?;
        if revision == 1 {
            transaction.execute(
                "INSERT INTO current_pointer(fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence) VALUES(?1,?2,1,?3,?4,1,?5)",
                params![
                    COMMITMENT_FACT_KIND,
                    pending.target_state_id,
                    fact_ref,
                    fact_fingerprint,
                    as_i64(next_sequence - 1)?
                ],
            )?;
        } else {
            let predecessor = predecessor
                .as_deref()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let updated = transaction.execute(
                "UPDATE current_pointer SET current_fact_revision=?1,current_fact_ref=?2,current_fact_fingerprint=?3,pointer_version=?1,updated_event_sequence=?4 WHERE fact_kind=?5 AND logical_id=?6 AND current_fact_revision=?7 AND current_fact_fingerprint=?8 AND pointer_version=?7",
                params![
                    as_i64(revision)?,
                    fact_ref,
                    fact_fingerprint,
                    as_i64(next_sequence - 1)?,
                    COMMITMENT_FACT_KIND,
                    pending.target_state_id,
                    as_i64(revision - 1)?,
                    predecessor,
                ],
            )?;
            if updated != 1 {
                return Err(LocalOwnerError::MmrCurrentConflict);
            }
        }
        // The committed operation outcome is part of the same atomic bundle.
        let basis_ref = authority["authorityBasisRef"]
            .as_str()
            .unwrap_or("authority-basis:unresolved");
        let basis_type = authority["authorityBasisType"]
            .as_str()
            .unwrap_or("UNRESOLVED");
        journal_operation_outcome(
            &transaction,
            &mut next_sequence,
            &pending.operation_id,
            &pending.operation_fingerprint,
            Some(basis_ref),
            Some(basis_type),
            predecessor.as_deref(),
            "COMMITTED",
            Some(&fact_fingerprint),
        )?;
        if fault == MmrCoreFault::AfterAtomicPublication {
            return Err(LocalOwnerError::InjectedCrash);
        }
        verify_transaction_state(&transaction)?;
        let visible = read_commitment_current(&transaction, &pending.target_state_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        if visible["factFingerprint"] != fact_fingerprint {
            return Err(LocalOwnerError::StateCorrupt);
        }
        transaction.commit()?;
        if fault == MmrCoreFault::AfterTransactionBeforeResponse {
            return Err(LocalOwnerError::ResponseLostAfterCommit);
        }
        Ok(json!({
            "commitmentId": pending.target_state_id,
            "lifecycleState": match mutation_type {
                "CREATE_COMMITMENT" => COMMITMENT_LIFECYCLE_ACTIVE,
                "FULFILL_COMMITMENT" => COMMITMENT_LIFECYCLE_FULFILLED,
                "RELEASE_COMMITMENT" => COMMITMENT_LIFECYCLE_RELEASED,
                _ => unreachable!(),
            },
            "localTransactionApplied": true,
            "mmrCommittedGuaranteeProven": false,
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "predecessorFactFingerprint": predecessor,
            "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF",
            "revision": revision,
            "stateId": pending.target_state_id,
            "successorFactFingerprint": fact_fingerprint,
        }))
    }

    /// Publishes the mechanical parts of a P2-F fact commit inside the existing
    /// single-writer transaction: event, canonical fact, Current CAS, immutable
    /// operation outcome journal, transaction verification, and commit.
    #[allow(clippy::too_many_arguments)]
    fn publish_kind_fact(
        transaction: Transaction<'_>,
        pending: &PendingMmrProposal,
        fact_kind: &str,
        revision: u64,
        predecessor: Option<&str>,
        subject_ref: &str,
        state_value: &Value,
        event_kind: &str,
        authority_basis_ref: &str,
        authority_basis_type: &str,
        fault: MmrCoreFault,
        validate_state: fn(&Value) -> Result<(), LocalOwnerError>,
        read_visible: fn(&Connection, &str) -> Result<Option<Value>, LocalOwnerError>,
    ) -> Result<Value, LocalOwnerError> {
        validate_state(state_value)?;
        let canonical_state_bytes = canonical_value_bytes(state_value)?;
        let fact_fingerprint_material = canonical_value_bytes(&json!({
            "factKind": fact_kind,
            "logicalId": pending.target_state_id,
            "predecessorFactFingerprint": predecessor,
            "revision": revision,
            "value": state_value,
        }))?;
        let fact_fingerprint = domain_fingerprint(
            &format!("agents-os.local-owner.fact.{fact_kind}.v1"),
            &fact_fingerprint_material,
        );
        let fact_ref = format!("fact:{fact_kind}:{}:{revision}", pending.target_state_id);
        let mut next_sequence = next_event_sequence(&transaction)?;
        let previous_event_fingerprint = latest_event_fingerprint(&transaction)?;
        let event_value = json!({
            "aggregateRef": pending.target_state_id,
            "aggregateRevision": revision,
            "commandFingerprint": pending.operation_fingerprint,
            "eventKind": event_kind,
            "eventSequence": next_sequence,
            "factFingerprint": fact_fingerprint,
            "factRef": fact_ref,
            "predecessorEventFingerprint": previous_event_fingerprint,
        });
        let event_bytes = canonical_value_bytes(&event_value)?;
        let event_fingerprint = domain_fingerprint(
            "agents-os.local-owner.event.v1",
            &event_bytes,
        );
        transaction.execute(
            "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
            params![
                as_i64(next_sequence)?,
                format!("event:local-owner:{next_sequence}"),
                event_kind,
                pending.target_state_id,
                as_i64(revision)?,
                pending.operation_fingerprint,
                previous_event_fingerprint,
                event_bytes,
                event_fingerprint,
            ],
        )?;
        next_sequence += 1;
        transaction.execute(
            "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?3,?6,?7,?8,?9)",
            params![
                fact_kind,
                pending.target_state_id,
                as_i64(revision)?,
                fact_ref,
                subject_ref,
                canonical_state_bytes,
                fact_fingerprint,
                predecessor,
                as_i64(next_sequence - 1)?,
            ],
        )?;
        if revision == 1 {
            transaction.execute(
                "INSERT INTO current_pointer(fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence) VALUES(?1,?2,1,?3,?4,1,?5)",
                params![
                    fact_kind,
                    pending.target_state_id,
                    fact_ref,
                    fact_fingerprint,
                    as_i64(next_sequence - 1)?
                ],
            )?;
        } else {
            let predecessor =
                predecessor.ok_or(LocalOwnerError::StateCorrupt)?;
            let updated = transaction.execute(
                "UPDATE current_pointer SET current_fact_revision=?1,current_fact_ref=?2,current_fact_fingerprint=?3,pointer_version=?1,updated_event_sequence=?4 WHERE fact_kind=?5 AND logical_id=?6 AND current_fact_revision=?7 AND current_fact_fingerprint=?8 AND pointer_version=?7",
                params![
                    as_i64(revision)?,
                    fact_ref,
                    fact_fingerprint,
                    as_i64(next_sequence - 1)?,
                    fact_kind,
                    pending.target_state_id,
                    as_i64(revision - 1)?,
                    predecessor,
                ],
            )?;
            if updated != 1 {
                return Err(LocalOwnerError::MmrCurrentConflict);
            }
        }
        journal_operation_outcome(
            &transaction,
            &mut next_sequence,
            &pending.operation_id,
            &pending.operation_fingerprint,
            Some(authority_basis_ref),
            Some(authority_basis_type),
            predecessor,
            "COMMITTED",
            Some(&fact_fingerprint),
        )?;
        if fault == MmrCoreFault::AfterAtomicPublication {
            return Err(LocalOwnerError::InjectedCrash);
        }
        verify_transaction_state(&transaction)?;
        let visible = read_visible(&transaction, &pending.target_state_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        if visible["factFingerprint"] != fact_fingerprint {
            return Err(LocalOwnerError::StateCorrupt);
        }
        transaction.commit()?;
        if fault == MmrCoreFault::AfterTransactionBeforeResponse {
            return Err(LocalOwnerError::ResponseLostAfterCommit);
        }
        Ok(json!({
            "localTransactionApplied": true,
            "mmrCommittedGuaranteeProven": false,
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "predecessorFactFingerprint": predecessor,
            "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF",
            "revision": revision,
            "stateId": pending.target_state_id,
            "successorFactFingerprint": fact_fingerprint,
        }))
    }

    /// Admit a durable evidence artifact with its origin/derivation graph.
    fn commit_evidence_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": "OPERATION_ALREADY_APPLIED_LOCALLY",
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        if require_string(mutation_object, "mutationType", 32)? != "CREATE_EVIDENCE" {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current =
            kind_current_metadata(&transaction, EVIDENCE_FACT_KIND, &pending.target_state_id)?;
        if current.is_some() || !mutation_object["expectedCurrentFingerprint"].is_null() {
            return Err(LocalOwnerError::MmrCurrentConflict);
        }
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        validate_mmr_evidence_identity(&transaction, mutation_object)?;
        let (components, authority, grant, _provenance, mutation_actor, subject_ref, basis_ref, basis_type) =
            p2f_bundle_parts(mutation_object)?;
        let content = mutation_object["components"]["content"]["value"].clone();
        let state_value = json!({
            "components": components,
            "evidenceIdentity": {
                "artifactAvailability": content["artifactAvailability"],
                "derivationAncestors": content["derivationAncestors"],
                "evidenceId": pending.target_state_id,
                "originRef": content["originRef"],
            },
            "localAuthorization": {
                "authorityBasisRef": authority["authorityBasisRef"],
                "consentCommitment": consent_commitment_value,
                "grantId": grant["grantId"],
                "mutationActorRef": mutation_actor["ref"],
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_F_CANDIDATE_AND_EVIDENCE_LIFECYCLE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": "CREATE_EVIDENCE",
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": EVIDENCE_PROTOCOL,
            "revision": 1,
            "stateId": pending.target_state_id,
        });
        let result = Self::publish_kind_fact(
            transaction,
            pending,
            EVIDENCE_FACT_KIND,
            1,
            None,
            &subject_ref,
            &state_value,
            "MMR_EVIDENCE_CORE_CREATED",
            &basis_ref,
            &basis_type,
            fault,
            validate_stored_mmr_evidence_state,
            read_evidence_current,
        )?;
        Ok(merge_result(result, json!({"evidenceId": pending.target_state_id})))
    }

    /// Create a Candidate whose status is exactly CANDIDATE.  The Candidate's
    /// creation can never be used to validate itself.
    fn commit_candidate_creation_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": "OPERATION_ALREADY_APPLIED_LOCALLY",
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        if require_string(mutation_object, "mutationType", 32)? != "CREATE_CANDIDATE" {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current =
            kind_current_metadata(&transaction, CANDIDATE_FACT_KIND, &pending.target_state_id)?;
        if current.is_some() || !mutation_object["expectedCurrentFingerprint"].is_null() {
            return Err(LocalOwnerError::MmrCurrentConflict);
        }
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        validate_mmr_candidate_creation(&transaction, mutation_object)?;
        let (components, authority, grant, _provenance, mutation_actor, subject_ref, basis_ref, basis_type) =
            p2f_bundle_parts(mutation_object)?;
        let content = mutation_object["components"]["content"]["value"].clone();
        let state_value = json!({
            "candidateState": {
                "candidateId": pending.target_state_id,
                "motivatingEvidenceRef": content["motivatingEvidenceRef"],
                "originRef": format!("origin:candidate:{}", pending.target_state_id),
                "status": CANDIDATE_STATUS_CANDIDATE,
                "supportingEvidenceFingerprint": Value::Null,
                "supportingEvidenceRef": Value::Null,
            },
            "components": components,
            "localAuthorization": {
                "authorityBasisRef": authority["authorityBasisRef"],
                "consentCommitment": consent_commitment_value,
                "grantId": grant["grantId"],
                "mutationActorRef": mutation_actor["ref"],
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_F_CANDIDATE_AND_EVIDENCE_LIFECYCLE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": "CREATE_CANDIDATE",
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": CANDIDATE_PROTOCOL,
            "revision": 1,
            "stateId": pending.target_state_id,
        });
        let result = Self::publish_kind_fact(
            transaction,
            pending,
            CANDIDATE_FACT_KIND,
            1,
            None,
            &subject_ref,
            &state_value,
            "MMR_CANDIDATE_CORE_CREATED",
            &basis_ref,
            &basis_type,
            fault,
            validate_stored_mmr_candidate_state,
            read_candidate_current,
        )?;
        Ok(merge_result(result, json!({"candidateId": pending.target_state_id, "status": CANDIDATE_STATUS_CANDIDATE})))
    }

    /// Create a derived Summary bound to an admitted evidence fact.
    fn commit_summary_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": "OPERATION_ALREADY_APPLIED_LOCALLY",
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        if require_string(mutation_object, "mutationType", 32)? != "CREATE_SUMMARY" {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current =
            kind_current_metadata(&transaction, SUMMARY_FACT_KIND, &pending.target_state_id)?;
        if current.is_some() || !mutation_object["expectedCurrentFingerprint"].is_null() {
            return Err(LocalOwnerError::MmrCurrentConflict);
        }
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        validate_mmr_summary_creation(&transaction, mutation_object)?;
        let (components, authority, grant, _provenance, mutation_actor, subject_ref, basis_ref, basis_type) =
            p2f_bundle_parts(mutation_object)?;
        let plane = mutation_object["components"]["plane"]
            .as_object()
            .ok_or(LocalOwnerError::InvalidInput)?;
        let support_ref = optional_plane_string(plane, "sharedEventStateId")?
            .ok_or(LocalOwnerError::MmrSummarySelfEvidenceRejected)?;
        let state_value = json!({
            "components": components,
            "localAuthorization": {
                "authorityBasisRef": authority["authorityBasisRef"],
                "consentCommitment": consent_commitment_value,
                "grantId": grant["grantId"],
                "mutationActorRef": mutation_actor["ref"],
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_F_CANDIDATE_AND_EVIDENCE_LIFECYCLE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": "CREATE_SUMMARY",
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": SUMMARY_PROTOCOL,
            "revision": 1,
            "stateId": pending.target_state_id,
            "summaryState": {
                "status": SUMMARY_LIFECYCLE_DERIVED,
                "summaryId": pending.target_state_id,
                "supportEvidenceRef": support_ref,
            },
        });
        let result = Self::publish_kind_fact(
            transaction,
            pending,
            SUMMARY_FACT_KIND,
            1,
            None,
            &subject_ref,
            &state_value,
            "MMR_SUMMARY_CORE_CREATED",
            &basis_ref,
            &basis_type,
            fault,
            validate_stored_mmr_summary_state,
            read_summary_current,
        )?;
        Ok(merge_result(result, json!({"summaryId": pending.target_state_id, "supportEvidenceRef": support_ref})))
    }

    /// Explicit ADD_EVIDENCE transition on a Candidate: only a truly distinct,
    /// later, independent evidence artifact can lawfully change Candidate state.
    fn commit_candidate_evidence_mutation(
        &mut self,
        pending: &PendingMmrProposal,
        consent_commitment_value: &str,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        if fault == MmrCoreFault::AfterAuthorityBeforeTransaction {
            return Err(LocalOwnerError::InjectedCrash);
        }
        if let Some(existing) = mmr_operation_outcome(&self.connection, &pending.operation_id)? {
            return if existing.operation_fingerprint == pending.operation_fingerprint {
                Ok(json!({
                    "localTransactionApplied": false,
                    "mmrCommittedGuaranteeProven": false,
                    "operationFingerprint": pending.operation_fingerprint,
                    "operationId": pending.operation_id,
                    "operationOutcome": existing.operation_outcome,
                    "resultCode": "OPERATION_ALREADY_APPLIED_LOCALLY",
                    "stateId": existing.state_id,
                }))
            } else {
                Err(LocalOwnerError::MmrOperationIdConflict)
            };
        }
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mutation = &pending.request["mutation"];
        let mutation_object = validate_mmr_core_mutation(mutation, true)?;
        if require_string(mutation_object, "mutationType", 32)? != "ADD_EVIDENCE" {
            return Err(LocalOwnerError::MmrMutationNotAuthorized);
        }
        let current =
            read_candidate_current(&transaction, &pending.target_state_id)?;
        let expected_current = mutation_object["expectedCurrentFingerprint"].as_str();
        let (revision, predecessor) = match current {
            Some(current) => {
                let current_revision = current["revision"]
                    .as_u64()
                    .ok_or(LocalOwnerError::StateCorrupt)?;
                let current_fingerprint = current["factFingerprint"]
                    .as_str()
                    .ok_or(LocalOwnerError::StateCorrupt)?;
                if expected_current != Some(current_fingerprint) {
                    return Err(LocalOwnerError::MmrCurrentConflict);
                }
                (
                    current_revision
                        .checked_add(1)
                        .ok_or(LocalOwnerError::StateCorrupt)?,
                    Some(current_fingerprint.to_owned()),
                )
            }
            None => return Err(LocalOwnerError::MmrCurrentConflict),
        };
        validate_mmr_plane_transition(&transaction, mutation_object)?;
        validate_mmr_candidate_evidence_transition(&transaction, mutation_object)?;
        let (components, authority, grant, _provenance, mutation_actor, subject_ref, basis_ref, basis_type) =
            p2f_bundle_parts(mutation_object)?;
        let content = mutation_object["components"]["content"]["value"]
            .as_object()
            .ok_or(LocalOwnerError::InvalidInput)?;
        let support_ref = require_nonempty_string(content, "supportingEvidenceRef", 200)?;
        let evidence_current =
            read_evidence_current(&transaction, support_ref)?.ok_or(LocalOwnerError::StateCorrupt)?;
        let evidence_fingerprint = evidence_current["factFingerprint"]
            .as_str()
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let current_candidate = read_candidate_current(&transaction, &pending.target_state_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let current_state = &current_candidate["state"];
        let current_candidate_state = current_state["candidateState"]
            .as_object()
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let lifecycle = mutation_object["components"]["lifecycle"]["lifecycleState"]
            .as_str()
            .ok_or(LocalOwnerError::InvalidInput)?;
        let state_value = json!({
            "candidateState": {
                "candidateId": pending.target_state_id,
                "motivatingEvidenceRef": current_candidate_state["motivatingEvidenceRef"],
                "originRef": current_candidate_state["originRef"],
                "status": lifecycle,
                "supportingEvidenceFingerprint": evidence_fingerprint,
                "supportingEvidenceRef": support_ref,
            },
            "components": components,
            "localAuthorization": {
                "authorityBasisRef": authority["authorityBasisRef"],
                "consentCommitment": consent_commitment_value,
                "grantId": grant["grantId"],
                "mutationActorRef": mutation_actor["ref"],
                "right": "MMR_DURABLE_STATE_MUTATION",
                "scope": "P2_F_CANDIDATE_AND_EVIDENCE_LIFECYCLE_AUTHORITY"
            },
            "localOutcome": {
                "mmrCommittedGuaranteeProven": false,
                "resultCode": "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
            },
            "mutationType": "ADD_EVIDENCE",
            "operationFingerprint": pending.operation_fingerprint,
            "operationId": pending.operation_id,
            "protocol": CANDIDATE_PROTOCOL,
            "revision": revision,
            "stateId": pending.target_state_id,
        });
        let result = Self::publish_kind_fact(
            transaction,
            pending,
            CANDIDATE_FACT_KIND,
            revision,
            predecessor.as_deref(),
            &subject_ref,
            &state_value,
            "MMR_CANDIDATE_CORE_EVIDENCE_ADDED",
            &basis_ref,
            &basis_type,
            fault,
            validate_stored_mmr_candidate_state,
            read_candidate_current,
        )?;
        Ok(merge_result(
            result,
            json!({
                "candidateId": pending.target_state_id,
                "status": lifecycle,
                "supportingEvidenceFingerprint": evidence_fingerprint,
                "supportingEvidenceRef": support_ref,
            }),
        ))
    }
}


/// Extracts the atomic-bundle parts shared by every P2-F commit path.
#[allow(clippy::type_complexity)]
fn p2f_bundle_parts<'a>(
    mutation_object: &'a Map<String, Value>,
) -> Result<
    (
        Value,
        &'a Map<String, Value>,
        &'a Map<String, Value>,
        &'a Map<String, Value>,
        &'a Map<String, Value>,
        String,
        String,
        String,
    ),
    LocalOwnerError,
> {
    let components = mutation_object["components"]
        .as_object()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let authority = components["authority"]
        .as_object()
        .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
    let grant = authority["grant"]
        .as_object()
        .ok_or(LocalOwnerError::MmrAuthorityScopeDenied)?;
    let provenance = components["provenance"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let mutation_actor = provenance["mutationActor"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let subject = provenance["subject"]
        .as_object()
        .ok_or(LocalOwnerError::MmrProvenanceRequired)?;
    let subject_ref = provenance_string(subject, "ref", 200)?.to_owned();
    let basis_ref = authority["authorityBasisRef"]
        .as_str()
        .unwrap_or("authority-basis:unresolved")
        .to_owned();
    let basis_type = authority["authorityBasisType"]
        .as_str()
        .unwrap_or("UNRESOLVED")
        .to_owned();
    Ok((
        mutation_object["components"].clone(),
        authority,
        grant,
        provenance,
        mutation_actor,
        subject_ref,
        basis_ref,
        basis_type,
    ))
}

fn merge_result(mut base: Value, extra: Value) -> Value {
    if let Some(base_map) = base.as_object_mut() {
        if let Some(extra_map) = extra.as_object() {
            for (key, value) in extra_map {
                base_map.insert(key.clone(), value.clone());
            }
        }
    }
    base
}

pub fn inspect_continuity(
    database_path: &std::path::Path,
) -> Result<LocalContinuitySnapshot, LocalOwnerError> {
    match std::fs::metadata(database_path) {
        Ok(metadata) if metadata.len() == 0 => return Ok(LocalContinuitySnapshot::empty()),
        Ok(_) => {}
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Ok(LocalContinuitySnapshot::empty());
        }
        Err(error) => return Err(LocalOwnerError::Io(error)),
    }
    let connection = Connection::open_with_flags(
        database_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?;
    connection.busy_timeout(std::time::Duration::ZERO)?;
    connection.pragma_update(None, "foreign_keys", "ON")?;
    // This check intentionally precedes generic schema/FK verification so a
    // missing or inconsistent MMR Current target fails with the deterministic
    // Current-identity code before admission can publish ACTIVE.
    verify_mmr_current_pointer_integrity(&connection)?;
    schema::verify(&connection)?;
    verify_event_and_epoch_chains(&connection)?;
    verify_mmr_transition_history_integrity(&connection)?;
    verify_commitment_pointer_integrity(&connection)?;
    verify_p2f_kind_integrity(&connection)?;
    continuity_snapshot_on(&connection)
}

fn continuity_snapshot_on(
    connection: &Connection,
) -> Result<LocalContinuitySnapshot, LocalOwnerError> {
    let resident_id: String = connection.query_row(
        "SELECT resident_id FROM resident_identity",
        [],
        |row| row.get(0),
    )?;
    let mut event_fingerprints = BTreeMap::new();
    let mut event_statement = connection.prepare(
        "SELECT event_sequence,event_fingerprint FROM event ORDER BY event_sequence",
    )?;
    let event_rows = event_statement.query_map([], |row| {
        Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?))
    })?;
    for row in event_rows {
        let (sequence, fingerprint) = row?;
        event_fingerprints.insert(as_u64(sequence)?, fingerprint);
    }
    let (&latest_event_sequence, latest_event_fingerprint) = event_fingerprints
        .last_key_value()
        .ok_or(LocalOwnerError::EventChainBroken)?;

    let mut authority_anchors = Vec::new();
    let mut statement = connection.prepare(
        "SELECT a.authority_epoch,a.incarnation_id,a.epoch_fingerprint,a.created_event_sequence,e.event_fingerprint FROM resident_authority_epoch a JOIN event e ON e.event_sequence=a.created_event_sequence ORDER BY a.authority_epoch",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, i64>(3)?,
            row.get::<_, String>(4)?,
        ))
    })?;
    for row in rows {
        let (epoch, incarnation_id, epoch_fingerprint, event_sequence, event_fingerprint) = row?;
        authority_anchors.push(ContinuityAnchor {
            resident_id: resident_id.clone(),
            authority_epoch: as_u64(epoch)?,
            incarnation_id,
            epoch_fingerprint,
            event_sequence: as_u64(event_sequence)?,
            event_fingerprint,
        });
    }
    let latest_authority = authority_anchors
        .last()
        .cloned()
        .ok_or(LocalOwnerError::EpochChainBroken)?;
    let current = ContinuityAnchor {
        event_sequence: latest_event_sequence,
        event_fingerprint: latest_event_fingerprint.clone(),
        ..latest_authority
    };
    Ok(LocalContinuitySnapshot {
        current: Some(current),
        authority_anchors,
        event_fingerprints,
    })
}

fn validate_operation_command_pair(operation: &str, command_type: &str) -> Result<(), LocalOwnerError> {
    let allowed = match operation {
        "PROPOSE_GOAL_MUTATION" => &schema::COMMAND_TYPES[..6],
        "PROPOSE_TASK_MUTATION" => &schema::COMMAND_TYPES[6..],
        _ => return Err(LocalOwnerError::InvalidInput),
    };
    if allowed.contains(&command_type) {
        Ok(())
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn consent_kind_for(command_type: &str) -> ConsentKind {
    match command_type {
        "CREATE_GOAL_BUNDLE" => ConsentKind::Create,
        "COMPLETE_TASK_MANUALLY" => ConsentKind::Complete,
        "CLOSE_GOAL_ACHIEVED" => ConsentKind::Close,
        _ => ConsentKind::Change,
    }
}

fn validate_mutation_payload(
    connection: &Connection,
    command_type: &str,
    payload: &Value,
) -> Result<(), LocalOwnerError> {
    match command_type {
        "CREATE_GOAL_BUNDLE" => validate_create_payload(payload),
        "START_GOAL" | "PAUSE_GOAL" | "RESUME_GOAL"
        | "REQUEST_COMPLETION_REVIEW" | "CLOSE_GOAL_ACHIEVED" => {
            let object = require_exact_object(payload, &["goalId"])?;
            let goal_id = require_string(object, "goalId", 200)?;
            require_goal_exists(connection, goal_id)?;
            Ok(())
        }
        "START_TASK" => {
            let object = require_exact_object(payload, &["activityContext", "taskId"])?;
            let task_id = require_string(object, "taskId", 200)?;
            require_task_exists(connection, task_id)?;
            require_nonempty_string(object, "activityContext", 2000)?;
            Ok(())
        }
        "PAUSE_TASK" | "RESUME_TASK" => {
            let object = require_exact_object(payload, &["taskId"])?;
            let task_id = require_string(object, "taskId", 200)?;
            require_task_exists(connection, task_id)?;
            Ok(())
        }
        "COMPLETE_TASK_MANUALLY" => {
            let object = require_exact_object(payload, &["resultSummary", "taskId"])?;
            let task_id = require_string(object, "taskId", 200)?;
            require_task_exists(connection, task_id)?;
            require_nonempty_string(object, "resultSummary", 4000)?;
            Ok(())
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn validate_transition_preconditions(
    connection: &Connection,
    command_type: &str,
    payload: &Value,
) -> Result<(), LocalOwnerError> {
    match command_type {
        "CREATE_GOAL_BUNDLE" => Ok(()),
        "START_GOAL" | "PAUSE_GOAL" | "RESUME_GOAL"
        | "REQUEST_COMPLETION_REVIEW" | "CLOSE_GOAL_ACHIEVED" => {
            let goal_id = payload["goalId"]
                .as_str()
                .ok_or(LocalOwnerError::InvalidInput)?;
            let current = current_state(connection, "GOAL_STATE", goal_id)?;
            let status = current.value["status"]
                .as_str()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            match command_type {
                "START_GOAL" if status == "READY" => Ok(()),
                "PAUSE_GOAL" if ["READY", "ACTIVE"].contains(&status) => {
                    let blocking = active_or_verifying_task_count(connection, goal_id)?;
                    if blocking == 0 {
                        Ok(())
                    } else {
                        Err(LocalOwnerError::TransitionRejected)
                    }
                }
                "RESUME_GOAL" if status == "PAUSED" => {
                    current.value["priorStatus"]
                        .as_str()
                        .filter(|value| ["READY", "ACTIVE"].contains(value))
                        .ok_or(LocalOwnerError::StateCorrupt)?;
                    Ok(())
                }
                "REQUEST_COMPLETION_REVIEW" if status == "ACTIVE" => {
                    require_selected_tasks_done(connection, goal_id)
                }
                "CLOSE_GOAL_ACHIEVED" if status == "COMPLETION_REVIEW" => {
                    require_selected_tasks_done(connection, goal_id)
                }
                _ => Err(LocalOwnerError::TransitionRejected),
            }
        }
        "START_TASK" | "PAUSE_TASK" | "RESUME_TASK" | "COMPLETE_TASK_MANUALLY" => {
            let task_id = payload["taskId"]
                .as_str()
                .ok_or(LocalOwnerError::InvalidInput)?;
            let current = current_state(connection, "TASK_STATE", task_id)?;
            let status = current.value["status"]
                .as_str()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            match command_type {
                "START_TASK" if status == "READY" => {
                    let goal_id: String = connection.query_row(
                        "SELECT goal_id FROM task WHERE task_id=?1",
                        [task_id],
                        |row| row.get(0),
                    )?;
                    let goal = current_state(connection, "GOAL_STATE", &goal_id)?;
                    if goal.value["status"] == "ACTIVE" {
                        Ok(())
                    } else {
                        Err(LocalOwnerError::TransitionRejected)
                    }
                }
                "PAUSE_TASK" if ["READY", "ACTIVE"].contains(&status) => Ok(()),
                "RESUME_TASK" if status == "PAUSED" => Ok(()),
                "COMPLETE_TASK_MANUALLY" if status == "ACTIVE" => Ok(()),
                _ => Err(LocalOwnerError::TransitionRejected),
            }
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn state_binding_for(
    connection: &Connection,
    command_type: &str,
    payload: &Value,
) -> Result<Value, LocalOwnerError> {
    match command_type {
        "CREATE_GOAL_BUNDLE" => Ok(json!({
            "bindingKind": "CREATE_GOAL_BUNDLE_V1"
        })),
        "START_GOAL" | "PAUSE_GOAL" | "RESUME_GOAL" | "REQUEST_COMPLETION_REVIEW" => {
            let goal_id = payload["goalId"]
                .as_str()
                .ok_or(LocalOwnerError::InvalidInput)?;
            let state = current_state(connection, "GOAL_STATE", goal_id)?;
            Ok(json!({
                "bindingKind": "GOAL_STATE_CAS_V1",
                "goalId": goal_id,
                "goalStateFingerprint": state.fingerprint,
                "goalStateRevision": state.revision,
            }))
        }
        "CLOSE_GOAL_ACHIEVED" => close_goal_binding(connection, payload),
        "START_TASK" | "PAUSE_TASK" | "RESUME_TASK" | "COMPLETE_TASK_MANUALLY" => {
            let task_id = payload["taskId"]
                .as_str()
                .ok_or(LocalOwnerError::InvalidInput)?;
            let state = current_state(connection, "TASK_STATE", task_id)?;
            let goal_id: String = connection.query_row(
                "SELECT goal_id FROM task WHERE task_id=?1",
                [task_id],
                |row| row.get(0),
            )?;
            let goal = current_state(connection, "GOAL_STATE", &goal_id)?;
            Ok(json!({
                "bindingKind": "TASK_AND_GOAL_STATE_CAS_V1",
                "goalId": goal_id,
                "goalStateFingerprint": goal.fingerprint,
                "goalStateRevision": goal.revision,
                "taskId": task_id,
                "taskStateFingerprint": state.fingerprint,
                "taskStateRevision": state.revision,
            }))
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn close_goal_binding(
    connection: &Connection,
    payload: &Value,
) -> Result<Value, LocalOwnerError> {
    let goal_id = payload["goalId"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let goal = current_state(connection, "GOAL_STATE", goal_id)?;
    let (plan_id, plan_fingerprint): (String, String) = connection.query_row(
        "SELECT plan_id,plan_fingerprint FROM plan_revision WHERE goal_id=?1 AND plan_revision=1",
        [goal_id],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;

    let mut memberships = Vec::new();
    let mut statement = connection.prepare(
        "SELECT m.criterion_id,m.task_id,m.selected_route,m.membership_fingerprint FROM plan_membership m WHERE m.plan_id=?1 AND m.plan_revision=1 ORDER BY m.criterion_id,m.task_id",
    )?;
    let rows = statement.query_map([&plan_id], |row| {
        Ok(json!({
            "criterionId": row.get::<_, String>(0)?,
            "membershipFingerprint": row.get::<_, String>(3)?,
            "selectedRoute": row.get::<_, i64>(2)? == 1,
            "taskId": row.get::<_, String>(1)?,
        }))
    })?;
    for row in rows {
        memberships.push(row?);
    }

    let mut criteria = Vec::new();
    let mut statement = connection.prepare(
        "SELECT c.criterion_id,c.criterion_ordinal,p.current_fact_fingerprint,m.task_id,m.membership_fingerprint,g.completion_ref FROM criterion c JOIN current_pointer p ON p.fact_kind='SUCCESS_CRITERION' AND p.logical_id=c.criterion_id JOIN plan_membership m ON m.plan_id=?2 AND m.plan_revision=1 AND m.criterion_id=c.criterion_id AND m.selected_route=1 JOIN completion_guard g ON g.task_id=m.task_id WHERE c.goal_id=?1 ORDER BY c.criterion_ordinal",
    )?;
    let rows = statement.query_map(params![goal_id, plan_id], |row| {
        Ok(json!({
            "completionRef": row.get::<_, String>(5)?,
            "criterionFactFingerprint": row.get::<_, String>(2)?,
            "criterionId": row.get::<_, String>(0)?,
            "criterionOrdinal": row.get::<_, i64>(1)?,
            "selectedMembershipFingerprint": row.get::<_, String>(4)?,
            "selectedTaskId": row.get::<_, String>(3)?,
        }))
    })?;
    for row in rows {
        criteria.push(row?);
    }
    let expected_criteria: i64 = connection.query_row(
        "SELECT COUNT(*) FROM criterion WHERE goal_id=?1",
        [goal_id],
        |row| row.get(0),
    )?;
    if criteria.len() as i64 != expected_criteria {
        return Err(LocalOwnerError::TransitionRejected);
    }
    Ok(json!({
        "bindingKind": "GOAL_CLOSE_CURRENTNESS_V1",
        "criteria": criteria,
        "goalId": goal_id,
        "goalStateFingerprint": goal.fingerprint,
        "goalStateRevision": goal.revision,
        "memberships": memberships,
        "planFingerprint": plan_fingerprint,
        "planId": plan_id,
        "planRevision": 1,
    }))
}

fn validate_create_payload(payload: &Value) -> Result<(), LocalOwnerError> {
    let object = require_exact_object(
        payload,
        &["description", "successCriteria", "tasks", "title"],
    )?;
    require_nonempty_string(object, "title", 200)?;
    require_string(object, "description", 2000)?;
    let criteria = require_array(object, "successCriteria", 1, 20)?;
    let tasks = require_array(object, "tasks", 1, 50)?;

    let mut selected = BTreeMap::new();
    for (index, criterion) in criteria.iter().enumerate() {
        let criterion = require_exact_object(
            criterion,
            &["description", "selectedTaskOrdinal"],
        )?;
        require_nonempty_string(criterion, "description", 1000)?;
        let task_ordinal = require_u64(criterion, "selectedTaskOrdinal")?;
        if task_ordinal == 0 || task_ordinal > tasks.len() as u64 {
            return Err(LocalOwnerError::InvalidInput);
        }
        selected.insert(index + 1, task_ordinal as usize);
    }

    let mut supported_criteria = BTreeSet::new();
    for (index, task) in tasks.iter().enumerate() {
        let task = require_exact_object(
            task,
            &["description", "supportsCriteria", "title"],
        )?;
        require_nonempty_string(task, "title", 200)?;
        require_string(task, "description", 2000)?;
        let supports = require_array(task, "supportsCriteria", 1, 20)?;
        let mut task_supports = BTreeSet::new();
        for criterion in supports {
            let ordinal = criterion.as_u64().ok_or(LocalOwnerError::InvalidInput)?;
            if ordinal == 0 || ordinal > criteria.len() as u64 {
                return Err(LocalOwnerError::InvalidInput);
            }
            if !task_supports.insert(ordinal as usize) {
                return Err(LocalOwnerError::InvalidInput);
            }
            supported_criteria.insert(ordinal as usize);
        }
        for (criterion_ordinal, selected_task_ordinal) in &selected {
            if *selected_task_ordinal == index + 1 && !task_supports.contains(criterion_ordinal) {
                return Err(LocalOwnerError::InvalidInput);
            }
        }
    }
    if supported_criteria.len() != criteria.len() {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

fn commit_create_goal_bundle(
    transaction: &Transaction<'_>,
    pending: &PendingProposal,
    payload: &Value,
    _consent_commitment: &str,
) -> Result<MutationCommit, LocalOwnerError> {
    validate_create_payload(payload)?;
    let object = payload.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let goal_id = derived_id("goal", &pending.proposal_fingerprint, 1);
    let plan_id = derived_id("plan", &pending.proposal_fingerprint, 1);
    let title = object["title"].as_str().ok_or(LocalOwnerError::InvalidInput)?;
    let description = object["description"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    transaction.execute(
        "INSERT INTO goal(goal_id,title,description,outcome_kind,created_proposal_fingerprint) VALUES(?1,?2,?3,'COMPLETE',?4)",
        params![goal_id, title, description, pending.proposal_fingerprint],
    )?;

    let first_sequence = next_event_sequence(transaction)?;
    let mut next_sequence = first_sequence;
    append_fact(
        transaction,
        &mut next_sequence,
        "GOAL_SPECIFICATION",
        &goal_id,
        1,
        json!({
            "description": description,
            "goalId": goal_id,
            "outcomeKind": "COMPLETE",
            "title": title,
        }),
        None,
        &pending.command_fingerprint,
    )?;
    append_fact(
        transaction,
        &mut next_sequence,
        "GOAL_STATE",
        &goal_id,
        1,
        json!({
            "goalId": goal_id,
            "outcome": Value::Null,
            "priorStatus": Value::Null,
            "status": "READY",
        }),
        None,
        &pending.command_fingerprint,
    )?;

    let tasks = object["tasks"].as_array().ok_or(LocalOwnerError::InvalidInput)?;
    let criteria = object["successCriteria"]
        .as_array()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let mut task_ids = Vec::new();
    for (index, task) in tasks.iter().enumerate() {
        let task_id = derived_id("task", &pending.proposal_fingerprint, index + 1);
        task_ids.push(task_id.clone());
        transaction.execute(
            "INSERT INTO task(task_id,goal_id,task_ordinal,title,description) VALUES(?1,?2,?3,?4,?5)",
            params![
                task_id,
                goal_id,
                as_i64((index + 1) as u64)?,
                task["title"].as_str().ok_or(LocalOwnerError::InvalidInput)?,
                task["description"].as_str().ok_or(LocalOwnerError::InvalidInput)?
            ],
        )?;
        append_fact(
            transaction,
            &mut next_sequence,
            "TASK_SPECIFICATION",
            &task_id,
            1,
            json!({
                "description": task["description"],
                "goalId": goal_id,
                "taskId": task_id,
                "title": task["title"],
            }),
            None,
            &pending.command_fingerprint,
        )?;
        append_fact(
            transaction,
            &mut next_sequence,
            "TASK_STATE",
            &task_id,
            1,
            json!({
                "activityContextCommitment": Value::Null,
                "status": "READY",
                "taskId": task_id,
            }),
            None,
            &pending.command_fingerprint,
        )?;
    }

    let mut criterion_ids = Vec::new();
    for (index, criterion) in criteria.iter().enumerate() {
        let criterion_id = derived_id("criterion", &pending.proposal_fingerprint, index + 1);
        criterion_ids.push(criterion_id.clone());
        transaction.execute(
            "INSERT INTO criterion(criterion_id,goal_id,criterion_ordinal,description,assessment_kind,owner_kind,required) VALUES(?1,?2,?3,?4,'HUMAN_JUDGMENT','JENN',1)",
            params![
                criterion_id,
                goal_id,
                as_i64((index + 1) as u64)?,
                criterion["description"].as_str().ok_or(LocalOwnerError::InvalidInput)?
            ],
        )?;
        append_fact(
            transaction,
            &mut next_sequence,
            "SUCCESS_CRITERION",
            &criterion_id,
            1,
            json!({
                "assessmentKind": "HUMAN_JUDGMENT",
                "criterionId": criterion_id,
                "description": criterion["description"],
                "goalId": goal_id,
                "ownerKind": "JENN",
                "required": true,
            }),
            None,
            &pending.command_fingerprint,
        )?;
    }

    let mut membership_values = Vec::new();
    let mut membership_rows = Vec::new();
    for (task_index, task) in tasks.iter().enumerate() {
        for criterion_value in task["supportsCriteria"]
            .as_array()
            .ok_or(LocalOwnerError::InvalidInput)?
        {
            let criterion_ordinal =
                criterion_value.as_u64().ok_or(LocalOwnerError::InvalidInput)? as usize;
            let selected = criteria[criterion_ordinal - 1]["selectedTaskOrdinal"]
                .as_u64()
                .ok_or(LocalOwnerError::InvalidInput)? as usize
                == task_index + 1;
            let membership_value = json!({
                "criterionId": criterion_ids[criterion_ordinal - 1],
                "planId": plan_id,
                "planRevision": 1,
                "selectedRoute": selected,
                "taskId": task_ids[task_index],
            });
            let membership_bytes = canonical_value_bytes(&membership_value)?;
            let membership_fingerprint = domain_fingerprint(
                "agents-os.local-owner.plan-membership.v1",
                &membership_bytes,
            );
            membership_rows.push((
                criterion_ids[criterion_ordinal - 1].clone(),
                task_ids[task_index].clone(),
                selected,
                membership_fingerprint,
            ));
            membership_values.push(membership_value);
        }
    }
    membership_values.sort_by(|left, right| {
        canonical_value_bytes(left)
            .unwrap_or_default()
            .cmp(&canonical_value_bytes(right).unwrap_or_default())
    });
    let plan_value = json!({
        "goalId": goal_id,
        "memberships": membership_values,
        "planId": plan_id,
        "planRevision": 1,
    });
    let plan_bytes = canonical_value_bytes(&plan_value)?;
    let plan_fingerprint =
        domain_fingerprint("agents-os.local-owner.plan.v1", &plan_bytes);
    transaction.execute(
        "INSERT INTO plan_revision(plan_id,plan_revision,goal_id,plan_fingerprint) VALUES(?1,1,?2,?3)",
        params![plan_id, goal_id, plan_fingerprint],
    )?;
    for (criterion_id, task_id, selected, membership_fingerprint) in membership_rows {
        transaction.execute(
            "INSERT INTO plan_membership(plan_id,plan_revision,criterion_id,task_id,selected_route,membership_fingerprint) VALUES(?1,1,?2,?3,?4,?5)",
            params![
                plan_id,
                criterion_id,
                task_id,
                i64::from(selected),
                membership_fingerprint
            ],
        )?;
    }
    append_fact(
        transaction,
        &mut next_sequence,
        "PLAN_REVISION",
        &plan_id,
        1,
        plan_value,
        None,
        &pending.command_fingerprint,
    )?;

    Ok(MutationCommit {
        first_event_sequence: first_sequence,
        last_event_sequence: next_sequence - 1,
        result: json!({
            "goalId": goal_id,
            "goalStatus": "READY",
            "planId": plan_id,
            "taskCount": task_ids.len(),
        }),
    })
}

fn commit_goal_transition(
    transaction: &Transaction<'_>,
    pending: &PendingProposal,
    payload: &Value,
    _consent_commitment: &str,
) -> Result<MutationCommit, LocalOwnerError> {
    let goal_id = payload["goalId"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let current = current_state(transaction, "GOAL_STATE", goal_id)?;
    let current_status = current.value["status"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let (next_status, next_outcome, prior_status) = match pending.command_type.as_str() {
        "START_GOAL" if current_status == "READY" => ("ACTIVE", None, None),
        "PAUSE_GOAL" if ["READY", "ACTIVE"].contains(&current_status) => {
            let blocking = active_or_verifying_task_count(transaction, goal_id)?;
            if blocking != 0 {
                return Err(LocalOwnerError::TransitionRejected);
            }
            ("PAUSED", None, Some(current_status))
        }
        "RESUME_GOAL" if current_status == "PAUSED" => {
            let prior = current.value["priorStatus"]
                .as_str()
                .filter(|value| ["READY", "ACTIVE"].contains(value))
                .ok_or(LocalOwnerError::StateCorrupt)?;
            (prior, None, None)
        }
        "REQUEST_COMPLETION_REVIEW" if current_status == "ACTIVE" => {
            require_selected_tasks_done(transaction, goal_id)?;
            ("COMPLETION_REVIEW", None, None)
        }
        "CLOSE_GOAL_ACHIEVED" if current_status == "COMPLETION_REVIEW" => {
            require_selected_tasks_done(transaction, goal_id)?;
            ("CLOSED", Some("ACHIEVED"), None)
        }
        _ => return Err(LocalOwnerError::TransitionRejected),
    };

    let first_sequence = next_event_sequence(transaction)?;
    let mut next_sequence = first_sequence;
    if pending.command_type == "CLOSE_GOAL_ACHIEVED" {
        commit_criterion_decisions(
            transaction,
            goal_id,
            &pending.command_fingerprint,
            &mut next_sequence,
        )?;
    }
    append_fact(
        transaction,
        &mut next_sequence,
        "GOAL_STATE",
        goal_id,
        current.revision + 1,
        json!({
            "goalId": goal_id,
            "outcome": next_outcome,
            "priorStatus": prior_status,
            "status": next_status,
        }),
        Some(current.fingerprint),
        &pending.command_fingerprint,
    )?;
    Ok(MutationCommit {
        first_event_sequence: first_sequence,
        last_event_sequence: next_sequence - 1,
        result: json!({
            "goalId": goal_id,
            "goalOutcome": next_outcome,
            "goalStatus": next_status,
        }),
    })
}

fn commit_task_transition(
    transaction: &Transaction<'_>,
    pending: &PendingProposal,
    payload: &Value,
    _consent_commitment: &str,
) -> Result<MutationCommit, LocalOwnerError> {
    let task_id = payload["taskId"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let current = current_state(transaction, "TASK_STATE", task_id)?;
    let current_status = current.value["status"]
        .as_str()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let (next_status, activity_commitment) = match pending.command_type.as_str() {
        "START_TASK" if current_status == "READY" => {
            let goal_id: String =
                transaction.query_row("SELECT goal_id FROM task WHERE task_id=?1", [task_id], |row| {
                    row.get(0)
                })?;
            let goal = current_state(transaction, "GOAL_STATE", &goal_id)?;
            if goal.value["status"] != "ACTIVE" {
                return Err(LocalOwnerError::TransitionRejected);
            }
            let context = payload["activityContext"]
                .as_str()
                .ok_or(LocalOwnerError::InvalidInput)?;
            (
                "ACTIVE",
                Some(domain_fingerprint(
                    "agents-os.local-owner.activity-context.v1",
                    normalize_transcript(context).as_bytes(),
                )),
            )
        }
        "PAUSE_TASK" if ["READY", "ACTIVE"].contains(&current_status) => ("PAUSED", None),
        "RESUME_TASK" if current_status == "PAUSED" => ("READY", None),
        _ => return Err(LocalOwnerError::TransitionRejected),
    };
    let first_sequence = next_event_sequence(transaction)?;
    let mut next_sequence = first_sequence;
    append_fact(
        transaction,
        &mut next_sequence,
        "TASK_STATE",
        task_id,
        current.revision + 1,
        json!({
            "activityContextCommitment": activity_commitment,
            "status": next_status,
            "taskId": task_id,
        }),
        Some(current.fingerprint),
        &pending.command_fingerprint,
    )?;
    Ok(MutationCommit {
        first_event_sequence: first_sequence,
        last_event_sequence: next_sequence - 1,
        result: json!({
            "taskId": task_id,
            "taskStatus": next_status,
        }),
    })
}

fn commit_manual_completion(
    transaction: &Transaction<'_>,
    pending: &PendingProposal,
    payload: &Value,
    consent_commitment: &str,
) -> Result<MutationCommit, LocalOwnerError> {
    let task_id = payload["taskId"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let current = current_state(transaction, "TASK_STATE", task_id)?;
    if current.value["status"] != "ACTIVE" {
        return Err(LocalOwnerError::TransitionRejected);
    }
    let result_summary = payload["resultSummary"]
        .as_str()
        .ok_or(LocalOwnerError::InvalidInput)?;
    let first_sequence = next_event_sequence(transaction)?;
    let mut next_sequence = first_sequence;
    append_fact(
        transaction,
        &mut next_sequence,
        "TASK_STATE",
        task_id,
        current.revision + 1,
        json!({
            "activityContextCommitment": current.value["activityContextCommitment"],
            "status": "VERIFYING",
            "taskId": task_id,
        }),
        Some(current.fingerprint.clone()),
        &pending.command_fingerprint,
    )?;

    let candidate_id = derived_id("result-candidate", &pending.proposal_fingerprint, 1);
    let candidate_fingerprint = domain_fingerprint(
        "agents-os.local-owner.result-candidate.v1",
        format!(
            "{task_id}\0{}\0{consent_commitment}",
            domain_fingerprint(
                "agents-os.local-owner.result-summary.v1",
                result_summary.as_bytes()
            )
        )
        .as_bytes(),
    );
    transaction.execute(
        "INSERT INTO result_candidate(candidate_id,task_id,candidate_revision,result_summary_commitment,consent_commitment,candidate_fingerprint,created_event_sequence) VALUES(?1,?2,1,?3,?4,?5,?6)",
        params![
            candidate_id,
            task_id,
            domain_fingerprint("agents-os.local-owner.result-summary.v1",result_summary.as_bytes()),
            consent_commitment,
            candidate_fingerprint,
            as_i64(next_sequence)?
        ],
    )?;
    append_event_only(
        transaction,
        &mut next_sequence,
        "RESULT_CANDIDATE_RECORDED",
        &candidate_id,
        1,
        &pending.command_fingerprint,
        json!({
            "candidateFingerprint": candidate_fingerprint,
            "candidateId": candidate_id,
            "taskId": task_id,
        }),
    )?;

    let requirement_id =
        derived_id("validation-requirement", &pending.proposal_fingerprint, 1);
    let requirement_value = json!({
        "candidateId": candidate_id,
        "requirementId": requirement_id,
        "requirementKind": "HUMAN_ACCEPTANCE",
        "requirementRevision": 1,
        "taskId": task_id,
    });
    let requirement_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-requirement.v1",
        &canonical_value_bytes(&requirement_value)?,
    );
    transaction.execute(
        "INSERT INTO validation_requirement(requirement_id,task_id,candidate_id,requirement_kind,requirement_revision,requirement_fingerprint,created_event_sequence) VALUES(?1,?2,?3,'HUMAN_ACCEPTANCE',1,?4,?5)",
        params![
            requirement_id,
            task_id,
            candidate_id,
            requirement_fingerprint,
            as_i64(next_sequence)?
        ],
    )?;
    append_event_only(
        transaction,
        &mut next_sequence,
        "VALIDATION_REQUIREMENT_RECORDED",
        &requirement_id,
        1,
        &pending.command_fingerprint,
        requirement_value,
    )?;

    let validation_set_id =
        derived_id("validation-set", &pending.proposal_fingerprint, 1);
    let pending_attempt_id =
        derived_id("validation-attempt", &pending.proposal_fingerprint, 1);
    let running_attempt_id =
        derived_id("validation-attempt", &pending.proposal_fingerprint, 2);
    let passed_attempt_id =
        derived_id("validation-attempt", &pending.proposal_fingerprint, 3);
    let pending_attempt_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.pending.v1",
        format!("{validation_set_id}\0{pending_attempt_id}").as_bytes(),
    );
    let running_attempt_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.running.v1",
        format!(
            "{validation_set_id}\0{running_attempt_id}\0{pending_attempt_fingerprint}"
        )
        .as_bytes(),
    );
    let passed_attempt_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-attempt.passed.v1",
        format!(
            "{validation_set_id}\0{passed_attempt_id}\0{running_attempt_fingerprint}\0{consent_commitment}"
        )
        .as_bytes(),
    );
    let validation_set_value = json!({
        "candidateId": candidate_id,
        "consentCommitment": consent_commitment,
        "currentAttemptId": passed_attempt_id,
        "currentDecision": "PASSED",
        "requirementId": requirement_id,
        "taskId": task_id,
        "validationSetId": validation_set_id,
        "validationSetRevision": 1,
    });
    let validation_set_fingerprint = domain_fingerprint(
        "agents-os.local-owner.validation-set.v1",
        &canonical_value_bytes(&validation_set_value)?,
    );
    transaction.execute(
        "INSERT INTO validation_set(validation_set_id,task_id,candidate_id,requirement_id,validation_set_revision,current_attempt_id,current_decision,consent_commitment,validation_set_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,1,?5,'PASSED',?6,?7,?8)",
        params![
            validation_set_id,
            task_id,
            candidate_id,
            requirement_id,
            passed_attempt_id,
            consent_commitment,
            validation_set_fingerprint,
            as_i64(next_sequence)?
        ],
    )?;
    append_event_only(
        transaction,
        &mut next_sequence,
        "VALIDATION_SET_RECORDED",
        &validation_set_id,
        1,
        &pending.command_fingerprint,
        validation_set_value,
    )?;
    for (ordinal, status, attempt_id, predecessor_attempt_id, evidence_commitment, fingerprint) in [
        (
            1_u64,
            "PENDING",
            pending_attempt_id.as_str(),
            None,
            None,
            pending_attempt_fingerprint.as_str(),
        ),
        (
            2_u64,
            "RUNNING",
            running_attempt_id.as_str(),
            Some(pending_attempt_id.as_str()),
            None,
            running_attempt_fingerprint.as_str(),
        ),
        (
            3_u64,
            "PASSED",
            passed_attempt_id.as_str(),
            Some(running_attempt_id.as_str()),
            Some(consent_commitment),
            passed_attempt_fingerprint.as_str(),
        ),
    ] {
        transaction.execute(
            "INSERT INTO validation_attempt(attempt_id,validation_set_id,attempt_ordinal,status,predecessor_attempt_id,evidence_commitment,attempt_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7,?8)",
            params![
                attempt_id,
                validation_set_id,
                as_i64(ordinal)?,
                status,
                predecessor_attempt_id,
                evidence_commitment,
                fingerprint,
                as_i64(next_sequence)?
            ],
        )?;
        append_event_only(
            transaction,
            &mut next_sequence,
            &format!("VALIDATION_ATTEMPT_{status}"),
            attempt_id,
            ordinal,
            &pending.command_fingerprint,
            json!({
                "attemptFingerprint": fingerprint,
                "attemptId": attempt_id,
                "candidateId": candidate_id,
                "predecessorAttemptId": predecessor_attempt_id,
                "status": status,
                "taskId": task_id,
                "validationSetId": validation_set_id,
            }),
        )?;
    }

    let proof_id = derived_id("quiescence-proof", &pending.proposal_fingerprint, 1);
    let proof_value = json!({
        "controlIntentCount": 0,
        "effectCount": 0,
        "outboxCount": 0,
        "proofId": proof_id,
        "runCount": 0,
        "taskId": task_id,
        "unknownStateCount": 0,
    });
    let proof_fingerprint = domain_fingerprint(
        "agents-os.local-owner.quiescence-proof.v1",
        &canonical_value_bytes(&proof_value)?,
    );
    transaction.execute(
        "INSERT INTO quiescence_proof(proof_id,task_id,run_count,effect_count,outbox_count,control_intent_count,unknown_state_count,proof_fingerprint,created_event_sequence) VALUES(?1,?2,0,0,0,0,0,?3,?4)",
        params![proof_id,task_id,proof_fingerprint,as_i64(next_sequence)?],
    )?;
    append_event_only(
        transaction,
        &mut next_sequence,
        "QUIESCENCE_PROVED",
        &proof_id,
        1,
        &pending.command_fingerprint,
        proof_value,
    )?;

    let completion_ref = derived_id("completion", &pending.proposal_fingerprint, 1);
    let completion_value = json!({
        "candidateId": candidate_id,
        "completionRef": completion_ref,
        "quiescenceProofId": proof_id,
        "taskId": task_id,
        "validationSetId": validation_set_id,
    });
    let completion_fingerprint = domain_fingerprint(
        "agents-os.local-owner.completion-guard.v1",
        &canonical_value_bytes(&completion_value)?,
    );
    transaction.execute(
        "INSERT INTO completion_guard(completion_ref,task_id,candidate_id,validation_set_id,quiescence_proof_id,completion_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?5,?6,?7)",
        params![
            completion_ref,
            task_id,
            candidate_id,
            validation_set_id,
            proof_id,
            completion_fingerprint,
            as_i64(next_sequence)?
        ],
    )?;
    append_event_only(
        transaction,
        &mut next_sequence,
        "TASK_COMPLETION_GUARD_RECORDED",
        &completion_ref,
        1,
        &pending.command_fingerprint,
        completion_value,
    )?;
    append_fact(
        transaction,
        &mut next_sequence,
        "TASK_STATE",
        task_id,
        current.revision + 2,
        json!({
            "activityContextCommitment": current.value["activityContextCommitment"],
            "completionRef": completion_ref,
            "status": "DONE",
            "taskId": task_id,
        }),
        Some(current_pointer_fingerprint(
            transaction,
            "TASK_STATE",
            task_id,
        )?),
        &pending.command_fingerprint,
    )?;
    Ok(MutationCommit {
        first_event_sequence: first_sequence,
        last_event_sequence: next_sequence - 1,
        result: json!({
            "completionRef": completion_ref,
            "taskId": task_id,
            "taskStatus": "DONE",
            "validationDecision": "PASSED",
        }),
    })
}

fn commit_criterion_decisions(
    transaction: &Transaction<'_>,
    goal_id: &str,
    command_fingerprint: &str,
    next_sequence: &mut u64,
) -> Result<(), LocalOwnerError> {
    let (plan_id, plan_fingerprint): (String, String) = transaction.query_row(
        "SELECT plan_id,plan_fingerprint FROM plan_revision WHERE goal_id=?1 AND plan_revision=1",
        [goal_id],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    let mut statement = transaction.prepare(
        "SELECT c.criterion_id,m.task_id,m.membership_fingerprint,g.completion_ref FROM criterion c JOIN plan_membership m ON m.criterion_id=c.criterion_id AND m.plan_id=?2 AND m.plan_revision=1 AND m.selected_route=1 JOIN completion_guard g ON g.task_id=m.task_id WHERE c.goal_id=?1 ORDER BY c.criterion_ordinal",
    )?;
    let rows = statement.query_map(params![goal_id, plan_id], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
        ))
    })?;
    let mut decisions = Vec::new();
    for row in rows {
        decisions.push(row?);
    }
    let criterion_count: i64 =
        transaction.query_row("SELECT COUNT(*) FROM criterion WHERE goal_id=?1", [goal_id], |row| {
            row.get(0)
        })?;
    if decisions.len() as i64 != criterion_count {
        return Err(LocalOwnerError::TransitionRejected);
    }
    for (ordinal, (criterion_id, task_id, membership_fingerprint, completion_ref)) in
        decisions.into_iter().enumerate()
    {
        let decision_ref = derived_id("criterion-decision", command_fingerprint, ordinal + 1);
        let value = json!({
            "completionRef": completion_ref,
            "criterionId": criterion_id,
            "decision": "SATISFIED",
            "goalId": goal_id,
            "membershipFingerprint": membership_fingerprint,
            "planFingerprint": plan_fingerprint,
            "taskId": task_id,
        });
        let decision_fingerprint = domain_fingerprint(
            "agents-os.local-owner.criterion-decision.v1",
            &canonical_value_bytes(&value)?,
        );
        transaction.execute(
            "INSERT INTO criterion_decision(decision_ref,criterion_id,goal_id,decision,plan_fingerprint,membership_fingerprint,completion_ref,decision_fingerprint,created_event_sequence) VALUES(?1,?2,?3,'SATISFIED',?4,?5,?6,?7,?8)",
            params![
                decision_ref,
                criterion_id,
                goal_id,
                plan_fingerprint,
                membership_fingerprint,
                completion_ref,
                decision_fingerprint,
                as_i64(*next_sequence)?
            ],
        )?;
        append_event_only(
            transaction,
            next_sequence,
            "CRITERION_SATISFIED",
            &criterion_id,
            1,
            command_fingerprint,
            value,
        )?;
    }
    Ok(())
}

#[derive(Debug)]
struct CurrentState {
    revision: u64,
    fingerprint: String,
    value: Value,
}

fn current_state(
    connection: &Connection,
    fact_kind: &str,
    logical_id: &str,
) -> Result<CurrentState, LocalOwnerError> {
    let row: (i64, String, Vec<u8>) = connection.query_row(
        "SELECT p.current_fact_revision,p.current_fact_fingerprint,f.canonical_bytes FROM current_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE p.fact_kind=?1 AND p.logical_id=?2",
        params![fact_kind, logical_id],
        |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?)),
    )?;
    let value = serde_json::from_slice(&row.2).map_err(|_| LocalOwnerError::StateCorrupt)?;
    Ok(CurrentState {
        revision: as_u64(row.0)?,
        fingerprint: row.1,
        value,
    })
}

fn current_pointer_fingerprint(
    connection: &Connection,
    fact_kind: &str,
    logical_id: &str,
) -> Result<String, LocalOwnerError> {
    connection
        .query_row(
            "SELECT current_fact_fingerprint FROM current_pointer WHERE fact_kind=?1 AND logical_id=?2",
            params![fact_kind, logical_id],
            |row| row.get(0),
        )
        .map_err(Into::into)
}

fn append_fact(
    transaction: &Transaction<'_>,
    next_sequence: &mut u64,
    fact_kind: &str,
    logical_id: &str,
    revision: u64,
    value: Value,
    predecessor_fingerprint: Option<String>,
    command_fingerprint: &str,
) -> Result<String, LocalOwnerError> {
    let canonical_bytes = canonical_value_bytes(&value)?;
    let fingerprint_material = canonical_value_bytes(&json!({
        "factKind": fact_kind,
        "logicalId": logical_id,
        "predecessorFactFingerprint": predecessor_fingerprint,
        "revision": revision,
        "value": value,
    }))?;
    let fact_fingerprint = domain_fingerprint(
        &format!("agents-os.local-owner.fact.{fact_kind}.v1"),
        &fingerprint_material,
    );
    let fact_ref = format!("fact:{fact_kind}:{logical_id}:{revision}");
    let event_sequence = *next_sequence;
    let previous_event_fingerprint = latest_event_fingerprint(transaction)?;
    let event_value = json!({
        "aggregateRef": logical_id,
        "aggregateRevision": revision,
        "commandFingerprint": command_fingerprint,
        "eventKind": format!("{fact_kind}_ADVANCED"),
        "eventSequence": event_sequence,
        "factFingerprint": fact_fingerprint,
        "factRef": fact_ref,
        "predecessorEventFingerprint": previous_event_fingerprint,
    });
    let event_bytes = canonical_value_bytes(&event_value)?;
    let event_fingerprint = domain_fingerprint(
        "agents-os.local-owner.event.v1",
        &event_bytes,
    );
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![
            as_i64(event_sequence)?,
            format!("event:local-owner:{event_sequence}"),
            format!("{fact_kind}_ADVANCED"),
            logical_id,
            as_i64(revision)?,
            command_fingerprint,
            previous_event_fingerprint,
            event_bytes,
            event_fingerprint
        ],
    )?;
    transaction.execute(
        "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4,?2,?3,?5,?6,?7,?8)",
        params![
            fact_kind,
            logical_id,
            as_i64(revision)?,
            fact_ref,
            canonical_bytes,
            fact_fingerprint,
            predecessor_fingerprint,
            as_i64(event_sequence)?
        ],
    )?;
    if revision == 1 {
        transaction.execute(
            "INSERT INTO current_pointer(fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence) VALUES(?1,?2,1,?3,?4,1,?5)",
            params![fact_kind,logical_id,fact_ref,fact_fingerprint,as_i64(event_sequence)?],
        )?;
    } else {
        let predecessor = predecessor_fingerprint.ok_or(LocalOwnerError::StateCorrupt)?;
        let updated = transaction.execute(
            "UPDATE current_pointer SET current_fact_revision=?1,current_fact_ref=?2,current_fact_fingerprint=?3,pointer_version=?1,updated_event_sequence=?4 WHERE fact_kind=?5 AND logical_id=?6 AND current_fact_revision=?7 AND current_fact_fingerprint=?8 AND pointer_version=?7",
            params![
                as_i64(revision)?,
                fact_ref,
                fact_fingerprint,
                as_i64(event_sequence)?,
                fact_kind,
                logical_id,
                as_i64(revision-1)?,
                predecessor
            ],
        )?;
        if updated != 1 {
            return Err(LocalOwnerError::TransitionRejected);
        }
    }
    *next_sequence += 1;
    Ok(fact_fingerprint)
}

fn append_event_only(
    transaction: &Transaction<'_>,
    next_sequence: &mut u64,
    event_kind: &str,
    aggregate_ref: &str,
    aggregate_revision: u64,
    command_fingerprint: &str,
    value: Value,
) -> Result<String, LocalOwnerError> {
    let event_sequence = *next_sequence;
    let predecessor = latest_event_fingerprint(transaction)?;
    let canonical = json!({
        "aggregateRef": aggregate_ref,
        "aggregateRevision": aggregate_revision,
        "commandFingerprint": command_fingerprint,
        "eventKind": event_kind,
        "eventSequence": event_sequence,
        "payload": value,
        "predecessorEventFingerprint": predecessor,
    });
    let bytes = canonical_value_bytes(&canonical)?;
    let fingerprint =
        domain_fingerprint("agents-os.local-owner.event.v1", &bytes);
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![
            as_i64(event_sequence)?,
            format!("event:local-owner:{event_sequence}"),
            event_kind,
            aggregate_ref,
            as_i64(aggregate_revision)?,
            command_fingerprint,
            predecessor,
            bytes,
            fingerprint
        ],
    )?;
    *next_sequence += 1;
    Ok(fingerprint)
}

fn require_selected_tasks_done(
    connection: &Connection,
    goal_id: &str,
) -> Result<(), LocalOwnerError> {
    let not_done: i64 = connection.query_row(
        "SELECT COUNT(DISTINCT m.task_id) FROM plan_revision p JOIN plan_membership m ON m.plan_id=p.plan_id AND m.plan_revision=p.plan_revision AND m.selected_route=1 JOIN current_pointer cp ON cp.fact_kind='TASK_STATE' AND cp.logical_id=m.task_id JOIN canonical_fact f ON f.fact_kind=cp.fact_kind AND f.logical_id=cp.logical_id AND f.fact_revision=cp.current_fact_revision WHERE p.goal_id=?1 AND json_extract(CAST(f.canonical_bytes AS TEXT),'$.status')!='DONE'",
        [goal_id],
        |row| row.get(0),
    )?;
    if not_done == 0 {
        Ok(())
    } else {
        Err(LocalOwnerError::TransitionRejected)
    }
}

fn active_or_verifying_task_count(
    connection: &Connection,
    goal_id: &str,
) -> Result<i64, LocalOwnerError> {
    connection
        .query_row(
            "SELECT COUNT(*) FROM task t JOIN current_pointer p ON p.fact_kind='TASK_STATE' AND p.logical_id=t.task_id JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE t.goal_id=?1 AND (json_extract(CAST(f.canonical_bytes AS TEXT),'$.status')='ACTIVE' OR json_extract(CAST(f.canonical_bytes AS TEXT),'$.status')='VERIFYING')",
            [goal_id],
            |row| row.get(0),
        )
        .map_err(Into::into)
}

fn query_goals(connection: &Connection, query: &Value) -> Result<Value, LocalOwnerError> {
    let object = query.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let mode = require_string(object, "mode", 16)?;
    match mode {
        "GET" => {
            require_allowed_keys(object, &["goalId", "mode"], &[])?;
            let goal_id = require_string(object, "goalId", 200)?;
            let state = current_state(connection, "GOAL_STATE", goal_id)?;
            let row: (String, String) = connection.query_row(
                "SELECT title,description FROM goal WHERE goal_id=?1",
                [goal_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )?;
            let task_count: i64 =
                connection.query_row("SELECT COUNT(*) FROM task WHERE goal_id=?1", [goal_id], |row| {
                    row.get(0)
                })?;
            let progress = goal_progress(connection, goal_id)?;
            Ok(json!({
                "accepted": true,
                "goal": {
                    "description": row.1,
                    "goalId": goal_id,
                    "outcome": state.value["outcome"],
                    "progress": progress,
                    "status": state.value["status"],
                    "taskCount": task_count,
                    "title": row.0,
                },
                "resultCode": "QUERY_OK"
            }))
        }
        "LIST" => {
            require_allowed_keys(object, &["mode"], &["cursor", "pageSize"])?;
            let page_size = page_size(object)?;
            let cursor = optional_string(object, "cursor", 200)?.unwrap_or("");
            let mut statement = connection.prepare(
                "SELECT g.goal_id,g.title,g.description,f.canonical_bytes FROM goal g JOIN current_pointer p ON p.fact_kind='GOAL_STATE' AND p.logical_id=g.goal_id JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE g.goal_id>?1 ORDER BY g.goal_id LIMIT ?2",
            )?;
            let rows = statement.query_map(params![cursor, as_i64(page_size + 1)?], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, Vec<u8>>(3)?,
                ))
            })?;
            let mut items = Vec::new();
            for row in rows {
                let (goal_id, title, description, state_bytes) = row?;
                let state: Value = serde_json::from_slice(&state_bytes)
                    .map_err(|_| LocalOwnerError::StateCorrupt)?;
                let progress = goal_progress(connection, &goal_id)?;
                items.push(json!({
                    "description": description,
                    "goalId": goal_id,
                    "outcome": state["outcome"],
                    "progress": progress,
                    "status": state["status"],
                    "title": title,
                }));
            }
            let has_more = items.len() as u64 > page_size;
            if has_more {
                items.pop();
            }
            let next_cursor = if has_more {
                items.last().and_then(|value| value["goalId"].as_str())
            } else {
                None
            };
            Ok(json!({
                "accepted": true,
                "items": items,
                "nextCursor": next_cursor,
                "resultCode": "QUERY_OK"
            }))
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn goal_progress(connection: &Connection, goal_id: &str) -> Result<Value, LocalOwnerError> {
    let criterion_count: i64 = connection.query_row(
        "SELECT COUNT(*) FROM criterion WHERE goal_id=?1",
        [goal_id],
        |row| row.get(0),
    )?;
    let selected_task_count: i64 = connection.query_row(
        "SELECT COUNT(DISTINCT m.task_id) FROM plan_revision p JOIN plan_membership m ON m.plan_id=p.plan_id AND m.plan_revision=p.plan_revision AND m.selected_route=1 WHERE p.goal_id=?1",
        [goal_id],
        |row| row.get(0),
    )?;
    let completed_selected_task_count: i64 = connection.query_row(
        "SELECT COUNT(DISTINCT m.task_id) FROM plan_revision p JOIN plan_membership m ON m.plan_id=p.plan_id AND m.plan_revision=p.plan_revision AND m.selected_route=1 JOIN current_pointer cp ON cp.fact_kind='TASK_STATE' AND cp.logical_id=m.task_id JOIN canonical_fact f ON f.fact_kind=cp.fact_kind AND f.logical_id=cp.logical_id AND f.fact_revision=cp.current_fact_revision WHERE p.goal_id=?1 AND json_extract(CAST(f.canonical_bytes AS TEXT),'$.status')='DONE'",
        [goal_id],
        |row| row.get(0),
    )?;
    let satisfied_criterion_count: i64 = connection.query_row(
        "SELECT COUNT(*) FROM criterion_decision WHERE goal_id=?1 AND decision='SATISFIED'",
        [goal_id],
        |row| row.get(0),
    )?;
    Ok(json!({
        "completedSelectedTaskCount": completed_selected_task_count,
        "criterionCount": criterion_count,
        "satisfiedCriterionCount": satisfied_criterion_count,
        "selectedTaskCount": selected_task_count,
    }))
}

fn query_tasks(connection: &Connection, query: &Value) -> Result<Value, LocalOwnerError> {
    let object = query.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let mode = require_string(object, "mode", 16)?;
    match mode {
        "GET" => {
            require_allowed_keys(object, &["mode", "taskId"], &[])?;
            let task_id = require_string(object, "taskId", 200)?;
            let state = current_state(connection, "TASK_STATE", task_id)?;
            let row: (String, String, String) = connection.query_row(
                "SELECT goal_id,title,description FROM task WHERE task_id=?1",
                [task_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
            )?;
            Ok(json!({
                "accepted": true,
                "resultCode": "QUERY_OK",
                "task": {
                    "completionRef": state.value.get("completionRef").cloned().unwrap_or(Value::Null),
                    "description": row.2,
                    "goalId": row.0,
                    "status": state.value["status"],
                    "taskId": task_id,
                    "title": row.1,
                }
            }))
        }
        "LIST" => {
            require_allowed_keys(object, &["mode"], &["cursor", "goalId", "pageSize"])?;
            let page_size = page_size(object)?;
            let cursor = optional_string(object, "cursor", 200)?.unwrap_or("");
            let goal_id = optional_string(object, "goalId", 200)?;
            let mut statement = connection.prepare(
                "SELECT t.task_id,t.goal_id,t.title,t.description,f.canonical_bytes FROM task t JOIN current_pointer p ON p.fact_kind='TASK_STATE' AND p.logical_id=t.task_id JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision WHERE t.task_id>?1 AND (?2 IS NULL OR t.goal_id=?2) ORDER BY t.task_id LIMIT ?3",
            )?;
            let rows = statement.query_map(
                params![cursor, goal_id, as_i64(page_size + 1)?],
                |row| {
                    Ok((
                        row.get::<_, String>(0)?,
                        row.get::<_, String>(1)?,
                        row.get::<_, String>(2)?,
                        row.get::<_, String>(3)?,
                        row.get::<_, Vec<u8>>(4)?,
                    ))
                },
            )?;
            let mut items = Vec::new();
            for row in rows {
                let (task_id, goal_id, title, description, state_bytes) = row?;
                let state: Value = serde_json::from_slice(&state_bytes)
                    .map_err(|_| LocalOwnerError::StateCorrupt)?;
                items.push(json!({
                    "description": description,
                    "goalId": goal_id,
                    "status": state["status"],
                    "taskId": task_id,
                    "title": title,
                }));
            }
            let has_more = items.len() as u64 > page_size;
            if has_more {
                items.pop();
            }
            let next_cursor = if has_more {
                items.last().and_then(|value| value["taskId"].as_str())
            } else {
                None
            };
            Ok(json!({
                "accepted": true,
                "items": items,
                "nextCursor": next_cursor,
                "resultCode": "QUERY_OK"
            }))
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn replay_response(
    connection: &Connection,
    commitment: &str,
) -> Result<Option<Value>, LocalOwnerError> {
    let bytes: Option<Vec<u8>> = connection
        .query_row(
            "SELECT canonical_response_bytes FROM owner_consent_replay_index WHERE consent_commitment=?1",
            [commitment],
            |row| row.get(0),
        )
        .optional()?;
    bytes
        .map(|bytes| {
            serde_json::from_slice(&bytes).map_err(|_| LocalOwnerError::StateCorrupt)
        })
        .transpose()
}

fn verify_transaction_state(transaction: &Transaction<'_>) -> Result<(), LocalOwnerError> {
    verify_mmr_current_pointer_integrity(transaction)?;
    let fk_errors: i64 =
        transaction.query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| {
            row.get(0)
        })?;
    if fk_errors != 0 {
        return Err(LocalOwnerError::StateCorrupt);
    }
    verify_event_chain_on(transaction)?;
    verify_mmr_transition_history_integrity(transaction)?;
    verify_commitment_pointer_integrity(transaction)?;
    verify_p2f_kind_integrity(transaction)?;
    Ok(())
}

fn verify_event_and_epoch_chains(connection: &Connection) -> Result<(), LocalOwnerError> {
    verify_event_chain_on(connection)?;
    let expected_identity = domain_fingerprint(
        "agents-os.local-owner.resident-identity.v1",
        PROFILE_ID.as_bytes(),
    );
    let identities: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_identity WHERE resident_id=?1 AND identity_revision=1 AND identity_fingerprint=?2",
        params![PROFILE_ID, expected_identity],
        |row| row.get(0),
    )?;
    let identity_total: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_identity", [], |row| row.get(0))?;
    let incarnation_total: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_incarnation", [], |row| row.get(0))?;
    let epoch_total: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_authority_epoch",
        [],
        |row| row.get(0),
    )?;
    let identity_valid = if epoch_total == 0 {
        identities == 0 && identity_total == 0 && incarnation_total == 0
    } else {
        identities == 1 && identity_total == 1 && incarnation_total == epoch_total
    };
    if !identity_valid {
        return Err(LocalOwnerError::EpochChainBroken);
    }
    let mut statement = connection.prepare(
        "SELECT authority_epoch,authority_generation,incarnation_id,expected_previous_authority_epoch,previous_epoch_fingerprint,previous_incarnation_id,epoch_fingerprint,created_event_sequence FROM resident_authority_epoch ORDER BY authority_epoch",
    )?;
    let rows = statement.query_map([], |row| {
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
    })?;
    let mut previous: Option<(u64, String, String)> = None;
    for row in rows {
        let (epoch, generation, incarnation, expected_previous, previous_fp, previous_incarnation, fingerprint, event_sequence) = row?;
        let epoch = as_u64(epoch)?;
        if generation != as_i64(epoch)? {
            return Err(LocalOwnerError::EpochChainBroken);
        }
        let expected = previous.as_ref().map(|value| value.0);
        if expected_previous.map(as_u64).transpose()? != expected
            || previous_fp != previous.as_ref().map(|value| value.1.clone())
            || previous_incarnation != previous.as_ref().map(|value| value.2.clone())
        {
            return Err(LocalOwnerError::EpochChainBroken);
        }
        let (event_kind, aggregate_ref, aggregate_revision, command_fingerprint, event_predecessor, event_bytes):
            (String, String, i64, Option<String>, Option<String>, Vec<u8>) =
            connection.query_row(
                "SELECT event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes FROM event WHERE event_sequence=?1",
                [event_sequence],
                |row| {
                    Ok((
                        row.get(0)?,
                        row.get(1)?,
                        row.get(2)?,
                        row.get(3)?,
                        row.get(4)?,
                        row.get(5)?,
                    ))
                },
            )?;
        let event_value: Value = serde_json::from_slice(&event_bytes)
            .map_err(|_| LocalOwnerError::EpochChainBroken)?;
        let payload = event_value
            .get("payload")
            .cloned()
            .ok_or(LocalOwnerError::EpochChainBroken)?;
        let expected_fingerprint = domain_fingerprint(
            "agents-os.local-owner.authority-epoch.v1",
            &canonical_value_bytes(&payload)?,
        );
        if expected_fingerprint != fingerprint {
            return Err(LocalOwnerError::EpochChainBroken);
        }
        let (incarnation_revision, nonce_commitment, incarnation_event_sequence):
            (i64, String, i64) = connection.query_row(
                "SELECT incarnation_revision,process_nonce_commitment,created_event_sequence FROM resident_incarnation WHERE incarnation_id=?1",
                [&incarnation],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
            )?;
        if incarnation_revision != as_i64(epoch)?
            || incarnation_event_sequence != event_sequence
            || incarnation
                != format!(
                    "incarnation:local-owner:{}",
                    nonce_commitment.get(..32).ok_or(LocalOwnerError::EpochChainBroken)?
                )
        {
            return Err(LocalOwnerError::EpochChainBroken);
        }
        let expected_event_bytes = canonical_value_bytes(&json!({
            "aggregateRef": PROFILE_ID,
            "aggregateRevision": epoch,
            "commandFingerprint": Value::Null,
            "eventKind": event_kind,
            "eventSequence": as_u64(event_sequence)?,
            "payload": payload,
            "predecessorEventFingerprint": event_predecessor,
        }))?;
        if event_kind != "RESIDENT_OWNERSHIP_STARTED"
            && event_kind != "RESIDENT_DISASTER_RESTORED"
            || aggregate_ref != PROFILE_ID
            || aggregate_revision != as_i64(epoch)?
            || command_fingerprint.is_some()
            || event_bytes != expected_event_bytes
        {
            return Err(LocalOwnerError::EpochChainBroken);
        }
        previous = Some((epoch, fingerprint, incarnation));
    }
    Ok(())
}

trait QueryConnection {
    fn query_event_rows(&self) -> Result<Vec<(i64, Option<String>, String, Vec<u8>)>, rusqlite::Error>;
}

impl QueryConnection for Connection {
    fn query_event_rows(&self) -> Result<Vec<(i64, Option<String>, String, Vec<u8>)>, rusqlite::Error> {
        query_event_rows(self)
    }
}

impl QueryConnection for Transaction<'_> {
    fn query_event_rows(&self) -> Result<Vec<(i64, Option<String>, String, Vec<u8>)>, rusqlite::Error> {
        query_event_rows(self)
    }
}

fn query_event_rows(
    connection: &Connection,
) -> Result<Vec<(i64, Option<String>, String, Vec<u8>)>, rusqlite::Error> {
    let mut statement = connection.prepare(
        "SELECT event_sequence,predecessor_event_fingerprint,event_fingerprint,canonical_bytes FROM event ORDER BY event_sequence",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?))
    })?;
    rows.collect()
}

fn verify_event_chain_on(connection: &impl QueryConnection) -> Result<(), LocalOwnerError> {
    let rows = connection.query_event_rows()?;
    let mut expected_sequence = 1_u64;
    let mut previous = None;
    for (sequence, predecessor, fingerprint, bytes) in rows {
        if as_u64(sequence)? != expected_sequence || predecessor != previous {
            return Err(LocalOwnerError::EventChainBroken);
        }
        if domain_fingerprint("agents-os.local-owner.event.v1", &bytes) != fingerprint {
            return Err(LocalOwnerError::EventChainBroken);
        }
        expected_sequence += 1;
        previous = Some(fingerprint);
    }
    Ok(())
}

fn append_authority_epoch(
    connection: &mut Connection,
    process_nonce: &[u8],
) -> Result<(), LocalOwnerError> {
    if process_nonce.len() < 32 {
        return Err(LocalOwnerError::RandomnessUnavailable);
    }
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let identity_fingerprint = domain_fingerprint(
        "agents-os.local-owner.resident-identity.v1",
        PROFILE_ID.as_bytes(),
    );
    transaction.execute(
        "INSERT OR IGNORE INTO resident_identity(resident_id,identity_revision,identity_fingerprint) VALUES(?1,1,?2)",
        params![PROFILE_ID, identity_fingerprint],
    )?;
    let previous: Option<(i64, String, String)> = transaction
        .query_row(
            "SELECT authority_epoch,epoch_fingerprint,incarnation_id FROM resident_authority_epoch ORDER BY authority_epoch DESC LIMIT 1",
            [],
            |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?)),
        )
        .optional()?;
    let authority_epoch = previous
        .as_ref()
        .map_or(1_u64, |value| as_u64(value.0).unwrap_or(u64::MAX).saturating_add(1));
    if authority_epoch == u64::MAX {
        return Err(LocalOwnerError::EpochChainBroken);
    }
    let event_sequence = next_event_sequence(&transaction)?;
    let nonce_commitment = domain_fingerprint(
        "agents-os.local-owner.process-nonce.v1",
        process_nonce,
    );
    let incarnation_id = format!("incarnation:local-owner:{}", &nonce_commitment[..32]);
    let value = json!({
        "authorityEpoch": authority_epoch,
        "authorityGeneration": authority_epoch,
        "createdEventSequence": event_sequence,
        "expectedPreviousAuthorityEpoch": previous.as_ref().map(|value| as_u64(value.0)).transpose()?,
        "incarnationId": incarnation_id,
        "previousEpochFingerprint": previous.as_ref().map(|value| value.1.clone()),
        "previousIncarnationId": previous.as_ref().map(|value| value.2.clone()),
        "residentId": PROFILE_ID,
    });
    let epoch_fingerprint = domain_fingerprint(
        "agents-os.local-owner.authority-epoch.v1",
        &canonical_value_bytes(&value)?,
    );
    let predecessor = latest_event_fingerprint(&transaction)?;
    let event_value = json!({
        "aggregateRef": PROFILE_ID,
        "aggregateRevision": authority_epoch,
        "commandFingerprint": Value::Null,
        "eventKind": "RESIDENT_OWNERSHIP_STARTED",
        "eventSequence": event_sequence,
        "payload": value,
        "predecessorEventFingerprint": predecessor,
    });
    let event_bytes = canonical_value_bytes(&event_value)?;
    let event_fingerprint =
        domain_fingerprint("agents-os.local-owner.event.v1", &event_bytes);
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,'RESIDENT_OWNERSHIP_STARTED',?3,?4,NULL,?5,?6,?7)",
        params![
            as_i64(event_sequence)?,
            format!("event:local-owner:{event_sequence}"),
            PROFILE_ID,
            as_i64(authority_epoch)?,
            predecessor,
            event_bytes,
            event_fingerprint
        ],
    )?;
    transaction.execute(
        "INSERT INTO resident_incarnation(incarnation_id,incarnation_revision,process_nonce_commitment,created_event_sequence) VALUES(?1,?2,?3,?4)",
        params![incarnation_id,as_i64(authority_epoch)?,nonce_commitment,as_i64(event_sequence)?],
    )?;
    transaction.execute(
        "INSERT INTO resident_authority_epoch(authority_epoch,authority_generation,incarnation_id,expected_previous_authority_epoch,previous_epoch_fingerprint,previous_incarnation_id,epoch_fingerprint,created_event_sequence) VALUES(?1,?1,?2,?3,?4,?5,?6,?7)",
        params![
            as_i64(authority_epoch)?,
            incarnation_id,
            previous.as_ref().map(|value| value.0),
            previous.as_ref().map(|value| value.1.as_str()),
            previous.as_ref().map(|value| value.2.as_str()),
            epoch_fingerprint,
            as_i64(event_sequence)?
        ],
    )?;
    verify_transaction_state(&transaction)?;
    transaction.commit()?;
    Ok(())
}

fn append_disaster_restore_epoch(
    connection: &mut Connection,
    process_nonce: &[u8],
    checkpoint_identity: &str,
    restored_from: &str,
    gap_known: bool,
    gap_possible: bool,
    gap_claim: &str,
    lineage_authority: &str,
    projection_states: Vec<Value>,
    exclusion_constraints: Vec<Value>,
) -> Result<Value, LocalOwnerError> {
    if process_nonce.len() < 32 {
        return Err(LocalOwnerError::RandomnessUnavailable);
    }
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let previous: (i64, String, String) = transaction.query_row(
        "SELECT authority_epoch,epoch_fingerprint,incarnation_id FROM resident_authority_epoch ORDER BY authority_epoch DESC LIMIT 1",
        [],
        |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
    )?;
    let authority_epoch = as_u64(previous.0)?
        .checked_add(1)
        .ok_or(LocalOwnerError::EpochChainBroken)?;
    let event_sequence = next_event_sequence(&transaction)?;
    let nonce_commitment = domain_fingerprint(
        "agents-os.local-owner.process-nonce.v1",
        process_nonce,
    );
    let incarnation_id = format!("incarnation:local-owner:{}", &nonce_commitment[..32]);
    let payload = json!({
        "authorityEpoch": authority_epoch,
        "authorityGeneration": authority_epoch,
        "checkpointIdentity": checkpoint_identity,
        "createdEventSequence": event_sequence,
        "gap": {
            "claim": gap_claim,
            "known": gap_known,
            "possible": gap_possible,
        },
        "incarnationId": incarnation_id,
        "expectedPreviousAuthorityEpoch": previous.0,
        "lineageAuthority": lineage_authority,
        "previousEpochFingerprint": previous.1,
        "previousIncarnationId": previous.2,
        "projectionStates": projection_states.clone(),
        "restoredFrom": restored_from,
        "residentId": PROFILE_ID,
        "exclusionConstraints": exclusion_constraints.clone(),
    });
    let epoch_fingerprint = domain_fingerprint(
        "agents-os.local-owner.authority-epoch.v1",
        &canonical_value_bytes(&payload)?,
    );
    let predecessor = latest_event_fingerprint(&transaction)?;
    let event_value = json!({
        "aggregateRef": PROFILE_ID,
        "aggregateRevision": authority_epoch,
        "commandFingerprint": Value::Null,
        "eventKind": "RESIDENT_DISASTER_RESTORED",
        "eventSequence": event_sequence,
        "payload": payload,
        "predecessorEventFingerprint": predecessor,
    });
    let event_bytes = canonical_value_bytes(&event_value)?;
    let event_fingerprint = domain_fingerprint("agents-os.local-owner.event.v1", &event_bytes);
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_fingerprint,predecessor_event_fingerprint,canonical_bytes,event_fingerprint) VALUES(?1,?2,'RESIDENT_DISASTER_RESTORED',?3,?4,NULL,?5,?6,?7)",
        params![
            as_i64(event_sequence)?,
            format!("event:local-owner:restore:{event_sequence}"),
            PROFILE_ID,
            as_i64(authority_epoch)?,
            predecessor,
            event_bytes,
            event_fingerprint,
        ],
    )?;
    transaction.execute(
        "INSERT INTO resident_incarnation(incarnation_id,incarnation_revision,process_nonce_commitment,created_event_sequence) VALUES(?1,?2,?3,?4)",
        params![
            incarnation_id,
            as_i64(authority_epoch)?,
            nonce_commitment,
            as_i64(event_sequence)?,
        ],
    )?;
    transaction.execute(
        "INSERT INTO resident_authority_epoch(authority_epoch,authority_generation,incarnation_id,expected_previous_authority_epoch,previous_epoch_fingerprint,previous_incarnation_id,epoch_fingerprint,created_event_sequence) VALUES(?1,?1,?2,?3,?4,?5,?6,?7)",
        params![
            as_i64(authority_epoch)?,
            incarnation_id,
            previous.0,
            previous.1,
            previous.2,
            epoch_fingerprint,
            as_i64(event_sequence)?,
        ],
    )?;
    verify_transaction_state(&transaction)?;
    transaction.commit()?;
    let excluded: BTreeSet<String> = exclusion_constraints
        .iter()
        .filter_map(|constraint| constraint["stateId"].as_str().map(str::to_owned))
        .collect();
    let current_projection: Vec<Value> = projection_states
        .iter()
        .filter(|state| {
            state["active"].as_bool() == Some(true)
                && state["stateId"].as_str().is_some_and(|id| !excluded.contains(id))
        })
        .cloned()
        .collect();
    Ok(json!({
        "accepted": true,
        "authorityEpoch": authority_epoch,
        "checkpointIdentity": checkpoint_identity,
        "currentProjection": current_projection,
        "exclusionConstraints": exclusion_constraints,
        "gap": {
            "claim": gap_claim,
            "known": gap_known,
            "possible": gap_possible,
        },
        "incarnationId": incarnation_id,
        "lineageAuthority": lineage_authority,
        "oldIncarnationFenced": true,
        "resultCode": "DISASTER_RESTORE_APPLIED",
        "restoredFrom": restored_from,
    }))
}

fn parse_projection_states(value: Option<&Value>) -> Result<Vec<Value>, LocalOwnerError> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };
    let values = value.as_array().ok_or(LocalOwnerError::InvalidInput)?;
    if values.len() > 100 {
        return Err(LocalOwnerError::InvalidInput);
    }
    values
        .iter()
        .map(|value| {
            let object = require_exact_object(value, &["active", "stateId"])?;
            let _ = require_nonempty_string(object, "stateId", 300)?;
            if object["active"].as_bool().is_none() {
                return Err(LocalOwnerError::InvalidInput);
            }
            Ok(value.clone())
        })
        .collect()
}

fn parse_exclusion_constraints(value: Option<&Value>) -> Result<Vec<Value>, LocalOwnerError> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };
    let values = value.as_array().ok_or(LocalOwnerError::InvalidInput)?;
    if values.len() > 100 {
        return Err(LocalOwnerError::InvalidInput);
    }
    values
        .iter()
        .map(|value| {
            let object = require_exact_object(value, &["authorityRef", "evidenceRef", "stateId", "strength"])?;
            let _ = require_nonempty_string(object, "authorityRef", 300)?;
            let _ = require_nonempty_string(object, "evidenceRef", 300)?;
            let _ = require_nonempty_string(object, "stateId", 300)?;
            let strength = require_string(object, "strength", 64)?;
            if strength != "LOGICAL_REMOVAL" && strength != "PROTECTED_EXCLUSION" {
                return Err(LocalOwnerError::InvalidInput);
            }
            Ok(value.clone())
        })
        .collect()
}

fn next_event_sequence(connection: &Connection) -> Result<u64, LocalOwnerError> {
    let current: i64 =
        connection.query_row("SELECT COALESCE(MAX(event_sequence),0) FROM event", [], |row| {
            row.get(0)
        })?;
    as_u64(current)?
        .checked_add(1)
        .ok_or(LocalOwnerError::EventChainBroken)
}

fn latest_event_fingerprint(
    connection: &Connection,
) -> Result<Option<String>, LocalOwnerError> {
    connection
        .query_row(
            "SELECT event_fingerprint FROM event ORDER BY event_sequence DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .optional()
        .map_err(Into::into)
}

fn canonical_value_bytes(value: &Value) -> Result<Vec<u8>, LocalOwnerError> {
    let bytes = serde_json::to_vec(value).map_err(|_| LocalOwnerError::InvalidInput)?;
    canonicalize_json(&bytes).map_err(|_| LocalOwnerError::InvalidInput)
}

fn domain_fingerprint(domain: &str, bytes: &[u8]) -> String {
    let mut input = Vec::with_capacity(domain.len() + bytes.len() + 1);
    input.extend_from_slice(domain.as_bytes());
    input.push(0);
    input.extend_from_slice(bytes);
    sha256_hex(&input)
}

fn derived_id(kind: &str, proposal_fingerprint: &str, ordinal: usize) -> String {
    let digest = domain_fingerprint(
        &format!("agents-os.local-owner.id.{kind}.v1"),
        format!("{proposal_fingerprint}\0{ordinal}").as_bytes(),
    );
    format!("{kind}:local-owner:{}", &digest[..32])
}

fn require_goal_exists(connection: &Connection, goal_id: &str) -> Result<(), LocalOwnerError> {
    if connection
        .query_row("SELECT 1 FROM goal WHERE goal_id=?1", [goal_id], |_| Ok(()))
        .optional()?
        .is_some()
    {
        Ok(())
    } else {
        Err(LocalOwnerError::NotFound)
    }
}

fn require_task_exists(connection: &Connection, task_id: &str) -> Result<(), LocalOwnerError> {
    if connection
        .query_row("SELECT 1 FROM task WHERE task_id=?1", [task_id], |_| Ok(()))
        .optional()?
        .is_some()
    {
        Ok(())
    } else {
        Err(LocalOwnerError::NotFound)
    }
}

fn require_exact_object<'a>(
    value: &'a Value,
    keys: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let mut actual: Vec<&str> = object.keys().map(String::as_str).collect();
    let mut expected = keys.to_vec();
    actual.sort();
    expected.sort();
    if actual == expected {
        Ok(object)
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn require_exact_object_value(
    object: &Map<String, Value>,
    keys: &[&str],
) -> Result<(), LocalOwnerError> {
    let mut actual: Vec<&str> = object.keys().map(String::as_str).collect();
    let mut expected = keys.to_vec();
    actual.sort();
    expected.sort();
    if actual == expected {
        Ok(())
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn require_allowed_keys(
    object: &Map<String, Value>,
    required: &[&str],
    optional: &[&str],
) -> Result<(), LocalOwnerError> {
    if required.iter().any(|key| !object.contains_key(*key))
        || object
            .keys()
            .any(|key| !required.contains(&key.as_str()) && !optional.contains(&key.as_str()))
    {
        Err(LocalOwnerError::InvalidInput)
    } else {
        Ok(())
    }
}

fn require_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    maximum_bytes: usize,
) -> Result<&'a str, LocalOwnerError> {
    let value = object
        .get(key)
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::InvalidInput)?;
    if value.len() <= maximum_bytes && value.nfc().eq(value.chars()) {
        Ok(value)
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn require_nonempty_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    maximum_bytes: usize,
) -> Result<&'a str, LocalOwnerError> {
    require_string(object, key, maximum_bytes)
        .and_then(|value| (!value.trim().is_empty()).then_some(value).ok_or(LocalOwnerError::InvalidInput))
}

fn optional_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    maximum_bytes: usize,
) -> Result<Option<&'a str>, LocalOwnerError> {
    object
        .get(key)
        .map(|_| require_string(object, key, maximum_bytes))
        .transpose()
}

fn require_u64(object: &Map<String, Value>, key: &str) -> Result<u64, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_u64)
        .filter(|value| *value <= 9_007_199_254_740_991)
        .ok_or(LocalOwnerError::InvalidInput)
}

fn require_array<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    minimum: usize,
    maximum: usize,
) -> Result<&'a Vec<Value>, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_array)
        .filter(|values| (minimum..=maximum).contains(&values.len()))
        .ok_or(LocalOwnerError::InvalidInput)
}

fn page_size(object: &Map<String, Value>) -> Result<u64, LocalOwnerError> {
    match object.get("pageSize") {
        None => Ok(20),
        Some(value) => value
            .as_u64()
            .filter(|value| (1..=50).contains(value))
            .ok_or(LocalOwnerError::InvalidInput),
    }
}

fn unix_ms() -> Result<u64, LocalOwnerError> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|value| value.as_millis() as u64)
        .map_err(|_| LocalOwnerError::ClockUnavailable)
}

fn as_i64(value: u64) -> Result<i64, LocalOwnerError> {
    i64::try_from(value)
        .ok()
        .filter(|value| *value <= 9_007_199_254_740_991)
        .ok_or(LocalOwnerError::InvalidInput)
}

fn as_u64(value: i64) -> Result<u64, LocalOwnerError> {
    u64::try_from(value).map_err(|_| LocalOwnerError::StateCorrupt)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_request() -> Value {
        json!({
            "mutation": {
                "mutationType": "CREATE_GOAL_BUNDLE",
                "payload": {
                    "description": "expiry test",
                    "successCriteria": [
                        {"description": "accepted", "selectedTaskOrdinal": 1}
                    ],
                    "tasks": [
                        {
                            "description": "one task",
                            "supportsCriteria": [1],
                            "title": "Task"
                        }
                    ],
                    "title": "Expiry"
                }
            },
            "operation": "PROPOSE_GOAL_MUTATION"
        })
    }

    #[test]
    fn expired_pending_proposal_is_invalidated_without_writes() {
        let parent = tempfile::tempdir().unwrap();
        let database_path = parent.path().join("local-owner.sqlite3");
        let mut store = LocalOwnerStore::open_admitted(
            &database_path,
            Some(&[0x5a_u8; 32]),
            true,
        )
        .unwrap();
        let proposal = store
            .prepare_proposal(&json!({
                "attachmentGeneration": 1,
                "request": create_request()
            }))
            .unwrap();
        store.pending.as_mut().unwrap().expires_at_unix_ms = 0;
        let result = store
            .submit_consent(
                &json!({
                    "attachmentGeneration": 1,
                    "ingress": "TYPED_TEXT",
                    "transcript": proposal["consentPrompt"],
                }),
                LocalOwnerFault::None,
            )
            .unwrap();
        assert_eq!(result["resultCode"], "PROPOSAL_EXPIRED");
        let goal_count: i64 = store
            .connection
            .query_row("SELECT COUNT(*) FROM goal", [], |row| row.get(0))
            .unwrap();
        assert_eq!(goal_count, 0);
        assert_eq!(
            store
                .submit_consent(
                    &json!({
                        "attachmentGeneration": 1,
                        "ingress": "TYPED_TEXT",
                        "transcript": proposal["consentPrompt"],
                    }),
                    LocalOwnerFault::None,
                )
                .unwrap()["resultCode"],
            "NO_PENDING_PROPOSAL"
        );
    }
}
