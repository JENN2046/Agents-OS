//! Synthetic DP-E vectors for the provider-neutral Continuity Witness seam.

use std::fs::OpenOptions;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use super::memory::MEMORY_INVENTORY_SLOT;
use super::memory_tests::{
    BODY as MEMORY_BODY, MEMORY_ID, apply as apply_memory, authority_content, candidate_create,
    candidate_fingerprint, inventory_content, state_fingerprint, state_mutation, write_body,
};
use super::store::{
    canonical_value_bytes, inspect_continuity, inspect_latest_declared_restore_witness_link,
};
use super::witness::{
    ContinuityWitnessProvider, ContinuityWitnessRecord, ProtectedFileWitnessProvider,
    TrustedWitnessSelector, WitnessCasOutcome, WitnessEnrollOutcome, WitnessReadOutcome,
    continuity_commitment, declared_restore_with_witness_provider,
    reconcile_declared_restore_with_witness_provider, start_with_witness_and_memory_body_root,
    start_with_witness_provider,
};
use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_LOCK_FILENAME, LOCAL_OWNER_ROOT_LEAF,
    LocalOwnerError, LocalOwnerKernel, PROFILE_ID,
};
use crate::resident::lock::ResidentLock;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ForcedRead {
    Normal,
    Unavailable,
    Invalid,
    Multiple,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum EnrollMode {
    Normal,
    UnknownPersisted,
    UnknownNotPersisted,
    Conflict,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum CasMode {
    Normal,
    UnknownPersisted,
    UnknownNotPersisted,
}

struct SyntheticWitnessProvider {
    root: PathBuf,
    record: Option<ContinuityWitnessRecord>,
    forced_read: ForcedRead,
    enroll_mode: EnrollMode,
    cas_mode: CasMode,
    enroll_attempts: u64,
    cas_attempts: u64,
    durable_writes: u64,
    reads: u64,
    cas_observed_local_generations: Vec<u64>,
    operations: Vec<&'static str>,
    observed_unlocked_call: bool,
}

impl SyntheticWitnessProvider {
    fn new(root: &Path) -> Self {
        Self {
            root: root.to_path_buf(),
            record: None,
            forced_read: ForcedRead::Normal,
            enroll_mode: EnrollMode::Normal,
            cas_mode: CasMode::Normal,
            enroll_attempts: 0,
            cas_attempts: 0,
            durable_writes: 0,
            reads: 0,
            cas_observed_local_generations: Vec::new(),
            operations: Vec::new(),
            observed_unlocked_call: false,
        }
    }

    fn observe_resident_lock(&mut self) {
        if let Ok(lock) = ResidentLock::acquire(self.root.join(LOCAL_OWNER_LOCK_FILENAME)) {
            self.observed_unlocked_call = true;
            lock.release()
                .expect("release synthetic Witness lock probe");
        }
    }
}

impl ContinuityWitnessProvider for SyntheticWitnessProvider {
    fn read(&mut self, _selector: &TrustedWitnessSelector) -> WitnessReadOutcome {
        self.observe_resident_lock();
        self.reads += 1;
        self.operations.push("READ");
        match self.forced_read {
            ForcedRead::Unavailable => WitnessReadOutcome::Unavailable,
            ForcedRead::Invalid => WitnessReadOutcome::InvalidOrUnauthenticated,
            ForcedRead::Multiple => WitnessReadOutcome::MultipleConflict,
            ForcedRead::Normal => self
                .record
                .clone()
                .map(|record| WitnessReadOutcome::PresentValid(Box::new(record)))
                .unwrap_or(WitnessReadOutcome::AbsentAuthenticated),
        }
    }

    fn enroll_if_absent(
        &mut self,
        _selector: &TrustedWitnessSelector,
        expected: &ContinuityWitnessRecord,
    ) -> WitnessEnrollOutcome {
        self.observe_resident_lock();
        self.enroll_attempts += 1;
        self.operations.push("ENROLL");
        match self.enroll_mode {
            EnrollMode::Conflict => WitnessEnrollOutcome::Conflict,
            EnrollMode::UnknownNotPersisted => WitnessEnrollOutcome::OutcomeUnknown,
            EnrollMode::Normal | EnrollMode::UnknownPersisted => {
                let outcome = match self.record.as_ref() {
                    Some(actual) if actual == expected => WitnessEnrollOutcome::ExactExisting,
                    Some(_) => return WitnessEnrollOutcome::Conflict,
                    None => {
                        self.record = Some(expected.clone());
                        self.durable_writes += 1;
                        WitnessEnrollOutcome::Created
                    }
                };
                if self.enroll_mode == EnrollMode::UnknownPersisted {
                    WitnessEnrollOutcome::OutcomeUnknown
                } else {
                    outcome
                }
            }
        }
    }

    fn compare_and_swap(
        &mut self,
        selector: &TrustedWitnessSelector,
        expected: &ContinuityWitnessRecord,
        successor: &ContinuityWitnessRecord,
    ) -> WitnessCasOutcome {
        self.observe_resident_lock();
        self.cas_attempts += 1;
        self.operations.push("CAS");
        if let Ok(local) = inspect_continuity(&self.root.join(LOCAL_OWNER_DATABASE_FILENAME))
            && let Some(current) = local.current
        {
            self.cas_observed_local_generations
                .push(current.authority_epoch);
        }
        if expected.validate(selector).is_err()
            || successor.validate(selector).is_err()
            || expected.witness_revision.checked_add(1) != Some(successor.witness_revision)
        {
            return WitnessCasOutcome::PredecessorMismatch;
        }
        match self.record.as_ref() {
            Some(actual) if actual == successor => {
                return WitnessCasOutcome::ExactSuccessorPresent;
            }
            Some(actual) if actual == expected => {}
            _ => return WitnessCasOutcome::PredecessorMismatch,
        }
        match self.cas_mode {
            CasMode::UnknownNotPersisted => WitnessCasOutcome::OutcomeUnknown,
            CasMode::Normal | CasMode::UnknownPersisted => {
                self.record = Some(successor.clone());
                self.durable_writes += 1;
                if self.cas_mode == CasMode::UnknownPersisted {
                    WitnessCasOutcome::OutcomeUnknown
                } else {
                    WitnessCasOutcome::Applied
                }
            }
        }
    }
}

fn witness_root() -> (tempfile::TempDir, PathBuf) {
    let parent = tempfile::tempdir().expect("temporary Witness parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create Witness root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set Witness root mode");
    OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(root.join(LOCAL_OWNER_LOCK_FILENAME))
        .expect("pre-create protected Resident lock for lock probe");
    (parent, root)
}

struct ProtectedWitnessFixture {
    _parent: tempfile::TempDir,
    resident_root: PathBuf,
    protected_root: PathBuf,
}

fn protected_witness_fixture(case_id: &str) -> ProtectedWitnessFixture {
    let parent = tempfile::tempdir().expect("temporary protected Witness parent");
    let resident_root = parent
        .path()
        .join(format!("resident-{case_id}"))
        .join(LOCAL_OWNER_ROOT_LEAF);
    let protected_root = parent.path().join(format!("private-witness-{case_id}"));
    std::fs::create_dir_all(&resident_root).expect("create protected Witness Resident root");
    std::fs::create_dir(&protected_root).expect("create independent protected Witness root");
    std::fs::set_permissions(&resident_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect protected Witness Resident root");
    std::fs::set_permissions(&protected_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect independent Witness root");
    ProtectedWitnessFixture {
        _parent: parent,
        resident_root,
        protected_root,
    }
}

fn protected_provisioning(case_id: &str, private_sentinel: &str) -> Value {
    json!({
        "authorityId": format!("authority:SELFTEST:PROTECTED-WITNESS:{case_id}"),
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": format!("provisioning:PROTECTED-WITNESS:{private_sentinel}"),
        "residentId": PROFILE_ID,
    })
}

fn sole_witness_record(root: &Path) -> PathBuf {
    let mut entries = std::fs::read_dir(root)
        .expect("read protected Witness root")
        .map(|entry| entry.expect("read protected Witness entry").path())
        .collect::<Vec<_>>();
    entries.sort();
    assert_eq!(entries.len(), 1, "exactly one Witness record is durable");
    let path = entries.pop().expect("single Witness record");
    let leaf = path
        .file_name()
        .and_then(|value| value.to_str())
        .expect("UTF-8 Witness record leaf");
    let digest = leaf
        .strip_suffix(".witness.json")
        .expect("fixed Witness record suffix");
    assert_eq!(digest.len(), 64);
    assert!(
        digest
            .bytes()
            .all(|byte| { byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte) })
    );
    path
}

fn expect_protected_open_code(root: &Path, resident_root: &Path, code: &str) {
    let error = ProtectedFileWitnessProvider::open(root, resident_root)
        .err()
        .expect("protected Witness root must be rejected");
    assert_eq!(error.fixed_code(), code);
    let rendered = error.to_string();
    assert!(!rendered.contains(&root.to_string_lossy().to_string()));
    assert!(!rendered.contains(&resident_root.to_string_lossy().to_string()));
}

fn selector(case_id: &str) -> TrustedWitnessSelector {
    TrustedWitnessSelector {
        witness_slot_id: format!("witness-slot:v1:{}", "a".repeat(64)),
        provisioning_scope_commitment: format!("sha256:{}", "b".repeat(64)),
        provider_identity: format!("witness-provider:synthetic:{case_id}"),
        independence_claim: "rollback-domain:synthetic-outside-resident-fixture".to_owned(),
    }
}

fn provisioning(case_id: &str) -> Value {
    json!({
        "authorityId": format!("authority:SELFTEST:WITNESS:{case_id}"),
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": format!("provisioning:WITNESS:{case_id}"),
        "residentId": PROFILE_ID,
    })
}

fn expect_code<T>(result: Result<T, LocalOwnerError>, code: &str) {
    let error = result.err().expect("operation must fail closed");
    assert_eq!(error.fixed_code(), code);
}

fn commit_goal_event(kernel: &LocalOwnerKernel) {
    let prepared = kernel
        .prepare_proposal(json!({
            "attachmentGeneration": 1,
            "request": {
                "mutation": {
                    "mutationType": "CREATE_GOAL_BUNDLE",
                    "payload": {
                        "description": "synthetic Witness descendant",
                        "successCriteria": [
                            {"description": "synthetic criterion", "selectedTaskOrdinal": 1}
                        ],
                        "tasks": [
                            {
                                "description": "synthetic task",
                                "supportsCriteria": [1],
                                "title": "synthetic"
                            }
                        ],
                        "title": "synthetic Witness goal"
                    }
                },
                "operation": "PROPOSE_GOAL_MUTATION"
            }
        }))
        .expect("prepare synthetic descendant event");
    let committed = kernel
        .submit_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "transcript": prepared["consentPrompt"],
        }))
        .expect("commit synthetic descendant event");
    assert_eq!(committed["resultCode"], "COMMITTED");
}

