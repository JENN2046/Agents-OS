//! Synthetic-only vectors for the private Memory body bridge.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use super::memory::{
    MEMORY_AUTHORITY_SCHEMA, MEMORY_CANDIDATE_SCHEMA, MEMORY_DESCRIPTOR_SCHEMA,
    MEMORY_INVENTORY_SCHEMA, MEMORY_INVENTORY_SLOT, MemoryBodyDescriptor, MemoryBodyVerifier,
    MemoryMutationBinding, body_locator, body_relative_path,
};
use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID};

const SUBJECT_REF: &str = "subject:synthetic:P2-F";
pub(super) const MEMORY_ID: &str =
    "memory:v1:2222222222222222222222222222222222222222222222222222222222222222";
const CANDIDATE_ID: &str =
    "state:candidate:memory:v1:1111111111111111111111111111111111111111111111111111111111111111";
pub(super) const BODY: &[u8] = b"synthetic-memory-body-sentinel-f8d240c8\n";

#[test]
fn m2_g1_rust_locator_matches_the_private_writer_golden_vector() {
    let identity = format!("resident:v1:{}", "4".repeat(64));
    let memory_id = format!("memory:v1:{}", "7".repeat(64));
    let body = "# SENTINEL_RAW_MEMORY_BODY_MUST_NOT_ESCAPE_6d2f\r\n\r\nExact UTF-8 bytes: 雪 / cafe\u{301}"
        .as_bytes();
    let identity_digest = "0844f1b5ad9ad01390ad6a67d8cf30da26bdb37870be8e410567ba2383442de8";
    let memory_digest = "8dd22b810169f8ef3c30beee190c873535f6d8699157902cb99e49d2f1cb4fac";
    let body_digest = "109342665fc73b177bc168304cb87fbc8f3c5abe0c87ce8984ae37fbacc29a68";
    assert_eq!(
        body_locator(&identity, &memory_id, body),
        (
            format!("memory-body:v1:{identity_digest}:{memory_digest}:{body_digest}"),
            format!("sha256:{body_digest}"),
        )
    );
    assert_eq!(
        body_relative_path(&identity, &memory_id, body),
        format!("{identity_digest}/{memory_digest}/{body_digest}.body")
    );
}

struct Fixture {
    _parent: tempfile::TempDir,
    resident_root: PathBuf,
    body_root: PathBuf,
}

fn fixture() -> Fixture {
    let parent = tempfile::tempdir().expect("temporary Memory bridge parent");
    let resident_root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    let body_root = parent.path().join("synthetic-private-memory-body-root");
    std::fs::create_dir(&resident_root).expect("create Resident root");
    std::fs::create_dir(&body_root).expect("create body root");
    std::fs::set_permissions(&resident_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect Resident root");
    std::fs::set_permissions(&body_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect body root");
    Fixture {
        _parent: parent,
        resident_root,
        body_root,
    }
}

fn empty_evidence() -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": "evidence:MEMORY-BRIDGE:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:MEMORY-BRIDGE",
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId": "authority:SELFTEST:MEMORY-BRIDGE",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:MEMORY-BRIDGE",
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(anchor: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": anchor,
        "evidenceId": "evidence:MEMORY-BRIDGE:restart",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:MEMORY-BRIDGE",
    })
}

fn admitted_kernel(fixture: &Fixture) -> LocalOwnerKernel {
    let genesis = LocalOwnerKernel::start_with_memory_body_root(
        &fixture.resident_root,
        Some(&empty_evidence()),
        Some(&provisioning()),
        Some(&fixture.body_root),
    )
    .expect("admitted Memory bridge genesis");
    let anchor = genesis.health().expect("Memory bridge anchor")["continuityAnchor"].clone();
    genesis.shutdown().expect("Memory bridge genesis shutdown");
    LocalOwnerKernel::start_with_memory_body_root(
        &fixture.resident_root,
        Some(&present_evidence(anchor)),
        None,
        Some(&fixture.body_root),
    )
    .expect("witnessed Memory bridge admission")
}

