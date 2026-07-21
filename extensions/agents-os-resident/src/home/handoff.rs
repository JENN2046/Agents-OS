//! WP4 synthetic, nonauthoritative F8 handoff composition.
//!
//! The reducer consumes the immutable F8 R5 owner-source anchor and canonical
//! F7 candidate history. It never recomputes an upstream owner assessment and
//! cannot commit a Command, Task, Memory or effect.

use serde_json::json;

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::{canonicalize_json, to_jcs_bytes};
use crate::canonical::types::{CanonicalValue, MAX_SAFE_INTEGER, parse_strict_json};
use crate::home::candidate::{
    CandidateSemanticClass, HomeCandidateRevision, canonical_candidate_history_fingerprint,
};
use crate::napi_frame::{MethodId, request_bytes};
use crate::reducers::command_intake::{
    CommandIntakeError, SyntheticHomeIntentPayload, home_intent_submission_value,
};

pub const MODULE_ID: &str = "agents-os.m0b.home.handoff.v0.1";
pub const IMPLEMENTATION_STATUS: &str = "WP4_F8_HANDOFF_COMPOSITION_ACTIVE";
pub const COMMAND_COMMIT_AUTHORIZED: bool = false;
pub const RUNTIME_USABLE: bool = false;

const HANDOFF_DOMAIN: &str = "agents-os.m0b.home-intent-handoff.v0.1";
const OWNER_SOURCE_DOMAIN: &str =
    "agents-os:f8-r5-h01-owner-commitment-stable-ref-closure:v0.1";
const TRUSTED_OWNER_SOURCE_ANCHOR: &str =
    "79fbc671c0852b990f2c605dc7c77733ff9e150087e2e30cc910eada638cdbaa";

