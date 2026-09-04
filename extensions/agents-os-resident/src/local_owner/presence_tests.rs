//! M2 no-schema Presence semantic vectors.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::store::{canonical_value_bytes, domain_fingerprint};
use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

const ONERING_SCHEMA: &str = "AGENTS_OS_ONERING_IDENTITY_BINDING_V1";
const SUBJECT_REF: &str = "subject:synthetic:P2-F";

fn presence_root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary Presence root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create Presence root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set Presence root mode");
    (parent, root)
}

fn empty_evidence() -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": "evidence:PRESENCE:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:PRESENCE",
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId": "authority:SELFTEST:PRESENCE",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:PRESENCE",
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(anchor: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": anchor,
        "evidenceId": "evidence:PRESENCE:restart",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:PRESENCE",
    })
}

fn admitted_kernel(root: &std::path::Path) -> LocalOwnerKernel {
    let genesis = LocalOwnerKernel::start(root, Some(&empty_evidence()), Some(&provisioning()))
        .expect("admitted Presence genesis bootstrap");
    let anchor = genesis.health().expect("Presence bootstrap anchor")["continuityAnchor"].clone();
    genesis
        .shutdown()
        .expect("Presence bootstrap shutdown before witnessed admission");
    LocalOwnerKernel::start(root, Some(&present_evidence(anchor)), None)
        .expect("witnessed Presence admission")
}

fn provenance() -> Value {
    json!({
        "interpreter": {
            "ref": "actor:synthetic-test-harness:PRESENCE",
            "type": "SYNTHETIC_TEST_HARNESS"
        },
        "mutationActor": {
            "ref": "actor:synthetic-test-harness:PRESENCE",
            "type": "SYNTHETIC_TEST_HARNESS"
        },
        "source": {
            "ref": "source:synthetic-test:PRESENCE",
            "type": "SYNTHETIC_TEST"
        },
        "sourceAuthority": {
            "recordRef": "source-authority-record:PRESENCE:SYNTHETIC_TEST",
            "sourceRef": "source:synthetic-test:PRESENCE",
            "sourceType": "SYNTHETIC_TEST",
            "supportingBasisRef": "basis:synthetic-test:PRESENCE"
        },
        "subject": {"ref": SUBJECT_REF},
        "supportingBasis": {"ref": "basis:synthetic-test:PRESENCE"}
    })
}

fn authority(operation: &str, target: &str, scope: &str) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:PRESENCE:{operation}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:PRESENCE:{operation}:{target}"),
            "granteeActorRef": "actor:synthetic-test-harness:PRESENCE",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": SUBJECT_REF,
            "targetStateId": target
        }
    })
}

fn state_create(state_id: &str, operation_id: &str, content: Value) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority("CREATE", state_id, "MMR_STATE_CORE"),
                    "content": {"value": content},
                    "lifecycle": {
                        "epistemicState": "UNASSESSED",
                        "lifecycleState": "P2_B_CREATED"
                    },
                    "plane": {
                        "claimScope": "MMR_STATE_CORE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "SCOPED_CLAIM",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance(),
                    "transition": {
                        "predecessorStateFingerprint": null,
                        "supersedesStateFingerprint": null
                    }
                },
                "expectedCurrentFingerprint": null,
                "mutationType": "CREATE",
                "operationId": operation_id,
                "targetStateId": state_id
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn apply_mmr(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) {
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare Presence MMR fixture");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit Presence MMR fixture");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
}

fn current_fingerprint(kernel: &LocalOwnerKernel, state_id: &str) -> String {
    let inspect = kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_PERSISTENCE_INSPECT",
            "query": {}
        }))
        .expect("Presence persistence inspection");
    inspect["inspect"]["currentView"]
        .as_array()
        .expect("current view")
        .iter()
        .find(|item| item["factKind"] == "MMR_STATE_CORE" && item["stateId"] == state_id)
        .and_then(|item| item["currentFactFingerprint"].as_str())
        .expect("current fingerprint")
        .to_owned()
}