fn presence_request(suffix: char) -> Value {
    json!({
        "attachmentGeneration": 1,
        "expectedSlots": {
            "lifeFactFingerprint": null,
            "memoryFactFingerprint": null,
            "oneRingFactFingerprint": null,
            "workSourceCutFingerprint": null,
        },
        "freshPresenceId": format!("fresh-presence:r1:{}", suffix.to_string().repeat(64)),
        "oneRing": {
            "externalKeyDigest": null,
            "frontendPlane": null,
            "frontendPrincipalDigest": null,
            "frontendSource": null,
            "requestHash": "b".repeat(64),
            "turnId": "turn:synthetic:memory-bridge:1",
        },
        "transcriptDigest": "c".repeat(64),
    })
}

fn identity(kernel: &LocalOwnerKernel) -> (String, u64) {
    let presence = kernel
        .query_presence_context(presence_request('0'))
        .expect("Memory bridge identity projection");
    (
        presence["identity"]["opaqueId"]
            .as_str()
            .expect("opaque identity")
            .to_owned(),
        presence["identity"]["authorityGeneration"]
            .as_u64()
            .expect("authority generation"),
    )
}

pub(super) fn write_body(root: &Path, identity: &str, body: &[u8]) -> PathBuf {
    let relative = body_relative_path(identity, MEMORY_ID, body);
    let path = root.join(relative);
    let first = path
        .parent()
        .and_then(Path::parent)
        .expect("identity directory");
    let second = path.parent().expect("memory directory");
    std::fs::create_dir(first).expect("create identity directory");
    std::fs::set_permissions(first, std::fs::Permissions::from_mode(0o700))
        .expect("protect identity directory");
    std::fs::create_dir(second).expect("create memory directory");
    std::fs::set_permissions(second, std::fs::Permissions::from_mode(0o700))
        .expect("protect memory directory");
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&path)
        .expect("create immutable synthetic body");
    file.write_all(body).expect("write synthetic body");
    file.sync_all().expect("sync synthetic body");
    path
}

fn descriptor(identity: &str, body: &[u8]) -> Value {
    let (body_ref, body_sha256) = body_locator(identity, MEMORY_ID, body);
    json!({
        "bodyByteLength": body.len(),
        "bodyFormat": "UTF8_MARKDOWN",
        "bodyRef": body_ref,
        "bodySha256": body_sha256,
        "schema": MEMORY_DESCRIPTOR_SCHEMA,
    })
}

fn provenance() -> Value {
    json!({
        "interpreter": {
            "ref": "actor:synthetic-test-harness:MEMORY-BRIDGE",
            "type": "SYNTHETIC_TEST_HARNESS"
        },
        "mutationActor": {
            "ref": "actor:synthetic-test-harness:MEMORY-BRIDGE",
            "type": "SYNTHETIC_TEST_HARNESS"
        },
        "source": {
            "ref": "source:synthetic-test:MEMORY-BRIDGE",
            "type": "SYNTHETIC_TEST"
        },
        "sourceAuthority": {
            "recordRef": "source-authority-record:MEMORY-BRIDGE:SYNTHETIC_TEST",
            "sourceRef": "source:synthetic-test:MEMORY-BRIDGE",
            "sourceType": "SYNTHETIC_TEST",
            "supportingBasisRef": "basis:synthetic-test:MEMORY-BRIDGE"
        },
        "subject": {"ref": SUBJECT_REF},
        "supportingBasis": {"ref": "basis:synthetic-test:MEMORY-BRIDGE"}
    })
}

fn authority(operation: &str, target: &str, scope: &str) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:MEMORY-BRIDGE:{operation}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:MEMORY-BRIDGE:{operation}:{target}"),
            "granteeActorRef": "actor:synthetic-test-harness:MEMORY-BRIDGE",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": SUBJECT_REF,
            "targetStateId": target
        }
    })
}

