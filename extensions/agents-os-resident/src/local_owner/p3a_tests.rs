//! P3-A targeted vectors: COMMITTED Durability Honesty.
//!
//! A1 — Acknowledged Mutation Durability
//!
//! A1-V1: caller observes COMMITTED -> real external abrupt kill (SIGKILL) of
//!        the Resident process -> canonical P1 restart -> S1 exists exactly
//!        once with exact payload/provenance/authority/transition/current.
//! A1-V2: caller observes COMMITTED -> actual ordinary OS reboot in a
//!        disposable host/VM -> new boot session -> canonical P1 restart ->
//!        S1 exists exactly once with exact semantic relations.
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::io::{BufRead, BufReader};
use std::os::unix::fs::PermissionsExt;
use std::os::unix::process::ExitStatusExt;
use std::process::{Child, Command, Stdio};

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, PROFILE_ID};

// ===========================================================================
// Embedded Node worker.  The worker hosts the real Resident runtime through
// the integrated activation chain (activation.js -> native addon ->
// LocalOwnerKernel::start) and runs as a real separate OS process so that
// A1-V1 can terminate it with an uncatchable external SIGKILL.
// ===========================================================================

const WORKER_JS: &str = r#"/* P3-A A1 worker: hosts the real Resident runtime via activation.js. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');

const RESIDENT_ROOT = process.env.P3A_RESIDENT_ROOT;
if (!RESIDENT_ROOT) {
  process.stderr.write('P3A_WORKER_ERROR missing P3A_RESIDENT_ROOT\n');
  process.exit(2);
}
const { createResidentLifecycle } = require(path.join(RESIDENT_ROOT, 'activation.js'));
const ACTIVATION_CONFIRMATION = 'I_ACCEPT_LOCAL_OWNER_SESSION_V1_RUNTIME_UNUSABLE';
const ACTIVATION_MODE = 'LOCAL_OWNER_SESSION_V1';

function arg(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error('missing argument ' + name);
  }
  return process.argv[index + 1];
}

async function main() {
  const config = JSON.parse(fs.readFileSync(arg('--config'), 'utf8'));
  const lifecycle = createResidentLifecycle();
  const init = await lifecycle.initialize({
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
    AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE,
    AGENTS_OS_RESIDENT_ROOT: config.rootPath,
    AGENTS_OS_RESIDENT_CONTINUITY_EVIDENCE: config.continuityEvidence || null,
    AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY: config.genesisProvisioningAuthority || null
  });
  if (init.activationState !== 'ACTIVE_LOCAL_OWNER') {
    throw new Error('NOT_ACTIVE ' + JSON.stringify(init));
  }

  if (config.mode === 'genesis') {
    const prepared = await lifecycle.prepareMmrMutation(config.request);
    if (!prepared || prepared.accepted !== true) {
      throw new Error('PREPARE_REJECTED ' + JSON.stringify(prepared));
    }
    const ack = await lifecycle.submitMmrMutationConsent({
      attachmentGeneration: 1,
      ingress: 'TYPED_TEXT',
      operationId: config.operationId,
      transcript: prepared.consentPrompt
    });
    const outcome = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_OPERATION_CORE',
      query: { operationId: config.operationId }
    });
    const inspect = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
      query: {}
    });
    const current = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_CURRENT_CORE',
      query: { stateId: config.targetStateId }
    });
    const status = await lifecycle.status();
    const observed = {
      event: 'ACK',
      mode: 'genesis',
      operationId: config.operationId,
      ackAccepted: ack.accepted === true,
      ackResultCode: ack.resultCode,
      ackResultOperationId: ack.result ? ack.result.operationId : null,
      ackResultSuccessorFactFingerprint: ack.result ? ack.result.successorFactFingerprint : null,
      callerObservedCommitted:
        ack.accepted === true && ack.resultCode === 'APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF',
      anchor: status.continuityAnchor,
      incarnationId: status.incarnationId,
      preState: { outcome, inspect: inspect.inspect, current }
    };
    process.stdout.write('P3A_ACK ' + JSON.stringify(observed) + '\n');
    // Stay alive so the harness can apply an uncatchable external kill after
    // the caller has observed the COMMITTED acknowledgement.
    await new Promise(() => {});
  } else if (config.mode === 'restart') {
    const outcome = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_OPERATION_CORE',
      query: { operationId: config.operationId }
    });
    const inspect = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
      query: {}
    });
    const current = await lifecycle.queryMmrMutationCore({
      operation: 'QUERY_MMR_CURRENT_CORE',
      query: { stateId: config.targetStateId }
    });
    const status = await lifecycle.status();
    process.stdout.write('P3A_INSPECT ' + JSON.stringify({
      event: 'INSPECT',
      mode: 'restart',
      admission: {
        activationAuthorized: status.continuityAdmission ? status.continuityAdmission.activationAuthorized : null,
        relation: status.continuityAdmission ? status.continuityAdmission.relation : null,
        result: status.continuityAdmission ? status.continuityAdmission.result : null
      },
      incarnationId: status.incarnationId,
      outcome,
      inspect: inspect.inspect,
      current
    }) + '\n');
    await lifecycle.shutdown();
    process.exit(0);
  } else {
    throw new Error('UNKNOWN_MODE ' + config.mode);
  }
}

