//! External-evidence continuity admission for the local-owner Resident.
//!
//! The Runtime derives a relation from raw local state and caller-supplied
//! external evidence. The caller remains responsible for admitting the
//! evidence source; Runtime output is never proof authority.

use std::collections::BTreeMap;

use serde_json::{Map, Value, json};

use super::{LocalOwnerError, PROFILE_ID};

pub const CONTINUITY_EVIDENCE_PROTOCOL: &str = "MMR0_CONTINUITY_EVIDENCE_V1";
pub const GENESIS_PROVISIONING_PROTOCOL: &str = "MMR0_GENESIS_PROVISIONING_V1";
const MAX_SAFE_INTEGER: u64 = 9_007_199_254_740_991;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ContinuityAnchor {
    pub resident_id: String,
    pub authority_epoch: u64,
    pub incarnation_id: String,
    pub epoch_fingerprint: String,
    pub event_sequence: u64,
    pub event_fingerprint: String,
}

impl ContinuityAnchor {
    pub fn as_json(&self) -> Value {
        json!({
            "authorityEpoch": self.authority_epoch,
            "epochFingerprint": self.epoch_fingerprint,
            "eventFingerprint": self.event_fingerprint,
            "eventSequence": self.event_sequence,
            "incarnationId": self.incarnation_id,
            "residentId": self.resident_id,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LocalContinuitySnapshot {
    pub current: Option<ContinuityAnchor>,
    pub authority_anchors: Vec<ContinuityAnchor>,
    pub event_fingerprints: BTreeMap<u64, String>,
}

impl LocalContinuitySnapshot {
    pub fn empty() -> Self {
        Self {
            current: None,
            authority_anchors: Vec::new(),
            event_fingerprints: BTreeMap::new(),
        }
    }

    pub fn is_empty(&self) -> bool {
        self.current.is_none()
            && self.authority_anchors.is_empty()
            && self.event_fingerprints.is_empty()
    }

    fn contains_anchor(&self, expected: &ContinuityAnchor) -> bool {
        self.authority_anchors.iter().any(|anchor| {
            anchor.resident_id == expected.resident_id
                && anchor.authority_epoch == expected.authority_epoch
                && anchor.incarnation_id == expected.incarnation_id
                && anchor.epoch_fingerprint == expected.epoch_fingerprint
        }) && self
            .event_fingerprints
            .get(&expected.event_sequence)
            .is_some_and(|fingerprint| fingerprint == &expected.event_fingerprint)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ContinuityRelation {
    Match,
    LocalDescendsFromWitness,
    LocalStale,
    SuccessorExists,
    LineageConflict,
    ExternalEvidenceUnavailable,
}

/// Exact checkpoint identity used by the P4-C authority plane.  The runtime
/// may parse and classify this identity, but never promotes its local copy to
/// an authoritative lineage source.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LineageNode {
    pub node_id: String,
    pub resident_id: String,
    pub incarnation_id: String,
    pub checkpoint_seq: u64,
    pub content_sha256: String,
    pub lineage_identity: String,
    pub parent_checkpoint_identity: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LineageEdge {
    pub from: String,
    pub to: String,
    pub kind: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReferenceDag {
    pub nodes: BTreeMap<String, LineageNode>,
    pub edges: Vec<LineageEdge>,
    pub canonical_node_id: String,
}

/// A11's authority vocabulary, deliberately distinct from the historical
/// compatibility strings emitted by `ContinuityRelation::as_str()`.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AuthorityRelation {
    Same,
    Descendant,
    AncestorStale,
    SuccessorExists,
    Incomparable,
    EvidenceUnavailable,
}

impl AuthorityRelation {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Same => "SAME",
            Self::Descendant => "DESCENDANT",
            Self::AncestorStale => "ANCESTOR_STALE",
            Self::SuccessorExists => "SUCCESSOR_EXISTS",
            Self::Incomparable => "INCOMPARABLE",
            Self::EvidenceUnavailable => "EVIDENCE_UNAVAILABLE",
        }
    }

    fn continuity_relation(self) -> ContinuityRelation {
        match self {
            Self::Same => ContinuityRelation::Match,
            Self::Descendant => ContinuityRelation::LocalDescendsFromWitness,
            Self::AncestorStale => ContinuityRelation::LocalStale,
            Self::SuccessorExists => ContinuityRelation::SuccessorExists,
            Self::Incomparable => ContinuityRelation::LineageConflict,
            Self::EvidenceUnavailable => ContinuityRelation::ExternalEvidenceUnavailable,
        }
    }
}

/// Pure A11 classifier.  Every positive relation is established from exact
/// node identity or explicit DAG reachability; counters and ordering metadata
/// are intentionally absent from this function.
pub fn classify_reference_dag(local: &LineageNode, dag: &ReferenceDag) -> AuthorityRelation {
    let Some(local_node) = dag.nodes.get(&local.node_id) else {
        return AuthorityRelation::Incomparable;
    };
    if local_node != local {
        return AuthorityRelation::Incomparable;
    }

    let Some(canonical) = dag.nodes.get(&dag.canonical_node_id) else {
        return AuthorityRelation::Incomparable;
    };
    if canonical == local {
        return AuthorityRelation::Same;
    }

    if canonical.resident_id == local.resident_id {
        if has_path(dag, &local.node_id, &dag.canonical_node_id) {
            return if canonical.incarnation_id == local.incarnation_id {
                AuthorityRelation::AncestorStale
            } else {
                AuthorityRelation::SuccessorExists
            };
        }
        if has_path(dag, &dag.canonical_node_id, &local.node_id) {
            return AuthorityRelation::Descendant;
        }
    }

    if dag.nodes.values().any(|other| {
        other.incarnation_id != local.incarnation_id
            && other.resident_id == local.resident_id
            && other.lineage_identity != local.lineage_identity
            && has_path(dag, &local.node_id, &other.node_id)
    }) {
        return AuthorityRelation::SuccessorExists;
    }
    AuthorityRelation::Incomparable
}

#[cfg(test)]
pub fn parse_test_reference_dag(
    local: &Value,
    dag: &Value,
) -> Result<(LineageNode, ReferenceDag), LocalOwnerError> {
    Ok((parse_lineage_node(local)?, parse_reference_dag(dag)?))
}

fn has_path(dag: &ReferenceDag, from: &str, to: &str) -> bool {
    let mut pending = vec![from.to_owned()];
    let mut seen = std::collections::BTreeSet::new();
    while let Some(current) = pending.pop() {
        if !seen.insert(current.clone()) {
            continue;
        }
        for edge in &dag.edges {
            if edge.from == current {
                if edge.to == to {
                    return true;
                }
                pending.push(edge.to.clone());
            }
        }
    }
    false
}

impl ContinuityRelation {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Match => "MATCH",
            Self::LocalDescendsFromWitness => "LOCAL_DESCENDS_FROM_WITNESS",
            Self::LocalStale => "LOCAL_STALE",
            Self::SuccessorExists => "SUCCESSOR_EXISTS",
            Self::LineageConflict => "LINEAGE_CONFLICT",
            Self::ExternalEvidenceUnavailable => "EXTERNAL_EVIDENCE_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Debug)]
pub struct ContinuityAdmission {
    pub relation: ContinuityRelation,
    pub admitted: bool,
    pub genesis_authorized: bool,
    pub mutation_eligible: bool,
    pub evidence_id: Option<String>,
    pub witness_id: Option<String>,
    pub provisioning_authority_id: Option<String>,
    pub local: Option<ContinuityAnchor>,
    pub witness: Option<ContinuityAnchor>,
    pub reason: &'static str,
    pub authority_relation: Option<AuthorityRelation>,
    pub grant_count: u64,
}

impl ContinuityAdmission {
    pub fn as_json(&self) -> Value {
        json!({
            "activationAuthorized": self.admitted,
            "authorityRelation": self.authority_relation.map(AuthorityRelation::as_str),
            "evidenceId": self.evidence_id,
            "genesisAuthorized": self.genesis_authorized,
            "grantCount": self.grant_count,
            "grantValid": self.grant_count == 1,
            "localAnchor": self.local.as_ref().map(ContinuityAnchor::as_json),
            "mutationEligible": self.mutation_eligible,
            "provisioningAuthorityId": self.provisioning_authority_id,
            "reason": self.reason,
            "relation": self.relation.as_str(),
            "result": if self.admitted { "PASS" } else { "DENY" },
            "witnessAnchor": self.witness.as_ref().map(ContinuityAnchor::as_json),
            "witnessId": self.witness_id,
        })
    }

    pub fn denial_error(&self) -> LocalOwnerError {
        match self.relation {
            ContinuityRelation::LocalStale => LocalOwnerError::ContinuityLocalStale,
            ContinuityRelation::SuccessorExists => LocalOwnerError::ContinuitySuccessorExists,
            ContinuityRelation::LineageConflict => LocalOwnerError::ContinuityLineageConflict,
            ContinuityRelation::ExternalEvidenceUnavailable => {
                LocalOwnerError::ContinuityEvidenceUnavailable
            }
            ContinuityRelation::Match | ContinuityRelation::LocalDescendsFromWitness => {
                LocalOwnerError::ContinuityAdmissionDenied
            }
        }
    }
}

#[derive(Clone, Debug)]
enum ExternalEvidence {
    Unavailable {
        evidence_id: String,
        witness_id: String,
    },
    Empty {
        evidence_id: String,
        witness_id: String,
    },
    Present {
        evidence_id: String,
        witness_id: String,
        current: ContinuityAnchor,
        ancestors: Vec<ContinuityAnchor>,
    },
    ReferenceDag {
        evidence_id: String,
        witness_id: String,
        local: LineageNode,
        dag: ReferenceDag,
    },
}

#[derive(Clone, Debug)]
struct ProvisioningAuthority {
    authority_id: String,
}

pub fn derive_admission(
    local: &LocalContinuitySnapshot,
    raw_evidence: Option<&Value>,
    raw_provisioning: Option<&Value>,
) -> Result<ContinuityAdmission, LocalOwnerError> {
    let Some(raw_evidence) = raw_evidence else {
        return Ok(denied(
            local.current.clone(),
            None,
            None,
            None,
            None,
            ContinuityRelation::ExternalEvidenceUnavailable,
            "EXTERNAL_EVIDENCE_NOT_SUPPLIED",
        ));
    };
    let evidence = parse_evidence(raw_evidence)?;
    let provisioning = raw_provisioning.map(parse_provisioning).transpose()?;

    match evidence {
        ExternalEvidence::Unavailable {
            evidence_id,
            witness_id,
        } => Ok(denied(
            local.current.clone(),
            None,
            Some(evidence_id),
            Some(witness_id),
            provisioning.map(|value| value.authority_id),
            ContinuityRelation::ExternalEvidenceUnavailable,
            "EXTERNAL_EVIDENCE_UNAVAILABLE",
        )),
        ExternalEvidence::Empty {
            evidence_id,
            witness_id,
        } => {
            if !local.is_empty() {
                return Ok(denied(
                    local.current.clone(),
                    None,
                    Some(evidence_id),
                    Some(witness_id),
                    provisioning.map(|value| value.authority_id),
                    ContinuityRelation::LineageConflict,
                    "WITNESS_EMPTY_BUT_LOCAL_PRESENT",
                ));
            }
            let Some(provisioning) = provisioning else {
                return Ok(denied(
                    None,
                    None,
                    Some(evidence_id),
                    Some(witness_id),
                    None,
                    ContinuityRelation::LineageConflict,
                    "GENESIS_PROVISIONING_AUTHORITY_MISSING",
                ));
            };
            Ok(ContinuityAdmission {
                relation: ContinuityRelation::Match,
                admitted: true,
                genesis_authorized: true,
                mutation_eligible: true,
                evidence_id: Some(evidence_id),
                witness_id: Some(witness_id),
                provisioning_authority_id: Some(provisioning.authority_id),
                local: None,
                witness: None,
                reason: "EXPLICIT_GENESIS_AUTHORIZED",
                authority_relation: Some(AuthorityRelation::Same),
                grant_count: 1,
            })
        }
        ExternalEvidence::Present {
            evidence_id,
            witness_id,
            current: witness,
            ancestors,
        } => {
            if provisioning.is_some() {
                return Err(LocalOwnerError::InvalidInput);
            }
            let Some(local_current) = local.current.clone() else {
                return Ok(denied(
                    None,
                    Some(witness),
                    Some(evidence_id),
                    Some(witness_id),
                    None,
                    ContinuityRelation::LocalStale,
                    "LOCAL_HISTORY_ABSENT_WHILE_WITNESS_PRESENT",
                ));
            };
            let relation = derive_present_relation(local, &local_current, &witness, &ancestors);
            let admitted = matches!(
                relation,
                ContinuityRelation::Match | ContinuityRelation::LocalDescendsFromWitness
            );
            Ok(ContinuityAdmission {
                relation,
                admitted,
                genesis_authorized: false,
                mutation_eligible: admitted,
                evidence_id: Some(evidence_id),
                witness_id: Some(witness_id),
                provisioning_authority_id: None,
                local: Some(local_current),
                witness: Some(witness),
                reason: relation_reason(relation),
                authority_relation: None,
                grant_count: if admitted { 1 } else { 0 },
            })
        }
        ExternalEvidence::ReferenceDag { evidence_id, witness_id, local, dag } => {
            let authority_relation = classify_reference_dag(&local, &dag);
            let relation = authority_relation.continuity_relation();
            let admitted = matches!(authority_relation, AuthorityRelation::Same | AuthorityRelation::Descendant);
            Ok(ContinuityAdmission {
                relation,
                admitted,
                genesis_authorized: false,
                mutation_eligible: admitted,
                evidence_id: Some(evidence_id),
                witness_id: Some(witness_id),
                provisioning_authority_id: None,
                local: None,
                witness: None,
                reason: relation_reason(relation),
                authority_relation: Some(authority_relation),
                grant_count: if admitted { 1 } else { 0 },
            })
        }
    }
}

fn derive_present_relation(
    local: &LocalContinuitySnapshot,
    local_current: &ContinuityAnchor,
    witness: &ContinuityAnchor,
    witness_ancestors: &[ContinuityAnchor],
) -> ContinuityRelation {
    if local_current.resident_id != witness.resident_id || witness.resident_id != PROFILE_ID {
        return ContinuityRelation::LineageConflict;
    }
    if local_current.authority_epoch == witness.authority_epoch
        && local_current.incarnation_id == witness.incarnation_id
    {
        if local_current.epoch_fingerprint != witness.epoch_fingerprint {
            return ContinuityRelation::LineageConflict;
        }
        return match local_current.event_sequence.cmp(&witness.event_sequence) {
            std::cmp::Ordering::Equal => {
                if local_current.event_fingerprint == witness.event_fingerprint {
                    ContinuityRelation::Match
                } else {
                    ContinuityRelation::LineageConflict
                }
            }
            std::cmp::Ordering::Greater => {
                if local
                    .event_fingerprints
                    .get(&witness.event_sequence)
                    .is_some_and(|value| value == &witness.event_fingerprint)
                {
                    ContinuityRelation::LocalDescendsFromWitness
                } else {
                    ContinuityRelation::LineageConflict
                }
            }
            std::cmp::Ordering::Less => ContinuityRelation::LocalStale,
        };
    }
    if witness_ancestors.iter().any(|anchor| anchor == local_current) {
        return ContinuityRelation::SuccessorExists;
    }
    if local.contains_anchor(witness) {
        return ContinuityRelation::LocalDescendsFromWitness;
    }
    ContinuityRelation::LineageConflict
}

fn denied(
    local: Option<ContinuityAnchor>,
    witness: Option<ContinuityAnchor>,
    evidence_id: Option<String>,
    witness_id: Option<String>,
    provisioning_authority_id: Option<String>,
    relation: ContinuityRelation,
    reason: &'static str,
) -> ContinuityAdmission {
    ContinuityAdmission {
        relation,
        admitted: false,
        genesis_authorized: false,
        mutation_eligible: false,
        evidence_id,
        witness_id,
        provisioning_authority_id,
        local,
        witness,
        reason,
        authority_relation: None,
        grant_count: 0,
    }
}

fn relation_reason(relation: ContinuityRelation) -> &'static str {
    match relation {
        ContinuityRelation::Match => "LOCAL_AND_WITNESS_MATCH",
        ContinuityRelation::LocalDescendsFromWitness => "LOCAL_PROVEN_DESCENDANT",
        ContinuityRelation::LocalStale => "LOCAL_BEHIND_WITNESS",
        ContinuityRelation::SuccessorExists => "WITNESS_PROVES_SUCCESSOR",
        ContinuityRelation::LineageConflict => "LINEAGE_RELATION_NOT_PROVEN",
        ContinuityRelation::ExternalEvidenceUnavailable => "EXTERNAL_EVIDENCE_UNAVAILABLE",
    }
}

fn parse_evidence(value: &Value) -> Result<ExternalEvidence, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    let availability = required_string(object, "availability", 32)?;
    match availability {
        "UNAVAILABLE" => {
            require_exact_keys(object, &["availability", "evidenceId", "protocol", "witnessId"])?;
            require_protocol(object, CONTINUITY_EVIDENCE_PROTOCOL)?;
            Ok(ExternalEvidence::Unavailable {
                evidence_id: required_string(object, "evidenceId", 200)?.to_owned(),
                witness_id: required_string(object, "witnessId", 200)?.to_owned(),
            })
        }
        "AVAILABLE" => {
            let state = required_string(object, "state", 32)?;
            match state {
                "EMPTY" => {
                    require_exact_keys(
                        object,
                        &["availability", "evidenceId", "protocol", "state", "witnessId"],
                    )?;
                    require_protocol(object, CONTINUITY_EVIDENCE_PROTOCOL)?;
                    Ok(ExternalEvidence::Empty {
                        evidence_id: required_string(object, "evidenceId", 200)?.to_owned(),
                        witness_id: required_string(object, "witnessId", 200)?.to_owned(),
                    })
                }
                "PRESENT" => {
                    if object.contains_key("referenceDag") {
                        require_exact_keys(
                            object,
                            &[
                                "availability", "evidenceId", "localNode", "protocol",
                                "referenceDag", "state", "witnessId",
                            ],
                        )?;
                        require_protocol(object, CONTINUITY_EVIDENCE_PROTOCOL)?;
                        return Ok(ExternalEvidence::ReferenceDag {
                            evidence_id: required_string(object, "evidenceId", 200)?.to_owned(),
                            witness_id: required_string(object, "witnessId", 200)?.to_owned(),
                            local: parse_lineage_node(object.get("localNode").ok_or(LocalOwnerError::InvalidInput)?)?,
                            dag: parse_reference_dag(object.get("referenceDag").ok_or(LocalOwnerError::InvalidInput)?)?,
                        });
                    }
                    require_exact_keys(
                        object,
                        &[
                            "ancestorAnchors",
                            "availability",
                            "current",
                            "evidenceId",
                            "protocol",
                            "state",
                            "witnessId",
                        ],
                    )?;
                    require_protocol(object, CONTINUITY_EVIDENCE_PROTOCOL)?;
                    let current = parse_anchor(object.get("current").ok_or(LocalOwnerError::InvalidInput)?)?;
                    let raw_ancestors = object
                        .get("ancestorAnchors")
                        .and_then(Value::as_array)
                        .ok_or(LocalOwnerError::InvalidInput)?;
                    if raw_ancestors.len() > 4096 {
                        return Err(LocalOwnerError::InvalidInput);
                    }
                    let ancestors = raw_ancestors
                        .iter()
                        .map(parse_anchor)
                        .collect::<Result<Vec<_>, _>>()?;
                    Ok(ExternalEvidence::Present {
                        evidence_id: required_string(object, "evidenceId", 200)?.to_owned(),
                        witness_id: required_string(object, "witnessId", 200)?.to_owned(),
                        current,
                        ancestors,
                    })
                }
                _ => Err(LocalOwnerError::InvalidInput),
            }
        }
        _ => Err(LocalOwnerError::InvalidInput),
    }
}

fn parse_provisioning(value: &Value) -> Result<ProvisioningAuthority, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_keys(
        object,
        &["authorityId", "protocol", "provisioningId", "residentId"],
    )?;
    require_protocol(object, GENESIS_PROVISIONING_PROTOCOL)?;
    if required_string(object, "residentId", 200)? != PROFILE_ID {
        return Err(LocalOwnerError::InvalidInput);
    }
    required_string(object, "provisioningId", 200)?;
    Ok(ProvisioningAuthority {
        authority_id: required_string(object, "authorityId", 200)?.to_owned(),
    })
}

fn parse_anchor(value: &Value) -> Result<ContinuityAnchor, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_keys(
        object,
        &[
            "authorityEpoch",
            "epochFingerprint",
            "eventFingerprint",
            "eventSequence",
            "incarnationId",
            "residentId",
        ],
    )?;
    let authority_epoch = required_u64(object, "authorityEpoch")?;
    let event_sequence = required_u64(object, "eventSequence")?;
    if authority_epoch == 0 || event_sequence == 0 {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(ContinuityAnchor {
        resident_id: required_string(object, "residentId", 200)?.to_owned(),
        authority_epoch,
        incarnation_id: required_string(object, "incarnationId", 300)?.to_owned(),
        epoch_fingerprint: required_hash(object, "epochFingerprint")?.to_owned(),
        event_sequence,
        event_fingerprint: required_hash(object, "eventFingerprint")?.to_owned(),
    })
}

fn parse_lineage_node(value: &Value) -> Result<LineageNode, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_keys(object, &[
        "checkpointSeq", "contentSha256", "incarnationId", "lineageIdentity",
        "nodeId", "parentCheckpointIdentity", "residentId",
    ])?;
    let checkpoint_seq = required_u64(object, "checkpointSeq")?;
    if checkpoint_seq == 0 {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(LineageNode {
        node_id: required_string(object, "nodeId", 300)?.to_owned(),
        resident_id: required_string(object, "residentId", 200)?.to_owned(),
        incarnation_id: required_string(object, "incarnationId", 300)?.to_owned(),
        checkpoint_seq,
        content_sha256: required_hash(object, "contentSha256")?.to_owned(),
        lineage_identity: required_string(object, "lineageIdentity", 300)?.to_owned(),
        parent_checkpoint_identity: object.get("parentCheckpointIdentity")
            .and_then(Value::as_str).map(str::to_owned),
    })
}

fn parse_reference_dag(value: &Value) -> Result<ReferenceDag, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    require_exact_keys(object, &["canonicalNodeId", "edges", "nodes"])?;
    let canonical_node_id = required_string(object, "canonicalNodeId", 300)?.to_owned();
    let raw_nodes = object.get("nodes").and_then(Value::as_array).ok_or(LocalOwnerError::InvalidInput)?;
    if raw_nodes.is_empty() || raw_nodes.len() > 4096 {
        return Err(LocalOwnerError::InvalidInput);
    }
    let mut nodes = BTreeMap::new();
    for value in raw_nodes {
        let node = parse_lineage_node(value)?;
        if nodes.insert(node.node_id.clone(), node).is_some() {
            return Err(LocalOwnerError::InvalidInput);
        }
    }
    let raw_edges = object.get("edges").and_then(Value::as_array).ok_or(LocalOwnerError::InvalidInput)?;
    if raw_edges.len() > 16384 {
        return Err(LocalOwnerError::InvalidInput);
    }
    let mut edges = Vec::with_capacity(raw_edges.len());
    for value in raw_edges {
        let edge = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
        require_exact_keys(edge, &["from", "kind", "to"])?;
        let from = required_string(edge, "from", 300)?.to_owned();
        let to = required_string(edge, "to", 300)?.to_owned();
        if !nodes.contains_key(&from) || !nodes.contains_key(&to) || from == to {
            return Err(LocalOwnerError::InvalidInput);
        }
        edges.push(LineageEdge { from, to, kind: required_string(edge, "kind", 100)?.to_owned() });
    }
    if !nodes.contains_key(&canonical_node_id) {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(ReferenceDag { nodes, edges, canonical_node_id })
}

fn require_exact_keys(object: &Map<String, Value>, expected: &[&str]) -> Result<(), LocalOwnerError> {
    if object.len() != expected.len() || expected.iter().any(|key| !object.contains_key(*key)) {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

fn require_protocol(object: &Map<String, Value>, expected: &str) -> Result<(), LocalOwnerError> {
    if required_string(object, "protocol", 100)? != expected {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

fn required_string<'a>(
    object: &'a Map<String, Value>,
    key: &str,
    max: usize,
) -> Result<&'a str, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty() && value.len() <= max && !value.contains('\0'))
        .ok_or(LocalOwnerError::InvalidInput)
}

fn required_hash<'a>(object: &'a Map<String, Value>, key: &str) -> Result<&'a str, LocalOwnerError> {
    let value = required_string(object, key, 64)?;
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(value)
    } else {
        Err(LocalOwnerError::InvalidInput)
    }
}

fn required_u64(object: &Map<String, Value>, key: &str) -> Result<u64, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_u64)
        .filter(|value| *value <= MAX_SAFE_INTEGER)
        .ok_or(LocalOwnerError::InvalidInput)
}