pub(super) fn candidate_create(
    identity: &str,
    generation: u64,
    body: &[u8],
    operation_id: &str,
) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority("CREATE_CANDIDATE", CANDIDATE_ID, "CANDIDATE_STATE"),
                    "content": {"value": {
                        "authorityGeneration": generation,
                        "bodyDescriptor": descriptor(identity, body),
                        "identityOpaqueId": identity,
                        "memoryId": MEMORY_ID,
                        "motivatingEvidenceRef": null,
                        "schema": MEMORY_CANDIDATE_SCHEMA,
                    }},
                    "lifecycle": {"epistemicState": "UNASSESSED", "lifecycleState": "CANDIDATE"},
                    "plane": {
                        "claimScope": "CANDIDATE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "CANDIDATE_STATE",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance(),
                    "transition": {
                        "predecessorStateFingerprint": null,
                        "supersedesStateFingerprint": null
                    }
                },
                "expectedCurrentFingerprint": null,
                "mutationType": "CREATE_CANDIDATE",
                "operationId": operation_id,
                "targetStateId": CANDIDATE_ID
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

pub(super) fn state_mutation(
    target: &str,
    operation_id: &str,
    mutation_type: &str,
    expected: Option<&str>,
    content: Value,
) -> Value {
    let lifecycle = match mutation_type {
        "CREATE" => "P2_B_CREATED",
        "REVISE" => "P2_B_SUCCESSOR",
        "RETIRE" => "P2_D_RETIRED",
        _ => unreachable!(),
    };
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority(mutation_type, target, "MMR_STATE_CORE"),
                    "content": {"value": content},
                    "lifecycle": {"epistemicState": "UNASSESSED", "lifecycleState": lifecycle},
                    "plane": {
                        "claimScope": "MMR_STATE_CORE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "SCOPED_CLAIM",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance(),
                    "transition": {
                        "predecessorStateFingerprint": expected,
                        "supersedesStateFingerprint": if mutation_type == "RETIRE" { None } else { expected }
                    }
                },
                "expectedCurrentFingerprint": expected,
                "mutationType": mutation_type,
                "operationId": operation_id,
                "targetStateId": target
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

pub(super) fn authority_content(
    identity: &str,
    generation: u64,
    candidate_fingerprint: &str,
    body: &[u8],
    status: &str,
) -> Value {
    json!({
        "authorityGeneration": generation,
        "authorityStatus": status,
        "bodyDescriptor": descriptor(identity, body),
        "candidateRef": {
            "candidateFactFingerprint": candidate_fingerprint,
            "candidateId": CANDIDATE_ID,
        },
        "identityOpaqueId": identity,
        "memoryId": MEMORY_ID,
        "schema": MEMORY_AUTHORITY_SCHEMA,
    })
}

pub(super) fn inventory_content(
    identity: &str,
    generation: u64,
    adopted_memory_id: Option<&str>,
) -> Value {
    json!({
        "adoptedMemoryId": adopted_memory_id,
        "authorityGeneration": generation,
        "candidateIds": [CANDIDATE_ID],
        "identityOpaqueId": identity,
        "schema": MEMORY_INVENTORY_SCHEMA,
    })
}

pub(super) fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare Memory bridge mutation");
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"],
        }))
        .expect("commit Memory bridge mutation")
}

pub(super) fn candidate_fingerprint(kernel: &LocalOwnerKernel) -> String {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CANDIDATE_CORE",
            "query": {"stateId": CANDIDATE_ID}
        }))
        .expect("query Memory Candidate")["current"]["factFingerprint"]
        .as_str()
        .expect("Candidate fingerprint")
        .to_owned()
}

pub(super) fn state_fingerprint(kernel: &LocalOwnerKernel, state_id: &str) -> String {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CURRENT_CORE",
            "query": {"stateId": state_id}
        }))
        .expect("query Memory authority")["current"]["factFingerprint"]
        .as_str()
        .expect("authority fingerprint")
        .to_owned()
}