fn event_sequence(kernel: &LocalOwnerKernel) -> u64 {
    kernel.health().expect("Presence health")["continuityAnchor"]["eventSequence"]
        .as_u64()
        .expect("event sequence")
}

fn digest_text(domain: &str, text: &str) -> String {
    let mut bytes = Vec::new();
    bytes.extend_from_slice(domain.as_bytes());
    bytes.push(0);
    bytes.extend_from_slice(text.as_bytes());
    format!("sha256:{}", sha256_hex(&bytes))
}

fn scoped_principal(frontend_plane: &str, principal_digest: &str) -> String {
    let material = json!({
        "frontendPlane": frontend_plane,
        "principalDigest": format!("sha256:{principal_digest}"),
    });
    format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.onering-frontend-principal.v1",
            &canonical_value_bytes(&material).expect("canonical principal material"),
        )
    )
}

fn expected_slots() -> Value {
    json!({
        "lifeFactFingerprint": null,
        "memoryFactFingerprint": null,
        "oneRingFactFingerprint": null,
        "workSourceCutFingerprint": null,
    })
}

fn one_ring_input(
    external_key_digest: Option<&str>,
    frontend_plane: Option<&str>,
    frontend_principal_digest: Option<&str>,
    frontend_source: Option<&str>,
) -> Value {
    json!({
        "externalKeyDigest": external_key_digest,
        "frontendPlane": frontend_plane,
        "frontendPrincipalDigest": frontend_principal_digest,
        "frontendSource": frontend_source,
        "requestHash": "b".repeat(64),
        "turnId": "turn:synthetic:presence:1",
    })
}

fn presence_request(generation: u64, suffix: char, one_ring: Value) -> Value {
    json!({
        "attachmentGeneration": generation,
        "expectedSlots": expected_slots(),
        "freshPresenceId": format!("fresh-presence:r1:{}", suffix.to_string().repeat(64)),
        "oneRing": one_ring,
        "transcriptDigest": "c".repeat(64),
    })
}

fn identity_projection(kernel: &LocalOwnerKernel) -> (String, u64) {
    let context = kernel
        .query_presence_context(presence_request(
            1,
            '0',
            one_ring_input(None, None, None, None),
        ))
        .expect("initial Presence identity projection");
    (
        context["identity"]["opaqueId"]
            .as_str()
            .expect("opaque identity")
            .to_owned(),
        context["identity"]["authorityGeneration"]
            .as_u64()
            .expect("authority generation"),
    )
}

fn binding_content(
    identity: &str,
    authority_generation: u64,
    external_key_digest: &str,
    frontend_plane: &str,
    principal_digest: &str,
    frontend_source: &str,
) -> Value {
    json!({
        "authorityGeneration": authority_generation,
        "bindingId": "binding:onering:synthetic:1",
        "bindingRevision": 1,
        "bindingStatus": "ACTIVE",
        "externalKeyClass": "OPAQUE_V1",
        "externalKeySha256": format!("sha256:{external_key_digest}"),
        "externalPlane": "ONERING",
        "frontendPlane": frontend_plane,
        "frontendPrincipalSha256": [scoped_principal(frontend_plane, principal_digest)],
        "frontendSourceSha256": [digest_text(
            "agents-os.local-owner.onering-frontend-source.v1",
            frontend_source,
        )],
        "identityOpaqueId": identity,
        "retired": false,
        "schema": ONERING_SCHEMA,
    })
}

fn legacy_memory_mapping(identity: &str, authority_generation: u64, candidate_ids: Value) -> Value {
    json!({
        "authorityGeneration": authority_generation,
        "authorityRelation": "ADOPTED",
        "authorityRevision": 1,
        "bodyAvailability": "UNKNOWN",
        "bodyRef": null,
        "bodySha256": null,
        "candidateIds": candidate_ids,
        "currentRelation": "SELECTED",
        "identityOpaqueId": identity,
        "memoryId": "memory:synthetic:adopted:1",
        "retired": false,
        "schema": "AGENTS_OS_MEMORY_AUTHORITY_MAPPING_V1",
    })
}

