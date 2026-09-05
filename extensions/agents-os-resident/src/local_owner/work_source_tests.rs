use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};

use rusqlite::{Connection, OpenFlags};
use serde_json::{Value, json};

use super::{
    WORK_CATEGORY, WORK_CURRENTNESS_POLICY_ID, WORK_ENVELOPE_SCHEMA, WORK_SOURCE_ID,
    WORK_SOURCE_OWNER, read_current_work_envelope,
};
use crate::local_owner::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel,
    PROFILE_ID,
};

const GOAL_TITLE_SENTINEL: &str = "D1_PRIVATE_GOAL_TITLE_MUST_NOT_LEAK";
const GOAL_BODY_SENTINEL: &str = "D1_PRIVATE_GOAL_BODY_MUST_NOT_LEAK";
const TASK_TITLE_SENTINEL: &str = "D1_PRIVATE_TASK_TITLE_MUST_NOT_LEAK";
const TASK_BODY_SENTINEL: &str = "D1_PRIVATE_TASK_BODY_MUST_NOT_LEAK";
const RESULT_BODY_SENTINEL: &str = "D1_PRIVATE_RESULT_BODY_MUST_NOT_LEAK";
const ACTIVITY_BODY_SENTINEL: &str = "D1_PRIVATE_ACTIVITY_BODY_MUST_NOT_LEAK";

fn root() -> (tempfile::TempDir, PathBuf) {
    let parent = tempfile::tempdir().unwrap();
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).unwrap();
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).unwrap();
    (parent, root)
}

fn empty_evidence(case_id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": format!("evidence:{case_id}:genesis"),
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:D1",
    })
}

fn provisioning(case_id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:D1",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": format!("provisioning:{case_id}"),
        "residentId": PROFILE_ID,
    })
}

fn start_genesis(root: &Path, case_id: &str) -> LocalOwnerKernel {
    let evidence = empty_evidence(case_id);
    let authority = provisioning(case_id);
    LocalOwnerKernel::start(root, Some(&evidence), Some(&authority)).unwrap()
}

fn start_restart(root: &Path, case_id: &str, anchor: &Value) -> LocalOwnerKernel {
    let evidence = json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": anchor,
        "evidenceId": format!("evidence:{case_id}:restart"),
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:D1",
    });
    LocalOwnerKernel::start(root, Some(&evidence), None).unwrap()
}

fn mutation(operation: &str, mutation_type: &str, payload: Value) -> Value {
    json!({
        "mutation": {
            "mutationType": mutation_type,
            "payload": payload,
        },
        "operation": operation,
    })
}

fn prepare(kernel: &LocalOwnerKernel, generation: u64, request: Value) -> Value {
    kernel
        .prepare_proposal(json!({
            "attachmentGeneration": generation,
            "request": request,
        }))
        .unwrap()
}

fn commit(kernel: &LocalOwnerKernel, generation: u64, request: Value) -> Value {
    let proposal = prepare(kernel, generation, request);
    assert_eq!(proposal["resultCode"], "PROPOSAL_PREPARED");
    kernel
        .submit_consent(json!({
            "attachmentGeneration": generation,
            "ingress": "TYPED_TEXT",
            "transcript": proposal["consentPrompt"],
        }))
        .unwrap()
}

fn create_and_start_goal(
    kernel: &LocalOwnerKernel,
    generation: u64,
    task_count: usize,
) -> (String, Vec<String>) {
    let criteria = (0..task_count)
        .map(|index| {
            json!({
                "description": format!("criterion-{index}"),
                "selectedTaskOrdinal": index + 1,
            })
        })
        .collect::<Vec<_>>();
    let tasks = (0..task_count)
        .map(|index| {
            json!({
                "description": format!("{TASK_BODY_SENTINEL}-{index}"),
                "supportsCriteria": [index + 1],
                "title": format!("{TASK_TITLE_SENTINEL}-{index}"),
            })
        })
        .collect::<Vec<_>>();
    let created = commit(
        kernel,
        generation,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "CREATE_GOAL_BUNDLE",
            json!({
                "description": GOAL_BODY_SENTINEL,
                "successCriteria": criteria,
                "tasks": tasks,
                "title": GOAL_TITLE_SENTINEL,
            }),
        ),
    );
    let goal_id = created["result"]["goalId"].as_str().unwrap().to_owned();
    let queried = kernel
        .query(json!({
            "attachmentGeneration": generation,
            "request": {
                "operation": "QUERY_TASKS",
                "query": {"goalId": goal_id, "mode": "LIST"},
            },
        }))
        .unwrap();
    let task_ids = queried["items"]
        .as_array()
        .unwrap()
        .iter()
        .map(|item| item["taskId"].as_str().unwrap().to_owned())
        .collect::<Vec<_>>();
    assert_eq!(task_ids.len(), task_count);
    commit(
        kernel,
        generation,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "START_GOAL",
            json!({"goalId": goal_id}),
        ),
    );
    (goal_id, task_ids)
}