main().catch((error) => {
  process.stderr.write('P3A_WORKER_ERROR ' + (error && error.message ? error.message : String(error)) + '\n');
  process.exit(2);
});
"#;

// ===========================================================================
// P1-style fixtures
// ===========================================================================

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P3-A root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P3-A root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P3-A root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P3-A",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P3-A",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(id: &str, current: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:P3-A",
    })
}

// ===========================================================================
// Claim mutation fixture (S1)
// ===========================================================================

fn provenance(source_type: &str, subject_ref: &str) -> Value {
    let (source_ref, basis_ref) = match source_type {
        "SYNTHETIC_TEST" => ("source:synthetic-test:P3-A", "basis:synthetic-test:P3-A"),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P3-A","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P3-A","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P3-A:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": basis_ref
        },
        "subject": {"ref":subject_ref},
        "supportingBasis": {"ref":basis_ref}
    })
}

fn claim_plane() -> Value {
    json!({
        "claimScope": "MMR_STATE_CORE",
        "controllerRole": "NON_CONTROLLER",
        "interpretationOwnerRef": null,
        "objectKind": "SCOPED_CLAIM",
        "sharedEventStateId": null
    })
}

fn valid_authority(scope: &str, operation: &str, subject_ref: &str, target_state_id: &str, basis_suffix: &str) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:{basis_suffix}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:{basis_suffix}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P3-A",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": subject_ref,
            "targetStateId": target_state_id
        }
    })
}

fn claim_create(operation_id: &str, target_state_id: &str, content: &str, basis_suffix: &str) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": valid_authority(
                        "MMR_STATE_CORE",
                        "CREATE",
                        "subject:synthetic:P3-A",
                        target_state_id,
                        basis_suffix,
                    ),
                    "content": {"value": content},
                    "lifecycle": {
                        "epistemicState":"UNASSESSED",
                        "lifecycleState": "P2_B_CREATED"
                    },
                    "plane": claim_plane(),
                    "provenance": provenance("SYNTHETIC_TEST", "subject:synthetic:P3-A"),
                    "transition": {
                        "predecessorStateFingerprint": Value::Null,
                        "supersedesStateFingerprint": Value::Null
                    }
                },
                "expectedCurrentFingerprint": Value::Null,
                "mutationType": "CREATE",
                "operationId": operation_id,
                "targetStateId": target_state_id
            },
            "operation":"PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

// ===========================================================================
// Worker process helpers
// ===========================================================================

fn write_worker(parent: &std::path::Path) -> std::path::PathBuf {
    let worker = parent.join("p3a_worker.cjs");
    std::fs::write(&worker, WORKER_JS).expect("write P3-A worker");
    worker
}

fn write_config(parent: &std::path::Path, name: &str, config: &Value) -> std::path::PathBuf {
    let path = parent.join(name);
    std::fs::write(&path, serde_json::to_vec(config).expect("serialize P3-A config"))
        .expect("write P3-A config");
    path
}

fn spawn_worker(worker: &std::path::Path, config: &std::path::Path) -> Child {
    Command::new("node")
        .arg(worker)
        .arg("--config")
        .arg(config)
        .env("P3A_RESIDENT_ROOT", env!("CARGO_MANIFEST_DIR"))
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("spawn P3-A node worker")
}

/// Reads the worker stdout until a `P3A_ACK ` or `P3A_INSPECT ` marker line
/// and returns the parsed JSON object.
fn read_worker_marker(child: &mut Child, marker: &str) -> Value {
    let stdout = child.stdout.take().expect("worker stdout");
    let mut reader = BufReader::new(stdout);
    let mut line = String::new();
    loop {
        line.clear();
        let read = reader.read_line(&mut line).expect("read worker stdout");
        if read == 0 {
            panic!("worker exited before {marker} marker");
        }
        let trimmed = line.trim_end();
        if let Some(payload) = trimmed.strip_prefix(marker) {
            return serde_json::from_str(payload)
                .unwrap_or_else(|_| panic!("invalid {marker} payload: {payload}"));
        }
        if trimmed.starts_with("P3A_WORKER_ERROR") {
            panic!("worker error: {trimmed}");
        }
    }
}