#[test]
fn m2_g1_body_first_candidate_adopted_current_mismatch_unavailable_and_retired() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    let body_path = write_body(&fixture.body_root, &identity, BODY);

    apply(
        &kernel,
        candidate_create(&identity, generation, BODY, "operation:MEMORY:candidate:1"),
        "operation:MEMORY:candidate:1",
    );
    let candidate_fingerprint = candidate_fingerprint(&kernel);
    assert_eq!(
        kernel
            .query_mmr_core(json!({
                "operation": "QUERY_MMR_CANDIDATE_CORE",
                "query": {"stateId": CANDIDATE_ID}
            }))
            .expect("query current Candidate")["current"]["state"]["candidateState"]["status"],
        "CANDIDATE"
    );
    apply(
        &kernel,
        state_mutation(
            MEMORY_INVENTORY_SLOT,
            "operation:MEMORY:inventory:candidate-only",
            "CREATE",
            None,
            inventory_content(&identity, generation, None),
        ),
        "operation:MEMORY:inventory:candidate-only",
    );
    let candidate_only = kernel
        .query_presence_context(presence_request('a'))
        .expect("candidate-only Memory projection");
    assert_eq!(
        candidate_only["memory"]["adopted"]["authorityRelation"],
        Value::Null
    );
    assert_eq!(
        candidate_only["memory"]["candidates"][0]["candidateStatus"],
        "CANDIDATE"
    );
    assert_eq!(candidate_only["memory"]["candidates"][0]["adopted"], false);

    apply(
        &kernel,
        state_mutation(
            MEMORY_ID,
            "operation:MEMORY:adopt:1",
            "CREATE",
            None,
            authority_content(
                &identity,
                generation,
                &candidate_fingerprint,
                BODY,
                "ADOPTED",
            ),
        ),
        "operation:MEMORY:adopt:1",
    );
    let adopted_not_selected = kernel
        .query_presence_context(presence_request('b'))
        .expect("adopted but non-selected Memory projection");
    assert_eq!(
        adopted_not_selected["memory"]["adopted"]["authorityRelation"],
        Value::Null
    );
    assert_eq!(
        adopted_not_selected["memory"]["candidates"][0]["candidateStatus"],
        "CANDIDATE"
    );
    let inventory_fingerprint = state_fingerprint(&kernel, MEMORY_INVENTORY_SLOT);
    apply(
        &kernel,
        state_mutation(
            MEMORY_INVENTORY_SLOT,
            "operation:MEMORY:inventory:select",
            "REVISE",
            Some(&inventory_fingerprint),
            inventory_content(&identity, generation, Some(MEMORY_ID)),
        ),
        "operation:MEMORY:inventory:select",
    );

    let verified = kernel
        .query_presence_context(presence_request('1'))
        .expect("verified Memory projection");
    assert_eq!(verified["capabilities"]["memoryBodyEnabled"], true);
    assert_eq!(
        verified["memory"]["adopted"]["authorityRelation"],
        "ADOPTED"
    );
    assert_eq!(verified["memory"]["adopted"]["currentRelation"], "SELECTED");
    assert_eq!(verified["memory"]["adopted"]["currentness"], "CURRENT");
    assert_eq!(
        verified["memory"]["adopted"]["bodyAvailability"],
        "VERIFIED"
    );
    assert_eq!(verified["memory"]["adopted"]["bodyRef"], Value::Null);
    assert_eq!(verified["memory"]["adopted"]["bodySha256"], Value::Null);
    let authority_revision = verified["memory"]["adopted"]["authorityRevision"].clone();
    let authority_fingerprint = verified["memory"]["adopted"]["factFingerprint"].clone();
    let selected_memory = verified["memory"]["adopted"]["memoryId"].clone();
    assert_eq!(verified["memory"]["candidates"][0]["adopted"], false);
    assert!(
        !verified
            .to_string()
            .contains(std::str::from_utf8(BODY).unwrap())
    );
    let persistence = kernel
        .query_mmr_core(json!({"operation": "QUERY_MMR_PERSISTENCE_INSPECT", "query": {}}))
        .expect("low-disclosure persistence inspection");
    assert!(
        !persistence
            .to_string()
            .contains(std::str::from_utf8(BODY).unwrap())
    );

    std::fs::write(&body_path, b"tampered-memory-body-sentinel-6de0a3a0\n")
        .expect("tamper synthetic body");
    let mismatch = kernel
        .query_presence_context(presence_request('2'))
        .expect("mismatched Memory projection");
    assert_eq!(
        mismatch["memory"]["adopted"]["bodyAvailability"],
        "MISMATCH"
    );
    assert_eq!(mismatch["memory"]["adopted"]["currentness"], "UNKNOWN");
    assert_eq!(mismatch["memory"]["adopted"]["currentRelation"], "SELECTED");
    assert_eq!(mismatch["memory"]["adopted"]["bodyRef"], Value::Null);
    assert_eq!(mismatch["memory"]["adopted"]["bodySha256"], Value::Null);
    assert_eq!(
        mismatch["memory"]["adopted"]["authorityRevision"],
        authority_revision
    );
    assert_eq!(
        mismatch["memory"]["adopted"]["factFingerprint"],
        authority_fingerprint
    );
    assert_eq!(mismatch["memory"]["adopted"]["memoryId"], selected_memory);

    std::fs::remove_file(&body_path).expect("remove synthetic body");
    let unavailable = kernel
        .query_presence_context(presence_request('3'))
        .expect("unavailable Memory projection");
    assert_eq!(
        unavailable["memory"]["adopted"]["bodyAvailability"],
        "UNAVAILABLE"
    );
    assert_eq!(
        unavailable["memory"]["adopted"]["factFingerprint"],
        verified["memory"]["adopted"]["factFingerprint"]
    );
    assert_eq!(unavailable["memory"]["adopted"]["bodyRef"], Value::Null);
    assert_eq!(unavailable["memory"]["adopted"]["bodySha256"], Value::Null);
    assert_eq!(
        unavailable["memory"]["adopted"]["authorityRevision"],
        authority_revision
    );
    assert_eq!(
        unavailable["memory"]["adopted"]["memoryId"],
        selected_memory
    );

    let mut restored_body = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&body_path)
        .expect("restore immutable synthetic body before retirement");
    restored_body
        .write_all(BODY)
        .expect("restore synthetic body bytes");
    restored_body.sync_all().expect("sync restored body");

    let adopted_fingerprint = state_fingerprint(&kernel, MEMORY_ID);
    apply(
        &kernel,
        state_mutation(
            MEMORY_ID,
            "operation:MEMORY:retire:1",
            "RETIRE",
            Some(&adopted_fingerprint),
            authority_content(
                &identity,
                generation,
                &candidate_fingerprint,
                BODY,
                "RETIRED",
            ),
        ),
        "operation:MEMORY:retire:1",
    );
    let retired = kernel
        .query_presence_context(presence_request('4'))
        .expect("retired Memory projection");
    assert_eq!(retired["memory"]["adopted"]["authorityRelation"], "RETIRED");
    assert_eq!(retired["memory"]["adopted"]["currentRelation"], "SELECTED");
    assert_eq!(retired["memory"]["adopted"]["currentness"], "UNKNOWN");
    assert_eq!(
        retired["memory"]["adopted"]["bodyAvailability"], "VERIFIED",
        "retirement must not fabricate body unavailability"
    );
    assert_eq!(retired["memory"]["adopted"]["bodyRef"], Value::Null);
    assert_eq!(retired["memory"]["adopted"]["bodySha256"], Value::Null);
    assert_eq!(retired["memory"]["adopted"]["retired"], true);

    std::fs::write(&body_path, b"retired-tampered-memory-body-2bda8255\n")
        .expect("tamper retired synthetic body");
    let retired_mismatch = kernel
        .query_presence_context(presence_request('5'))
        .expect("retired mismatched Memory projection");
    assert_eq!(
        retired_mismatch["memory"]["adopted"]["bodyAvailability"],
        "MISMATCH"
    );
    assert_eq!(
        retired_mismatch["memory"]["adopted"]["currentness"],
        "UNKNOWN"
    );
    std::fs::remove_file(&body_path).expect("remove retired synthetic body");
    let retired_unavailable = kernel
        .query_presence_context(presence_request('6'))
        .expect("retired unavailable Memory projection");
    assert_eq!(
        retired_unavailable["memory"]["adopted"]["bodyAvailability"],
        "UNAVAILABLE"
    );
    let mut restored_body = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&body_path)
        .expect("restore retired synthetic body");
    restored_body
        .write_all(BODY)
        .expect("restore retired body bytes");
    restored_body.sync_all().expect("sync retired body");

    let anchor = kernel.health().expect("Memory bridge restart anchor")["continuityAnchor"].clone();
    kernel
        .shutdown()
        .expect("Memory bridge pre-restart shutdown");
    let restarted = LocalOwnerKernel::start_with_memory_body_root(
        &fixture.resident_root,
        Some(&present_evidence(anchor)),
        None,
        Some(&fixture.body_root),
    )
    .expect("restart Memory bridge");
    let after_restart = restarted
        .query_presence_context(presence_request('7'))
        .expect("Memory projection after restart");
    assert_eq!(
        after_restart["memory"]["adopted"]["authorityRelation"],
        "RETIRED"
    );
    assert_eq!(
        after_restart["memory"]["adopted"]["bodyAvailability"],
        "VERIFIED"
    );
    let no_verifier_anchor =
        restarted.health().expect("no-verifier restart anchor")["continuityAnchor"].clone();
    restarted
        .shutdown()
        .expect("Memory bridge restart shutdown");
    let no_verifier = LocalOwnerKernel::start(
        &fixture.resident_root,
        Some(&present_evidence(no_verifier_anchor)),
        None,
    )
    .expect("restart retired Memory without body verifier");
    let unknown = no_verifier
        .query_presence_context(presence_request('8'))
        .expect("retired Memory projection without verifier");
    assert_eq!(unknown["capabilities"]["memoryBodyEnabled"], false);
    assert_eq!(unknown["memory"]["adopted"]["bodyAvailability"], "UNKNOWN");
    assert_eq!(unknown["memory"]["adopted"]["currentness"], "UNKNOWN");
    no_verifier
        .shutdown()
        .expect("no-verifier Memory restart shutdown");
}

