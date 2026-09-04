//! Read-only Presence projection and stateless provider-attempt sealing.
//!
//! This module deliberately owns no persistence.  It resolves canonical
//! Resident state, projects only low-disclosure references, and binds an
//! individual provider attempt to a freshly re-read Presence generation.

use std::collections::BTreeSet;

use rusqlite::Connection;
use serde_json::{Map, Value, json};

use crate::canonical::fingerprint::sha256_hex;

use super::LocalOwnerError;
use super::continuity::ContinuityAdmission;
use super::memory::{
    MEMORY_AUTHORITY_SCHEMA, MEMORY_CANDIDATE_PREFIX, MEMORY_ID_PREFIX, MEMORY_INVENTORY_SCHEMA,
    MEMORY_INVENTORY_SLOT, MemoryBodyVerifier, descriptor_from_authority_content,
};
use super::store::{
    canonical_value_bytes, domain_fingerprint, read_candidate_current, read_mmr_current,
};
use super::work_source;

pub const PRESENCE_CONTEXT_SCHEMA: &str = "AGENTS_OS_PRESENCE_CONTEXT_V1";
pub const PROVIDER_ATTEMPT_SEAL_SCHEMA: &str = "AGENTS_OS_PROVIDER_ATTEMPT_SEAL_V1";

const ONE_RING_SLOT: &str = "state:presence:onering-binding:v1";
const LIFE_SLOT: &str = "state:presence:life:v1";
const ONE_RING_BINDING_SCHEMA: &str = "AGENTS_OS_ONERING_IDENTITY_BINDING_V1";
const LIFE_CATEGORY: &str = "EXPLICITLY_ADOPTED_LIFE_CONTEXT";
const MAX_SAFE_INTEGER: u64 = 9_007_199_254_740_991;
const MAX_CANDIDATES: usize = 16;
const MAX_FRONTEND_SOURCES: usize = 16;

#[derive(Clone, Debug)]
struct AcceptedIdentity {
    authority_generation: u64,
    opaque_id: String,
}

#[derive(Clone, Debug)]
struct OneRingInput {
    external_key_digest: Option<String>,
    frontend_plane: Option<String>,
    frontend_principal_digest: Option<String>,
    frontend_source: Option<String>,
    request_hash: Option<String>,
    turn_id: Option<String>,
}

#[derive(Clone, Debug)]
struct ExpectedSlots {
    life: Option<String>,
    memory: Option<String>,
    one_ring: Option<String>,
    work: Option<String>,
}

#[derive(Clone, Debug)]
struct PresenceRequest {
    attachment_generation: u64,
    expected: ExpectedSlots,
    fresh_presence_id: String,
    one_ring: OneRingInput,
    transcript_digest: String,
}

pub(super) fn query_presence_context(
    connection: &Connection,
    memory_body_verifier: Option<&MemoryBodyVerifier>,
    input: &Value,
    admission: &ContinuityAdmission,
) -> Result<Value, LocalOwnerError> {
    let request = parse_presence_request(input)?;
    let projection_generation = projection_generation(connection)?;
    let identity = accepted_identity(connection, admission)?;
    let memory = memory_projection(
        connection,
        memory_body_verifier,
        request.expected.memory.as_deref(),
        &request.fresh_presence_id,
        &identity,
    )?;
    let one_ring = one_ring_projection(
        connection,
        &request.one_ring,
        request.expected.one_ring.as_deref(),
        &identity,
    )?;
    let work = work_projection(connection, request.expected.work.as_deref(), &identity)?;
    let life = life_projection(connection, request.expected.life.as_deref())?;
    let witness = witness_projection(admission)?;
    let provider_attempt_eligible = one_ring["binding"] == "BOUND";

    let material = json!({
        "attachmentGeneration": request.attachment_generation,
        "capabilities": {
            "memoryBodyEnabled": memory_body_verifier.is_some(),
            "providerEnabled": false,
        },
        "freshPresenceId": request.fresh_presence_id,
        "identity": {
            "authorityGeneration": identity.authority_generation,
            "opaqueId": identity.opaque_id,
        },
        "life": life,
        "memory": memory,
        "oneRing": one_ring,
        "projectionGeneration": projection_generation,
        "providerAttemptEligible": provider_attempt_eligible,
        "schema": PRESENCE_CONTEXT_SCHEMA,
        "transcriptDigest": format!("sha256:{}", request.transcript_digest),
        "witness": witness,
        "work": work,
    });
    let context_id = format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.presence-context.v1",
            &canonical_value_bytes(&material)?,
        )
    );
    let mut response = material
        .as_object()
        .cloned()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    response.insert("accepted".to_owned(), Value::Bool(true));
    response.insert("contextId".to_owned(), Value::String(context_id));
    response.insert(
        "resultCode".to_owned(),
        Value::String("PRESENCE_CONTEXT_READ_ONLY_OK".to_owned()),
    );
    Ok(Value::Object(response))
}