fn declared_restore_request(case_id: &str) -> Value {
    let checkpoint = format!("checkpoint:M5:{case_id}");
    json!({
        "checkpointIdentity": checkpoint,
        "gap": {
            "claim": format!("KNOWN_GAP_M5_{case_id}"),
            "known": true,
            "possible": true,
        },
        "lineageAuthority": format!("external:M5:{case_id}:declared-restore"),
        "protectionOutcome": "PROTECTED",
        "restoredFrom": checkpoint,
    })
}

fn unknown_presence_request(suffix: char) -> Value {
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
            "requestHash": null,
            "turnId": null,
        },
        "transcriptDigest": "d".repeat(64),
    })
}

#[test]
fn dp_h_h1_declared_restore_finalizes_after_durable_local_transition() {
    let (_parent, root) = witness_root();
    let selector = selector("DP-H-H1");
    let mut provider = SyntheticWitnessProvider::new(&root);
    provider.cas_mode = CasMode::UnknownPersisted;
    let kernel = start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("DP-H-H1")),
    )
    .expect("reuse DP-E bootstrap fixture");
    let predecessor = provider.record.clone().expect("enrolled predecessor");
    let (kernel, restored) = declared_restore_with_witness_provider(
        kernel,
        &selector,
        &mut provider,
        declared_restore_request("H1"),
    )
    .expect("unknown CAS acknowledgement is resolved by exact read-back");
    assert_eq!(restored["authorityEpoch"], 2);
    assert_eq!(restored["oldIncarnationFenced"], true);
    assert_eq!(restored["restoredFrom"], "checkpoint:M5:H1");
    assert_eq!(restored["gap"]["known"], true);
    assert_eq!(restored["gap"]["possible"], true);
    assert_eq!(restored["gap"]["claim"], "KNOWN_GAP_M5_H1");

    let local = inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    let link =
        inspect_latest_declared_restore_witness_link(&root.join(LOCAL_OWNER_DATABASE_FILENAME))
            .unwrap()
            .expect("durable declared-restore Witness link");
    let successor = provider.record.as_ref().expect("finalized successor");
    assert_eq!(provider.cas_attempts, 1);
    assert_eq!(provider.cas_observed_local_generations, [2]);
    assert_eq!(provider.durable_writes, 2);
    assert_eq!(successor.witness_revision, predecessor.witness_revision + 1);
    assert_eq!(
        successor.accepted_authority_generation,
        predecessor.accepted_authority_generation + 1
    );
    assert_eq!(successor.transition_kind, "DECLARED_RESTORE");
    assert_eq!(successor.generation_anchor, link.anchor);
    assert_eq!(local.current.as_ref(), Some(&successor.generation_anchor));
    assert_eq!(
        successor.restore_source_commitment.as_deref(),
        Some(format!("sha256:{}", successor.generation_anchor.event_fingerprint).as_str())
    );
    assert_eq!(
        link.witness_predecessor_commitment,
        predecessor.integrity_authenticity_evidence
    );
    assert_eq!(link.checkpoint_identity, "checkpoint:M5:H1");
    assert_eq!(link.restored_from, "checkpoint:M5:H1");
    assert_eq!(link.lineage_authority, "external:M5:H1:declared-restore");
    assert_eq!(link.gap["claim"], "KNOWN_GAP_M5_H1");
    assert_eq!(
        kernel.health().unwrap()["continuityAdmission"]["relation"],
        "MATCH"
    );
    assert!(!provider.observed_unlocked_call);
    kernel.shutdown().expect("shutdown finalized H1");
    let restarted = start_with_witness_provider(&root, &selector, &mut provider, None)
        .expect("ordinary restart uses the finalized head");
    assert_eq!(
        restarted.health().unwrap()["continuityAdmission"]["relation"],
        "MATCH"
    );
    assert_eq!(
        provider.durable_writes, 2,
        "restart must not advance Witness"
    );
    restarted.shutdown().expect("shutdown H1 restart");
}