fn provider_attempt(context: &Value, request: Value, body: char, model: char) -> Value {
    json!({
        "attempt": {
            "attemptId": "attempt:synthetic:presence:1",
            "bodyByteLength": 128,
            "bodySha256": format!("sha256:{}", body.to_string().repeat(64)),
            "credentialSlotRef": "credential-slot:synthetic:provider-1",
            "method": "POST",
            "ordinal": 1,
            "providerPathId": "VCP-CHAT-COMPLETIONS",
            "selectedModelSha256": format!("sha256:{}", model.to_string().repeat(64)),
            "targetSha256": format!("sha256:{}", "e".repeat(64)),
        },
        "expectedAuthorityGeneration": context["identity"]["authorityGeneration"],
        "expectedContextId": context["contextId"],
        "expectedProjectionGeneration": context["projectionGeneration"],
        "presenceRequest": request,
    })
}

#[test]
fn m2_presence_projects_typed_cut_read_only_and_survives_restart() {
    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    let (identity, authority_generation) = identity_projection(&kernel);
    assert_eq!(authority_generation, 1);

    let unknown = kernel
        .query_presence_context(presence_request(
            1,
            '1',
            one_ring_input(None, None, None, None),
        ))
        .expect("explicit unknown Presence projection");
    assert_eq!(unknown["oneRing"]["binding"], "UNKNOWN");
    assert_eq!(unknown["oneRing"]["sessionAvailability"], "UNKNOWN");
    assert_eq!(unknown["memory"]["adopted"]["currentness"], "UNKNOWN");
    assert_eq!(unknown["work"]["currentness"], "CURRENT");
    assert_eq!(
        unknown["work"]["facts"][4]["category"],
        "LAST_VALIDATED_RESULT"
    );
    assert_eq!(unknown["work"]["facts"][4]["categoryState"], "ABSENT");
    assert_eq!(unknown["work"]["sourceAvailability"], "AVAILABLE");
    assert_eq!(
        unknown["work"]["schema"],
        "AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1"
    );
    assert_eq!(unknown["life"]["currentness"], "UNKNOWN");
    assert_eq!(unknown["life"]["categoryState"], "UNKNOWN");

    let external_key = "a".repeat(64);
    let principal = "d".repeat(64);
    let frontend_plane = "VCP_CHAT";
    let frontend_source = "synthetic-fresh-frontend";
    apply_mmr(
        &kernel,
        state_create(
            "state:presence:onering-binding:v1",
            "operation:PRESENCE:onering:1",
            binding_content(
                &identity,
                authority_generation,
                &external_key,
                frontend_plane,
                &principal,
                frontend_source,
            ),
        ),
        "operation:PRESENCE:onering:1",
    );
    let mut request = presence_request(
        1,
        '2',
        one_ring_input(
            Some(&external_key),
            Some(frontend_plane),
            Some(&principal),
            Some(frontend_source),
        ),
    );
    request["expectedSlots"]["oneRingFactFingerprint"] = json!(current_fingerprint(
        &kernel,
        "state:presence:onering-binding:v1"
    ));
    request["expectedSlots"]["workSourceCutFingerprint"] =
        unknown["work"]["sourceCutFingerprint"].clone();

    let before_query = event_sequence(&kernel);
    let context = kernel
        .query_presence_context(request.clone())
        .expect("bound typed Presence projection");
    assert_eq!(
        before_query,
        event_sequence(&kernel),
        "Presence query must be read-only"
    );
    assert_eq!(context["identity"]["opaqueId"], identity);
    assert_eq!(
        context["identity"]["authorityGeneration"],
        authority_generation
    );
    assert_eq!(context["projectionGeneration"], before_query);
    assert_eq!(context["oneRing"]["binding"], "BOUND");
    assert_eq!(context["oneRing"]["bindingRevision"], 1);
    assert_eq!(context["oneRing"]["bindingStatus"], "ACTIVE");
    assert_eq!(context["oneRing"]["sessionAvailability"], "AVAILABLE");
    assert_eq!(context["providerAttemptEligible"], true);
    assert_eq!(context["memory"]["adopted"]["currentness"], "UNKNOWN");
    assert_eq!(context["memory"]["adopted"]["bodyAvailability"], "UNKNOWN");
    assert_eq!(context["memory"]["adopted"]["bodyRef"], Value::Null);
    assert_eq!(context["memory"]["adopted"]["bodySha256"], Value::Null);
    assert_eq!(context["memory"]["candidates"], json!([]));
    assert_eq!(context["work"]["currentness"], "CURRENT");
    assert_eq!(context["work"]["facts"][4]["categoryState"], "ABSENT");
    assert_eq!(context["work"]["sourceAvailability"], "AVAILABLE");
    assert_eq!(
        context["work"]["sourceOwner"],
        "RESIDENT_VALIDATION_SUBSTRATE"
    );
    assert_eq!(
        context["life"]["category"],
        "EXPLICITLY_ADOPTED_LIFE_CONTEXT"
    );
    assert_eq!(
        context["life"]["sourcePolicyId"],
        "MIPD_ACCEPTED_LIFE_SOURCE_INVENTORY_V1"
    );
    assert_eq!(context["capabilities"]["providerEnabled"], false);
    assert_eq!(context["capabilities"]["memoryBodyEnabled"], false);
    let serialized = context.to_string();
    assert!(!serialized.contains(PROFILE_ID));
    assert!(!serialized.contains(frontend_source));
    assert!(!serialized.contains("witness:SELFTEST:PRESENCE"));

    let sealed = kernel
        .seal_provider_attempt(provider_attempt(&context, request.clone(), '3', '4'))
        .expect("seal exact provider-attempt material");
    assert_eq!(sealed["providerInvoked"], false);
    assert_eq!(sealed["authorityGeneration"], authority_generation);
    assert_eq!(
        sealed["projectionGeneration"],
        context["projectionGeneration"]
    );
    let changed_body = kernel
        .seal_provider_attempt(provider_attempt(&context, request.clone(), '5', '4'))
        .expect("seal body variant");
    assert_ne!(sealed["sealId"], changed_body["sealId"]);
    let mut stale_authority = provider_attempt(&context, request.clone(), '3', '4');
    stale_authority["expectedAuthorityGeneration"] = json!(authority_generation + 1);
    assert!(matches!(
        kernel.seal_provider_attempt(stale_authority),
        Err(LocalOwnerError::PresenceContextStale)
    ));

    apply_mmr(
        &kernel,
        state_create(
            "state:presence:generation-advance:1",
            "operation:PRESENCE:generation-advance:1",
            json!({"opaque": "generation advance only"}),
        ),
        "operation:PRESENCE:generation-advance:1",
    );
    assert!(matches!(
        kernel.seal_provider_attempt(provider_attempt(&context, request.clone(), '3', '4')),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    request["freshPresenceId"] = json!(format!("fresh-presence:r1:{}", "7".repeat(64)));
    let advanced = kernel
        .query_presence_context(request.clone())
        .expect("fresh Presence after unrelated event");
    assert_eq!(
        advanced["work"]["sourceCutFingerprint"], context["work"]["sourceCutFingerprint"],
        "unrelated MMR state must not advance the direct Goal/Task source cut"
    );

    let anchor = kernel.health().expect("Presence restart anchor")["continuityAnchor"].clone();
    kernel.shutdown().expect("Presence pre-restart shutdown");
    let restarted = LocalOwnerKernel::start(&root, Some(&present_evidence(anchor)), None)
        .expect("admitted Presence restart");
    request["attachmentGeneration"] = json!(2);
    request["freshPresenceId"] = json!(format!("fresh-presence:r1:{}", "8".repeat(64)));
    let restarted_context = restarted
        .query_presence_context(request)
        .expect("typed Presence projection after restart");
    assert_eq!(restarted_context["identity"]["opaqueId"], identity);
    assert_eq!(restarted_context["oneRing"]["binding"], "BOUND");
    assert_eq!(restarted_context["work"]["currentness"], "CURRENT");
    assert_eq!(
        restarted_context["memory"]["adopted"]["currentness"],
        "UNKNOWN"
    );
    restarted.shutdown().expect("Presence restart shutdown");
}

#[test]
fn m2_onering_requires_explicit_key_plane_principal_and_active_binding() {
    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    let (identity, generation) = identity_projection(&kernel);
    let external_key = "1".repeat(64);
    let principal = "2".repeat(64);
    let source = "synthetic-fresh-frontend";
    apply_mmr(
        &kernel,
        state_create(
            "state:presence:onering-binding:v1",
            "operation:PRESENCE:onering:boundary",
            binding_content(
                &identity,
                generation,
                &external_key,
                "VCP_CHAT",
                &principal,
                source,
            ),
        ),
        "operation:PRESENCE:onering:boundary",
    );

    let bound = kernel
        .query_presence_context(presence_request(
            1,
            '1',
            one_ring_input(
                Some(&external_key),
                Some("VCP_CHAT"),
                Some(&principal),
                Some(source),
            ),
        ))
        .expect("exact OneRing binding");
    assert_eq!(bound["oneRing"]["binding"], "BOUND");

    let wrong_key = "3".repeat(64);
    let wrong_principal = "4".repeat(64);
    for (suffix, input) in [
        (
            '2',
            one_ring_input(
                Some(&wrong_key),
                Some("VCP_CHAT"),
                Some(&principal),
                Some(source),
            ),
        ),
        (
            '3',
            one_ring_input(
                Some(&external_key),
                Some("VCP_CHAT"),
                Some(&wrong_principal),
                Some(source),
            ),
        ),
        (
            '4',
            one_ring_input(
                Some(&external_key),
                Some("OTHER_FRONTEND"),
                Some(&principal),
                Some(source),
            ),
        ),
        (
            '5',
            one_ring_input(
                Some(&external_key),
                Some("VCP_CHAT"),
                Some(&principal),
                Some("same-name-different-frontend"),
            ),
        ),
    ] {
        let mismatch = kernel
            .query_presence_context(presence_request(1, suffix, input))
            .expect("mismatched OneRing metadata remains low-disclosure");
        assert_eq!(mismatch["oneRing"]["binding"], "MISMATCH");
        assert_eq!(mismatch["oneRing"]["sessionAvailability"], "UNKNOWN");
        assert_eq!(mismatch["providerAttemptEligible"], false);
    }
    let no_principal = kernel
        .query_presence_context(presence_request(
            1,
            '6',
            one_ring_input(Some(&external_key), Some("VCP_CHAT"), None, Some(source)),
        ))
        .expect("frontend source cannot self-prove a principal");
    assert_eq!(no_principal["oneRing"]["binding"], "UNKNOWN");
    assert_eq!(no_principal["oneRing"]["sessionAvailability"], "UNKNOWN");
    assert_eq!(no_principal["providerAttemptEligible"], false);
    kernel.shutdown().expect("OneRing boundary shutdown");

    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    let (_identity, generation) = identity_projection(&kernel);
    apply_mmr(
        &kernel,
        state_create(
            "state:presence:onering-binding:v1",
            "operation:PRESENCE:onering:different-identity",
            binding_content(
                &format!("resident:v1:{}", "f".repeat(64)),
                generation,
                &external_key,
                "VCP_CHAT",
                &principal,
                source,
            ),
        ),
        "operation:PRESENCE:onering:different-identity",
    );
    let mismatch = kernel
        .query_presence_context(presence_request(
            1,
            '7',
            one_ring_input(
                Some(&external_key),
                Some("VCP_CHAT"),
                Some(&principal),
                Some(source),
            ),
        ))
        .expect("same external key bound to different identity");
    assert_eq!(mismatch["oneRing"]["binding"], "MISMATCH");
    assert_eq!(mismatch["oneRing"]["sessionAvailability"], "UNKNOWN");
    kernel.shutdown().expect("different identity shutdown");

    for case in ["INACTIVE", "RETIRED"] {
        let (_parent, root) = presence_root();
        let kernel = admitted_kernel(&root);
        let (identity, generation) = identity_projection(&kernel);
        let mut content = binding_content(
            &identity,
            generation,
            &external_key,
            "VCP_CHAT",
            &principal,
            source,
        );
        if case == "INACTIVE" {
            content["bindingStatus"] = json!("INACTIVE");
        } else {
            content["retired"] = json!(true);
        }
        apply_mmr(
            &kernel,
            state_create(
                "state:presence:onering-binding:v1",
                "operation:PRESENCE:onering:inactive",
                content,
            ),
            "operation:PRESENCE:onering:inactive",
        );
        assert!(matches!(
            kernel.query_presence_context(presence_request(
                1,
                '8',
                one_ring_input(
                    Some(&external_key),
                    Some("VCP_CHAT"),
                    Some(&principal),
                    Some(source),
                ),
            )),
            Err(LocalOwnerError::StateCorrupt)
        ));
        kernel.shutdown().expect("inactive binding shutdown");
    }
}

#[test]
fn m2_onering_converges_authorized_frontends_only_through_one_opaque_key() {
    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    let (identity, generation) = identity_projection(&kernel);
    let external_key = "5".repeat(64);
    let principals = ["6".repeat(64), "7".repeat(64)];
    let sources = ["synthetic-desktop", "synthetic-mobile"];
    let mut content = binding_content(
        &identity,
        generation,
        &external_key,
        "VCP_CHAT",
        &principals[0],
        sources[0],
    );
    content["frontendPrincipalSha256"] = json!([
        scoped_principal("VCP_CHAT", &principals[0]),
        scoped_principal("VCP_CHAT", &principals[1]),
    ]);
    content["frontendSourceSha256"] = json!([
        digest_text(
            "agents-os.local-owner.onering-frontend-source.v1",
            sources[0],
        ),
        digest_text(
            "agents-os.local-owner.onering-frontend-source.v1",
            sources[1],
        ),
    ]);
    apply_mmr(
        &kernel,
        state_create(
            "state:presence:onering-binding:v1",
            "operation:PRESENCE:onering:multi-frontend",
            content,
        ),
        "operation:PRESENCE:onering:multi-frontend",
    );

    for (suffix, principal, source) in [
        ('1', &principals[0], sources[0]),
        ('2', &principals[1], sources[1]),
    ] {
        let context = kernel
            .query_presence_context(presence_request(
                1,
                suffix,
                one_ring_input(
                    Some(&external_key),
                    Some("VCP_CHAT"),
                    Some(principal),
                    Some(source),
                ),
            ))
            .expect("authorized frontend converges through the same opaque key");
        assert_eq!(context["identity"]["opaqueId"], identity);
        assert_eq!(context["oneRing"]["binding"], "BOUND");
        assert_eq!(context["providerAttemptEligible"], true);
    }

    let different_key_same_frontend = kernel
        .query_presence_context(presence_request(
            1,
            '3',
            one_ring_input(
                Some(&"8".repeat(64)),
                Some("VCP_CHAT"),
                Some(&principals[0]),
                Some(sources[0]),
            ),
        ))
        .expect("frontend labels cannot collapse distinct opaque keys");
    assert_eq!(
        different_key_same_frontend["oneRing"]["binding"],
        "MISMATCH"
    );
    assert_eq!(
        different_key_same_frontend["providerAttemptEligible"],
        false
    );
    assert_eq!(
        different_key_same_frontend["identity"]["opaqueId"],
        identity
    );
    kernel.shutdown().expect("multi-frontend identity shutdown");
}

#[test]
fn m2_memory_bridge_cannot_self_verify_or_self_promote() {
    for case in ["UNTYPED", "FAKE_VERIFIED", "SELF_PROMOTED"] {
        let (_parent, root) = presence_root();
        let kernel = admitted_kernel(&root);
        let (identity, generation) = identity_projection(&kernel);
        let mut content = legacy_memory_mapping(&identity, generation, json!([]));
        match case {
            "UNTYPED" => {
                content = json!({
                    "bodyRef": "memory-body:untyped:self-label",
                    "bodySha256": format!("sha256:{}", "1".repeat(64)),
                    "candidateIds": [],
                });
            }
            "FAKE_VERIFIED" => {
                content["bodyAvailability"] = json!("VERIFIED");
                content["bodyRef"] = json!("memory-body:fake-private-receipt");
                content["bodySha256"] = json!(format!("sha256:{}", "2".repeat(64)));
            }
            "SELF_PROMOTED" => content["authorityRelation"] = json!("CANDIDATE"),
            _ => unreachable!(),
        }
        assert!(matches!(
            kernel.prepare_mmr_mutation(state_create(
                "state:presence:memory-adopted:v1",
                "operation:PRESENCE:memory:invalid",
                content,
            )),
            Err(LocalOwnerError::MemoryAuthorityProfileRejected)
        ));
        kernel.shutdown().expect("invalid Memory bridge shutdown");
    }
}

#[test]
fn m3_work_source_projection_cannot_be_prebuilt_through_generic_mmr() {
    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    for (target, content) in [
        (
            "state:presence:work:v1",
            json!({"generic": "caller-supplied-current-work"}),
        ),
        (
            "state:synthetic:work-schema-smuggle:current",
            json!({"schema": "AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1"}),
        ),
        (
            "state:synthetic:work-schema-smuggle:legacy",
            json!({"schema": "AGENTS_OS_WORK_D1_FIRST_PROOF_ENVELOPE_V1"}),
        ),
    ] {
        assert!(matches!(
            kernel.prepare_mmr_mutation(state_create(
                target,
                "operation:PRESENCE:work-source-bypass",
                content,
            )),
            Err(LocalOwnerError::WorkSourceProfileRejected)
        ));
    }
    kernel.shutdown().expect("Work source bypass shutdown");
}

#[test]
fn m2_selectors_and_life_reserved_slot_fail_closed() {
    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    let mut stale = presence_request(1, '5', one_ring_input(None, None, None, None));
    stale["expectedSlots"]["memoryFactFingerprint"] = json!("9".repeat(64));
    assert!(matches!(
        kernel.query_presence_context(stale),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    let mut stale_work = presence_request(1, '4', one_ring_input(None, None, None, None));
    stale_work["expectedSlots"]["workSourceCutFingerprint"] =
        json!(format!("sha256:{}", "7".repeat(64)));
    assert!(matches!(
        kernel.query_presence_context(stale_work),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    let mut life_expected = presence_request(1, '6', one_ring_input(None, None, None, None));
    life_expected["expectedSlots"]["lifeFactFingerprint"] = json!("8".repeat(64));
    assert!(matches!(
        kernel.query_presence_context(life_expected),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    kernel.shutdown().expect("selector fixture shutdown");

    let (_parent, root) = presence_root();
    let kernel = admitted_kernel(&root);
    assert!(matches!(
        kernel.prepare_mmr_mutation(state_create(
            "state:presence:life:v1",
            "operation:PRESENCE:life:self-label",
            json!({
                "bodyRef": "life-body:generic-self-label",
                "bodySha256": format!("sha256:{}", "7".repeat(64)),
                "currentness": "CURRENT",
            }),
        )),
        Err(LocalOwnerError::WorkSourceProfileRejected)
    ));
    kernel.shutdown().expect("Life self-label shutdown");
}
