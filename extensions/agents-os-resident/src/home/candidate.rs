//! Immutable, low-disclosure F7 candidate revision and promotion derivation.
//!
//! WP2 derives and validates candidate bytes. WP3 adds explicit promotion
//! choices for Life Stream candidates. Neither boundary has a ledger dependency
//! or performs an Event, pointer, Goal, Task, Command, Memory or effect write.

use std::collections::HashSet;

use serde_json::json;

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::{canonicalize_json, to_jcs_bytes};
use crate::canonical::types::{CanonicalValue, MAX_SAFE_INTEGER, parse_strict_json};

pub const MODULE_ID: &str = "agents-os.m0b.home.candidate.v0.1";
pub const IMPLEMENTATION_STATUS: &str = "WP3_EXPLICIT_PROMOTION_ACTIVE";
pub const CANONICAL_WRITE_AUTHORIZED: bool = false;
pub const RUNTIME_USABLE: bool = false;

const PROPOSAL_FIELDS: [&str; 13] = [
    "candidate_id",
    "candidate_revision",
    "semantic_class",
    "source_subject_ref",
    "source_subject_revision",
    "source_subject_fingerprint",
    "payload_commitment",
    "creator_assessment_ref",
    "creator_assessment_fingerprint",
    "predecessor_candidate_revision",
    "predecessor_candidate_ref",
    "predecessor_candidate_fingerprint",
    "created_event_sequence",
];

const CANDIDATE_DOMAIN: &str = "agents-os.m0b.home-candidate.v0.1";
const CANDIDATE_HISTORY_DOMAIN: &str = "agents-os.m0b.candidate-history.v0.1";