const HANDOFF_FIELDS: [&str; 9] = [
    "handoff_candidate_id",
    "handoff_candidate_revision",
    "explicit_handoff_choice",
    "intent_candidate_ref",
    "intent_candidate_revision",
    "intent_candidate_fingerprint",
    "owner_commitment_set_fingerprint",
    "canonical_candidate_history_fingerprint",
    "minimum_trusted_event_sequence",
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TrustedOwnerCommitment {
    pub role: &'static str,
    pub owner_contract: &'static str,
    pub commitment_ref: &'static str,
    pub commitment_revision: u64,
    pub assessment_id: &'static str,
    pub assessment_revision: u64,
    pub assessment_fingerprint: &'static str,
    pub issued_event_ref: &'static str,
    pub issued_event_sequence: u64,
    pub issued_event_fingerprint: &'static str,
    pub commitment_fingerprint: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HomeIntentHandoffCandidate {
    pub handoff_candidate_id: String,
    pub handoff_candidate_revision: u64,
    pub handoff_candidate_ref: String,
    pub intent_candidate_ref: String,
    pub intent_candidate_revision: u64,
    pub intent_candidate_fingerprint: String,
    pub owner_commitment_set_fingerprint: String,
    pub canonical_candidate_history_fingerprint: String,
    pub minimum_trusted_event_sequence: u64,
    pub canonical_bytes: Vec<u8>,
    pub handoff_candidate_fingerprint: String,
    pub runtime_usable: bool,
    pub command_authority: bool,
    pub task_write_authority: bool,
    pub effect_authority: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticHomeIntentSubmission {
    pub command_id: String,
    pub command_fingerprint: String,
    pub submission_bytes: Vec<u8>,
    pub request_bytes: Vec<u8>,
    pub request_fingerprint: String,
    pub idempotency_key: String,
    pub runtime_usable: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HandoffResult {
    CandidateFormed,
    ExactReplay,
    Indeterminate,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HandoffDecision {
    pub result: HandoffResult,
    pub reason: &'static str,
    pub candidate: Option<HomeIntentHandoffCandidate>,
    pub canonical_write_count: u64,
    pub event_write_count: u64,
    pub f3_recheck_required: bool,
    pub command_authority: bool,
    pub task_write_authority: bool,
    pub effect_authority: bool,
    pub runtime_usable: bool,
}

#[derive(Debug, thiserror::Error, Eq, PartialEq)]
pub enum HandoffError {
    #[error("handoff request is not valid strict canonical JSON")]
    MalformedCanonicalJson,
    #[error("handoff request bytes are not canonical JCS")]
    NonCanonicalBytes,
    #[error("handoff request schema is invalid: {0}")]
    InvalidSchema(&'static str),
    #[error("trusted owner commitment source does not match the frozen F8 R5 anchor")]
    OwnerCommitmentMismatch,
    #[error("intent candidate does not resolve to the exact current canonical history head")]
    IntentCandidateMismatch,
    #[error("same handoff revision cannot be rewritten")]
    SameRevisionRewrite,
    #[error("handoff history is invalid")]
    InvalidHandoffHistory,
    #[error("synthetic F3 Home Intent submission could not be derived")]
    InvalidSyntheticSubmission,
}

/// Adapts one exact WP4 candidate into the existing F3 `execute_command`
/// request frame. This creates bytes only; F3 remains the sole authenticator,
/// replay owner and Command/Event writer.
pub fn synthetic_f3_home_intent_submission(
    candidate: &HomeIntentHandoffCandidate,
) -> Result<SyntheticHomeIntentSubmission, HandoffError> {
    let expected_handoff_ref = format!(
        "handoff:SYNTHETIC_TEST:{}:{}",
        candidate.handoff_candidate_id, candidate.handoff_candidate_revision
    );
    let expected_bytes = handoff_bytes(
        &candidate.handoff_candidate_id,
        candidate.handoff_candidate_revision,
        &expected_handoff_ref,
        &candidate.intent_candidate_ref,
        candidate.intent_candidate_revision,
        &candidate.intent_candidate_fingerprint,
        &candidate.owner_commitment_set_fingerprint,
        &candidate.canonical_candidate_history_fingerprint,
        candidate.minimum_trusted_event_sequence,
    )?;
    if candidate.runtime_usable
        || candidate.command_authority
        || candidate.task_write_authority
        || candidate.effect_authority
        || candidate.handoff_candidate_revision == 0
        || candidate.intent_candidate_revision == 0
        || candidate.minimum_trusted_event_sequence == 0
        || candidate.handoff_candidate_ref != expected_handoff_ref
        || candidate.canonical_bytes != expected_bytes
        || sha256_hex(&candidate.canonical_bytes) != candidate.handoff_candidate_fingerprint
    {
        return Err(HandoffError::InvalidSyntheticSubmission);
    }
    let payload = SyntheticHomeIntentPayload {
        handoff_candidate_ref: candidate.handoff_candidate_ref.clone(),
        handoff_candidate_revision: candidate.handoff_candidate_revision,
        handoff_candidate_fingerprint: candidate.handoff_candidate_fingerprint.clone(),
        intent_candidate_ref: candidate.intent_candidate_ref.clone(),
        intent_candidate_revision: candidate.intent_candidate_revision,
        intent_candidate_fingerprint: candidate.intent_candidate_fingerprint.clone(),
        owner_commitment_set_fingerprint: candidate.owner_commitment_set_fingerprint.clone(),
        canonical_candidate_history_fingerprint: candidate
            .canonical_candidate_history_fingerprint
            .clone(),
        minimum_trusted_event_sequence: candidate.minimum_trusted_event_sequence,
    };
    let command_id = payload
        .command_id()
        .map_err(map_submission_error)?;
    let submission = home_intent_submission_value(&payload).map_err(map_submission_error)?;
    let submission_bytes = canonicalize_json(
        &serde_json::to_vec(&submission).map_err(|_| HandoffError::InvalidSyntheticSubmission)?,
    )
    .map_err(|_| HandoffError::InvalidSyntheticSubmission)?;
    let command_bytes = canonicalize_json(
        &serde_json::to_vec(&submission["canonical_command"])
            .map_err(|_| HandoffError::InvalidSyntheticSubmission)?,
    )
    .map_err(|_| HandoffError::InvalidSyntheticSubmission)?;
    let command_fingerprint = sha256_hex(&command_bytes);
    let request_bytes = request_bytes(MethodId::ExecuteCommand, &command_id, submission)
        .map_err(|_| HandoffError::InvalidSyntheticSubmission)?;
    let request_fingerprint = sha256_hex(&request_bytes);
    let idempotency_bytes = canonicalize_json(
        &serde_json::to_vec(&json!([
            "agents-os.m0b.home-intent-idempotency.v0.1",
            command_id,
            request_fingerprint
        ]))
        .map_err(|_| HandoffError::InvalidSyntheticSubmission)?,
    )
    .map_err(|_| HandoffError::InvalidSyntheticSubmission)?;
    Ok(SyntheticHomeIntentSubmission {
        command_id,
        command_fingerprint,
        submission_bytes,
        request_bytes,
        request_fingerprint,
        idempotency_key: sha256_hex(&idempotency_bytes),
        runtime_usable: false,
    })
}

fn map_submission_error(_: CommandIntakeError) -> HandoffError {
    HandoffError::InvalidSyntheticSubmission
}

pub fn compose_f8_handoff(
    input: &[u8],
    candidate_history: &[HomeCandidateRevision],
    owner_source: &[TrustedOwnerCommitment],
    handoff_history: &[HomeIntentHandoffCandidate],
) -> Result<HandoffDecision, HandoffError> {
    validate_owner_source(owner_source)?;
    validate_handoff_history(handoff_history)?;
    let canonical_history_fingerprint = canonical_candidate_history_fingerprint(candidate_history)
        .map_err(|_| HandoffError::IntentCandidateMismatch)?;

    let value = parse_strict_json(input).map_err(|_| HandoffError::MalformedCanonicalJson)?;
    if to_jcs_bytes(&value) != input {
        return Err(HandoffError::NonCanonicalBytes);
    }
    let choice_missing = field_is_absent(&value, "explicit_handoff_choice")?;
    if choice_missing {
        let fields: Vec<&str> = HANDOFF_FIELDS
            .iter()
            .copied()
            .filter(|field| *field != "explicit_handoff_choice")
            .collect();
        value.require_exact_fields(&fields).map_err(|_| {
            HandoffError::InvalidSchema("closed handoff field inventory mismatch")
        })?;
    } else {
        value.require_exact_fields(&HANDOFF_FIELDS).map_err(|_| {
            HandoffError::InvalidSchema("closed handoff field inventory mismatch")
        })?;
    }

    let handoff_id = require_stable_ref(&value, "handoff_candidate_id")?;
    let handoff_revision = require_positive_integer(&value, "handoff_candidate_revision")?;
    if handoff_revision != 1 {
        return Err(HandoffError::InvalidSchema(
            "M0-B handoff candidate revision must equal 1",
        ));
    }
    let intent_ref = require_synthetic_ref(&value, "intent_candidate_ref")?;
    let intent_revision = require_positive_integer(&value, "intent_candidate_revision")?;
    let intent_fingerprint = require_hash(&value, "intent_candidate_fingerprint")?;
    let supplied_owner_set = require_hash(&value, "owner_commitment_set_fingerprint")?;
    let supplied_history = require_hash(
        &value,
        "canonical_candidate_history_fingerprint",
    )?;
    let minimum_sequence = require_positive_integer(
        &value,
        "minimum_trusted_event_sequence",
    )?;

    if supplied_owner_set != owner_commitment_set_fingerprint(owner_source)?
        || supplied_history != canonical_history_fingerprint
    {
        return Err(HandoffError::OwnerCommitmentMismatch);
    }
    if owner_source
        .iter()
        .any(|commitment| commitment.issued_event_sequence < minimum_sequence)
    {
        return Err(HandoffError::OwnerCommitmentMismatch);
    }

    let intent = exact_current_intent(
        candidate_history,
        intent_ref,
        intent_revision,
        intent_fingerprint,
    )?;
    if intent.created_event_sequence < minimum_sequence {
        return Err(HandoffError::IntentCandidateMismatch);
    }

    if choice_missing {
        return Ok(indeterminate("EXPLICIT_INTENT_CHOICE_MISSING"));
    }
    if require_string(&value, "explicit_handoff_choice")? != "PROPOSE_F8_HANDOFF" {
        return Ok(indeterminate("UNKNOWN_EXPLICIT_INTENT_CHOICE"));
    }

    let handoff_ref = format!(
        "handoff:SYNTHETIC_TEST:{handoff_id}:{handoff_revision}"
    );
    let canonical_bytes = handoff_bytes(
        handoff_id,
        handoff_revision,
        &handoff_ref,
        &intent.candidate_ref,
        intent.candidate_revision,
        &intent.candidate_fingerprint,
        supplied_owner_set,
        supplied_history,
        minimum_sequence,
    )?;
    let candidate = HomeIntentHandoffCandidate {
        handoff_candidate_id: handoff_id.to_owned(),
        handoff_candidate_revision: handoff_revision,
        handoff_candidate_ref: handoff_ref,
        intent_candidate_ref: intent.candidate_ref.clone(),
        intent_candidate_revision: intent.candidate_revision,
        intent_candidate_fingerprint: intent.candidate_fingerprint.clone(),
        owner_commitment_set_fingerprint: supplied_owner_set.to_owned(),
        canonical_candidate_history_fingerprint: supplied_history.to_owned(),
        minimum_trusted_event_sequence: minimum_sequence,
        handoff_candidate_fingerprint: sha256_hex(&canonical_bytes),
        canonical_bytes,
        runtime_usable: false,
        command_authority: false,
        task_write_authority: false,
        effect_authority: false,
    };

    if let Some(existing) = handoff_history.iter().find(|existing| {
        existing.handoff_candidate_id == candidate.handoff_candidate_id
            && existing.handoff_candidate_revision == candidate.handoff_candidate_revision
    }) {
        if existing == &candidate {
            return Ok(favorable(HandoffResult::ExactReplay, candidate));
        }
        return Err(HandoffError::SameRevisionRewrite);
    }
    if handoff_history.iter().any(|existing| {
        existing.handoff_candidate_ref == candidate.handoff_candidate_ref
            || existing.handoff_candidate_fingerprint == candidate.handoff_candidate_fingerprint
    }) {
        return Err(HandoffError::InvalidHandoffHistory);
    }

    Ok(favorable(HandoffResult::CandidateFormed, candidate))
}

pub fn trusted_owner_commitments() -> Vec<TrustedOwnerCommitment> {
    vec![
        trusted("actor_identity", "F2", "synthetic://f2/assessment-commitment/r5-h01-actor_identity@1", "A-ACTOR-ACTIVE", "916e54ec748a09d19de659b9a1097e6513ee7fba63e934e1bb7ff650d5454ab2", "synthetic://f2/event/r5-h01-actor_identity-commitment", "2eec0311265710a143ff33ac98c28e19cbb0027e5995563a17e89f00d95d740a", "46a92670de10070886f498fd1b882d2420d78ba108750356ae5d7a487c219142"),
        trusted("f3_readiness", "F3", "synthetic://f3/assessment-commitment/r5-h01-f3_readiness@1", "A-F3-READY", "137fcb5a7321923a339452c87c7caef0dad4735c8a2cc7c0d48b8deae88ee5e8", "synthetic://f3/event/r5-h01-f3_readiness-commitment", "04210e0235fc5c884eb177fde327a951fecf75153a8ea3ac9db6050187838ad5", "bae84d47996b3c97cbb50f1d1283fa8f5e4a5e311f8362d6ea096954037e43d4"),
        trusted("f7_intent_currentness", "F7", "synthetic://f7/assessment-commitment/r5-h01-f7_intent_currentness@1", "A-F7-CURRENT", "bb2c684e7028ece39ef864a10c8740513567f825be826e1a747a245153d8d861", "synthetic://f7/event/r5-h01-f7_intent_currentness-commitment", "b1bb31278f363521d9ff96cc6a7892cbf09e54a7c4ae29938c38f81e224bd2dc", "957f90ae9b6e61e5fc9cdf9192b58d46c2df8976e5f331cdc65439ce755ec3ca"),
        trusted("jenn_requirement", "POLICY", "synthetic://policy/assessment-commitment/r5-h01-jenn_requirement@1", "A-JREQ-NONE", "e53734933433c564f8d2cab9f773b754bc7dfb3714a2d3451297a2ae0c0ce207", "synthetic://policy/event/r5-h01-jenn_requirement-commitment", "9a9f97268f558988c68cab1ce10d3ee7cc10ffa21b55beebafcd17eb66c7e325", "2f6b194f7eec4c547ebe450584cbcd4083078da2cbf15a1050577fbe14b3af16"),
        trusted("pbl_currentness", "POLICY", "synthetic://policy/assessment-commitment/r5-h01-pbl_currentness@1", "A-PBL-CLEAR", "4291cb480ae1470f4215a690cb4f345e8ab0c1b64410ef8e48b72f16f62efdc9", "synthetic://policy/event/r5-h01-pbl_currentness-commitment", "9a752eee496f4965c4ac15af9304b6db114cca270fd56abf61f2907fea559d12", "958b65b41938ecdc3972a5b21a03fb2c632f99abd2e7efbcf6ac33e4274cc231"),
        trusted("principal_binding", "F2", "synthetic://f2/assessment-commitment/r5-h01-principal_binding@1", "A-PRINCIPAL-ACTIVE", "edabdfef642525eb9037af9f764ff040dc613b2161fe2ceb2f20d88450ecc039", "synthetic://f2/event/r5-h01-principal_binding-commitment", "7c50548651efc9728ba742c718bdbc602a50f84bde2d7ce8907a2da2a2f0c119", "d1b58217bd39bfb85411981641969b3e73dc6881a8d43e52a395994ebcf107b3"),
        trusted("responsibility", "F2", "synthetic://f2/assessment-commitment/r5-h01-responsibility@1", "A-RESP-ACTIVE", "10943831ea4dcc6101d70a43fe8b8d1b73c1c0f656008f52988feb082b68d144", "synthetic://f2/event/r5-h01-responsibility-commitment", "36e88e3068917d2adeca9a794c11b6ee9f67d14885077ff7647f48356b430d52", "0f85f16892e858b8b7da22b279ebb786e5d6c1b3bf95b5161ace10c70fd75bca"),
    ]
}

pub fn owner_commitment_set_fingerprint(
    commitments: &[TrustedOwnerCommitment],
) -> Result<String, HandoffError> {
    validate_owner_source(commitments)?;
    let rows: Vec<_> = commitments
        .iter()
        .map(|row| {
            json!([
                row.role,
                row.commitment_ref,
                row.commitment_revision,
                row.commitment_fingerprint,
                row.assessment_id,
                row.assessment_revision,
                row.assessment_fingerprint
            ])
        })
        .collect();
    let bytes = canonicalize_json(
        &serde_json::to_vec(&json!(["agents-os.m0b.owner-commitment-set.v0.1", rows]))
            .map_err(|_| HandoffError::OwnerCommitmentMismatch)?,
    )
    .map_err(|_| HandoffError::OwnerCommitmentMismatch)?;
    Ok(sha256_hex(&bytes))
}

#[allow(clippy::too_many_arguments)]
fn trusted(
    role: &'static str,
    owner_contract: &'static str,
    commitment_ref: &'static str,
    assessment_id: &'static str,
    assessment_fingerprint: &'static str,
    issued_event_ref: &'static str,
    issued_event_fingerprint: &'static str,
    commitment_fingerprint: &'static str,
) -> TrustedOwnerCommitment {
    TrustedOwnerCommitment {
        role,
        owner_contract,
        commitment_ref,
        commitment_revision: 1,
        assessment_id,
        assessment_revision: 1,
        assessment_fingerprint,
        issued_event_ref,
        issued_event_sequence: 100,
        issued_event_fingerprint,
        commitment_fingerprint,
    }
}

fn validate_owner_source(source: &[TrustedOwnerCommitment]) -> Result<(), HandoffError> {
    if source != trusted_owner_commitments() {
        return Err(HandoffError::OwnerCommitmentMismatch);
    }
    let rows: Vec<_> = source.iter().map(owner_source_json).collect();
    let anchor = tagged_digest(
        &format!("{OWNER_SOURCE_DOMAIN}:trusted-owner-source-anchor"),
        &rows,
    )?;
    if anchor != TRUSTED_OWNER_SOURCE_ANCHOR {
        return Err(HandoffError::OwnerCommitmentMismatch);
    }
    for row in source {
        let event = json!({
            "assessment_id": row.assessment_id,
            "assessment_revision": row.assessment_revision,
            "issued_event_ref": row.issued_event_ref,
            "issued_event_sequence": row.issued_event_sequence,
            "owner_contract": row.owner_contract,
            "role": row.role
        });
        if tagged_digest(&format!("{OWNER_SOURCE_DOMAIN}:owner-issued-event"), &event)?
            != row.issued_event_fingerprint
        {
            return Err(HandoffError::OwnerCommitmentMismatch);
        }
        let base = json!({
            "assessment_fingerprint": row.assessment_fingerprint,
            "assessment_id": row.assessment_id,
            "assessment_revision": row.assessment_revision,
            "commitment_ref": row.commitment_ref,
            "commitment_revision": row.commitment_revision,
            "issued_event_fingerprint": row.issued_event_fingerprint,
            "issued_event_ref": row.issued_event_ref,
            "issued_event_sequence": row.issued_event_sequence,
            "owner_contract": row.owner_contract,
            "role": row.role
        });
        if tagged_digest(
            &format!("{OWNER_SOURCE_DOMAIN}:trusted-owner-commitment"),
            &base,
        )? != row.commitment_fingerprint
        {
            return Err(HandoffError::OwnerCommitmentMismatch);
        }
    }
    Ok(())
}

fn owner_source_json(row: &TrustedOwnerCommitment) -> serde_json::Value {
    json!({
        "assessment_fingerprint": row.assessment_fingerprint,
        "assessment_id": row.assessment_id,
        "assessment_revision": row.assessment_revision,
        "commitment_fingerprint": row.commitment_fingerprint,
        "commitment_ref": row.commitment_ref,
        "commitment_revision": row.commitment_revision,
        "issued_event_fingerprint": row.issued_event_fingerprint,
        "issued_event_ref": row.issued_event_ref,
        "issued_event_sequence": row.issued_event_sequence,
        "owner_contract": row.owner_contract,
        "role": row.role
    })
}

fn tagged_digest(tag: &str, value: &impl serde::Serialize) -> Result<String, HandoffError> {
    let canonical = canonicalize_json(
        &serde_json::to_vec(value).map_err(|_| HandoffError::OwnerCommitmentMismatch)?,
    )
    .map_err(|_| HandoffError::OwnerCommitmentMismatch)?;
    let mut bytes = tag.as_bytes().to_vec();
    bytes.push(0);
    bytes.extend_from_slice(&canonical);
    Ok(sha256_hex(&bytes))
}

fn exact_current_intent<'a>(
    history: &'a [HomeCandidateRevision],
    reference: &str,
    revision: u64,
    fingerprint: &str,
) -> Result<&'a HomeCandidateRevision, HandoffError> {
    let candidate = history
        .iter()
        .find(|candidate| {
            candidate.candidate_ref == reference
                && candidate.candidate_revision == revision
                && candidate.candidate_fingerprint == fingerprint
        })
        .ok_or(HandoffError::IntentCandidateMismatch)?;
    if candidate.semantic_class != CandidateSemanticClass::Intent {
        return Err(HandoffError::IntentCandidateMismatch);
    }
    let current = history
        .iter()
        .filter(|other| other.candidate_id == candidate.candidate_id)
        .max_by_key(|other| other.candidate_revision)
        .ok_or(HandoffError::IntentCandidateMismatch)?;
    if current.candidate_ref != candidate.candidate_ref
        || current.candidate_fingerprint != candidate.candidate_fingerprint
    {
        return Err(HandoffError::IntentCandidateMismatch);
    }
    Ok(candidate)
}

fn validate_handoff_history(history: &[HomeIntentHandoffCandidate]) -> Result<(), HandoffError> {
    for (index, candidate) in history.iter().enumerate() {
        let expected_bytes = handoff_bytes(
            &candidate.handoff_candidate_id,
            candidate.handoff_candidate_revision,
            &candidate.handoff_candidate_ref,
            &candidate.intent_candidate_ref,
            candidate.intent_candidate_revision,
            &candidate.intent_candidate_fingerprint,
            &candidate.owner_commitment_set_fingerprint,
            &candidate.canonical_candidate_history_fingerprint,
            candidate.minimum_trusted_event_sequence,
        )?;
        if candidate.handoff_candidate_revision != 1
            || candidate.handoff_candidate_ref
                != format!(
                    "handoff:SYNTHETIC_TEST:{}:{}",
                    candidate.handoff_candidate_id, candidate.handoff_candidate_revision
                )
            || candidate.canonical_bytes != expected_bytes
            || candidate.handoff_candidate_fingerprint != sha256_hex(&expected_bytes)
            || candidate.runtime_usable
            || candidate.command_authority
            || candidate.task_write_authority
            || candidate.effect_authority
        {
            return Err(HandoffError::InvalidHandoffHistory);
        }
        if history[..index].iter().any(|previous| {
            previous.handoff_candidate_id == candidate.handoff_candidate_id
                || previous.handoff_candidate_ref == candidate.handoff_candidate_ref
                || previous.handoff_candidate_fingerprint == candidate.handoff_candidate_fingerprint
        }) {
            return Err(HandoffError::InvalidHandoffHistory);
        }
    }
    Ok(())
}

/// Revalidates one materialized handoff against the closed F8 canonical
/// representation. This does not grant authority; it only prevents a caller
/// from presenting mutually inconsistent struct fields and canonical bytes.
pub(crate) fn validate_materialized_handoff(
    candidate: &HomeIntentHandoffCandidate,
) -> Result<(), HandoffError> {
    validate_handoff_history(std::slice::from_ref(candidate))
}

#[allow(clippy::too_many_arguments)]
fn handoff_bytes(
    handoff_id: &str,
    handoff_revision: u64,
    handoff_ref: &str,
    intent_ref: &str,
    intent_revision: u64,
    intent_fingerprint: &str,
    owner_set: &str,
    history_fingerprint: &str,
    minimum_sequence: u64,
) -> Result<Vec<u8>, HandoffError> {
    canonicalize_json(
        &serde_json::to_vec(&json!([HANDOFF_DOMAIN, {
            "canonical_candidate_history_fingerprint": history_fingerprint,
            "handoff_candidate_id": handoff_id,
            "handoff_candidate_ref": handoff_ref,
            "handoff_candidate_revision": handoff_revision,
            "intent_candidate_fingerprint": intent_fingerprint,
            "intent_candidate_ref": intent_ref,
            "intent_candidate_revision": intent_revision,
            "minimum_trusted_event_sequence": minimum_sequence,
            "owner_commitment_set_fingerprint": owner_set
        }]))
        .map_err(|_| HandoffError::InvalidSchema("handoff serialization failed"))?,
    )
    .map_err(|_| HandoffError::InvalidSchema("handoff canonicalization failed"))
}

fn favorable(
    result: HandoffResult,
    candidate: HomeIntentHandoffCandidate,
) -> HandoffDecision {
    HandoffDecision {
        result,
        reason: "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE",
        candidate: Some(candidate),
        canonical_write_count: 0,
        event_write_count: 0,
        f3_recheck_required: true,
        command_authority: false,
        task_write_authority: false,
        effect_authority: false,
        runtime_usable: false,
    }
}

fn indeterminate(reason: &'static str) -> HandoffDecision {
    HandoffDecision {
        result: HandoffResult::Indeterminate,
        reason,
        candidate: None,
        canonical_write_count: 0,
        event_write_count: 0,
        f3_recheck_required: true,
        command_authority: false,
        task_write_authority: false,
        effect_authority: false,
        runtime_usable: false,
    }
}

fn field<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a CanonicalValue, HandoffError> {
    value
        .as_object()
        .map_err(|_| HandoffError::InvalidSchema("expected object"))?
        .iter()
        .find_map(|(key, value)| (key == name).then_some(value))
        .ok_or(HandoffError::InvalidSchema("required field is missing"))
}

fn field_is_absent(value: &CanonicalValue, name: &str) -> Result<bool, HandoffError> {
    Ok(!value
        .as_object()
        .map_err(|_| HandoffError::InvalidSchema("expected object"))?
        .iter()
        .any(|(key, _)| key == name))
}

fn require_string<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a str, HandoffError> {
    match field(value, name)? {
        CanonicalValue::String(value) => Ok(value),
        _ => Err(HandoffError::InvalidSchema("expected string")),
    }
}

fn require_synthetic_ref<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, HandoffError> {
    let reference = require_string(value, name)?;
    if reference.is_empty() || !reference.contains(":SYNTHETIC_TEST:") {
        return Err(HandoffError::InvalidSchema(
            "stable ref must be nonempty and synthetic-only",
        ));
    }
    Ok(reference)
}

fn require_stable_ref<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, HandoffError> {
    let reference = require_string(value, name)?;
    if reference.is_empty() {
        return Err(HandoffError::InvalidSchema(
            "stable ref must be a nonempty NFC string",
        ));
    }
    Ok(reference)
}

fn require_hash<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a str, HandoffError> {
    let hash = require_string(value, name)?;
    if hash.len() == 64
        && hash
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(hash)
    } else {
        Err(HandoffError::InvalidSchema("expected lowercase SHA-256"))
    }
}

fn require_positive_integer(value: &CanonicalValue, name: &str) -> Result<u64, HandoffError> {
    match field(value, name)? {
        CanonicalValue::Integer(integer) if (1..=MAX_SAFE_INTEGER).contains(integer) => {
            Ok(*integer as u64)
        }
        _ => Err(HandoffError::InvalidSchema(
            "expected positive safe integer",
        )),
    }
}
