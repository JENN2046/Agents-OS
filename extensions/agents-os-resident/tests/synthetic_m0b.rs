use agents_os_resident::{home, ledger::schema};
use agents_os_resident::canonical::jcs::canonicalize_json;
use agents_os_resident::home::candidate::{
    CandidateError, CandidateRevisionResult, CandidateSemanticClass, HomeCandidateRevision,
    derive_candidate_revision,
};
use agents_os_resident::home::session_boundary::{
    SessionBoundaryError, SessionBranchChoice, decode_synthetic_observation, reduce_nonpromotion,
};
use serde_json::{Value, json};

#[test]
fn wp1_preserves_the_home_layout_and_later_boundaries() {
    assert_eq!(home::M0B_ENVIRONMENT, "SYNTHETIC_TEST");
    assert!(!home::M0B_RUNTIME_USABLE);
    assert_eq!(
        home::module_ids(),
        [
            "agents-os.m0b.home.session-boundary.v0.1",
            "agents-os.m0b.home.candidate.v0.1",
            "agents-os.m0b.home.handoff.v0.1",
        ]
    );
    assert_eq!(
        home::session_boundary::IMPLEMENTATION_STATUS,
        "WP1_NONPROMOTION_ACTIVE"
    );
    assert_eq!(
        home::candidate::IMPLEMENTATION_STATUS,
        "WP2_CANDIDATE_REVISION_ACTIVE"
    );
    assert_eq!(home::handoff::IMPLEMENTATION_STATUS, "WP0_LAYOUT_ONLY");
    assert!(!home::session_boundary::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::candidate::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::handoff::COMMAND_COMMIT_AUTHORIZED);
}

fn candidate_proposal(
    candidate_id: &str,
    candidate_revision: u64,
    semantic_class: &str,
    predecessor: Option<&HomeCandidateRevision>,
    created_event_sequence: u64,
    payload_byte: char,
) -> Vec<u8> {
    canonicalize_json(
        &serde_json::to_vec(&json!({
            "candidate_id": candidate_id,
            "candidate_revision": candidate_revision,
            "created_event_sequence": created_event_sequence,
            "creator_assessment_fingerprint": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "creator_assessment_ref": "assessment:SYNTHETIC_TEST:creator:1",
            "payload_commitment": payload_byte.to_string().repeat(64),
            "predecessor_candidate_fingerprint": predecessor.map(|value| value.candidate_fingerprint.as_str()),
            "predecessor_candidate_ref": predecessor.map(|value| value.candidate_ref.as_str()),
            "predecessor_candidate_revision": predecessor.map(|value| value.candidate_revision),
            "semantic_class": semantic_class,
            "source_subject_fingerprint": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "source_subject_ref": "subject:SYNTHETIC_TEST:session:1",
            "source_subject_revision": 1,
        }))
        .unwrap(),
    )
    .unwrap()
}

fn derive_candidate(
    candidate_id: &str,
    candidate_revision: u64,
    semantic_class: &str,
    predecessor: Option<&HomeCandidateRevision>,
    created_event_sequence: u64,
    payload_byte: char,
    history: &[HomeCandidateRevision],
) -> HomeCandidateRevision {
    derive_candidate_revision(
        &candidate_proposal(
            candidate_id,
            candidate_revision,
            semantic_class,
            predecessor,
            created_event_sequence,
            payload_byte,
        ),
        history,
    )
    .unwrap()
    .candidate
}

#[test]
fn wp2_derives_three_candidate_classes_without_writes_or_authority() {
    let cases = [
        ("life-stream", "LIFE_STREAM_CANDIDATE", CandidateSemanticClass::LifeStream),
        ("memory", "MEMORY_CANDIDATE", CandidateSemanticClass::Memory),
        ("intent", "INTENT_CANDIDATE", CandidateSemanticClass::Intent),
    ];
    let mut history = Vec::new();
    for (index, (candidate_id, class, expected)) in cases.into_iter().enumerate() {
        let decision = derive_candidate_revision(
            &candidate_proposal(candidate_id, 1, class, None, index as u64 + 1, 'a'),
            &history,
        )
        .unwrap();
        assert_eq!(decision.result, CandidateRevisionResult::Derived);
        assert_eq!(decision.candidate.semantic_class, expected);
        assert_eq!(decision.canonical_write_count, 0);
        assert_eq!(decision.event_write_count, 0);
        assert!(!decision.action_authority);
        assert!(!decision.task_write_authority);
        assert!(!decision.command_authority);
        assert!(!decision.memory_write_authority);
        assert!(!decision.effect_authority);
        assert!(!decision.runtime_usable);
        history.push(decision.candidate);
    }
}