fn complete_task(kernel: &LocalOwnerKernel, generation: u64, task_id: &str, suffix: &str) {
    commit(
        kernel,
        generation,
        mutation(
            "PROPOSE_TASK_MUTATION",
            "START_TASK",
            json!({
                "activityContext": format!("{ACTIVITY_BODY_SENTINEL}-{suffix}"),
                "taskId": task_id,
            }),
        ),
    );
    let completed = commit(
        kernel,
        generation,
        mutation(
            "PROPOSE_TASK_MUTATION",
            "COMPLETE_TASK_MANUALLY",
            json!({
                "resultSummary": format!("{RESULT_BODY_SENTINEL}-{suffix}"),
                "taskId": task_id,
            }),
        ),
    );
    assert_eq!(completed["result"]["taskStatus"], "DONE");
    assert_eq!(completed["result"]["validationDecision"], "PASSED");
}

fn read_work(root: &Path, expected_cut: Option<&str>) -> Result<Value, LocalOwnerError> {
    let connection = Connection::open_with_flags(
        root.join(LOCAL_OWNER_DATABASE_FILENAME),
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?;
    connection.pragma_update(None, "query_only", true)?;
    read_current_work_envelope(&connection, 1, expected_cut)
}

fn presence_request(suffix: char, expected_work_cut: Option<&str>) -> Value {
    json!({
        "attachmentGeneration": 1,
        "expectedSlots": {
            "lifeFactFingerprint": null,
            "memoryFactFingerprint": null,
            "oneRingFactFingerprint": null,
            "workSourceCutFingerprint": expected_work_cut,
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
        "transcriptDigest": "c".repeat(64),
    })
}

fn assert_zero_disclosure(value: &Value) {
    let serialized = serde_json::to_string(value).unwrap();
    for sentinel in [
        GOAL_TITLE_SENTINEL,
        GOAL_BODY_SENTINEL,
        TASK_TITLE_SENTINEL,
        TASK_BODY_SENTINEL,
        RESULT_BODY_SENTINEL,
        ACTIVITY_BODY_SENTINEL,
    ] {
        assert!(!serialized.contains(sentinel), "D1 disclosed {sentinel}");
    }
    for forbidden_key in [
        "title",
        "description",
        "resultSummary",
        "activityContext",
        "resultSummaryCommitment",
        "activityContextCommitment",
    ] {
        assert!(
            value.get(forbidden_key).is_none(),
            "D1 exposed forbidden key {forbidden_key}"
        );
    }
}

fn work_fact<'a>(value: &'a Value, category: &str) -> &'a Value {
    value["facts"]
        .as_array()
        .and_then(|facts| facts.iter().find(|fact| fact["category"] == category))
        .expect("explicit Work category assessment")
}