fn count_facts(inspect: &Value, state_id: &str) -> usize {
    inspect["stateSet"]
        .as_array()
        .unwrap_or(&Vec::new())
        .iter()
        .filter(|fact| fact["stateId"] == state_id)
        .count()
}

fn count_current(inspect: &Value, state_id: &str) -> usize {
    inspect["currentView"]
        .as_array()
        .unwrap_or(&Vec::new())
        .iter()
        .filter(|entry| entry["stateId"] == state_id)
        .count()
}

fn count_transitions(inspect: &Value, state_id: &str) -> usize {
    inspect["transitionHistory"]
        .as_array()
        .unwrap_or(&Vec::new())
        .iter()
        .filter(|transition| transition["aggregateRef"] == state_id)
        .count()
}

fn emit_ok(case_id: &str, observed_code: &str, extra: Value) {
    let mut object = json!({
        "caseId": case_id,
        "derivedResult": "PASS",
        "observedCode": observed_code,
        "runtimeSelfReportIsProofAuthority": false,
    });
    if let Some(target) = object.as_object_mut() {
        if let Some(extra_map) = extra.as_object() {
            for (key, value) in extra_map {
                target.insert(key.clone(), value.clone());
            }
        }
    }
    println!("{}", object);
}

// ===========================================================================
// A1-V1 — Abrupt Resident Termination
// ===========================================================================