pub(super) fn seal_provider_attempt(
    connection: &Connection,
    memory_body_verifier: Option<&MemoryBodyVerifier>,
    input: &Value,
    admission: &ContinuityAdmission,
) -> Result<Value, LocalOwnerError> {
    let object = exact_object(
        input,
        &[
            "attempt",
            "expectedAuthorityGeneration",
            "expectedContextId",
            "expectedProjectionGeneration",
            "presenceRequest",
        ],
    )?;
    let expected_authority_generation = safe_u64(object.get("expectedAuthorityGeneration"), true)?;
    let expected_context_id = prefixed_sha256(object.get("expectedContextId"))?;
    let expected_generation = safe_u64(object.get("expectedProjectionGeneration"), false)?;
    let current = query_presence_context(
        connection,
        memory_body_verifier,
        object
            .get("presenceRequest")
            .ok_or(LocalOwnerError::InvalidInput)?,
        admission,
    )?;
    if current["identity"]["authorityGeneration"] != expected_authority_generation
        || current["contextId"] != expected_context_id
        || current["projectionGeneration"] != expected_generation
    {
        return Err(LocalOwnerError::PresenceContextStale);
    }
    if current["providerAttemptEligible"] != true || current["oneRing"]["binding"] != "BOUND" {
        return Err(LocalOwnerError::PresenceBindingDenied);
    }

    let attempt = exact_object(
        object.get("attempt").ok_or(LocalOwnerError::InvalidInput)?,
        &[
            "attemptId",
            "bodyByteLength",
            "bodySha256",
            "credentialSlotRef",
            "method",
            "ordinal",
            "providerPathId",
            "selectedModelSha256",
            "targetSha256",
        ],
    )?;
    let attempt_id = opaque_string(attempt.get("attemptId"), 200)?;
    let ordinal = safe_u64(attempt.get("ordinal"), true)?;
    let method = ascii_token(attempt.get("method"), 16)?;
    if method != "POST" {
        return Err(LocalOwnerError::InvalidInput);
    }
    let provider_path_id = ascii_token(attempt.get("providerPathId"), 64)?;
    if provider_path_id != "VCP-CHAT-COMPLETIONS" {
        return Err(LocalOwnerError::InvalidInput);
    }
    let body_byte_length = safe_u64(attempt.get("bodyByteLength"), false)?;
    let body_sha256 = prefixed_sha256(attempt.get("bodySha256"))?;
    let target_sha256 = prefixed_sha256(attempt.get("targetSha256"))?;
    let selected_model_sha256 = prefixed_sha256(attempt.get("selectedModelSha256"))?;
    let credential_slot_ref = opaque_string(attempt.get("credentialSlotRef"), 200)?;
    let turn_id_sha256 = current["oneRing"]["turnIdSha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let request_hash_sha256 = current["oneRing"]["requestHashSha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let binding_id_digest = current["oneRing"]["bindingIdDigest"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let binding_revision = current["oneRing"]["bindingRevision"]
        .as_u64()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    if current["oneRing"]["bindingStatus"] != "ACTIVE" {
        return Err(LocalOwnerError::PresenceBindingDenied);
    }
    let external_key_sha256 = current["oneRing"]["externalKeySha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let frontend_source_sha256 = current["oneRing"]["frontendSourceSha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let frontend_plane_sha256 = current["oneRing"]["frontendPlaneSha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let frontend_principal_sha256 = current["oneRing"]["frontendPrincipalSha256"]
        .as_str()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    let authority_generation = current["identity"]["authorityGeneration"]
        .as_u64()
        .ok_or(LocalOwnerError::PresenceBindingDenied)?;
    if authority_generation != expected_authority_generation {
        return Err(LocalOwnerError::PresenceContextStale);
    }
    let material = json!({
        "attachmentGeneration": current["attachmentGeneration"],
        "attemptId": attempt_id,
        "authorityGeneration": authority_generation,
        "bodyByteLength": body_byte_length,
        "bodySha256": body_sha256,
        "contextId": expected_context_id,
        "credentialSlotRef": credential_slot_ref,
        "method": method,
        "oneRingBindingIdDigest": binding_id_digest,
        "oneRingBindingRevision": binding_revision,
        "oneRingBindingStatus": "ACTIVE",
        "oneRingExternalKeySha256": external_key_sha256,
        "oneRingFrontendPlaneSha256": frontend_plane_sha256,
        "oneRingFrontendPrincipalSha256": frontend_principal_sha256,
        "oneRingFrontendSourceSha256": frontend_source_sha256,
        "oneRingRequestHashSha256": request_hash_sha256,
        "oneRingTurnIdSha256": turn_id_sha256,
        "ordinal": ordinal,
        "providerPathId": provider_path_id,
        "projectionGeneration": expected_generation,
        "schema": PROVIDER_ATTEMPT_SEAL_SCHEMA,
        "selectedModelSha256": selected_model_sha256,
        "targetSha256": target_sha256,
    });
    let seal_id = format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.provider-attempt-seal.v1",
            &canonical_value_bytes(&material)?,
        )
    );
    Ok(json!({
        "accepted": true,
        "attachmentGeneration": current["attachmentGeneration"],
        "attemptId": attempt_id,
        "authorityGeneration": authority_generation,
        "contextId": expected_context_id,
        "credentialSlotDigest": digest_text(
            "agents-os.local-owner.credential-slot-ref.v1",
            credential_slot_ref,
        ),
        "ordinal": ordinal,
        "projectionGeneration": expected_generation,
        "providerInvoked": false,
        "resultCode": "PRESENCE_PROVIDER_ATTEMPT_MATERIAL_SEALED_NOT_INVOKED",
        "schema": PROVIDER_ATTEMPT_SEAL_SCHEMA,
        "sealId": seal_id,
    }))
}

fn parse_presence_request(input: &Value) -> Result<PresenceRequest, LocalOwnerError> {
    let object = exact_object(
        input,
        &[
            "attachmentGeneration",
            "expectedSlots",
            "freshPresenceId",
            "oneRing",
            "transcriptDigest",
        ],
    )?;
    let attachment_generation = safe_u64(object.get("attachmentGeneration"), true)?;
    let fresh_presence_id = opaque_string(object.get("freshPresenceId"), 128)?;
    if fresh_presence_id
        .strip_prefix("fresh-presence:r1:")
        .is_none_or(|suffix| !is_hex_64(suffix))
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    let transcript_digest = raw_sha256(object.get("transcriptDigest"))?.to_owned();
    let expected = exact_object(
        object
            .get("expectedSlots")
            .ok_or(LocalOwnerError::InvalidInput)?,
        &[
            "lifeFactFingerprint",
            "memoryFactFingerprint",
            "oneRingFactFingerprint",
            "workSourceCutFingerprint",
        ],
    )?;
    let expected = ExpectedSlots {
        life: nullable_raw_sha256(expected.get("lifeFactFingerprint"))?,
        memory: nullable_raw_sha256(expected.get("memoryFactFingerprint"))?,
        one_ring: nullable_raw_sha256(expected.get("oneRingFactFingerprint"))?,
        work: nullable_prefixed_sha256(expected.get("workSourceCutFingerprint"))?,
    };
    let one_ring = exact_object(
        object.get("oneRing").ok_or(LocalOwnerError::InvalidInput)?,
        &[
            "externalKeyDigest",
            "frontendPlane",
            "frontendPrincipalDigest",
            "frontendSource",
            "requestHash",
            "turnId",
        ],
    )?;
    let one_ring = OneRingInput {
        external_key_digest: nullable_raw_sha256(one_ring.get("externalKeyDigest"))?,
        frontend_plane: nullable_plane_token(one_ring.get("frontendPlane"), 64)?,
        frontend_principal_digest: nullable_raw_sha256(one_ring.get("frontendPrincipalDigest"))?,
        frontend_source: nullable_opaque_string(one_ring.get("frontendSource"), 200)?,
        request_hash: nullable_raw_sha256(one_ring.get("requestHash"))?,
        turn_id: nullable_opaque_string(one_ring.get("turnId"), 300)?,
    };
    Ok(PresenceRequest {
        attachment_generation,
        expected,
        fresh_presence_id: fresh_presence_id.to_owned(),
        one_ring,
        transcript_digest,
    })
}

fn projection_generation(connection: &Connection) -> Result<u64, LocalOwnerError> {
    let generation: i64 = connection.query_row(
        "SELECT COALESCE(MAX(event_sequence),0) FROM event",
        [],
        |row| row.get(0),
    )?;
    u64::try_from(generation).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn accepted_identity(
    connection: &Connection,
    admission: &ContinuityAdmission,
) -> Result<AcceptedIdentity, LocalOwnerError> {
    let rows: i64 = connection.query_row("SELECT COUNT(*) FROM resident_identity", [], |row| {
        row.get(0)
    })?;
    if rows != 1 {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let (resident_id, fingerprint): (String, String) = connection.query_row(
        "SELECT resident_id,identity_fingerprint FROM resident_identity",
        [],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    let authority_generation: i64 = connection.query_row(
        "SELECT authority_generation FROM resident_authority_epoch ORDER BY authority_epoch DESC LIMIT 1",
        [],
        |row| row.get(0),
    )?;
    let authority_generation = u64::try_from(authority_generation)
        .ok()
        .filter(|value| *value > 0 && *value <= MAX_SAFE_INTEGER)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let local = admission
        .local
        .as_ref()
        .ok_or(LocalOwnerError::ContinuityAdmissionDenied)?;
    if !is_hex_64(&fingerprint) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    if local.resident_id != resident_id || local.authority_epoch != authority_generation {
        return Err(LocalOwnerError::ContinuityAdmissionDenied);
    }
    Ok(AcceptedIdentity {
        authority_generation,
        opaque_id: format!("resident:v1:{fingerprint}"),
    })
}

fn memory_projection(
    connection: &Connection,
    memory_body_verifier: Option<&MemoryBodyVerifier>,
    expected_fingerprint: Option<&str>,
    fresh_presence_id: &str,
    identity: &AcceptedIdentity,
) -> Result<Value, LocalOwnerError> {
    let Some(current) = read_mmr_current(connection, MEMORY_INVENTORY_SLOT)? else {
        require_selector(expected_fingerprint, None)?;
        return Ok(unknown_memory());
    };
    let (fact_fingerprint, content) = slot_content(&current, MEMORY_INVENTORY_SLOT)?;
    require_selector(expected_fingerprint, Some(fact_fingerprint))?;
    exact_map_keys(
        content,
        &[
            "adoptedMemoryId",
            "authorityGeneration",
            "candidateIds",
            "identityOpaqueId",
            "schema",
        ],
    )?;
    stored_literal(content.get("schema"), MEMORY_INVENTORY_SCHEMA)?;
    let identity_opaque_id = stored_opaque_string(content.get("identityOpaqueId"), 200)?;
    let authority_generation = stored_safe_u64(content.get("authorityGeneration"), true)?;
    if identity_opaque_id != identity.opaque_id {
        return Err(LocalOwnerError::StateCorrupt);
    }
    // A declared restore advances Resident authority without silently rewriting
    // an individual Memory. The exact predecessor remains read-only evidence
    // with UNKNOWN currentness; Memory mutation still requires current identity.
    let retained_after_declared_restore = if authority_generation == identity.authority_generation {
        false
    } else if is_exact_declared_restore_predecessor(
        connection,
        authority_generation,
        identity.authority_generation,
    )? {
        true
    } else {
        return Err(LocalOwnerError::StateCorrupt);
    };
    let candidate_ids = content
        .get("candidateIds")
        .and_then(Value::as_array)
        .filter(|values| values.len() <= MAX_CANDIDATES)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let mut seen = BTreeSet::new();
    let mut candidates = Vec::new();
    for candidate in candidate_ids {
        let candidate_id = stored_opaque_string(Some(candidate), 200)?;
        if !candidate_id
            .strip_prefix(MEMORY_CANDIDATE_PREFIX)
            .is_some_and(is_hex_64)
            || !seen.insert(candidate_id.to_owned())
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        let candidate_current = read_candidate_current(connection, candidate_id)?
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let candidate_fingerprint = candidate_current["factFingerprint"]
            .as_str()
            .filter(|value| is_hex_64(value))
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let _candidate_status = candidate_current["state"]["candidateState"]["status"]
            .as_str()
            .filter(|status| matches!(*status, "CANDIDATE" | "EVIDENCE_BACKED" | "REVISED"))
            .ok_or(LocalOwnerError::StateCorrupt)?;
        let candidate_content = &candidate_current["state"]["components"]["content"]["value"];
        if candidate_content["schema"] != super::memory::MEMORY_CANDIDATE_SCHEMA
            || candidate_content["identityOpaqueId"] != identity.opaque_id
            || candidate_content["authorityGeneration"].as_u64() != Some(authority_generation)
        {
            return Err(LocalOwnerError::StateCorrupt);
        }
        candidates.push(json!({
            "adopted": false,
            "candidateDigest": format!("sha256:{candidate_fingerprint}"),
            "candidateId": candidate_id,
            "candidateStatus": "CANDIDATE",
            "executionAuthority": false,
            "projectedAs": "HYPOTHESIS",
            "promotionAuthority": false,
        }));
    }
    let adopted = match content.get("adoptedMemoryId") {
        Some(Value::Null) => unknown_memory()["adopted"].clone(),
        Some(value) => {
            let memory_id = stored_typed_ref(Some(value), MEMORY_ID_PREFIX, 200)?;
            if !memory_id
                .strip_prefix(MEMORY_ID_PREFIX)
                .is_some_and(is_hex_64)
            {
                return Err(LocalOwnerError::StateCorrupt);
            }
            let authority =
                read_mmr_current(connection, memory_id)?.ok_or(LocalOwnerError::StateCorrupt)?;
            let authority_fingerprint = authority["factFingerprint"]
                .as_str()
                .filter(|value| is_hex_64(value))
                .ok_or(LocalOwnerError::StateCorrupt)?;
            let authority_revision = stored_safe_u64(authority.get("revision"), true)?;
            let authority_content = authority["state"]["components"]["content"]["value"]
                .as_object()
                .ok_or(LocalOwnerError::StateCorrupt)?;
            exact_map_keys(
                authority_content,
                &[
                    "authorityGeneration",
                    "authorityStatus",
                    "bodyDescriptor",
                    "candidateRef",
                    "identityOpaqueId",
                    "memoryId",
                    "schema",
                ],
            )?;
            stored_literal(authority_content.get("schema"), MEMORY_AUTHORITY_SCHEMA)?;
            if stored_opaque_string(authority_content.get("identityOpaqueId"), 200)?
                != identity.opaque_id
                || stored_safe_u64(authority_content.get("authorityGeneration"), true)?
                    != authority_generation
                || stored_typed_ref(authority_content.get("memoryId"), MEMORY_ID_PREFIX, 200)?
                    != memory_id
            {
                return Err(LocalOwnerError::StateCorrupt);
            }
            let status = stored_opaque_string(authority_content.get("authorityStatus"), 16)?;
            if !matches!(status, "ADOPTED" | "RETIRED") {
                return Err(LocalOwnerError::StateCorrupt);
            }
            let descriptor = descriptor_from_authority_content(
                &Value::Object(authority_content.clone()),
                &identity.opaque_id,
                memory_id,
            )?;
            let availability = if retained_after_declared_restore {
                "UNKNOWN"
            } else if let Some(verifier) = memory_body_verifier {
                verifier
                    .verify_for_read(&descriptor, fresh_presence_id, authority_fingerprint)?
                    .availability
                    .as_str()
            } else {
                "UNKNOWN"
            };
            let currentness = if status == "ADOPTED" && availability == "VERIFIED" {
                "CURRENT"
            } else {
                "UNKNOWN"
            };
            json!({
                "authorityGeneration": authority_generation,
                "authorityRelation": status,
                "authorityRevision": authority_revision,
                "bodyAvailability": availability,
                // The descriptor remains canonical private authority, but its
                // locator and digest never cross the Presence boundary.
                "bodyRef": Value::Null,
                "bodySha256": Value::Null,
                "currentRelation": "SELECTED",
                "currentness": currentness,
                "factFingerprint": authority_fingerprint,
                "identityOpaqueId": identity.opaque_id,
                "memoryId": memory_id,
                "retired": status == "RETIRED",
                "schema": MEMORY_AUTHORITY_SCHEMA,
            })
        }
        None => return Err(LocalOwnerError::StateCorrupt),
    };
    Ok(json!({
        "adopted": adopted,
        "candidates": candidates,
        "mappingFactFingerprint": fact_fingerprint,
    }))
}

fn is_exact_declared_restore_predecessor(
    connection: &Connection,
    stored_generation: u64,
    accepted_generation: u64,
) -> Result<bool, LocalOwnerError> {
    if stored_generation.checked_add(1) != Some(accepted_generation) {
        return Ok(false);
    }
    let (latest_generation, expected_previous, event_kind): (i64, Option<i64>, String) = connection
        .query_row(
            "SELECT a.authority_generation,a.expected_previous_authority_epoch,e.event_kind \
             FROM resident_authority_epoch a \
             JOIN event e ON e.event_sequence=a.created_event_sequence \
             ORDER BY a.authority_epoch DESC LIMIT 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )?;
    Ok(
        u64::try_from(latest_generation).ok() == Some(accepted_generation)
            && expected_previous.and_then(|value| u64::try_from(value).ok())
                == Some(stored_generation)
            && event_kind == "RESIDENT_DISASTER_RESTORED",
    )
}

fn unknown_memory() -> Value {
    json!({
        "adopted": {
            "authorityGeneration": Value::Null,
            "authorityRelation": Value::Null,
            "authorityRevision": Value::Null,
            "bodyAvailability": "UNKNOWN",
            "bodyRef": Value::Null,
            "bodySha256": Value::Null,
            "currentRelation": Value::Null,
            "currentness": "UNKNOWN",
            "factFingerprint": Value::Null,
            "identityOpaqueId": Value::Null,
            "memoryId": Value::Null,
            "retired": Value::Null,
            "schema": Value::Null,
        },
        "candidates": [],
        "mappingFactFingerprint": Value::Null,
    })
}

fn one_ring_projection(
    connection: &Connection,
    input: &OneRingInput,
    expected_fingerprint: Option<&str>,
    identity: &AcceptedIdentity,
) -> Result<Value, LocalOwnerError> {
    let external_key_sha256 = input
        .external_key_digest
        .as_deref()
        .map(|value| format!("sha256:{value}"));
    let frontend_source_sha256 = input
        .frontend_source
        .as_deref()
        .map(|value| digest_text("agents-os.local-owner.onering-frontend-source.v1", value));
    let frontend_plane_sha256 = input
        .frontend_plane
        .as_deref()
        .map(|value| digest_text("agents-os.local-owner.onering-frontend-plane.v1", value));
    let frontend_principal_sha256 = match (
        input.frontend_plane.as_deref(),
        input.frontend_principal_digest.as_deref(),
    ) {
        (Some(frontend_plane), Some(principal_digest)) => Some(scoped_frontend_principal_digest(
            frontend_plane,
            principal_digest,
        )?),
        _ => None,
    };
    let turn_id_sha256 = input
        .turn_id
        .as_deref()
        .map(|value| digest_text("agents-os.local-owner.onering-turn-id.v1", value));
    let request_hash_sha256 = input
        .request_hash
        .as_deref()
        .map(|value| format!("sha256:{value}"));
    let metadata_complete = external_key_sha256.is_some()
        && frontend_plane_sha256.is_some()
        && frontend_principal_sha256.is_some()
        && frontend_source_sha256.is_some()
        && turn_id_sha256.is_some()
        && request_hash_sha256.is_some();
    let Some(current) = read_mmr_current(connection, ONE_RING_SLOT)? else {
        require_selector(expected_fingerprint, None)?;
        return Ok(json!({
            "binding": "UNKNOWN",
            "bindingIdDigest": Value::Null,
            "bindingRevision": Value::Null,
            "bindingStatus": Value::Null,
            "externalKeySha256": external_key_sha256,
            "factFingerprint": Value::Null,
            "frontendPlaneSha256": frontend_plane_sha256,
            "frontendPrincipalSha256": frontend_principal_sha256,
            "frontendSourceSha256": frontend_source_sha256,
            "requestHashSha256": request_hash_sha256,
            "sessionAvailability": "UNKNOWN",
            "turnIdSha256": turn_id_sha256,
        }));
    };
    let (fact_fingerprint, content) = slot_content(&current, ONE_RING_SLOT)?;
    require_selector(expected_fingerprint, Some(fact_fingerprint))?;
    exact_map_keys(
        content,
        &[
            "authorityGeneration",
            "bindingId",
            "bindingRevision",
            "bindingStatus",
            "externalKeyClass",
            "externalKeySha256",
            "externalPlane",
            "frontendPlane",
            "frontendPrincipalSha256",
            "frontendSourceSha256",
            "identityOpaqueId",
            "retired",
            "schema",
        ],
    )?;
    stored_literal(content.get("schema"), ONE_RING_BINDING_SCHEMA)?;
    let binding_id = stored_opaque_string(content.get("bindingId"), 200)?;
    let identity_opaque_id = stored_opaque_string(content.get("identityOpaqueId"), 200)?;
    let authority_generation = stored_safe_u64(content.get("authorityGeneration"), true)?;
    stored_literal(content.get("externalPlane"), "ONERING")?;
    let external_key_class = stored_opaque_string(content.get("externalKeyClass"), 64)?;
    if !["OPAQUE_V1", "LEGACY_EXPLICIT_BINDING"].contains(&external_key_class) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let bound_external_key = stored_prefixed_sha256(content.get("externalKeySha256"))?;
    let bound_frontend_plane = stored_plane_token(content.get("frontendPlane"), 64)?;
    let binding_revision = stored_safe_u64(content.get("bindingRevision"), true)?;
    let current_revision = stored_safe_u64(current.get("revision"), true)?;
    if binding_revision != current_revision {
        return Err(LocalOwnerError::StateCorrupt);
    }
    stored_literal(content.get("bindingStatus"), "ACTIVE")?;
    if content.get("retired") != Some(&Value::Bool(false)) {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let frontend_sources = content
        .get("frontendSourceSha256")
        .and_then(Value::as_array)
        .filter(|values| !values.is_empty() && values.len() <= MAX_FRONTEND_SOURCES)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let mut unique_frontends = BTreeSet::new();
    for frontend in frontend_sources {
        let digest = stored_prefixed_sha256(Some(frontend))?;
        if !unique_frontends.insert(digest.to_owned()) {
            return Err(LocalOwnerError::StateCorrupt);
        }
    }
    let frontend_principals = content
        .get("frontendPrincipalSha256")
        .and_then(Value::as_array)
        .filter(|values| !values.is_empty() && values.len() <= MAX_FRONTEND_SOURCES)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let mut unique_principals = BTreeSet::new();
    for principal in frontend_principals {
        let digest = stored_prefixed_sha256(Some(principal))?;
        if !unique_principals.insert(digest.to_owned()) {
            return Err(LocalOwnerError::StateCorrupt);
        }
    }
    let binding_matches = identity_opaque_id == identity.opaque_id
        && authority_generation == identity.authority_generation
        && external_key_sha256.as_deref() == Some(bound_external_key)
        && input.frontend_plane.as_deref() == Some(bound_frontend_plane)
        && frontend_principal_sha256
            .as_deref()
            .is_some_and(|digest| unique_principals.contains(digest))
        && frontend_source_sha256
            .as_deref()
            .is_some_and(|digest| unique_frontends.contains(digest));
    let binding = if !metadata_complete {
        "UNKNOWN"
    } else if binding_matches {
        "BOUND"
    } else {
        "MISMATCH"
    };
    Ok(json!({
        "binding": binding,
        "bindingIdDigest": digest_text(
            "agents-os.local-owner.onering-binding-id.v1",
            binding_id,
        ),
        "bindingRevision": binding_revision,
        "bindingStatus": "ACTIVE",
        "externalKeySha256": external_key_sha256,
        "factFingerprint": fact_fingerprint,
        "frontendPlaneSha256": frontend_plane_sha256,
        "frontendPrincipalSha256": frontend_principal_sha256,
        "frontendSourceSha256": frontend_source_sha256,
        "requestHashSha256": request_hash_sha256,
        "sessionAvailability": if binding == "BOUND" { "AVAILABLE" } else { "UNKNOWN" },
        "turnIdSha256": turn_id_sha256,
    }))
}

fn work_projection(
    connection: &Connection,
    expected_source_cut_fingerprint: Option<&str>,
    identity: &AcceptedIdentity,
) -> Result<Value, LocalOwnerError> {
    work_source::read_current_work_envelope(
        connection,
        identity.authority_generation,
        expected_source_cut_fingerprint,
    )
}

fn life_projection(
    connection: &Connection,
    expected_fingerprint: Option<&str>,
) -> Result<Value, LocalOwnerError> {
    if expected_fingerprint.is_some() {
        return Err(LocalOwnerError::PresenceContextStale);
    }
    if read_mmr_current(connection, LIFE_SLOT)?.is_some() {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(json!({
        "category": LIFE_CATEGORY,
        "categoryState": "UNKNOWN",
        "currentness": "UNKNOWN",
        "currentnessReason": "NO_ACCEPTED_CLOSED_WORLD_LIFE_SOURCE",
        "factFingerprint": Value::Null,
        "sourcePolicyId": "MIPD_ACCEPTED_LIFE_SOURCE_INVENTORY_V1",
    }))
}

fn witness_projection(admission: &ContinuityAdmission) -> Result<Value, LocalOwnerError> {
    if !admission.admitted || admission.grant_count != 1 {
        return Err(LocalOwnerError::ContinuityAdmissionDenied);
    }
    let anchor_digest = admission
        .local
        .as_ref()
        .map(|anchor| {
            canonical_value_bytes(&anchor.as_json()).map(|bytes| {
                format!(
                    "sha256:{}",
                    domain_fingerprint("agents-os.local-owner.presence-anchor.v1", &bytes)
                )
            })
        })
        .transpose()?;
    Ok(json!({
        "admitted": true,
        "anchorDigest": anchor_digest,
        "authorityRelation": admission.authority_relation.map(|value| value.as_str()),
        "evidenceDigest": admission.evidence_id.as_deref().map(|value| digest_text(
            "agents-os.local-owner.presence-evidence-id.v1",
            value,
        )),
        "relation": admission.relation.as_str(),
        "witnessDigest": admission.witness_id.as_deref().map(|value| digest_text(
            "agents-os.local-owner.presence-witness-id.v1",
            value,
        )),
    }))
}

fn slot_content<'a>(
    current: &'a Value,
    state_id: &str,
) -> Result<(&'a str, &'a Map<String, Value>), LocalOwnerError> {
    if current["state"]["stateId"] != state_id {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let fingerprint = current["factFingerprint"]
        .as_str()
        .filter(|value| is_hex_64(value))
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let content = current["state"]["components"]["content"]["value"]
        .as_object()
        .ok_or(LocalOwnerError::StateCorrupt)?;
    Ok((fingerprint, content))
}

fn exact_object<'a>(
    value: &'a Value,
    keys: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    exact_map_keys(object, keys).map_err(|_| LocalOwnerError::InvalidInput)?;
    Ok(object)
}

fn exact_map_keys(object: &Map<String, Value>, keys: &[&str]) -> Result<(), LocalOwnerError> {
    if object.len() != keys.len() || object.keys().any(|key| !keys.contains(&key.as_str())) {
        Err(LocalOwnerError::StateCorrupt)
    } else {
        Ok(())
    }
}

fn require_selector(
    expected_fingerprint: Option<&str>,
    actual_fingerprint: Option<&str>,
) -> Result<(), LocalOwnerError> {
    if expected_fingerprint.is_some_and(|expected| Some(expected) != actual_fingerprint) {
        Err(LocalOwnerError::PresenceContextStale)
    } else {
        Ok(())
    }
}

fn stored_literal(value: Option<&Value>, expected: &str) -> Result<(), LocalOwnerError> {
    if value.and_then(Value::as_str) == Some(expected) {
        Ok(())
    } else {
        Err(LocalOwnerError::StateCorrupt)
    }
}

fn stored_safe_u64(value: Option<&Value>, nonzero: bool) -> Result<u64, LocalOwnerError> {
    safe_u64(value, nonzero).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn stored_opaque_string(value: Option<&Value>, maximum: usize) -> Result<&str, LocalOwnerError> {
    opaque_string(value, maximum).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn stored_typed_ref<'a>(
    value: Option<&'a Value>,
    prefix: &str,
    maximum: usize,
) -> Result<&'a str, LocalOwnerError> {
    typed_ref(value, prefix, maximum).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn stored_prefixed_sha256(value: Option<&Value>) -> Result<&str, LocalOwnerError> {
    prefixed_sha256(value).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn plane_token(value: Option<&Value>, maximum: usize) -> Result<&str, LocalOwnerError> {
    opaque_string(value, maximum).and_then(|value| {
        let mut bytes = value.bytes();
        let valid = bytes.next().is_some_and(|byte| byte.is_ascii_uppercase())
            && bytes.all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_');
        valid.then_some(value).ok_or(LocalOwnerError::InvalidInput)
    })
}

fn nullable_plane_token(
    value: Option<&Value>,
    maximum: usize,
) -> Result<Option<String>, LocalOwnerError> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(value) => plane_token(Some(value), maximum).map(|value| Some(value.to_owned())),
        None => Err(LocalOwnerError::InvalidInput),
    }
}

fn stored_plane_token(value: Option<&Value>, maximum: usize) -> Result<&str, LocalOwnerError> {
    plane_token(value, maximum).map_err(|_| LocalOwnerError::StateCorrupt)
}

fn scoped_frontend_principal_digest(
    frontend_plane: &str,
    principal_digest: &str,
) -> Result<String, LocalOwnerError> {
    let material = json!({
        "frontendPlane": frontend_plane,
        "principalDigest": format!("sha256:{principal_digest}"),
    });
    Ok(format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.onering-frontend-principal.v1",
            &canonical_value_bytes(&material)?,
        )
    ))
}

fn safe_u64(value: Option<&Value>, nonzero: bool) -> Result<u64, LocalOwnerError> {
    value
        .and_then(Value::as_u64)
        .filter(|value| *value <= MAX_SAFE_INTEGER && (!nonzero || *value > 0))
        .ok_or(LocalOwnerError::InvalidInput)
}

fn opaque_string(value: Option<&Value>, maximum: usize) -> Result<&str, LocalOwnerError> {
    value
        .and_then(Value::as_str)
        .filter(|value| {
            !value.is_empty()
                && value.len() <= maximum
                && !value.chars().any(char::is_control)
                && value.trim() == *value
        })
        .ok_or(LocalOwnerError::InvalidInput)
}

fn nullable_opaque_string(
    value: Option<&Value>,
    maximum: usize,
) -> Result<Option<String>, LocalOwnerError> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(value) => opaque_string(Some(value), maximum).map(|value| Some(value.to_owned())),
        None => Err(LocalOwnerError::InvalidInput),
    }
}

fn ascii_token(value: Option<&Value>, maximum: usize) -> Result<&str, LocalOwnerError> {
    opaque_string(value, maximum).and_then(|value| {
        value
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte == b'-')
            .then_some(value)
            .ok_or(LocalOwnerError::InvalidInput)
    })
}

fn typed_ref<'a>(
    value: Option<&'a Value>,
    prefix: &str,
    maximum: usize,
) -> Result<&'a str, LocalOwnerError> {
    opaque_string(value, maximum).and_then(|value| {
        value
            .starts_with(prefix)
            .then_some(value)
            .ok_or(LocalOwnerError::StateCorrupt)
    })
}