#[test]
fn real_goal_task_completion_projects_low_disclosure_and_restart_stable_cut() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "D1-REAL-COMPLETION");
    let (_goal_id, tasks) = create_and_start_goal(&kernel, 41, 1);

    let absent = read_work(&root, None).unwrap();
    assert_eq!(absent["schema"], WORK_ENVELOPE_SCHEMA);
    assert_eq!(absent["sourceId"], WORK_SOURCE_ID);
    assert_eq!(absent["sourceOwner"], WORK_SOURCE_OWNER);
    assert_eq!(absent["currentness"], "CURRENT");
    assert_eq!(
        absent["currentnessReasonCodes"],
        json!(["SOURCE_CUT_VERIFIED_CURRENT"])
    );
    assert_eq!(absent["sourceAvailability"], "AVAILABLE");
    let absent_result = work_fact(&absent, WORK_CATEGORY);
    assert_eq!(absent_result["categoryState"], "ABSENT");
    assert_eq!(absent_result["factCurrentness"], "CURRENT");
    assert!(absent_result["boundedRef"].is_null());
    for category in [
        "ACTIVE_COMMITMENT",
        "CURRENT_FOCUS_PROJECT_TASK",
        "NEXT_STEP",
        "WAITING_OR_BLOCKER",
    ] {
        let fact = work_fact(&absent, category);
        assert_eq!(fact["categoryState"], "UNKNOWN");
        assert_eq!(fact["factCurrentness"], "UNKNOWN");
    }
    assert_zero_disclosure(&absent);

    complete_task(&kernel, 41, &tasks[0], "accepted");
    let current = read_work(&root, None).unwrap();
    assert_eq!(current["schema"], WORK_ENVELOPE_SCHEMA);
    assert_eq!(current["currentnessPolicyId"], WORK_CURRENTNESS_POLICY_ID);
    assert_eq!(current["currentness"], "CURRENT");
    assert_eq!(current["authorityGeneration"], 1);
    assert_eq!(
        current["sourceCutEventSequence"],
        current["observedAtEventSequence"]
    );
    assert_eq!(current["sourceRevision"], current["sourceCutEventSequence"]);
    let current_result = work_fact(&current, WORK_CATEGORY);
    assert_eq!(current_result["categoryState"], "PRESENT");
    assert_eq!(current_result["factCurrentness"], "CURRENT");
    assert!(
        current_result["boundedRef"]
            .as_str()
            .unwrap()
            .starts_with("validation-result:sha256:")
    );
    assert!(
        current_result["subjectRef"]
            .as_str()
            .unwrap()
            .starts_with("work-subject:v1:")
    );
    assert!(
        current_result["validationRef"]
            .as_str()
            .unwrap()
            .starts_with("work-validation:v1:")
    );
    assert!(
        current["sourceCutFingerprint"]
            .as_str()
            .unwrap()
            .starts_with("sha256:")
    );
    assert!(
        current["projectionDigest"]
            .as_str()
            .unwrap()
            .starts_with("sha256:")
    );
    assert_zero_disclosure(&current);

    let expected_keys = [
        "authorityGeneration",
        "currentness",
        "currentnessPolicyId",
        "currentnessReasonCodes",
        "facts",
        "observedAtEventSequence",
        "projectionDigest",
        "schema",
        "sourceAvailability",
        "sourceCutEventSequence",
        "sourceCutFingerprint",
        "sourceId",
        "sourceOwner",
        "sourceRevision",
        "subjectIdentityRef",
    ];
    let object = current.as_object().unwrap();
    assert_eq!(object.len(), expected_keys.len());
    assert!(expected_keys.iter().all(|key| object.contains_key(*key)));

    let source_cut = current["sourceCutFingerprint"].as_str().unwrap();
    assert_eq!(read_work(&root, Some(source_cut)).unwrap(), current);
    assert!(matches!(
        read_work(
            &root,
            Some("sha256:0000000000000000000000000000000000000000000000000000000000000000")
        ),
        Err(LocalOwnerError::PresenceContextStale)
    ));

    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();
    let restarted = start_restart(&root, "D1-REAL-COMPLETION", &anchor);
    let after_restart = read_work(&root, Some(source_cut)).unwrap();
    assert_eq!(after_restart, current);
    restarted.shutdown().unwrap();
}