#[test]
fn wp2_exact_predecessor_and_exact_replay_are_deterministic() {
    let first = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    let second_bytes = candidate_proposal(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&first),
        11,
        'b',
    );
    let second = derive_candidate_revision(&second_bytes, std::slice::from_ref(&first))
        .unwrap()
        .candidate;
    assert_eq!(second.predecessor.as_ref().unwrap().candidate_revision, 1);
    assert_eq!(
        second.predecessor.as_ref().unwrap().candidate_fingerprint,
        first.candidate_fingerprint
    );

    let replay = derive_candidate_revision(&second_bytes, &[first, second.clone()]).unwrap();
    assert_eq!(replay.result, CandidateRevisionResult::ExactReplay);
    assert_eq!(replay.candidate, second);
    assert_eq!(replay.canonical_write_count, 0);
}

#[test]
fn wp2_rejects_same_revision_rewrite_gap_cross_identity_and_stale_head() {
    let intent1 = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    let memory1 = derive_candidate(
        "memory",
        1,
        "MEMORY_CANDIDATE",
        None,
        11,
        'b',
        std::slice::from_ref(&intent1),
    );
    let history = vec![intent1.clone(), memory1.clone()];

    let rewrite = candidate_proposal(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        10,
        'f',
    );
    assert_eq!(
        derive_candidate_revision(&rewrite, &history).unwrap_err(),
        CandidateError::SameRevisionRewrite
    );

    let gap = candidate_proposal(
        "intent",
        3,
        "INTENT_CANDIDATE",
        Some(&intent1),
        12,
        'c',
    );
    assert!(matches!(
        derive_candidate_revision(&gap, &history),
        Err(CandidateError::InvalidSchema(_))
    ));

    let cross_identity = candidate_proposal(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&memory1),
        12,
        'c',
    );
    assert_eq!(
        derive_candidate_revision(&cross_identity, &history).unwrap_err(),
        CandidateError::StaleOrMissingHead
    );
}

#[test]
fn wp2_rejects_mutated_or_duplicate_immutable_history() {
    let first = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    let mut changed = first.clone();
    changed.payload_commitment = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff".to_owned();
    let proposal = candidate_proposal(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&first),
        11,
        'b',
    );
    assert!(matches!(
        derive_candidate_revision(&proposal, &[changed]),
        Err(CandidateError::InvalidHistory(_))
    ));
    assert!(matches!(
        derive_candidate_revision(&proposal, &[first.clone(), first]),
        Err(CandidateError::InvalidHistory(_))
    ));
}

#[test]
fn wp2_candidate_schema_and_privacy_inputs_fail_closed() {
    let valid = candidate_proposal(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        10,
        'a',
    );
    let raw = mutate(valid.clone(), |object| {
        object.insert("raw_content".to_owned(), json!("must-not-be-consumed"));
    });
    let unknown_class = mutate(valid.clone(), |object| {
        object.insert("semantic_class".to_owned(), json!("TASK_CANONICAL_FACT"));
    });
    let production_ref = mutate(valid.clone(), |object| {
        object.insert("source_subject_ref".to_owned(), json!("subject:PRODUCTION:1"));
    });
    let boolean_revision = mutate(valid.clone(), |object| {
        object.insert("candidate_revision".to_owned(), json!(true));
    });
    let mixed_predecessor = mutate(valid.clone(), |object| {
        object.insert("predecessor_candidate_revision".to_owned(), json!(1));
    });
    let mut noncanonical = valid;
    noncanonical.push(b'\n');

    assert!(derive_candidate_revision(&raw, &[]).is_err());
    assert!(derive_candidate_revision(&unknown_class, &[]).is_err());
    assert!(derive_candidate_revision(&production_ref, &[]).is_err());
    assert!(derive_candidate_revision(&boolean_revision, &[]).is_err());
    assert!(derive_candidate_revision(&mixed_predecessor, &[]).is_err());
    assert_eq!(
        derive_candidate_revision(&noncanonical, &[]).unwrap_err(),
        CandidateError::NonCanonicalBytes
    );
}