#[test]
fn m2_g1_commit_rehashes_and_rejects_a_changed_body_without_candidate_authority() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    let body_path = write_body(&fixture.body_root, &identity, BODY);
    let operation_id = "operation:MEMORY:double-verify:1";
    let prepared = kernel
        .prepare_mmr_mutation(candidate_create(&identity, generation, BODY, operation_id))
        .expect("prepare body-bound Candidate");
    std::fs::write(&body_path, b"tampered-memory-body-sentinel-6de0a3a0\n")
        .expect("change body between prepare and commit");
    assert!(matches!(
        kernel.submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"],
        })),
        Err(LocalOwnerError::MemoryBodyMismatch)
    ));
    let query = kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CANDIDATE_CORE",
            "query": {"stateId": CANDIDATE_ID}
        }))
        .expect("query absent Candidate");
    assert_eq!(query["current"], Value::Null);
    kernel.shutdown().expect("double verification shutdown");
}

#[test]
fn m2_g1_verifier_requires_final_nlink_and_ignores_unrelated_temp_residue() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    let body_path = write_body(&fixture.body_root, &identity, BODY);
    let memory_directory = body_path.parent().expect("Memory body directory");
    let linked_temp = memory_directory.join(".same-body-hard-link.body.tmp");
    std::fs::hard_link(&body_path, &linked_temp).expect("link unfinalized body temp");
    assert_eq!(
        std::fs::metadata(&body_path)
            .expect("unfinalized body metadata")
            .nlink(),
        2
    );
    assert!(matches!(
        kernel.prepare_mmr_mutation(candidate_create(
            &identity,
            generation,
            BODY,
            "operation:MEMORY:unfinalized-hard-link:1",
        )),
        Err(LocalOwnerError::MemoryBodyUnavailable)
    ));
    std::fs::remove_file(&linked_temp).expect("remove unfinalized hard link");
    File::open(memory_directory)
        .expect("open Memory body directory")
        .sync_all()
        .expect("sync finalized Memory body directory");

    let unrelated_temp = memory_directory.join(".same-digest-crash-residue.body.tmp");
    let residue = b"incomplete-private-memory-body-residue";
    let mut residue_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&unrelated_temp)
        .expect("create unrelated crash residue");
    residue_file
        .write_all(residue)
        .expect("write unrelated crash residue");
    residue_file
        .sync_all()
        .expect("sync unrelated crash residue");
    File::open(memory_directory)
        .expect("reopen Memory body directory")
        .sync_all()
        .expect("sync crash residue directory entry");

    kernel
        .prepare_mmr_mutation(candidate_create(
            &identity,
            generation,
            BODY,
            "operation:MEMORY:unrelated-residue:1",
        ))
        .expect("exact finalized body ignores unrelated residue");
    assert_eq!(
        std::fs::read(&unrelated_temp).expect("read unrelated crash residue"),
        residue
    );
    kernel.shutdown().expect("temp residue test shutdown");
}