#[test]
fn dp_h_h2_ambiguous_finalize_blocks_until_read_first_reconciliation() {
    let (_parent, root) = witness_root();
    let selector = selector("DP-H-H2");
    let mut provider = SyntheticWitnessProvider::new(&root);
    let kernel = start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("DP-H-H2")),
    )
    .expect("reuse DP-E bootstrap fixture");
    let predecessor = provider.record.clone().expect("enrolled predecessor");
    provider.cas_mode = CasMode::UnknownNotPersisted;
    expect_code(
        declared_restore_with_witness_provider(
            kernel,
            &selector,
            &mut provider,
            declared_restore_request("H2"),
        ),
        "RECONCILIATION_REQUIRED",
    );
    let interrupted = inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    assert_eq!(interrupted.current.as_ref().unwrap().authority_epoch, 2);
    assert_eq!(provider.record.as_ref(), Some(&predecessor));
    assert_eq!(provider.durable_writes, 1);
    assert_eq!(provider.cas_observed_local_generations, [2]);

    expect_code(
        start_with_witness_provider(&root, &selector, &mut provider, None),
        "RECONCILIATION_REQUIRED",
    );
    assert_eq!(
        inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap(),
        interrupted
    );
    assert_eq!(provider.record.as_ref(), Some(&predecessor));

    provider.cas_mode = CasMode::Normal;
    let operation_start = provider.operations.len();
    let reconciled =
        reconcile_declared_restore_with_witness_provider(&root, &selector, &mut provider)
            .expect("exact read-first reconciliation finalizes without repeating restore");
    assert_eq!(
        &provider.operations[operation_start..],
        &["READ", "CAS", "READ"]
    );
    assert_eq!(
        inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap(),
        interrupted,
        "reconciliation must not create another local generation or event"
    );
    let successor = provider.record.as_ref().expect("reconciled successor");
    assert_eq!(successor.witness_revision, 2);
    assert_eq!(successor.accepted_authority_generation, 2);
    assert_eq!(successor.transition_kind, "DECLARED_RESTORE");
    assert_eq!(provider.durable_writes, 2);
    assert_eq!(
        reconciled.health().unwrap()["continuityAdmission"]["relation"],
        "MATCH"
    );
    assert!(!provider.observed_unlocked_call);
    reconciled.shutdown().expect("shutdown reconciled H2");
}