fn observation(choice: &str) -> Vec<u8> {
    canonicalize_json(
        &serde_json::to_vec(&json!({
            "creator_assessment_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "creator_assessment_ref": "assessment:SYNTHETIC_TEST:creator:1",
            "explicit_branch_choice": choice,
            "observation_id": "observation:SYNTHETIC_TEST:1",
            "observation_revision": 1,
            "payload_commitment": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "session_ref": "session:SYNTHETIC_TEST:1",
            "session_revision": 1,
            "source_subject_fingerprint": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "source_subject_ref": "subject:SYNTHETIC_TEST:1",
            "source_subject_revision": 1,
            "trusted_event_sequence": 1
        }))
        .unwrap(),
    )
    .unwrap()
}

#[test]
fn wp1_three_explicit_nonpromotion_paths_are_deterministic_and_zero_write() {
    let paths = [
        ("EPHEMERAL_ONLY", SessionBranchChoice::EphemeralOnly),
        ("DISCARD", SessionBranchChoice::Discard),
        ("REMAIN_IN_SESSION", SessionBranchChoice::RemainInSession),
    ];
    for (choice, expected) in paths {
        let bytes = observation(choice);
        let first = reduce_nonpromotion(&bytes).unwrap();
        let second = reduce_nonpromotion(&bytes).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.result, "NO_PROMOTION");
        assert_eq!(first.reason, choice);
        assert_eq!(first.explicit_branch_choice, Some(expected));
        assert_eq!(first.canonical_writes.total(), 0);
        assert!(!first.candidate_authority);
        assert!(!first.task_write_authority);
        assert!(!first.command_authority);
        assert!(!first.effect_authority);
        assert!(!first.runtime_usable);
    }
}

fn mutate(
    mut bytes: Vec<u8>,
    mutation: impl FnOnce(&mut serde_json::Map<String, Value>),
) -> Vec<u8> {
    let mut value: Value = serde_json::from_slice(&bytes).unwrap();
    mutation(value.as_object_mut().unwrap());
    bytes = canonicalize_json(&serde_json::to_vec(&value).unwrap()).unwrap();
    bytes
}

#[test]
fn wp1_missing_and_unknown_choices_are_indeterminate_and_candidate_waits_for_wp2() {
    let missing = mutate(observation("DISCARD"), |object| {
        object.remove("explicit_branch_choice");
    });
    let unknown = mutate(observation("DISCARD"), |object| {
        object.insert("explicit_branch_choice".to_owned(), json!("UNKNOWN"));
    });
    let candidate = mutate(observation("DISCARD"), |object| {
        object.insert(
            "explicit_branch_choice".to_owned(),
            json!("PROPOSE_LIFE_STREAM_CANDIDATE"),
        );
    });
    for (bytes, reason) in [(missing, "MISSING_BRANCH"), (unknown, "UNKNOWN_BRANCH")] {
        let decision = reduce_nonpromotion(&bytes).unwrap();
        assert_eq!(decision.result, "INDETERMINATE");
        assert_eq!(decision.reason, reason);
        assert_eq!(decision.explicit_branch_choice, None);
        assert_eq!(decision.canonical_writes.total(), 0);
    }
    assert_eq!(
        decode_synthetic_observation(&candidate)
            .unwrap()
            .explicit_branch_choice,
        SessionBranchChoice::ProposeLifeStreamCandidate
    );
    assert_eq!(
        reduce_nonpromotion(&candidate).unwrap_err(),
        SessionBoundaryError::CandidateBranchNotImplemented
    );

    let malformed_missing = mutate(observation("DISCARD"), |object| {
        object.remove("explicit_branch_choice");
        object.insert("session_ref".to_owned(), json!("session:PRODUCTION:1"));
    });
    assert!(matches!(
        reduce_nonpromotion(&malformed_missing),
        Err(SessionBoundaryError::InvalidSchema(_))
    ));
}

#[test]
fn wp1_raw_content_and_authority_shaped_fields_fail_closed() {
    for forbidden in [
        "raw_content",
        "conversation_text",
        "thought_text",
        "private_memory",
        "provider_response",
        "credential",
        "token",
        "cookie",
        "secret",
        "filesystem_path",
        "task_write_authority",
    ] {
        let bytes = mutate(observation("EPHEMERAL_ONLY"), |object| {
            object.insert(forbidden.to_owned(), json!("must-not-be-consumed"));
        });
        assert!(reduce_nonpromotion(&bytes).is_err(), "accepted {forbidden}");
    }
}