#[test]
fn m2_g1_malformed_utf8_is_rejected_before_candidate_authority() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    let malformed_utf8 = [0x66, 0x6f, 0x80, 0x6f];
    write_body(&fixture.body_root, &identity, &malformed_utf8);
    assert!(matches!(
        kernel.prepare_mmr_mutation(candidate_create(
            &identity,
            generation,
            &malformed_utf8,
            "operation:MEMORY:malformed-utf8:1",
        )),
        Err(LocalOwnerError::MemoryBodyMismatch)
    ));
    let query = kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CANDIDATE_CORE",
            "query": {"stateId": CANDIDATE_ID}
        }))
        .expect("query absent malformed UTF-8 Candidate");
    assert_eq!(query["current"], Value::Null);
    kernel.shutdown().expect("malformed UTF-8 shutdown");
}

#[test]
fn m2_g1_verification_receipt_rejects_same_digest_path_rebinding() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    let body_path = write_body(&fixture.body_root, &identity, BODY);
    let parsed_descriptor =
        MemoryBodyDescriptor::parse(&descriptor(&identity, BODY), &identity, MEMORY_ID)
            .expect("parse body descriptor");
    let verifier = MemoryBodyVerifier::open(&fixture.body_root, &fixture.resident_root)
        .expect("open protected verifier");
    let receipt = verifier
        .verify_for_mutation(
            &MemoryMutationBinding {
                identity_opaque_id: identity,
                authority_generation: generation,
                memory_id: MEMORY_ID.to_owned(),
                target_state_id: CANDIDATE_ID.to_owned(),
                transition: "CANDIDATE".to_owned(),
                candidate_fact_fingerprint: None,
                descriptor: parsed_descriptor,
            },
            "operation:MEMORY:path-rebind:1",
            &"a".repeat(64),
        )
        .expect("verify exact original body");
    let displaced_path = body_path.with_extension("verified-original");
    std::fs::rename(&body_path, &displaced_path).expect("displace verified inode");
    let mut replacement = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&body_path)
        .expect("create same-digest replacement");
    replacement
        .write_all(BODY)
        .expect("write same-digest replacement");
    replacement.sync_all().expect("sync replacement");

    assert!(matches!(
        receipt.ensure_stable(),
        Err(LocalOwnerError::MemoryVerificationStale)
    ));
    kernel.shutdown().expect("path-rebind test shutdown");
}