#[test]
fn dp_h_h3_stale_predecessor_and_unknown_domains_do_not_rewrite_continuity() {
    let fixture = protected_witness_fixture("DP-H-H3");
    let body_root = fixture
        ._parent
        .path()
        .join("synthetic-private-memory-body-root");
    std::fs::create_dir(&body_root).expect("create H3 Memory body root");
    std::fs::set_permissions(&body_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect H3 Memory body root");
    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open protected Witness provider");
    let selector = provider.selector().clone();
    let kernel = start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning("DP-H-H3", "synthetic-h3")),
        Some(&body_root),
    )
    .expect("reuse protected DP-E bootstrap fixture");
    let initial_presence = kernel
        .query_presence_context(unknown_presence_request('1'))
        .expect("read H3 identity before creating individual Memory");
    let identity = initial_presence["identity"]["opaqueId"]
        .as_str()
        .expect("H3 identity")
        .to_owned();
    let generation = initial_presence["identity"]["authorityGeneration"]
        .as_u64()
        .expect("H3 authority generation");
    let body_path = write_body(&body_root, &identity, MEMORY_BODY);
    apply_memory(
        &kernel,
        candidate_create(
            &identity,
            generation,
            MEMORY_BODY,
            "operation:DP-H-H3:memory-candidate",
        ),
        "operation:DP-H-H3:memory-candidate",
    );
    let candidate_fact = candidate_fingerprint(&kernel);
    apply_memory(
        &kernel,
        state_mutation(
            MEMORY_INVENTORY_SLOT,
            "operation:DP-H-H3:memory-inventory-candidate",
            "CREATE",
            None,
            inventory_content(&identity, generation, None),
        ),
        "operation:DP-H-H3:memory-inventory-candidate",
    );
    apply_memory(
        &kernel,
        state_mutation(
            MEMORY_ID,
            "operation:DP-H-H3:memory-adopted",
            "CREATE",
            None,
            authority_content(
                &identity,
                generation,
                &candidate_fact,
                MEMORY_BODY,
                "ADOPTED",
            ),
        ),
        "operation:DP-H-H3:memory-adopted",
    );
    let inventory_fact = state_fingerprint(&kernel, MEMORY_INVENTORY_SLOT);
    apply_memory(
        &kernel,
        state_mutation(
            MEMORY_INVENTORY_SLOT,
            "operation:DP-H-H3:memory-inventory-adopted",
            "REVISE",
            Some(&inventory_fact),
            inventory_content(&identity, generation, Some(MEMORY_ID)),
        ),
        "operation:DP-H-H3:memory-inventory-adopted",
    );
    let adopted_before_restore = kernel
        .query_presence_context(unknown_presence_request('2'))
        .expect("H3 individual Memory is adopted before restore");
    assert_eq!(
        adopted_before_restore["memory"]["adopted"]["memoryId"],
        MEMORY_ID
    );
    assert_eq!(
        adopted_before_restore["memory"]["adopted"]["authorityRelation"],
        "ADOPTED"
    );
    assert_eq!(
        adopted_before_restore["memory"]["adopted"]["bodyAvailability"],
        "VERIFIED"
    );
    let memory_authority_fact =
        adopted_before_restore["memory"]["adopted"]["factFingerprint"].clone();
    assert!(memory_authority_fact.as_str().is_some());
    std::fs::remove_file(body_path).expect("make H3 individual Memory body unavailable");
    let predecessor = match provider.read(&selector) {
        WitnessReadOutcome::PresentValid(record) => *record,
        _ => panic!("protected predecessor must read exactly"),
    };
    let (kernel, _) = declared_restore_with_witness_provider(
        kernel,
        &selector,
        &mut provider,
        declared_restore_request("H3"),
    )
    .expect("finalize protected H3 successor");
    let finalized = match provider.read(&selector) {
        WitnessReadOutcome::PresentValid(record) => *record,
        _ => panic!("protected successor must read exactly"),
    };
    let record_path = sole_witness_record(&fixture.protected_root);
    let witness_before = std::fs::read(&record_path).expect("read finalized Witness bytes");
    let resident_before =
        inspect_continuity(&fixture.resident_root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();

    let presence = kernel
        .query_presence_context(unknown_presence_request('3'))
        .expect("restored Resident projects domain-local UNKNOWN honestly");
    assert_eq!(presence["identity"]["authorityGeneration"], generation + 1);
    assert_eq!(presence["oneRing"]["sessionAvailability"], "UNKNOWN");
    assert_eq!(presence["memory"]["adopted"]["memoryId"], MEMORY_ID);
    assert_eq!(presence["memory"]["adopted"]["identityOpaqueId"], identity);
    assert_eq!(
        presence["memory"]["adopted"]["authorityGeneration"],
        generation
    );
    assert_eq!(
        presence["memory"]["adopted"]["authorityRelation"],
        "ADOPTED"
    );
    assert_eq!(
        presence["memory"]["adopted"]["factFingerprint"],
        memory_authority_fact
    );
    assert_eq!(presence["memory"]["adopted"]["currentness"], "UNKNOWN");
    assert_eq!(presence["memory"]["adopted"]["bodyAvailability"], "UNKNOWN");
    assert_eq!(
        presence["memory"]["candidates"].as_array().unwrap().len(),
        1
    );
    assert_eq!(
        presence["memory"]["candidates"][0]["executionAuthority"],
        false
    );
    let work_facts = presence["work"]["facts"].as_array().expect("Work facts");
    assert!(work_facts[..4].iter().all(|fact| {
        fact["categoryState"] == "UNKNOWN" && fact["factCurrentness"] == "UNKNOWN"
    }));
    assert_eq!(presence["life"]["categoryState"], "UNKNOWN");
    assert_eq!(presence["life"]["currentness"], "UNKNOWN");
    assert_eq!(presence["witness"]["relation"], "MATCH");

    let mut divergent = finalized.clone();
    divergent.generation_anchor.event_fingerprint = "f".repeat(64);
    divergent.continuity_commitment = continuity_commitment(&divergent.generation_anchor).unwrap();
    divergent.restore_source_commitment = Some(format!(
        "sha256:{}",
        divergent.generation_anchor.event_fingerprint
    ));
    divergent.integrity_authenticity_evidence = divergent.integrity_digest(&selector).unwrap();
    divergent
        .validate(&selector)
        .expect("valid divergent successor candidate");
    assert_eq!(
        provider.compare_and_swap(&selector, &predecessor, &divergent),
        WitnessCasOutcome::PredecessorMismatch
    );
    assert_eq!(
        std::fs::read(&record_path).expect("read Witness after stale CAS"),
        witness_before
    );
    assert_eq!(
        inspect_continuity(&fixture.resident_root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap(),
        resident_before
    );
    kernel.shutdown().expect("shutdown finalized H3 kernel");

    let mut stale_provider = SyntheticWitnessProvider::new(&fixture.resident_root);
    stale_provider.record = Some(predecessor);
    expect_code(
        start_with_witness_provider(&fixture.resident_root, &selector, &mut stale_provider, None),
        "RECONCILIATION_REQUIRED",
    );
    assert_eq!(
        inspect_continuity(&fixture.resident_root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap(),
        resident_before
    );
    assert_eq!(
        std::fs::read(&record_path).expect("read Witness after stale Resident admission"),
        witness_before
    );
}

#[test]
fn dp_e_bootstrap_exact_readback_and_descendant_restart_are_stable() {
    let (_parent, root) = witness_root();
    let selector = selector("BOOTSTRAP");
    let mut provider = SyntheticWitnessProvider::new(&root);

    let kernel = start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("BOOTSTRAP")),
    )
    .expect("authenticated absence may bootstrap and enroll");
    assert_eq!(
        kernel.health().unwrap()["continuityAdmission"]["relation"],
        "MATCH"
    );
    assert_eq!(provider.enroll_attempts, 1);
    assert_eq!(provider.durable_writes, 1);
    assert!(
        !provider.observed_unlocked_call,
        "Witness calls must be under the Resident lock"
    );
    let witness_before = provider.record.clone().expect("enrolled record");
    let generation_before = witness_before.accepted_authority_generation;
    commit_goal_event(&kernel);
    kernel.shutdown().expect("shutdown after descendant event");

    let snapshot_before = inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    let restarted = start_with_witness_provider(&root, &selector, &mut provider, None)
        .expect("local descendant of enrolled Witness anchor must be admitted");
    assert_eq!(
        restarted.health().unwrap()["continuityAdmission"]["relation"],
        "LOCAL_DESCENDS_FROM_WITNESS"
    );
    restarted.shutdown().expect("restart shutdown");
    let snapshot_after = inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    assert_eq!(
        snapshot_after.authority_anchors,
        snapshot_before.authority_anchors
    );
    assert_eq!(
        provider.enroll_attempts, 1,
        "ordinary restart must not write Witness"
    );
    assert_eq!(provider.durable_writes, 1);
    assert_eq!(provider.record.as_ref().unwrap().witness_revision, 1);
    assert_eq!(
        provider
            .record
            .as_ref()
            .unwrap()
            .accepted_authority_generation,
        generation_before
    );
    assert_eq!(provider.record.as_ref(), Some(&witness_before));
    assert!(!provider.observed_unlocked_call);
}