#[test]
fn wp1_strict_json_and_schema_totality_fail_closed_without_echoing_payloads() {
    let duplicate = br#"{"creator_assessment_fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","creator_assessment_ref":"assessment:SYNTHETIC_TEST:creator:1","explicit_branch_choice":"DISCARD","observation_id":"observation:SYNTHETIC_TEST:1","observation_id":"raw private words","observation_revision":1,"payload_commitment":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","session_ref":"session:SYNTHETIC_TEST:1","session_revision":1,"source_subject_fingerprint":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","source_subject_ref":"subject:SYNTHETIC_TEST:1","source_subject_revision":1,"trusted_event_sequence":1}"#;
    assert_eq!(
        reduce_nonpromotion(duplicate).unwrap_err(),
        SessionBoundaryError::MalformedCanonicalJson
    );
    assert!(!reduce_nonpromotion(duplicate).unwrap_err().to_string().contains("raw private words"));

    let mut noncanonical = observation("DISCARD");
    noncanonical.push(b'\n');
    assert_eq!(
        reduce_nonpromotion(&noncanonical).unwrap_err(),
        SessionBoundaryError::NonCanonicalBytes
    );

    let canonical = String::from_utf8(observation("DISCARD")).unwrap();
    let float = canonical
        .replace("\"trusted_event_sequence\":1", "\"trusted_event_sequence\":1.0")
        .into_bytes();
    let boolean = mutate(observation("DISCARD"), |object| {
        object.insert("trusted_event_sequence".to_owned(), json!(true));
    });
    let unsafe_integer = canonical
        .replace(
            "\"trusted_event_sequence\":1",
            "\"trusted_event_sequence\":9007199254740992",
        )
        .into_bytes();
    let production_ref = mutate(observation("DISCARD"), |object| {
        object.insert("session_ref".to_owned(), json!("session:PRODUCTION:1"));
    });
    let uppercase_hash = mutate(observation("DISCARD"), |object| {
        object.insert(
            "payload_commitment".to_owned(),
            json!("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"),
        );
    });
    let zero_revision = mutate(observation("DISCARD"), |object| {
        object.insert("observation_revision".to_owned(), json!(0));
    });
    assert!(reduce_nonpromotion(&float).is_err());
    assert!(reduce_nonpromotion(&boolean).is_err());
    assert!(reduce_nonpromotion(&unsafe_integer).is_err());
    assert!(reduce_nonpromotion(&production_ref).is_err());
    assert!(reduce_nonpromotion(&uppercase_hash).is_err());
    assert!(reduce_nonpromotion(&zero_revision).is_err());
}

#[test]
fn wp0_declares_but_does_not_activate_schema_v2() {
    assert_eq!(schema::SCHEMA_VERSION, 1);
    assert_eq!(schema::M0B_SCHEMA_V2_TARGET_VERSION, 2);
    assert_eq!(schema::M0B_SCHEMA_V2_MIGRATION_STATUS, "WP0_DECLARED_NOT_ACTIVE");
    assert_eq!(
        schema::M0B_SCHEMA_V2_NEW_TABLES,
        [
            "home_candidate_revision",
            "home_candidate_head",
            "home_handoff_link",
        ]
    );
    assert_eq!(schema::M0B_SCHEMA_V2_NEW_INDEXES.len(), 3);
    assert_eq!(schema::M0B_SCHEMA_V2_NEW_TRIGGERS.len(), 4);
    assert_eq!(schema::m0b_schema_v2_migration_sql(), None);
}

#[test]
fn wp0_preserves_the_five_method_napi_surface() {
    let source = include_str!("../src/lib.rs");
    let exports = [
        "execute_command",
        "execute_query",
        "claim_outbox",
        "acknowledge_outbox",
        "reconcile",
    ];
    for export in exports {
        let marker = format!("#[napi(js_name = \"{export}\")]");
        assert_eq!(
            source.matches(&marker).count(),
            1,
            "missing or duplicate {export}"
        );
    }
    assert_eq!(source.matches("#[napi(js_name = ").count(), exports.len());
}