const PROMOTION_FIELDS: [&str; 9] = [
    "promotion_id",
    "promotion_revision",
    "source_candidate_ref",
    "source_candidate_revision",
    "source_candidate_fingerprint",
    "explicit_promotion_choice",
    "target_candidate_id",
    "target_created_event_sequence",
    "minimum_trusted_event_sequence",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CandidateSemanticClass {
    LifeStream,
    Memory,
    Intent,
}

impl CandidateSemanticClass {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::LifeStream => "LIFE_STREAM_CANDIDATE",
            Self::Memory => "MEMORY_CANDIDATE",
            Self::Intent => "INTENT_CANDIDATE",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CandidatePredecessor {
    pub candidate_revision: u64,
    pub candidate_ref: String,
    pub candidate_fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HomeCandidateRevision {
    pub candidate_id: String,
    pub candidate_revision: u64,
    pub candidate_ref: String,
    pub semantic_class: CandidateSemanticClass,
    pub source_subject_ref: String,
    pub source_subject_revision: u64,
    pub source_subject_fingerprint: String,
    pub payload_commitment: String,
    pub creator_assessment_ref: String,
    pub creator_assessment_fingerprint: String,
    pub predecessor: Option<CandidatePredecessor>,
    pub created_event_sequence: u64,
    pub canonical_bytes: Vec<u8>,
    pub candidate_fingerprint: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CandidateRevisionResult {
    Derived,
    ExactReplay,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExplicitPromotionChoice {
    ObserveWithoutPromotion,
    Discard,
    ProposeMemoryCandidate,
    ProposeIntentCandidate,
}

impl ExplicitPromotionChoice {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ObserveWithoutPromotion => "OBSERVE_WITHOUT_PROMOTION",
            Self::Discard => "DISCARD",
            Self::ProposeMemoryCandidate => "PROPOSE_MEMORY_CANDIDATE",
            Self::ProposeIntentCandidate => "PROPOSE_INTENT_CANDIDATE",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PromotionResult {
    ObservedNoFurtherPromotion,
    DiscardedNoFurtherPromotion,
    MemoryCandidateOnly,
    IntentCandidateOnly,
    Indeterminate,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PromotionDecision {
    pub result: PromotionResult,
    pub reason: &'static str,
    pub explicit_choice: Option<ExplicitPromotionChoice>,
    pub promotion_fingerprint: String,
    pub source_candidate_ref: Option<String>,
    pub derived_candidate: Option<HomeCandidateRevision>,
    pub canonical_write_count: u64,
    pub event_write_count: u64,
    pub action_authority: bool,
    pub task_write_authority: bool,
    pub command_authority: bool,
    pub memory_write_authority: bool,
    pub effect_authority: bool,
    pub runtime_usable: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CandidateRevisionDecision {
    pub result: CandidateRevisionResult,
    pub candidate: HomeCandidateRevision,
    pub canonical_write_count: u64,
    pub event_write_count: u64,
    pub action_authority: bool,
    pub task_write_authority: bool,
    pub command_authority: bool,
    pub memory_write_authority: bool,
    pub effect_authority: bool,
    pub runtime_usable: bool,
}

#[derive(Debug, thiserror::Error, Eq, PartialEq)]
pub enum CandidateError {
    #[error("candidate proposal is not valid strict canonical JSON")]
    MalformedCanonicalJson,
    #[error("candidate proposal bytes are not canonical JCS")]
    NonCanonicalBytes,
    #[error("candidate proposal schema is invalid: {0}")]
    InvalidSchema(&'static str),
    #[error("candidate history is not an exact immutable lineage: {0}")]
    InvalidHistory(&'static str),
    #[error("candidate revision is not contiguous with the exact current head")]
    StaleOrMissingHead,
    #[error("same candidate revision cannot be rewritten")]
    SameRevisionRewrite,
    #[error("promotion source is not the exact current Life Stream candidate")]
    InvalidPromotionSource,
}

pub fn reduce_explicit_promotion(
    input: &[u8],
    history: &[HomeCandidateRevision],
) -> Result<PromotionDecision, CandidateError> {
    validate_history(history)?;
    let value = parse_strict_json(input).map_err(|_| CandidateError::MalformedCanonicalJson)?;
    if to_jcs_bytes(&value) != input {
        return Err(CandidateError::NonCanonicalBytes);
    }

    let choice_is_missing = field_is_absent(&value, "explicit_promotion_choice")?;
    if choice_is_missing {
        let fields: Vec<&str> = PROMOTION_FIELDS
            .iter()
            .copied()
            .filter(|field| *field != "explicit_promotion_choice")
            .collect();
        value
            .require_exact_fields(&fields)
            .map_err(|_| CandidateError::InvalidSchema("closed promotion field inventory mismatch"))?;
    } else {
        value
            .require_exact_fields(&PROMOTION_FIELDS)
            .map_err(|_| CandidateError::InvalidSchema("closed promotion field inventory mismatch"))?;
    }

    require_synthetic_ref(&value, "promotion_id")?;
    require_positive_integer(&value, "promotion_revision")?;
    let source_ref = require_synthetic_ref(&value, "source_candidate_ref")?;
    let source_revision = require_positive_integer(&value, "source_candidate_revision")?;
    let source_fingerprint = require_hash(&value, "source_candidate_fingerprint")?;
    let minimum_sequence = require_positive_integer(&value, "minimum_trusted_event_sequence")?;
    let target_id = require_nullable_candidate_id(&value, "target_candidate_id")?;
    let target_event_sequence = require_nullable_positive_integer(
        &value,
        "target_created_event_sequence",
    )?;

    let source = exact_current_candidate(
        history,
        source_ref,
        source_revision,
        source_fingerprint,
    )?;
    if source.semantic_class != CandidateSemanticClass::LifeStream
        || source.created_event_sequence < minimum_sequence
    {
        return Err(CandidateError::InvalidPromotionSource);
    }

    if choice_is_missing {
        require_null_target(target_id, target_event_sequence)?;
        return Ok(promotion_decision(
            PromotionResult::Indeterminate,
            "EXPLICIT_LIFE_STREAM_CHOICE_MISSING",
            None,
            input,
            source,
            None,
        ));
    }

    let choice = match require_string(&value, "explicit_promotion_choice")? {
        "OBSERVE_WITHOUT_PROMOTION" => ExplicitPromotionChoice::ObserveWithoutPromotion,
        "DISCARD" => ExplicitPromotionChoice::Discard,
        "PROPOSE_MEMORY_CANDIDATE" => ExplicitPromotionChoice::ProposeMemoryCandidate,
        "PROPOSE_INTENT_CANDIDATE" => ExplicitPromotionChoice::ProposeIntentCandidate,
        _ => {
            require_null_target(target_id, target_event_sequence)?;
            return Ok(promotion_decision(
                PromotionResult::Indeterminate,
                "UNKNOWN_EXPLICIT_LIFE_STREAM_CHOICE",
                None,
                input,
                source,
                None,
            ));
        }
    };

    match choice {
        ExplicitPromotionChoice::ObserveWithoutPromotion => {
            require_null_target(target_id, target_event_sequence)?;
            Ok(promotion_decision(
                PromotionResult::ObservedNoFurtherPromotion,
                "VALID_OBSERVE",
                Some(choice),
                input,
                source,
                None,
            ))
        }
        ExplicitPromotionChoice::Discard => {
            require_null_target(target_id, target_event_sequence)?;
            Ok(promotion_decision(
                PromotionResult::DiscardedNoFurtherPromotion,
                "VALID_DISCARD",
                Some(choice),
                input,
                source,
                None,
            ))
        }
        ExplicitPromotionChoice::ProposeMemoryCandidate
        | ExplicitPromotionChoice::ProposeIntentCandidate => {
            let target_id = target_id.ok_or(CandidateError::InvalidSchema(
                "candidate proposal requires target candidate id",
            ))?;
            let target_event_sequence = target_event_sequence.ok_or(
                CandidateError::InvalidSchema(
                    "candidate proposal requires target Event sequence",
                ),
            )?;
            if target_event_sequence < minimum_sequence {
                return Err(CandidateError::InvalidSchema(
                    "target Event sequence is below the trusted minimum",
                ));
            }
            let semantic_class = match choice {
                ExplicitPromotionChoice::ProposeMemoryCandidate => {
                    CandidateSemanticClass::Memory
                }
                ExplicitPromotionChoice::ProposeIntentCandidate => {
                    CandidateSemanticClass::Intent
                }
                _ => unreachable!(),
            };
            let proposal = canonicalize_json(
                &serde_json::to_vec(&json!({
                    "candidate_id": target_id,
                    "candidate_revision": 1,
                    "created_event_sequence": target_event_sequence,
                    "creator_assessment_fingerprint": source.creator_assessment_fingerprint,
                    "creator_assessment_ref": source.creator_assessment_ref,
                    "payload_commitment": source.payload_commitment,
                    "predecessor_candidate_fingerprint": null,
                    "predecessor_candidate_ref": null,
                    "predecessor_candidate_revision": null,
                    "semantic_class": semantic_class.as_str(),
                    "source_subject_fingerprint": source.candidate_fingerprint,
                    "source_subject_ref": source.candidate_ref,
                    "source_subject_revision": source.candidate_revision
                }))
                .map_err(|_| CandidateError::InvalidSchema("promotion serialization failed"))?,
            )
            .map_err(|_| CandidateError::InvalidSchema("promotion canonicalization failed"))?;
            let candidate = derive_candidate_revision(&proposal, history)?.candidate;
            let (result, reason) = match choice {
                ExplicitPromotionChoice::ProposeMemoryCandidate => {
                    (PromotionResult::MemoryCandidateOnly, "VALID_MEMORY_CANDIDATE")
                }
                ExplicitPromotionChoice::ProposeIntentCandidate => {
                    (PromotionResult::IntentCandidateOnly, "VALID_INTENT_CANDIDATE")
                }
                _ => unreachable!(),
            };
            Ok(promotion_decision(
                result,
                reason,
                Some(choice),
                input,
                source,
                Some(candidate),
            ))
        }
    }
}

pub fn derive_candidate_revision(
    input: &[u8],
    history: &[HomeCandidateRevision],
) -> Result<CandidateRevisionDecision, CandidateError> {
    validate_history(history)?;
    let value = parse_strict_json(input).map_err(|_| CandidateError::MalformedCanonicalJson)?;
    if to_jcs_bytes(&value) != input {
        return Err(CandidateError::NonCanonicalBytes);
    }
    value
        .require_exact_fields(&PROPOSAL_FIELDS)
        .map_err(|_| CandidateError::InvalidSchema("closed field inventory mismatch"))?;

    let candidate_id = require_candidate_id(&value)?;
    let candidate_revision = require_positive_integer(&value, "candidate_revision")?;
    let semantic_class = require_semantic_class(&value)?;
    let source_subject_ref = require_synthetic_ref(&value, "source_subject_ref")?;
    let source_subject_revision = require_positive_integer(&value, "source_subject_revision")?;
    let source_subject_fingerprint = require_hash(&value, "source_subject_fingerprint")?;
    let payload_commitment = require_hash(&value, "payload_commitment")?;
    let creator_assessment_ref = require_synthetic_ref(&value, "creator_assessment_ref")?;
    let creator_assessment_fingerprint =
        require_hash(&value, "creator_assessment_fingerprint")?;
    let created_event_sequence = require_positive_integer(&value, "created_event_sequence")?;
    let predecessor = require_predecessor(&value)?;

    if candidate_revision == 1 && predecessor.is_some() {
        return Err(CandidateError::InvalidSchema(
            "revision 1 requires a null predecessor tuple",
        ));
    }
    if candidate_revision > 1 {
        let predecessor = predecessor.as_ref().ok_or(CandidateError::InvalidSchema(
            "revision greater than 1 requires a complete predecessor tuple",
        ))?;
        if predecessor.candidate_revision != candidate_revision - 1 {
            return Err(CandidateError::InvalidSchema(
                "predecessor revision must equal candidate revision minus 1",
            ));
        }
    }

    let candidate_ref = format!(
        "candidate:SYNTHETIC_TEST:{candidate_id}:{candidate_revision}"
    );
    let canonical_bytes = candidate_bytes(
        candidate_id,
        candidate_revision,
        &candidate_ref,
        semantic_class,
        source_subject_ref,
        source_subject_revision,
        source_subject_fingerprint,
        payload_commitment,
        creator_assessment_ref,
        creator_assessment_fingerprint,
        predecessor.as_ref(),
        created_event_sequence,
    )?;
    let candidate = HomeCandidateRevision {
        candidate_id: candidate_id.to_owned(),
        candidate_revision,
        candidate_ref,
        semantic_class,
        source_subject_ref: source_subject_ref.to_owned(),
        source_subject_revision,
        source_subject_fingerprint: source_subject_fingerprint.to_owned(),
        payload_commitment: payload_commitment.to_owned(),
        creator_assessment_ref: creator_assessment_ref.to_owned(),
        creator_assessment_fingerprint: creator_assessment_fingerprint.to_owned(),
        predecessor,
        created_event_sequence,
        candidate_fingerprint: sha256_hex(&canonical_bytes),
        canonical_bytes,
    };

    if let Some(existing) = history.iter().find(|existing| {
        existing.candidate_id == candidate.candidate_id
            && existing.candidate_revision == candidate.candidate_revision
    }) {
        if existing == &candidate {
            return Ok(decision(CandidateRevisionResult::ExactReplay, candidate));
        }
        return Err(CandidateError::SameRevisionRewrite);
    }
    if history
        .iter()
        .any(|existing| existing.candidate_ref == candidate.candidate_ref)
    {
        return Err(CandidateError::InvalidHistory(
            "candidate ref is already bound to another immutable identity",
        ));
    }

    match candidate.predecessor.as_ref() {
        None => {
            if history
                .iter()
                .any(|existing| existing.candidate_id == candidate.candidate_id)
            {
                return Err(CandidateError::StaleOrMissingHead);
            }
        }
        Some(predecessor) => {
            let head = history
                .iter()
                .filter(|existing| existing.candidate_id == candidate.candidate_id)
                .max_by_key(|existing| existing.candidate_revision)
                .ok_or(CandidateError::StaleOrMissingHead)?;
            if head.candidate_revision != predecessor.candidate_revision
                || head.candidate_ref != predecessor.candidate_ref
                || head.candidate_fingerprint != predecessor.candidate_fingerprint
            {
                return Err(CandidateError::StaleOrMissingHead);
            }
        }
    }

    Ok(decision(CandidateRevisionResult::Derived, candidate))
}

pub fn canonical_candidate_history_fingerprint(
    history: &[HomeCandidateRevision],
) -> Result<String, CandidateError> {
    validate_history(history)?;
    let mut ordered: Vec<&HomeCandidateRevision> = history.iter().collect();
    ordered.sort_by(|left, right| {
        left.candidate_id
            .as_bytes()
            .cmp(right.candidate_id.as_bytes())
            .then(left.candidate_revision.cmp(&right.candidate_revision))
    });
    if !ordered
        .iter()
        .zip(history.iter())
        .all(|(expected, actual)| std::ptr::eq(*expected, actual))
    {
        return Err(CandidateError::InvalidHistory(
            "candidate history is not in canonical identity and revision order",
        ));
    }
    let rows: Vec<_> = ordered
        .iter()
        .map(|candidate| {
            json!([
                candidate.candidate_id,
                candidate.candidate_revision,
                candidate.candidate_ref,
                candidate.candidate_fingerprint
            ])
        })
        .collect();
    let bytes = canonicalize_json(
        &serde_json::to_vec(&json!([CANDIDATE_HISTORY_DOMAIN, rows]))
            .map_err(|_| CandidateError::InvalidHistory("history serialization failed"))?,
    )
    .map_err(|_| CandidateError::InvalidHistory("history canonicalization failed"))?;
    Ok(sha256_hex(&bytes))
}

fn decision(
    result: CandidateRevisionResult,
    candidate: HomeCandidateRevision,
) -> CandidateRevisionDecision {
    CandidateRevisionDecision {
        result,
        candidate,
        canonical_write_count: 0,
        event_write_count: 0,
        action_authority: false,
        task_write_authority: false,
        command_authority: false,
        memory_write_authority: false,
        effect_authority: false,
        runtime_usable: false,
    }
}

fn promotion_decision(
    result: PromotionResult,
    reason: &'static str,
    explicit_choice: Option<ExplicitPromotionChoice>,
    input: &[u8],
    source: &HomeCandidateRevision,
    derived_candidate: Option<HomeCandidateRevision>,
) -> PromotionDecision {
    PromotionDecision {
        result,
        reason,
        explicit_choice,
        promotion_fingerprint: sha256_hex(input),
        source_candidate_ref: Some(source.candidate_ref.clone()),
        derived_candidate,
        canonical_write_count: 0,
        event_write_count: 0,
        action_authority: false,
        task_write_authority: false,
        command_authority: false,
        memory_write_authority: false,
        effect_authority: false,
        runtime_usable: false,
    }
}

fn exact_current_candidate<'a>(
    history: &'a [HomeCandidateRevision],
    candidate_ref: &str,
    candidate_revision: u64,
    candidate_fingerprint: &str,
) -> Result<&'a HomeCandidateRevision, CandidateError> {
    let candidate = history
        .iter()
        .find(|candidate| {
            candidate.candidate_ref == candidate_ref
                && candidate.candidate_revision == candidate_revision
                && candidate.candidate_fingerprint == candidate_fingerprint
        })
        .ok_or(CandidateError::InvalidPromotionSource)?;
    let current = history
        .iter()
        .filter(|other| other.candidate_id == candidate.candidate_id)
        .max_by_key(|other| other.candidate_revision)
        .ok_or(CandidateError::InvalidPromotionSource)?;
    if current.candidate_ref != candidate.candidate_ref
        || current.candidate_fingerprint != candidate.candidate_fingerprint
    {
        return Err(CandidateError::InvalidPromotionSource);
    }
    Ok(candidate)
}

fn require_null_target(
    target_id: Option<&str>,
    target_event_sequence: Option<u64>,
) -> Result<(), CandidateError> {
    if target_id.is_some() || target_event_sequence.is_some() {
        return Err(CandidateError::InvalidSchema(
            "nonpromotion choice requires a null target tuple",
        ));
    }
    Ok(())
}

fn validate_history(history: &[HomeCandidateRevision]) -> Result<(), CandidateError> {
    let mut identities = HashSet::new();
    let mut refs = HashSet::new();
    let mut fingerprints = HashSet::new();
    for candidate in history {
        if !identities.insert((candidate.candidate_id.as_str(), candidate.candidate_revision)) {
            return Err(CandidateError::InvalidHistory(
                "duplicate candidate identity and revision",
            ));
        }
        if !refs.insert(candidate.candidate_ref.as_str()) {
            return Err(CandidateError::InvalidHistory("duplicate candidate ref"));
        }
        if !fingerprints.insert(candidate.candidate_fingerprint.as_str()) {
            return Err(CandidateError::InvalidHistory(
                "duplicate candidate fingerprint",
            ));
        }
        validate_stored_candidate(candidate)?;
    }
    for candidate in history {
        match &candidate.predecessor {
            None if candidate.candidate_revision == 1 => {}
            Some(predecessor) if candidate.candidate_revision > 1 => {
                let parent = history.iter().find(|parent| {
                    parent.candidate_id == candidate.candidate_id
                        && parent.candidate_revision == predecessor.candidate_revision
                });
                let Some(parent) = parent else {
                    return Err(CandidateError::InvalidHistory(
                        "predecessor does not resolve",
                    ));
                };
                if predecessor.candidate_revision != candidate.candidate_revision - 1
                    || predecessor.candidate_ref != parent.candidate_ref
                    || predecessor.candidate_fingerprint != parent.candidate_fingerprint
                {
                    return Err(CandidateError::InvalidHistory(
                        "predecessor tuple is not exact",
                    ));
                }
            }
            _ => {
                return Err(CandidateError::InvalidHistory(
                    "genesis or advance predecessor shape is invalid",
                ));
            }
        }
    }
    Ok(())
}

/// Revalidates one materialized candidate against the same closed canonical
/// representation used by the F7 reducer. Persistence code must call this
/// before trusting caller-supplied struct fields or fingerprints.
pub(crate) fn validate_materialized_candidate(
    candidate: &HomeCandidateRevision,
) -> Result<(), CandidateError> {
    validate_stored_candidate(candidate)
}

fn validate_stored_candidate(candidate: &HomeCandidateRevision) -> Result<(), CandidateError> {
    if candidate.candidate_id.is_empty()
        || candidate.candidate_revision == 0
        || candidate.candidate_revision > MAX_SAFE_INTEGER as u64
    {
        return Err(CandidateError::InvalidHistory(
            "candidate identity or revision is invalid",
        ));
    }
    let expected_ref = format!(
        "candidate:SYNTHETIC_TEST:{}:{}",
        candidate.candidate_id, candidate.candidate_revision
    );
    if candidate.candidate_ref != expected_ref {
        return Err(CandidateError::InvalidHistory(
            "candidate ref formula mismatch",
        ));
    }
    let expected_bytes = candidate_bytes(
        &candidate.candidate_id,
        candidate.candidate_revision,
        &candidate.candidate_ref,
        candidate.semantic_class,
        &candidate.source_subject_ref,
        candidate.source_subject_revision,
        &candidate.source_subject_fingerprint,
        &candidate.payload_commitment,
        &candidate.creator_assessment_ref,
        &candidate.creator_assessment_fingerprint,
        candidate.predecessor.as_ref(),
        candidate.created_event_sequence,
    )?;
    if candidate.canonical_bytes != expected_bytes
        || candidate.candidate_fingerprint != sha256_hex(&expected_bytes)
    {
        return Err(CandidateError::InvalidHistory(
            "candidate canonical bytes or fingerprint changed",
        ));
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn candidate_bytes(
    candidate_id: &str,
    candidate_revision: u64,
    candidate_ref: &str,
    semantic_class: CandidateSemanticClass,
    source_subject_ref: &str,
    source_subject_revision: u64,
    source_subject_fingerprint: &str,
    payload_commitment: &str,
    creator_assessment_ref: &str,
    creator_assessment_fingerprint: &str,
    predecessor: Option<&CandidatePredecessor>,
    created_event_sequence: u64,
) -> Result<Vec<u8>, CandidateError> {
    canonicalize_json(
        &serde_json::to_vec(&json!([
            CANDIDATE_DOMAIN,
            {
                "candidate_id": candidate_id,
                "candidate_ref": candidate_ref,
                "candidate_revision": candidate_revision,
                "created_event_sequence": created_event_sequence,
                "creator_assessment_fingerprint": creator_assessment_fingerprint,
                "creator_assessment_ref": creator_assessment_ref,
                "payload_commitment": payload_commitment,
                "predecessor_candidate_fingerprint": predecessor.map(|value| value.candidate_fingerprint.as_str()),
                "predecessor_candidate_ref": predecessor.map(|value| value.candidate_ref.as_str()),
                "predecessor_candidate_revision": predecessor.map(|value| value.candidate_revision),
                "semantic_class": semantic_class.as_str(),
                "source_subject_fingerprint": source_subject_fingerprint,
                "source_subject_ref": source_subject_ref,
                "source_subject_revision": source_subject_revision
            }
        ]))
        .map_err(|_| CandidateError::InvalidSchema("candidate serialization failed"))?,
    )
    .map_err(|_| CandidateError::InvalidSchema("candidate canonicalization failed"))
}

fn field<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a CanonicalValue, CandidateError> {
    value
        .as_object()
        .map_err(|_| CandidateError::InvalidSchema("expected object"))?
        .iter()
        .find_map(|(key, value)| (key == name).then_some(value))
        .ok_or(CandidateError::InvalidSchema("required field is missing"))
}

fn field_is_absent(value: &CanonicalValue, name: &str) -> Result<bool, CandidateError> {
    Ok(!value
        .as_object()
        .map_err(|_| CandidateError::InvalidSchema("expected object"))?
        .iter()
        .any(|(key, _)| key == name))
}

fn require_string<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, CandidateError> {
    match field(value, name)? {
        CanonicalValue::String(value) => Ok(value),
        _ => Err(CandidateError::InvalidSchema("expected string")),
    }
}

fn require_candidate_id(value: &CanonicalValue) -> Result<&str, CandidateError> {
    let candidate_id = require_string(value, "candidate_id")?;
    if candidate_id.is_empty() {
        Err(CandidateError::InvalidSchema("candidate id must be nonempty"))
    } else {
        Ok(candidate_id)
    }
}

fn require_nullable_candidate_id<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<Option<&'a str>, CandidateError> {
    match field(value, name)? {
        CanonicalValue::Null => Ok(None),
        CanonicalValue::String(candidate_id) if !candidate_id.is_empty() => {
            Ok(Some(candidate_id))
        }
        _ => Err(CandidateError::InvalidSchema(
            "target candidate id must be null or a nonempty string",
        )),
    }
}

fn require_nullable_positive_integer(
    value: &CanonicalValue,
    name: &str,
) -> Result<Option<u64>, CandidateError> {
    match field(value, name)? {
        CanonicalValue::Null => Ok(None),
        CanonicalValue::Integer(integer) if (1..=MAX_SAFE_INTEGER).contains(integer) => {
            Ok(Some(*integer as u64))
        }
        _ => Err(CandidateError::InvalidSchema(
            "target Event sequence must be null or a positive safe integer",
        )),
    }
}

fn require_synthetic_ref<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, CandidateError> {
    let reference = require_string(value, name)?;
    if reference.is_empty() || !reference.contains(":SYNTHETIC_TEST:") {
        Err(CandidateError::InvalidSchema(
            "stable ref must be nonempty and synthetic-only",
        ))
    } else {
        Ok(reference)
    }
}

fn require_hash<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, CandidateError> {
    let hash = require_string(value, name)?;
    if hash.len() == 64
        && hash
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(hash)
    } else {
        Err(CandidateError::InvalidSchema(
            "expected lowercase SHA-256",
        ))
    }
}

fn require_positive_integer(
    value: &CanonicalValue,
    name: &str,
) -> Result<u64, CandidateError> {
    match field(value, name)? {
        CanonicalValue::Integer(integer) if (1..=MAX_SAFE_INTEGER).contains(integer) => {
            Ok(*integer as u64)
        }
        _ => Err(CandidateError::InvalidSchema(
            "expected positive safe integer",
        )),
    }
}

fn require_semantic_class(
    value: &CanonicalValue,
) -> Result<CandidateSemanticClass, CandidateError> {
    match require_string(value, "semantic_class")? {
        "LIFE_STREAM_CANDIDATE" => Ok(CandidateSemanticClass::LifeStream),
        "MEMORY_CANDIDATE" => Ok(CandidateSemanticClass::Memory),
        "INTENT_CANDIDATE" => Ok(CandidateSemanticClass::Intent),
        _ => Err(CandidateError::InvalidSchema(
            "semantic class is outside the closed M0-B registry",
        )),
    }
}

fn require_predecessor(
    value: &CanonicalValue,
) -> Result<Option<CandidatePredecessor>, CandidateError> {
    let revision = field(value, "predecessor_candidate_revision")?;
    let reference = field(value, "predecessor_candidate_ref")?;
    let fingerprint = field(value, "predecessor_candidate_fingerprint")?;
    match (revision, reference, fingerprint) {
        (CanonicalValue::Null, CanonicalValue::Null, CanonicalValue::Null) => Ok(None),
        (
            CanonicalValue::Integer(revision),
            CanonicalValue::String(reference),
            CanonicalValue::String(fingerprint),
        ) if (1..=MAX_SAFE_INTEGER).contains(revision)
            && !reference.is_empty()
            && reference.contains(":SYNTHETIC_TEST:")
            && fingerprint.len() == 64
            && fingerprint
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)) =>
        {
            Ok(Some(CandidatePredecessor {
                candidate_revision: *revision as u64,
                candidate_ref: reference.clone(),
                candidate_fingerprint: fingerprint.clone(),
            }))
        }
        _ => Err(CandidateError::InvalidSchema(
            "predecessor tuple must be all null or exact all-nonnull",
        )),
    }
}