#[test]
fn later_real_validated_completion_advances_value_and_transition_cut() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "D1-LATEST-VALIDATED");
    let (_goal_id, tasks) = create_and_start_goal(&kernel, 43, 2);

    complete_task(&kernel, 43, &tasks[0], "first");
    let first = read_work(&root, None).unwrap();
    complete_task(&kernel, 43, &tasks[1], "second");
    let second = read_work(&root, None).unwrap();

    assert_eq!(work_fact(&first, WORK_CATEGORY)["categoryState"], "PRESENT");
    assert_eq!(
        work_fact(&second, WORK_CATEGORY)["categoryState"],
        "PRESENT"
    );
    assert_ne!(
        work_fact(&first, WORK_CATEGORY)["boundedRef"],
        work_fact(&second, WORK_CATEGORY)["boundedRef"]
    );
    assert_ne!(
        first["sourceCutFingerprint"],
        second["sourceCutFingerprint"]
    );
    assert!(second["sourceRevision"].as_u64().unwrap() > first["sourceRevision"].as_u64().unwrap());
    assert!(matches!(
        read_work(&root, Some(first["sourceCutFingerprint"].as_str().unwrap())),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    assert_zero_disclosure(&first);
    assert_zero_disclosure(&second);
    kernel.shutdown().unwrap();
}

#[test]
fn real_completion_reaches_presence_and_stale_source_cut_fails_closed() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "D1-PRESENCE-INTEGRATION");
    let (_goal_id, tasks) = create_and_start_goal(&kernel, 61, 2);

    complete_task(&kernel, 61, &tasks[0], "presence-first");
    let first = read_work(&root, None).unwrap();
    let first_cut = first["sourceCutFingerprint"].as_str().unwrap().to_owned();
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();
    let kernel = start_restart(&root, "D1-PRESENCE-INTEGRATION", &anchor);
    let projected = kernel
        .query_presence_context(presence_request('a', Some(&first_cut)))
        .expect("real validated Work must reach Presence");
    assert_eq!(projected["work"], first);
    assert_eq!(projected["work"]["currentness"], "CURRENT");
    assert_eq!(
        work_fact(&projected["work"], WORK_CATEGORY)["categoryState"],
        "PRESENT"
    );
    assert_zero_disclosure(&projected["work"]);

    complete_task(&kernel, 61, &tasks[1], "presence-second");
    assert!(matches!(
        kernel.query_presence_context(presence_request('b', Some(&first_cut))),
        Err(LocalOwnerError::PresenceContextStale)
    ));
    let latest = kernel
        .query_presence_context(presence_request('c', None))
        .expect("fresh Presence must select the latest validated completion");
    assert_ne!(latest["work"]["sourceCutFingerprint"], first_cut);
    assert_ne!(
        work_fact(&latest["work"], WORK_CATEGORY)["boundedRef"],
        work_fact(&first, WORK_CATEGORY)["boundedRef"]
    );
    assert_zero_disclosure(&latest["work"]);
    kernel.shutdown().unwrap();
}

#[test]
fn completion_chain_fingerprint_corruption_fails_closed() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "D1-CORRUPT-CHAIN");
    let (_goal_id, tasks) = create_and_start_goal(&kernel, 47, 1);
    complete_task(&kernel, 47, &tasks[0], "corrupt-chain");
    kernel.shutdown().unwrap();

    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    connection
        .execute("DROP TRIGGER immutable_validation_attempt_update", [])
        .unwrap();
    connection
        .execute(
            "UPDATE validation_attempt SET attempt_fingerprint=?1 WHERE status='PASSED'",
            ["ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"],
        )
        .unwrap();
    drop(connection);

    assert!(matches!(
        read_work(&root, None),
        Err(LocalOwnerError::StateCorrupt)
    ));
}

#[test]
fn stale_task_current_pointer_cannot_resurrect_an_older_work_cut() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "D1-STALE-POINTER");
    let (_goal_id, tasks) = create_and_start_goal(&kernel, 53, 1);
    complete_task(&kernel, 53, &tasks[0], "stale-pointer");
    kernel.shutdown().unwrap();

    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    connection
        .execute(
            "UPDATE current_pointer SET current_fact_revision=current_fact_revision-1,current_fact_ref=(SELECT fact_ref FROM canonical_fact WHERE fact_kind='TASK_STATE' AND logical_id=?1 AND fact_revision=current_pointer.current_fact_revision-1),current_fact_fingerprint=(SELECT fact_fingerprint FROM canonical_fact WHERE fact_kind='TASK_STATE' AND logical_id=?1 AND fact_revision=current_pointer.current_fact_revision-1),pointer_version=pointer_version-1,updated_event_sequence=(SELECT created_event_sequence FROM canonical_fact WHERE fact_kind='TASK_STATE' AND logical_id=?1 AND fact_revision=current_pointer.current_fact_revision-1) WHERE fact_kind='TASK_STATE' AND logical_id=?1",
            [&tasks[0]],
        )
        .unwrap();
    drop(connection);

    assert!(matches!(
        read_work(&root, None),
        Err(LocalOwnerError::StateCorrupt)
    ));
}