#[test]
fn m2_g1_reserved_domains_reject_generic_and_caller_receipt_bypasses() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    let (identity, generation) = identity(&kernel);
    for request in [
        state_mutation(
            MEMORY_ID,
            "operation:MEMORY:bypass:target",
            "CREATE",
            None,
            json!({"generic": true}),
        ),
        state_mutation(
            "state:synthetic:memory-schema-smuggle",
            "operation:MEMORY:bypass:schema",
            "CREATE",
            None,
            json!({"schema": MEMORY_AUTHORITY_SCHEMA}),
        ),
    ] {
        assert!(matches!(
            kernel.prepare_mmr_mutation(request),
            Err(LocalOwnerError::MemoryAuthorityProfileRejected)
        ));
    }
    let mut candidate = candidate_create(
        &identity,
        generation,
        BODY,
        "operation:MEMORY:bypass:receipt",
    );
    candidate["request"]["mutation"]["components"]["content"]["value"]["memoryBodyVerification"] =
        json!({"receiptDigest": "0".repeat(64)});
    assert!(matches!(
        kernel.prepare_mmr_mutation(candidate),
        Err(LocalOwnerError::MemoryAuthorityProfileRejected)
    ));
    let legacy_candidate = json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority("CREATE_CANDIDATE", CANDIDATE_ID, "CANDIDATE_STATE"),
                    "content": {"value": {"description": "generic", "motivatingEvidenceRef": null}},
                    "lifecycle": {"epistemicState": "UNASSESSED", "lifecycleState": "CANDIDATE"},
                    "plane": {
                        "claimScope": "CANDIDATE", "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null, "objectKind": "CANDIDATE_STATE",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance(),
                    "transition": {"predecessorStateFingerprint": null, "supersedesStateFingerprint": null}
                },
                "expectedCurrentFingerprint": null,
                "mutationType": "CREATE_CANDIDATE",
                "operationId": "operation:MEMORY:bypass:generic-candidate",
                "targetStateId": CANDIDATE_ID
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    });
    assert!(matches!(
        kernel.prepare_mmr_mutation(legacy_candidate),
        Err(LocalOwnerError::MemoryAuthorityProfileRejected)
    ));
    kernel.shutdown().expect("reserved bypass shutdown");
}