#[test]
fn dp_e_unknown_enrollment_response_is_admitted_only_after_exact_readback() {
    let (_parent, root) = witness_root();
    let selector = selector("UNKNOWN-PERSISTED");
    let mut provider = SyntheticWitnessProvider::new(&root);
    provider.enroll_mode = EnrollMode::UnknownPersisted;

    let kernel = start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("UNKNOWN-PERSISTED")),
    )
    .expect("unknown response with exact durable readback is reconcilable");
    assert_eq!(kernel.health().unwrap()["mutationEligible"], true);
    kernel.shutdown().unwrap();
    assert_eq!(provider.enroll_attempts, 1);
    assert_eq!(provider.durable_writes, 1);
    assert!(provider.reads >= 2);
    assert!(!provider.observed_unlocked_call);
}

#[test]
fn dp_e_missing_readback_leaves_only_reconcilable_genesis_and_never_silent_authority() {
    let (_parent, root) = witness_root();
    let selector = selector("UNKNOWN-ABSENT");
    let mut provider = SyntheticWitnessProvider::new(&root);
    provider.enroll_mode = EnrollMode::UnknownNotPersisted;

    expect_code(
        start_with_witness_provider(
            &root,
            &selector,
            &mut provider,
            Some(&provisioning("UNKNOWN-ABSENT")),
        ),
        "LINEAGE_CONFLICT",
    );
    let interrupted = inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    assert_eq!(interrupted.authority_anchors.len(), 1);
    assert_eq!(interrupted.event_fingerprints.len(), 1);

    provider.enroll_mode = EnrollMode::Normal;
    let reconciled = start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("UNKNOWN-ABSENT")),
    )
    .expect("exact genesis-only state may retry the same enrollment");
    assert_eq!(
        reconciled.health().unwrap()["continuityAdmission"]["relation"],
        "MATCH"
    );
    reconciled.shutdown().unwrap();
    assert_eq!(provider.durable_writes, 1);
    assert_eq!(provider.enroll_attempts, 2);
    assert!(!provider.observed_unlocked_call);
}

