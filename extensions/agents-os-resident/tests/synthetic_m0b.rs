use agents_os_resident::{home, ledger::schema};
use agents_os_resident::canonical::jcs::canonicalize_json;
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
    assert_eq!(home::candidate::IMPLEMENTATION_STATUS, "WP0_LAYOUT_ONLY");
    assert_eq!(home::handoff::IMPLEMENTATION_STATUS, "WP0_LAYOUT_ONLY");
    assert!(!home::session_boundary::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::candidate::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::handoff::COMMAND_COMMIT_AUTHORIZED);
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