#[test]
fn m2_g1_protected_root_and_locator_reject_resident_descendants_and_symlinks() {
    let fixture = fixture();
    let kernel = admitted_kernel(&fixture);
    assert!(matches!(
        super::memory::MemoryBodyVerifier::open(fixture._parent.path(), &fixture.resident_root),
        Err(LocalOwnerError::MemoryBodyLocatorRejected)
    ));
    let parent_alias = fixture._parent.path().join("body-parent-alias");
    std::os::unix::fs::symlink(fixture._parent.path(), &parent_alias)
        .expect("create body-root parent alias");
    assert!(matches!(
        super::memory::MemoryBodyVerifier::open(
            &parent_alias.join("synthetic-private-memory-body-root"),
            &fixture.resident_root,
        ),
        Err(LocalOwnerError::MemoryBodyLocatorRejected)
    ));
    let nested = fixture.resident_root.join("memory-bodies");
    std::fs::create_dir(&nested).expect("create invalid nested body root");
    std::fs::set_permissions(&nested, std::fs::Permissions::from_mode(0o700))
        .expect("protect invalid nested body root");
    assert!(matches!(
        super::memory::MemoryBodyVerifier::open(&nested, &fixture.resident_root),
        Err(LocalOwnerError::MemoryBodyLocatorRejected)
    ));

    let (identity, generation) = identity(&kernel);
    let relative = body_relative_path(&identity, MEMORY_ID, BODY);
    let link_path = fixture.body_root.join(relative);
    let first = link_path
        .parent()
        .and_then(Path::parent)
        .expect("identity directory");
    let second = link_path.parent().expect("memory directory");
    std::fs::create_dir(first).expect("create locator identity directory");
    std::fs::set_permissions(first, std::fs::Permissions::from_mode(0o700)).unwrap();
    std::fs::create_dir(second).expect("create locator memory directory");
    std::fs::set_permissions(second, std::fs::Permissions::from_mode(0o700)).unwrap();
    let outside = fixture._parent.path().join("outside-body");
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&outside)
        .expect("create outside body");
    file.write_all(BODY).expect("write outside body");
    std::os::unix::fs::symlink(&outside, &link_path).expect("create forbidden body symlink");
    assert!(matches!(
        kernel.prepare_mmr_mutation(candidate_create(
            &identity,
            generation,
            BODY,
            "operation:MEMORY:locator:symlink",
        )),
        Err(LocalOwnerError::MemoryBodyUnavailable)
    ));
    kernel.shutdown().expect("locator safety shutdown");
}