#[test]
fn dp_e_required_unavailable_invalid_multiple_and_conflict_all_block() {
    for (case_id, forced_read, code) in [
        (
            "UNAVAILABLE",
            ForcedRead::Unavailable,
            "EXTERNAL_EVIDENCE_UNAVAILABLE",
        ),
        ("INVALID", ForcedRead::Invalid, "LINEAGE_CONFLICT"),
        ("MULTIPLE", ForcedRead::Multiple, "LINEAGE_CONFLICT"),
    ] {
        let (_parent, root) = witness_root();
        let selector = selector(case_id);
        let mut provider = SyntheticWitnessProvider::new(&root);
        provider.forced_read = forced_read;
        expect_code(
            start_with_witness_provider(
                &root,
                &selector,
                &mut provider,
                Some(&provisioning(case_id)),
            ),
            code,
        );
        assert!(!root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
    }

    let (_parent, root) = witness_root();
    let selector = selector("ENROLL-CONFLICT");
    let mut provider = SyntheticWitnessProvider::new(&root);
    provider.enroll_mode = EnrollMode::Conflict;
    expect_code(
        start_with_witness_provider(
            &root,
            &selector,
            &mut provider,
            Some(&provisioning("ENROLL-CONFLICT")),
        ),
        "LINEAGE_CONFLICT",
    );
}

#[test]
fn dp_e_intact_enrollment_blocks_rebootstrap_after_local_rollback() {
    let (_parent, root) = witness_root();
    let selector = selector("DUAL-ROLLBACK");
    let mut provider = SyntheticWitnessProvider::new(&root);
    start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("DUAL-ROLLBACK")),
    )
    .expect("initial enrollment")
    .shutdown()
    .unwrap();
    let enrolled = provider.record.clone();

    std::fs::remove_file(root.join(LOCAL_OWNER_DATABASE_FILENAME))
        .expect("synthetically roll back only the Resident DB");
    expect_code(
        start_with_witness_provider(&root, &selector, &mut provider, None),
        "LOCAL_STALE",
    );
    expect_code(
        start_with_witness_provider(
            &root,
            &selector,
            &mut provider,
            Some(&provisioning("DUAL-ROLLBACK-RETRY")),
        ),
        "LOCAL_OWNER_INVALID_INPUT",
    );
    assert_eq!(provider.record, enrolled);
    assert_eq!(provider.durable_writes, 1);
}

#[test]
fn dp_e_authenticated_but_divergent_record_is_not_a_grant() {
    let (_parent, root) = witness_root();
    let selector = selector("DIVERGENT");
    let mut provider = SyntheticWitnessProvider::new(&root);
    start_with_witness_provider(
        &root,
        &selector,
        &mut provider,
        Some(&provisioning("DIVERGENT")),
    )
    .unwrap()
    .shutdown()
    .unwrap();

    let mut divergent = provider.record.clone().unwrap();
    divergent.generation_anchor.event_fingerprint = "f".repeat(64);
    divergent.continuity_commitment = continuity_commitment(&divergent.generation_anchor).unwrap();
    divergent.integrity_authenticity_evidence = divergent.integrity_digest(&selector).unwrap();
    divergent
        .validate(&selector)
        .expect("internally valid synthetic contradiction");
    provider.record = Some(divergent);
    expect_code(
        start_with_witness_provider(&root, &selector, &mut provider, None),
        "LINEAGE_CONFLICT",
    );
}

