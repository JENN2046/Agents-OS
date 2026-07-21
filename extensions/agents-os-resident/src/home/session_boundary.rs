//! Synthetic Session observation decoding and the WP1 nonpromotion boundary.
//!
//! This module deliberately has no ledger or Resident dependency. A successful
//! reduction can therefore describe only a deterministic zero-write outcome;
//! it cannot create a candidate, Event, pointer, Inbox or Outbox row.

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::to_jcs_bytes;
use crate::canonical::types::{CanonicalValue, MAX_SAFE_INTEGER, parse_strict_json};

pub const MODULE_ID: &str = "agents-os.m0b.home.session-boundary.v0.1";
pub const IMPLEMENTATION_STATUS: &str = "WP1_NONPROMOTION_ACTIVE";
pub const CANONICAL_WRITE_AUTHORIZED: bool = false;
pub const RUNTIME_USABLE: bool = false;

const OBSERVATION_FIELDS: [&str; 12] = [
    "observation_id",
    "observation_revision",
    "session_ref",
    "session_revision",
    "source_subject_ref",
    "source_subject_revision",
    "source_subject_fingerprint",
    "payload_commitment",
    "creator_assessment_ref",
    "creator_assessment_fingerprint",
    "explicit_branch_choice",
    "trusted_event_sequence",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SessionBranchChoice {
    EphemeralOnly,
    Discard,
    RemainInSession,
    ProposeLifeStreamCandidate,
}

impl SessionBranchChoice {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::EphemeralOnly => "EPHEMERAL_ONLY",
            Self::Discard => "DISCARD",
            Self::RemainInSession => "REMAIN_IN_SESSION",
            Self::ProposeLifeStreamCandidate => "PROPOSE_LIFE_STREAM_CANDIDATE",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticSessionObservation {
    pub observation_id: String,
    pub observation_revision: u64,
    pub session_ref: String,
    pub session_revision: u64,
    pub source_subject_ref: String,
    pub source_subject_revision: u64,
    pub source_subject_fingerprint: String,
    pub payload_commitment: String,
    pub creator_assessment_ref: String,
    pub creator_assessment_fingerprint: String,
    pub explicit_branch_choice: SessionBranchChoice,
    pub trusted_event_sequence: u64,
    pub canonical_fingerprint: String,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct CanonicalWriteAccounting {
    pub candidate_rows: u64,
    pub event_rows: u64,
    pub pointer_rows: u64,
    pub inbox_rows: u64,
    pub outbox_rows: u64,
    pub goal_rows: u64,
    pub task_rows: u64,
}

impl CanonicalWriteAccounting {
    pub fn total(self) -> u64 {
        self.candidate_rows
            + self.event_rows
            + self.pointer_rows
            + self.inbox_rows
            + self.outbox_rows
            + self.goal_rows
            + self.task_rows
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NonpromotionDecision {
    pub result: &'static str,
    pub reason: &'static str,
    pub explicit_branch_choice: Option<SessionBranchChoice>,
    pub observation_fingerprint: String,
    pub canonical_writes: CanonicalWriteAccounting,
    pub candidate_authority: bool,
    pub task_write_authority: bool,
    pub command_authority: bool,
    pub effect_authority: bool,
    pub runtime_usable: bool,
}

#[derive(Debug, thiserror::Error, Eq, PartialEq)]
pub enum SessionBoundaryError {
    #[error("synthetic observation is not valid strict canonical JSON")]
    MalformedCanonicalJson,
    #[error("synthetic observation bytes are not canonical JCS")]
    NonCanonicalBytes,
    #[error("synthetic observation schema is invalid: {0}")]
    InvalidSchema(&'static str),
    #[error("synthetic observation has no explicit branch choice")]
    MissingBranch,
    #[error("synthetic observation branch choice is unknown")]
    UnknownBranch,
    #[error("candidate proposal belongs to the later WP2 boundary")]
    CandidateBranchNotImplemented,
}

pub fn decode_synthetic_observation(
    input: &[u8],
) -> Result<SyntheticSessionObservation, SessionBoundaryError> {
    let value = parse_strict_json(input)
        .map_err(|_| SessionBoundaryError::MalformedCanonicalJson)?;
    if to_jcs_bytes(&value) != input {
        return Err(SessionBoundaryError::NonCanonicalBytes);
    }
    let branch_is_missing = field_is_absent(&value, "explicit_branch_choice")?;
    if branch_is_missing {
        let without_branch: Vec<&str> = OBSERVATION_FIELDS
            .iter()
            .copied()
            .filter(|name| *name != "explicit_branch_choice")
            .collect();
        value
            .require_exact_fields(&without_branch)
            .map_err(|_| SessionBoundaryError::InvalidSchema("closed field inventory mismatch"))?;
    } else {
        value
            .require_exact_fields(&OBSERVATION_FIELDS)
            .map_err(|_| SessionBoundaryError::InvalidSchema("closed field inventory mismatch"))?;
    }

    let observation_id = require_synthetic_ref(&value, "observation_id")?;
    let observation_revision = require_positive_integer(&value, "observation_revision")?;
    let session_ref = require_synthetic_ref(&value, "session_ref")?;
    let session_revision = require_positive_integer(&value, "session_revision")?;
    let source_subject_ref = require_synthetic_ref(&value, "source_subject_ref")?;
    let source_subject_revision = require_positive_integer(&value, "source_subject_revision")?;
    let source_subject_fingerprint = require_hash(&value, "source_subject_fingerprint")?;
    let payload_commitment = require_hash(&value, "payload_commitment")?;
    let creator_assessment_ref = require_synthetic_ref(&value, "creator_assessment_ref")?;
    let creator_assessment_fingerprint = require_hash(&value, "creator_assessment_fingerprint")?;
    let trusted_event_sequence = require_positive_integer(&value, "trusted_event_sequence")?;
    if branch_is_missing {
        return Err(SessionBoundaryError::MissingBranch);
    }
    let explicit_branch_choice = match require_string(&value, "explicit_branch_choice")? {
        "EPHEMERAL_ONLY" => SessionBranchChoice::EphemeralOnly,
        "DISCARD" => SessionBranchChoice::Discard,
        "REMAIN_IN_SESSION" => SessionBranchChoice::RemainInSession,
        "PROPOSE_LIFE_STREAM_CANDIDATE" => SessionBranchChoice::ProposeLifeStreamCandidate,
        _ => return Err(SessionBoundaryError::UnknownBranch),
    };

    Ok(SyntheticSessionObservation {
        observation_id: observation_id.to_owned(),
        observation_revision,
        session_ref: session_ref.to_owned(),
        session_revision,
        source_subject_ref: source_subject_ref.to_owned(),
        source_subject_revision,
        source_subject_fingerprint: source_subject_fingerprint.to_owned(),
        payload_commitment: payload_commitment.to_owned(),
        creator_assessment_ref: creator_assessment_ref.to_owned(),
        creator_assessment_fingerprint: creator_assessment_fingerprint.to_owned(),
        explicit_branch_choice,
        trusted_event_sequence,
        canonical_fingerprint: sha256_hex(input),
    })
}

pub fn reduce_nonpromotion(input: &[u8]) -> Result<NonpromotionDecision, SessionBoundaryError> {
    let observation = match decode_synthetic_observation(input) {
        Ok(observation) => observation,
        Err(SessionBoundaryError::MissingBranch) => {
            return Ok(indeterminate_decision(input, "MISSING_BRANCH"));
        }
        Err(SessionBoundaryError::UnknownBranch) => {
            return Ok(indeterminate_decision(input, "UNKNOWN_BRANCH"));
        }
        Err(error) => return Err(error),
    };
    if observation.explicit_branch_choice == SessionBranchChoice::ProposeLifeStreamCandidate {
        return Err(SessionBoundaryError::CandidateBranchNotImplemented);
    }
    Ok(NonpromotionDecision {
        result: "NO_PROMOTION",
        reason: match observation.explicit_branch_choice {
            SessionBranchChoice::EphemeralOnly => "EPHEMERAL_ONLY",
            SessionBranchChoice::Discard => "DISCARD",
            SessionBranchChoice::RemainInSession => "REMAIN_IN_SESSION",
            SessionBranchChoice::ProposeLifeStreamCandidate => unreachable!(),
        },
        explicit_branch_choice: Some(observation.explicit_branch_choice),
        observation_fingerprint: observation.canonical_fingerprint,
        canonical_writes: CanonicalWriteAccounting::default(),
        candidate_authority: false,
        task_write_authority: false,
        command_authority: false,
        effect_authority: false,
        runtime_usable: false,
    })
}

fn indeterminate_decision(input: &[u8], reason: &'static str) -> NonpromotionDecision {
    NonpromotionDecision {
        result: "INDETERMINATE",
        reason,
        explicit_branch_choice: None,
        observation_fingerprint: sha256_hex(input),
        canonical_writes: CanonicalWriteAccounting::default(),
        candidate_authority: false,
        task_write_authority: false,
        command_authority: false,
        effect_authority: false,
        runtime_usable: false,
    }
}

fn field_is_absent(value: &CanonicalValue, name: &str) -> Result<bool, SessionBoundaryError> {
    Ok(!value
        .as_object()
        .map_err(|_| SessionBoundaryError::InvalidSchema("expected object"))?
        .iter()
        .any(|(key, _)| key == name))
}

fn field<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a CanonicalValue, SessionBoundaryError> {
    value
        .as_object()
        .map_err(|_| SessionBoundaryError::InvalidSchema("expected object"))?
        .iter()
        .find_map(|(key, value)| (key == name).then_some(value))
        .ok_or(SessionBoundaryError::InvalidSchema("required field is missing"))
}

fn require_string<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, SessionBoundaryError> {
    match field(value, name)? {
        CanonicalValue::String(value) => Ok(value),
        _ => Err(SessionBoundaryError::InvalidSchema("expected string")),
    }
}

fn require_synthetic_ref<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, SessionBoundaryError> {
    let reference = require_string(value, name)?;
    if reference.is_empty() || !reference.contains(":SYNTHETIC_TEST:") {
        Err(SessionBoundaryError::InvalidSchema(
            "stable ref must be nonempty and synthetic-only",
        ))
    } else {
        Ok(reference)
    }
}

fn require_hash<'a>(
    value: &'a CanonicalValue,
    name: &str,
) -> Result<&'a str, SessionBoundaryError> {
    let hash = require_string(value, name)?;
    if hash.len() == 64
        && hash
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        Ok(hash)
    } else {
        Err(SessionBoundaryError::InvalidSchema(
            "expected lowercase SHA-256",
        ))
    }
}

fn require_positive_integer(
    value: &CanonicalValue,
    name: &str,
) -> Result<u64, SessionBoundaryError> {
    match field(value, name)? {
        CanonicalValue::Integer(integer) if (1..=MAX_SAFE_INTEGER).contains(integer) => {
            Ok(*integer as u64)
        }
        _ => Err(SessionBoundaryError::InvalidSchema(
            "expected positive safe integer",
        )),
    }
}