fn raw_sha256(value: Option<&Value>) -> Result<&str, LocalOwnerError> {
    value
        .and_then(Value::as_str)
        .filter(|value| is_hex_64(value))
        .ok_or(LocalOwnerError::InvalidInput)
}

fn nullable_raw_sha256(value: Option<&Value>) -> Result<Option<String>, LocalOwnerError> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(value) => raw_sha256(Some(value)).map(|value| Some(value.to_owned())),
        None => Err(LocalOwnerError::InvalidInput),
    }
}

fn nullable_prefixed_sha256(value: Option<&Value>) -> Result<Option<String>, LocalOwnerError> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(value) => prefixed_sha256(Some(value)).map(|value| Some(value.to_owned())),
        None => Err(LocalOwnerError::InvalidInput),
    }
}

fn prefixed_sha256(value: Option<&Value>) -> Result<&str, LocalOwnerError> {
    value
        .and_then(Value::as_str)
        .filter(|value| value.strip_prefix("sha256:").is_some_and(is_hex_64))
        .ok_or(LocalOwnerError::InvalidInput)
}

fn is_hex_64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn digest_text(domain: &str, value: &str) -> String {
    let mut bytes = Vec::with_capacity(domain.len() + value.len() + 1);
    bytes.extend_from_slice(domain.as_bytes());
    bytes.push(0);
    bytes.extend_from_slice(value.as_bytes());
    format!("sha256:{}", sha256_hex(&bytes))
}