#[test]
fn dp_e_selector_and_provisioning_are_exact_and_caller_cannot_self_report_absence() {
    let (_parent, root) = witness_root();
    let mut invalid_selector = selector("BAD-SELECTOR");
    invalid_selector.witness_slot_id = "witness-slot:v1:not-a-digest".to_owned();
    let mut provider = SyntheticWitnessProvider::new(&root);
    expect_code(
        start_with_witness_provider(
            &root,
            &invalid_selector,
            &mut provider,
            Some(&provisioning("BAD-SELECTOR")),
        ),
        "LOCAL_OWNER_INVALID_INPUT",
    );

    let selector = selector("BAD-PROVISIONING");
    let mut bad = provisioning("BAD-PROVISIONING");
    bad["unexpected"] = json!(true);
    expect_code(
        start_with_witness_provider(&root, &selector, &mut provider, Some(&bad)),
        "LOCAL_OWNER_INVALID_INPUT",
    );
    assert!(!root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
}

#[test]
fn protected_file_genesis_is_private_canonical_and_restarts_as_match_without_caller_evidence() {
    const PRIVATE_SENTINEL: &str = "PRIVATE-PROVISIONING-SENTINEL-7f0f6c2d";
    let fixture = protected_witness_fixture(PRIVATE_SENTINEL);
    let protected_metadata = std::fs::symlink_metadata(&fixture.protected_root)
        .expect("independent protected Witness root metadata");
    assert!(protected_metadata.is_dir());
    assert!(!protected_metadata.file_type().is_symlink());
    assert_eq!(protected_metadata.permissions().mode() & 0o777, 0o700);

    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open independent protected Witness root");
    let selector = provider.selector().clone();
    let genesis = start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning("GENESIS", PRIVATE_SENTINEL)),
        None,
    )
    .expect("authenticated protected Witness absence may enroll genesis");
    let genesis_health = genesis.health().expect("protected Witness genesis health");
    assert_eq!(genesis_health["continuityAdmission"]["relation"], "MATCH");
    assert_eq!(genesis_health["mutationEligible"], true);

    let record_path = sole_witness_record(&fixture.protected_root);
    let metadata = std::fs::symlink_metadata(&record_path).expect("Witness record metadata");
    assert!(metadata.is_file());
    assert!(!metadata.file_type().is_symlink());
    assert_eq!(metadata.permissions().mode() & 0o777, 0o600);
    assert_eq!(metadata.nlink(), 1);
    let enrolled_bytes = std::fs::read(&record_path).expect("read enrolled Witness record");
    let enrolled: Value =
        serde_json::from_slice(&enrolled_bytes).expect("parse enrolled Witness record");
    assert_eq!(
        canonical_value_bytes(&enrolled).expect("canonicalize enrolled Witness record"),
        enrolled_bytes,
        "the durable Witness record must use exact canonical JSON"
    );
    let object = enrolled.as_object().expect("Witness record object");
    let mut keys = object.keys().map(String::as_str).collect::<Vec<_>>();
    keys.sort_unstable();
    assert_eq!(
        keys,
        vec![
            "acceptedAuthorityGeneration",
            "continuityCommitment",
            "contractVersion",
            "enrollmentState",
            "generationAnchor",
            "identityCommitment",
            "integrityAuthenticityEvidence",
            "restoreSourceCommitment",
            "transitionKind",
            "witnessRevision",
            "witnessSlotId",
        ]
    );
    let record_text = String::from_utf8(enrolled_bytes.clone()).expect("UTF-8 Witness record");
    let health_text = serde_json::to_string(&genesis_health).expect("serialize genesis health");
    for public_text in [&record_text, &health_text] {
        assert!(!public_text.contains(PRIVATE_SENTINEL));
        assert!(!public_text.contains(&fixture.protected_root.to_string_lossy().to_string()));
        assert!(!public_text.contains(&fixture.resident_root.to_string_lossy().to_string()));
    }
    genesis
        .shutdown()
        .expect("protected Witness genesis shutdown");

    let mut restarted_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("reopen protected Witness provider");
    assert_eq!(restarted_provider.selector(), &selector);
    let restarted = start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut restarted_provider,
        None,
        None,
    )
    .expect("ordinary restart derives continuity only from protected Witness");
    assert_eq!(
        restarted.health().expect("restart health")["continuityAdmission"]["relation"],
        "MATCH"
    );
    restarted
        .shutdown()
        .expect("protected Witness restart shutdown");
    assert_eq!(
        std::fs::read(&record_path).expect("read Witness record after restart"),
        enrolled_bytes,
        "ordinary restart must not rewrite the enrolled Witness record"
    );
}

#[test]
fn protected_file_ignores_crash_residue_until_a_complete_final_record_is_published() {
    let fixture = protected_witness_fixture("ATOMIC-PUBLISH");
    let residue = fixture
        .protected_root
        .join(format!(".{}.deadbeef.witness.tmp", "a".repeat(64)));
    std::fs::write(&residue, b"partial").expect("create synthetic pre-publication crash residue");
    std::fs::set_permissions(&residue, std::fs::Permissions::from_mode(0o600))
        .expect("protect synthetic crash residue");

    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around harmless temp residue");
    let selector = provider.selector().clone();
    start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning(
            "ATOMIC-PUBLISH",
            "private-atomic-publish",
        )),
        None,
    )
    .expect("a non-final temp inode cannot impersonate an enrolled Witness")
    .shutdown()
    .expect("shutdown atomically published Witness");

    assert_eq!(
        std::fs::read(&residue).expect("read unchanged crash residue"),
        b"partial"
    );
    let final_records = std::fs::read_dir(&fixture.protected_root)
        .expect("read protected Witness root after atomic publication")
        .map(|entry| entry.expect("read Witness entry").file_name())
        .filter(|leaf| {
            leaf.to_str()
                .is_some_and(|value| value.ends_with(".witness.json"))
        })
        .count();
    assert_eq!(final_records, 1);

    let mut restarted_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("reopen provider with harmless temp residue");
    let restarted_selector = restarted_provider.selector().clone();
    start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &restarted_selector,
        &mut restarted_provider,
        None,
        None,
    )
    .expect("complete final record remains authoritative after restart")
    .shutdown()
    .expect("shutdown restarted atomic Witness");
}

#[test]
fn protected_file_present_witness_rejects_an_empty_second_resident_root() {
    let fixture = protected_witness_fixture("SECOND-ROOT");
    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open first protected Witness provider");
    let selector = provider.selector().clone();
    start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning("FIRST-ROOT", "private-first-root")),
        None,
    )
    .expect("enroll first Resident root")
    .shutdown()
    .expect("shutdown first Resident root");
    let record_path = sole_witness_record(&fixture.protected_root);
    let record_before = std::fs::read(&record_path).expect("read enrolled Witness record");

    let second_root = fixture
        ._parent
        .path()
        .join("second-resident")
        .join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir_all(&second_root).expect("create empty second Resident root");
    std::fs::set_permissions(&second_root, std::fs::Permissions::from_mode(0o700))
        .expect("protect empty second Resident root");
    assert_eq!(
        std::fs::read_dir(&second_root)
            .expect("read empty second Resident root")
            .count(),
        0
    );
    let mut second_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &second_root)
            .expect("open existing protected Witness for second Resident root");
    assert_eq!(second_provider.selector(), &selector);
    expect_code(
        start_with_witness_and_memory_body_root(
            &second_root,
            &selector,
            &mut second_provider,
            None,
            None,
        ),
        "LOCAL_STALE",
    );
    assert!(!second_root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
    assert_eq!(
        std::fs::read(&record_path).expect("read Witness after rejected second root"),
        record_before
    );
}