/// A1-V1 — caller observes COMMITTED, then the Resident process is terminated
/// with an uncatchable external SIGKILL; a canonical P1 restart shows S1
/// exists exactly once with exact payload/provenance/authority/transition/
/// current relations and no cleanup write.
#[test]
fn p3a_targeted_a1_v1_acknowledged_mutation_survives_abrupt_kill() {
    let (parent, root) = root();
    let case = "A1-V1";
    let target = "state:claim:A1-V1-S1";
    let operation_id = "operation:A1-V1:O1";
    let content = "P3-A A1-V1 acknowledged durable S1";

    // --- Genesis worker: canonical Home H1, lawful P1 admission, create S1. ---
    let worker = write_worker(parent.path());
    let genesis_config = json!({
        "mode": "genesis",
        "rootPath": root,
        "continuityEvidence": empty_evidence(&format!("evidence:{case}:genesis")),
        "genesisProvisioningAuthority": provisioning(&format!("provisioning:{case}")),
        "operationId": operation_id,
        "targetStateId": target,
        "request": claim_create(operation_id, target, content, "P3-A:a1-v1:O1"),
    });
    let genesis_cfg_path = write_config(parent.path(), "a1_v1_genesis.json", &genesis_config);
    let mut genesis = spawn_worker(&worker, &genesis_cfg_path);

    // OBS-ACK: the caller actually observed the COMMITTED acknowledgement.
    let ack = read_worker_marker(&mut genesis, "P3A_ACK ");
    assert_eq!(ack["callerObservedCommitted"], true, "caller must observe COMMITTED ack");
    assert_eq!(ack["ackResultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    assert_eq!(ack["operationId"], operation_id);
    let anchor = ack["anchor"].clone();
    assert!(anchor.is_object() && !anchor.as_object().unwrap().is_empty(), "anchor must be present");
    let pre_state = ack["preState"].clone();

    // Pre-fault durable truth: exactly one S1 fact/current/transition and a
    // COMMITTED operation outcome.
    let pre_inspect = &pre_state["inspect"];
    assert_eq!(count_facts(pre_inspect, target), 1, "pre-kill fact cardinality");
    assert_eq!(count_current(pre_inspect, target), 1, "pre-kill current cardinality");
    assert_eq!(count_transitions(pre_inspect, target), 1, "pre-kill transition cardinality");
    assert_eq!(pre_state["outcome"]["operationOutcome"], "COMMITTED");
    let pre_fact = pre_inspect["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .find(|fact| fact["stateId"] == target)
        .cloned()
        .expect("pre-kill S1 fact");
    let pre_current = pre_inspect["currentView"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry["stateId"] == target)
        .cloned()
        .expect("pre-kill S1 current");
    let pre_transition = pre_inspect["transitionHistory"]
        .as_array()
        .unwrap()
        .iter()
        .find(|transition| transition["aggregateRef"] == target)
        .cloned()
        .expect("pre-kill S1 transition");

    // MUT-FI-6: uncatchable external abrupt kill after the caller observed
    // COMMITTED.  No graceful shutdown, no destructor, no cleanup.
    drop(genesis.stdout.take());
    genesis.kill().expect("SIGKILL the Resident process");
    let status = genesis.wait().expect("reap killed Resident process");
    assert!(
        status.signal() == Some(9),
        "Resident must be terminated by an uncatchable external SIGKILL (signal 9), got {status:?}"
    );

    // --- Canonical P1 restart with PRESENT continuity evidence. ---
    let restart_config = json!({
        "mode": "restart",
        "rootPath": root,
        "continuityEvidence": present_evidence(&format!("evidence:{case}:restart"), anchor),
        "operationId": operation_id,
        "targetStateId": target,
    });
    let restart_cfg_path = write_config(parent.path(), "a1_v1_restart.json", &restart_config);
    let mut restarted = spawn_worker(&worker, &restart_cfg_path);
    let inspect_msg = read_worker_marker(&mut restarted, "P3A_INSPECT ");
    let exit = restarted.wait().expect("reap restarted Resident process");
    assert!(exit.success(), "restarted Resident must exit cleanly");

    // P1 admission must PASS (MATCH) — the restart used PRESENT evidence.
    assert_eq!(inspect_msg["admission"]["result"], "PASS");
    assert_eq!(inspect_msg["admission"]["relation"], "MATCH");

    // Post-restart durable truth: S1 exists exactly once, immediately visible
    // through canonical query surfaces without any cleanup write.
    let post_inspect = &inspect_msg["inspect"];
    assert_eq!(count_facts(post_inspect, target), 1, "post-restart fact cardinality");
    assert_eq!(count_current(post_inspect, target), 1, "post-restart current cardinality");
    assert_eq!(count_transitions(post_inspect, target), 1, "post-restart transition cardinality");
    assert_eq!(inspect_msg["outcome"]["operationOutcome"], "COMMITTED");
    let post_fact = post_inspect["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .find(|fact| fact["stateId"] == target)
        .cloned()
        .expect("post-restart S1 fact");
    let post_current = post_inspect["currentView"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entry| entry["stateId"] == target)
        .cloned()
        .expect("post-restart S1 current");
    let post_transition = post_inspect["transitionHistory"]
        .as_array()
        .unwrap()
        .iter()
        .find(|transition| transition["aggregateRef"] == target)
        .cloned()
        .expect("post-restart S1 transition");

    // Exact semantics: payload digest, provenance, authority, transition, and
    // Current relation must be identical pre-kill and post-restart.
    assert_eq!(post_fact["contentDigest"], pre_fact["contentDigest"], "payload digest exact");
    assert_eq!(post_fact["factFingerprint"], pre_fact["factFingerprint"], "fact fingerprint exact");
    assert_eq!(post_current["currentFactFingerprint"], pre_current["currentFactFingerprint"], "Current exact");
    assert_eq!(post_transition["eventFingerprint"], pre_transition["eventFingerprint"], "transition exact");
    assert_eq!(inspect_msg["outcome"]["outcome"]["operationFingerprint"], pre_state["outcome"]["outcome"]["operationFingerprint"], "operation identity exact");
    assert_eq!(inspect_msg["outcome"]["operationOutcome"], pre_state["outcome"]["operationOutcome"], "outcome exact");

    emit_ok("A1-V1", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({
        "abruptKill": true,
        "callerObservedCommittedBeforeFault": true,
        "cleanupWriteRequired": false,
        "currentCardinality": 1,
        "exactSemanticsVerified": true,
        "factCardinality": 1,
        "killMechanism": "external SIGKILL (signal 9) on real Resident process",
        "outcomeCardinality": 1,
        "p1ContinuityAdmission": "PASS",
        "prePostStateExact": true,
        "realProcessTermination": true,
        "realRestart": true,
        "stateCardinality": 1,
        "transitionCardinality": 1
    }));
}

// ===========================================================================
// A1-V2 — Actual Ordinary OS Reboot (disposable host/VM)
// ===========================================================================

const DEFAULT_REBOOT_EVIDENCE: &str =
    "/home/jenn/src/nobao-memory-td1-r1e/MMR-0_TD2_R4_P3_A_A1_V2_OS_Reboot_Evidence.json";

/// A1-V2 — caller observes COMMITTED, then an ACTUAL ordinary OS reboot occurs
/// in a disposable host/VM (boot-session identifier must change); after a
/// canonical P1 restart S1 exists exactly once with exact semantic relations.
///
/// This vector CANNOT be satisfied by a process/container restart.  The test
/// consumes the reboot evidence produced by the external disposable-VM harness
/// and re-validates it independently.  Without genuine reboot evidence the
/// vector fails closed (BLOCKED on environment), never PASS.
#[test]
fn p3a_targeted_a1_v2_acknowledged_mutation_survives_os_reboot() {
    let evidence_path = std::env::var("MMR_P3A_REBOOT_EVIDENCE")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| std::path::PathBuf::from(DEFAULT_REBOOT_EVIDENCE));
    if !evidence_path.exists() {
        panic!(
            "BLOCKED_MMR_0_TD2_R4_P3_A_DISPOSABLE_REBOOT_ENVIRONMENT_UNAVAILABLE: \
             no A1-V2 OS-reboot evidence at {}. An actual disposable-host/VM OS reboot is \
             mandatory; a process/container restart cannot substitute.",
            evidence_path.display()
        );
    }
    let evidence: Value = serde_json::from_str(
        &std::fs::read_to_string(&evidence_path).expect("read A1-V2 reboot evidence"),
    )
    .expect("parse A1-V2 reboot evidence");

    let boot_before = evidence["bootIdBefore"].as_str().expect("bootIdBefore");
    let boot_after = evidence["bootIdAfter"].as_str().expect("bootIdAfter");
    if boot_before == boot_after || boot_before.is_empty() || boot_after.is_empty() {
        panic!("REBOOT_NOT_ACTUALLY_PERFORMED: boot session identifier did not change");
    }
    assert_eq!(evidence["callerObservedCommittedBeforeReboot"], true, "COMMITTED must be observed before reboot");
    assert_eq!(evidence["ackResultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    let target = evidence["targetStateId"].as_str().expect("targetStateId");

    let post = &evidence["postReboot"];
    assert_eq!(post["admission"]["result"], "PASS", "P1 admission must PASS after reboot");
    assert_eq!(post["admission"]["relation"], "MATCH", "restart must MATCH via PRESENT evidence");
    let post_inspect = &post["inspect"];
    assert_eq!(count_facts(post_inspect, target), 1, "post-reboot fact cardinality");
    assert_eq!(count_current(post_inspect, target), 1, "post-reboot current cardinality");
    assert_eq!(count_transitions(post_inspect, target), 1, "post-reboot transition cardinality");
    assert_eq!(post["outcome"]["operationOutcome"], "COMMITTED", "post-reboot outcome");

    // Exact pre/post semantic equality against the pre-reboot fixture.
    let pre = &evidence["preReboot"];
    let pre_inspect = &pre["inspect"];
    let pre_fact = pre_inspect["stateSet"].as_array().unwrap().iter()
        .find(|fact| fact["stateId"] == target).cloned().expect("pre-reboot S1 fact");
    let post_fact = post_inspect["stateSet"].as_array().unwrap().iter()
        .find(|fact| fact["stateId"] == target).cloned().expect("post-reboot S1 fact");
    let pre_current = pre_inspect["currentView"].as_array().unwrap().iter()
        .find(|entry| entry["stateId"] == target).cloned().expect("pre-reboot S1 current");
    let post_current = post_inspect["currentView"].as_array().unwrap().iter()
        .find(|entry| entry["stateId"] == target).cloned().expect("post-reboot S1 current");
    assert_eq!(post_fact["contentDigest"], pre_fact["contentDigest"], "payload digest exact after reboot");
    assert_eq!(post_fact["factFingerprint"], pre_fact["factFingerprint"], "fact fingerprint exact after reboot");
    assert_eq!(post_current["currentFactFingerprint"], pre_current["currentFactFingerprint"], "Current exact after reboot");
    assert_eq!(post["outcome"]["operationOutcome"], pre["outcome"]["operationOutcome"], "outcome exact after reboot");
    assert_eq!(evidence["cleanupWriteRequired"], false, "no cleanup-only write may be required");

    emit_ok("A1-V2", "OS_REBOOT_DURABILITY_EVIDENCE_VALID", json!({
        "actualOsReboot": true,
        "bootIdAfter": boot_after,
        "bootIdBefore": boot_before,
        "bootIdChanged": true,
        "callerObservedCommittedBeforeReboot": true,
        "cleanupWriteRequired": false,
        "currentCardinality": 1,
        "disposableEnvironment": evidence["disposableEnvironment"],
        "exactSemanticsVerified": true,
        "factCardinality": 1,
        "outcomeCardinality": 1,
        "p1ContinuityAdmission": "PASS",
        "prePostStateExact": true,
        "stateCardinality": 1,
        "transitionCardinality": 1
    }));
}