#[test]
fn protected_file_root_identity_topology_symlink_and_permissions_fail_closed() {
    let fixture = protected_witness_fixture("ROOT-GUARDS");

    expect_protected_open_code(
        &fixture.resident_root,
        &fixture.resident_root,
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );
    std::fs::set_permissions(
        fixture._parent.path(),
        std::fs::Permissions::from_mode(0o700),
    )
    .expect("protect ancestor root");
    expect_protected_open_code(
        fixture._parent.path(),
        &fixture.resident_root,
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );

    let descendant = fixture.resident_root.join("protected-witness-descendant");
    std::fs::create_dir(&descendant).expect("create protected Witness descendant");
    std::fs::set_permissions(&descendant, std::fs::Permissions::from_mode(0o700))
        .expect("protect Witness descendant");
    expect_protected_open_code(
        &descendant,
        &fixture.resident_root,
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );

    let symlink_root = fixture._parent.path().join("protected-witness-symlink");
    symlink(&fixture.protected_root, &symlink_root).expect("create protected Witness root symlink");
    expect_protected_open_code(
        &symlink_root,
        &fixture.resident_root,
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );

    let wrong_mode_root = fixture._parent.path().join("protected-witness-wrong-mode");
    std::fs::create_dir(&wrong_mode_root).expect("create wrong-mode protected Witness root");
    std::fs::set_permissions(&wrong_mode_root, std::fs::Permissions::from_mode(0o750))
        .expect("set rejected protected Witness root mode");
    expect_protected_open_code(
        &wrong_mode_root,
        &fixture.resident_root,
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );
}

#[test]
fn protected_file_record_wrong_mode_and_symlink_fail_closed() {
    let fixture = protected_witness_fixture("RECORD-METADATA");
    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open protected Witness provider");
    let selector = provider.selector().clone();
    start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning("RECORD-METADATA", "private-record")),
        None,
    )
    .expect("enroll protected Witness record")
    .shutdown()
    .expect("shutdown protected Witness enrollment");
    let record_path = sole_witness_record(&fixture.protected_root);
    let original = std::fs::read(&record_path).expect("read original Witness record");

    std::fs::set_permissions(&record_path, std::fs::Permissions::from_mode(0o640))
        .expect("make Witness record mode unsafe");
    let mut wrong_mode_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around wrong-mode record");
    expect_code(
        start_with_witness_and_memory_body_root(
            &fixture.resident_root,
            &selector,
            &mut wrong_mode_provider,
            None,
            None,
        ),
        "LINEAGE_CONFLICT",
    );

    let symlink_target = fixture._parent.path().join("private-witness-record-target");
    let mut target = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&symlink_target)
        .expect("create private Witness symlink target");
    use std::io::Write as _;
    target
        .write_all(&original)
        .expect("write private Witness symlink target");
    target
        .sync_all()
        .expect("sync private Witness symlink target");
    drop(target);
    std::fs::remove_file(&record_path).expect("remove wrong-mode Witness record");
    symlink(&symlink_target, &record_path).expect("replace Witness record with symlink");
    let mut symlink_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around Witness record symlink");
    expect_code(
        start_with_witness_and_memory_body_root(
            &fixture.resident_root,
            &selector,
            &mut symlink_provider,
            None,
            None,
        ),
        "EXTERNAL_EVIDENCE_UNAVAILABLE",
    );
}

#[test]
fn protected_file_tampered_noncanonical_and_invalid_records_are_rejected() {
    let fixture = protected_witness_fixture("RECORD-CONTENT");
    let mut provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open protected Witness provider");
    let selector = provider.selector().clone();
    start_with_witness_and_memory_body_root(
        &fixture.resident_root,
        &selector,
        &mut provider,
        Some(&protected_provisioning("RECORD-CONTENT", "private-content")),
        None,
    )
    .expect("enroll protected Witness record")
    .shutdown()
    .expect("shutdown protected Witness enrollment");
    let record_path = sole_witness_record(&fixture.protected_root);
    let original = std::fs::read(&record_path).expect("read original Witness record");

    let mut tampered: Value =
        serde_json::from_slice(&original).expect("parse original Witness record");
    tampered["witnessRevision"] = json!(2);
    std::fs::write(
        &record_path,
        canonical_value_bytes(&tampered).expect("canonical tampered Witness record"),
    )
    .expect("write internally inconsistent Witness record");
    let mut tampered_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around tampered Witness record");
    expect_code(
        start_with_witness_and_memory_body_root(
            &fixture.resident_root,
            &selector,
            &mut tampered_provider,
            None,
            None,
        ),
        "LINEAGE_CONFLICT",
    );

    let mut noncanonical = original.clone();
    noncanonical.push(b'\n');
    std::fs::write(&record_path, noncanonical).expect("write noncanonical Witness record");
    let mut noncanonical_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around noncanonical Witness record");
    expect_code(
        start_with_witness_and_memory_body_root(
            &fixture.resident_root,
            &selector,
            &mut noncanonical_provider,
            None,
            None,
        ),
        "LINEAGE_CONFLICT",
    );

    std::fs::write(&record_path, b"{\"unexpected\":true}")
        .expect("write invalid Witness record schema");
    let mut invalid_provider =
        ProtectedFileWitnessProvider::open(&fixture.protected_root, &fixture.resident_root)
            .expect("open provider around invalid Witness record");
    expect_code(
        start_with_witness_and_memory_body_root(
            &fixture.resident_root,
            &selector,
            &mut invalid_provider,
            None,
            None,
        ),
        "LINEAGE_CONFLICT",
    );
}
