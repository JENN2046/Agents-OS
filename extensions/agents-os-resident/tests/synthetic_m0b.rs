use agents_os_resident::{home, ledger::schema};
use agents_os_resident::canonical::jcs::canonicalize_json;
use agents_os_resident::ledger::recovery::M0BIntegratedWitness;
use agents_os_resident::ledger::replay::TerminalIntake;
use agents_os_resident::home::candidate::{
    CandidateError, CandidateRevisionResult, CandidateSemanticClass, ExplicitPromotionChoice,
    HomeCandidateRevision, PromotionResult, derive_candidate_revision,
    reduce_explicit_promotion,
};
use agents_os_resident::home::session_boundary::{
    SessionBoundaryError, SessionBranchChoice, decode_synthetic_observation, reduce_nonpromotion,
};
use agents_os_resident::home::handoff::{
    HandoffError, HandoffResult, HomeIntentHandoffCandidate, compose_f8_handoff,
    owner_commitment_set_fingerprint, synthetic_f3_home_intent_submission,
    trusted_owner_commitments,
};
use agents_os_resident::ledger::transaction::{
    HomeCommitFault, HomeCommitObservation, HomeHeadExpectation,
};
use agents_os_resident::napi_frame::{
    CommandBoundary, Disposition, MethodId, parse_request, request_bytes,
};
use agents_os_resident::reducers::command_intake::{
    HOME_INTENT_COMMAND_TYPE_ID, SyntheticHomeIntentPayload, home_intent_submission_value,
    validate_submission,
};
use agents_os_resident::resident::{
    ResidentError, ResidentKernel, ResidentKernelConfig, SYNTHETIC_DATABASE_FILENAME,
    SyntheticOwnership,
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
        "WP3_EXPLICIT_PROMOTION_ACTIVE"
    );
    assert_eq!(
        home::handoff::IMPLEMENTATION_STATUS,
        "WP4_F8_HANDOFF_COMPOSITION_ACTIVE"
    );
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

fn resign_materialized_candidate(candidate: &mut HomeCandidateRevision) {
    let predecessor = candidate.predecessor.as_ref();
    candidate.canonical_bytes = canonicalize_json(
        &serde_json::to_vec(&json!([
            "agents-os.m0b.home-candidate.v0.1",
            {
                "candidate_id": candidate.candidate_id.as_str(),
                "candidate_ref": candidate.candidate_ref.as_str(),
                "candidate_revision": candidate.candidate_revision,
                "created_event_sequence": candidate.created_event_sequence,
                "creator_assessment_fingerprint": candidate.creator_assessment_fingerprint.as_str(),
                "creator_assessment_ref": candidate.creator_assessment_ref.as_str(),
                "payload_commitment": candidate.payload_commitment.as_str(),
                "predecessor_candidate_fingerprint": predecessor.map(|value| value.candidate_fingerprint.as_str()),
                "predecessor_candidate_ref": predecessor.map(|value| value.candidate_ref.as_str()),
                "predecessor_candidate_revision": predecessor.map(|value| value.candidate_revision),
                "semantic_class": candidate.semantic_class.as_str(),
                "source_subject_fingerprint": candidate.source_subject_fingerprint.as_str(),
                "source_subject_ref": candidate.source_subject_ref.as_str(),
                "source_subject_revision": candidate.source_subject_revision
            }
        ]))
        .unwrap(),
    )
    .unwrap();
    candidate.candidate_fingerprint =
        agents_os_resident::canonical::fingerprint::sha256_hex(&candidate.canonical_bytes);
}

fn promotion_request(
    source: &HomeCandidateRevision,
    choice: Option<&str>,
    target_id: Option<&str>,
    target_event_sequence: Option<u64>,
    minimum_trusted_event_sequence: u64,
) -> Vec<u8> {
    let mut value = json!({
        "explicit_promotion_choice": choice,
        "minimum_trusted_event_sequence": minimum_trusted_event_sequence,
        "promotion_id": "promotion:SYNTHETIC_TEST:1",
        "promotion_revision": 1,
        "source_candidate_fingerprint": source.candidate_fingerprint,
        "source_candidate_ref": source.candidate_ref,
        "source_candidate_revision": source.candidate_revision,
        "target_candidate_id": target_id,
        "target_created_event_sequence": target_event_sequence
    });
    if choice.is_none() {
        value
            .as_object_mut()
            .unwrap()
            .remove("explicit_promotion_choice");
    }
    canonicalize_json(&serde_json::to_vec(&value).unwrap()).unwrap()
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
    let namespace_smuggle = mutate(valid.clone(), |object| {
        object.insert(
            "source_subject_ref".to_owned(),
            json!("subject:PRODUCTION:case:SYNTHETIC_TEST:leak"),
        );
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
    assert!(derive_candidate_revision(&namespace_smuggle, &[]).is_err());
    assert!(derive_candidate_revision(&boolean_revision, &[]).is_err());
    assert!(derive_candidate_revision(&mixed_predecessor, &[]).is_err());
    assert_eq!(
        derive_candidate_revision(&noncanonical, &[]).unwrap_err(),
        CandidateError::NonCanonicalBytes
    );
}

#[test]
fn wp3_observe_and_discard_are_explicit_zero_write_terminal_choices() {
    let life = derive_candidate(
        "life",
        1,
        "LIFE_STREAM_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    for (choice, expected_choice, expected_result) in [
        (
            "OBSERVE_WITHOUT_PROMOTION",
            ExplicitPromotionChoice::ObserveWithoutPromotion,
            PromotionResult::ObservedNoFurtherPromotion,
        ),
        (
            "DISCARD",
            ExplicitPromotionChoice::Discard,
            PromotionResult::DiscardedNoFurtherPromotion,
        ),
    ] {
        let request = promotion_request(&life, Some(choice), None, None, 10);
        let first = reduce_explicit_promotion(&request, std::slice::from_ref(&life)).unwrap();
        let second = reduce_explicit_promotion(&request, std::slice::from_ref(&life)).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.result, expected_result);
        assert_eq!(first.explicit_choice, Some(expected_choice));
        assert_eq!(first.canonical_write_count, 0);
        assert_eq!(first.event_write_count, 0);
        assert!(first.derived_candidate.is_none());
        assert!(!first.action_authority);
        assert!(!first.task_write_authority);
        assert!(!first.command_authority);
        assert!(!first.memory_write_authority);
        assert!(!first.effect_authority);
        assert!(!first.runtime_usable);
    }
}

#[test]
fn wp3_memory_and_intent_choices_derive_candidate_only_results() {
    let life = derive_candidate(
        "life",
        1,
        "LIFE_STREAM_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    for (choice, target_id, expected_class, expected_result) in [
        (
            "PROPOSE_MEMORY_CANDIDATE",
            "memory-from-life",
            CandidateSemanticClass::Memory,
            PromotionResult::MemoryCandidateOnly,
        ),
        (
            "PROPOSE_INTENT_CANDIDATE",
            "intent-from-life",
            CandidateSemanticClass::Intent,
            PromotionResult::IntentCandidateOnly,
        ),
    ] {
        let request = promotion_request(&life, Some(choice), Some(target_id), Some(11), 10);
        let decision = reduce_explicit_promotion(&request, std::slice::from_ref(&life)).unwrap();
        let candidate = decision.derived_candidate.unwrap();
        assert_eq!(decision.result, expected_result);
        assert_eq!(candidate.semantic_class, expected_class);
        assert_eq!(candidate.candidate_revision, 1);
        assert_eq!(candidate.source_subject_ref, life.candidate_ref);
        assert_eq!(candidate.source_subject_fingerprint, life.candidate_fingerprint);
        assert_eq!(candidate.payload_commitment, life.payload_commitment);
        assert_eq!(decision.canonical_write_count, 0);
        assert!(!decision.memory_write_authority);
        assert!(!decision.command_authority);
        assert!(!decision.task_write_authority);
    }
}

#[test]
fn wp3_missing_unknown_or_implicit_choices_fail_closed() {
    let life = derive_candidate(
        "life",
        1,
        "LIFE_STREAM_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    for request in [
        promotion_request(&life, None, None, None, 10),
        promotion_request(&life, Some("UNKNOWN"), None, None, 10),
    ] {
        let decision = reduce_explicit_promotion(&request, std::slice::from_ref(&life)).unwrap();
        assert_eq!(decision.result, PromotionResult::Indeterminate);
        assert_eq!(decision.canonical_write_count, 0);
        assert!(decision.derived_candidate.is_none());
    }

    let implicit_target = promotion_request(
        &life,
        Some("OBSERVE_WITHOUT_PROMOTION"),
        Some("implicit"),
        Some(11),
        10,
    );
    assert!(reduce_explicit_promotion(&implicit_target, std::slice::from_ref(&life)).is_err());

    let missing_target = promotion_request(
        &life,
        Some("PROPOSE_MEMORY_CANDIDATE"),
        None,
        None,
        10,
    );
    assert!(reduce_explicit_promotion(&missing_target, std::slice::from_ref(&life)).is_err());
}

#[test]
fn wp3_rejects_non_life_stale_or_untrusted_sources() {
    let life1 = derive_candidate(
        "life",
        1,
        "LIFE_STREAM_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    let life2 = derive_candidate(
        "life",
        2,
        "LIFE_STREAM_CANDIDATE",
        Some(&life1),
        11,
        'b',
        std::slice::from_ref(&life1),
    );
    let memory = derive_candidate(
        "memory",
        1,
        "MEMORY_CANDIDATE",
        None,
        12,
        'c',
        &[life1.clone(), life2.clone()],
    );
    let history = vec![life1.clone(), life2.clone(), memory.clone()];

    for request in [
        promotion_request(
            &life1,
            Some("PROPOSE_INTENT_CANDIDATE"),
            Some("intent"),
            Some(13),
            10,
        ),
        promotion_request(
            &memory,
            Some("PROPOSE_INTENT_CANDIDATE"),
            Some("intent"),
            Some(13),
            10,
        ),
        promotion_request(
            &life2,
            Some("PROPOSE_INTENT_CANDIDATE"),
            Some("intent"),
            Some(13),
            12,
        ),
    ] {
        assert_eq!(
            reduce_explicit_promotion(&request, &history).unwrap_err(),
            CandidateError::InvalidPromotionSource
        );
    }
}

#[test]
fn wp3_schema_privacy_and_authority_shaped_fields_fail_closed() {
    let life = derive_candidate(
        "life",
        1,
        "LIFE_STREAM_CANDIDATE",
        None,
        10,
        'a',
        &[],
    );
    let valid = promotion_request(
        &life,
        Some("PROPOSE_INTENT_CANDIDATE"),
        Some("intent"),
        Some(11),
        10,
    );
    for forbidden in [
        "raw_content",
        "private_memory",
        "formal_memory_write",
        "task_write_authority",
        "command_authority",
        "relationship_authority",
        "pbl_no_match_permission",
    ] {
        let request = mutate(valid.clone(), |object| {
            object.insert(forbidden.to_owned(), json!(true));
        });
        assert!(reduce_explicit_promotion(&request, std::slice::from_ref(&life)).is_err());
    }

    let mixed_target = mutate(valid.clone(), |object| {
        object.insert("target_created_event_sequence".to_owned(), Value::Null);
    });
    let production = mutate(valid.clone(), |object| {
        object.insert(
            "source_candidate_ref".to_owned(),
            json!("candidate:PRODUCTION:life:1"),
        );
    });
    let mut noncanonical = valid;
    noncanonical.push(b'\n');
    assert!(reduce_explicit_promotion(&mixed_target, std::slice::from_ref(&life)).is_err());
    assert!(reduce_explicit_promotion(&production, std::slice::from_ref(&life)).is_err());
    assert_eq!(
        reduce_explicit_promotion(&noncanonical, std::slice::from_ref(&life)).unwrap_err(),
        CandidateError::NonCanonicalBytes
    );
}

fn handoff_request(
    intent: &HomeCandidateRevision,
    history: &[HomeCandidateRevision],
    choice: Option<&str>,
    minimum_sequence: u64,
) -> Vec<u8> {
    let owner_source = trusted_owner_commitments();
    let mut value = json!({
        "canonical_candidate_history_fingerprint": agents_os_resident::home::candidate::canonical_candidate_history_fingerprint(history).unwrap(),
        "explicit_handoff_choice": choice,
        "handoff_candidate_id": "home-intent",
        "handoff_candidate_revision": 1,
        "intent_candidate_fingerprint": intent.candidate_fingerprint,
        "intent_candidate_ref": intent.candidate_ref,
        "intent_candidate_revision": intent.candidate_revision,
        "minimum_trusted_event_sequence": minimum_sequence,
        "owner_commitment_set_fingerprint": owner_commitment_set_fingerprint(&owner_source).unwrap()
    });
    if choice.is_none() {
        value.as_object_mut().unwrap().remove("explicit_handoff_choice");
    }
    canonicalize_json(&serde_json::to_vec(&value).unwrap()).unwrap()
}

fn formed_handoff() -> agents_os_resident::home::handoff::HomeIntentHandoffCandidate {
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let history = vec![intent.clone()];
    let owner_source = trusted_owner_commitments();
    compose_f8_handoff(
        &handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100),
        &history,
        &owner_source,
        &[],
    )
    .unwrap()
    .candidate
    .unwrap()
}

fn v2_kernel_with_formed_handoff(
    root: &std::path::Path,
    suffix: &str,
) -> (ResidentKernel, HomeIntentHandoffCandidate) {
    let ownership = SyntheticOwnership::genesis(
        &format!("incarnation:SYNTHETIC_TEST:{suffix}"),
        suffix.as_bytes(),
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).unwrap();
    let schema = kernel.migrate_synthetic_ledger_v2().unwrap();
    assert_eq!(schema.version, 2);
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    assert_eq!(
        kernel
            .commit_home_candidate(
                intent.clone(),
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );
    let history = vec![intent.clone()];
    let handoff = compose_f8_handoff(
        &handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100),
        &history,
        &trusted_owner_commitments(),
        &[],
    )
    .unwrap()
    .candidate
    .unwrap();
    assert_eq!(
        kernel
            .commit_home_handoff(
                handoff.clone(),
                "intent",
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );
    (kernel, handoff)
}

#[test]
fn wp4_forms_only_an_exact_nonauthoritative_handoff_candidate() {
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let history = vec![intent.clone()];
    let owner_source = trusted_owner_commitments();
    let request = handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100);
    let first = compose_f8_handoff(&request, &history, &owner_source, &[]).unwrap();
    let second = compose_f8_handoff(&request, &history, &owner_source, &[]).unwrap();
    assert_eq!(first, second);
    assert_eq!(first.result, HandoffResult::CandidateFormed);
    assert_eq!(first.reason, "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE");
    assert_eq!(first.canonical_write_count, 0);
    assert_eq!(first.event_write_count, 0);
    assert!(first.f3_recheck_required);
    assert!(!first.command_authority);
    assert!(!first.task_write_authority);
    assert!(!first.effect_authority);
    assert!(!first.runtime_usable);
    let candidate = first.candidate.unwrap();
    assert_eq!(candidate.intent_candidate_ref, intent.candidate_ref);
    assert!(!candidate.command_authority);
    assert!(!candidate.runtime_usable);
}

#[test]
fn wp4_exact_replay_succeeds_and_same_revision_rewrite_rejects() {
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let history = vec![intent.clone()];
    let owner_source = trusted_owner_commitments();
    let request = handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100);
    let candidate = compose_f8_handoff(&request, &history, &owner_source, &[])
        .unwrap()
        .candidate
        .unwrap();
    let replay = compose_f8_handoff(
        &request,
        &history,
        &owner_source,
        std::slice::from_ref(&candidate),
    )
    .unwrap();
    assert_eq!(replay.result, HandoffResult::ExactReplay);

    let mut mutated_history = candidate.clone();
    mutated_history.minimum_trusted_event_sequence = 99;
    assert_eq!(
        compose_f8_handoff(
            &request,
            &history,
            &owner_source,
            std::slice::from_ref(&mutated_history),
        )
        .unwrap_err(),
        HandoffError::InvalidHandoffHistory
    );

    let rewrite = handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 99);
    assert_eq!(
        compose_f8_handoff(
            &rewrite,
            &history,
            &owner_source,
            std::slice::from_ref(&candidate),
        )
        .unwrap_err(),
        HandoffError::SameRevisionRewrite
    );
}

#[test]
fn wp4_missing_unknown_and_direct_write_shapes_fail_closed() {
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let history = vec![intent.clone()];
    let owner_source = trusted_owner_commitments();
    for request in [
        handoff_request(&intent, &history, None, 100),
        handoff_request(&intent, &history, Some("UNKNOWN"), 100),
    ] {
        let decision = compose_f8_handoff(&request, &history, &owner_source, &[]).unwrap();
        assert_eq!(decision.result, HandoffResult::Indeterminate);
        assert!(decision.candidate.is_none());
    }

    let valid = handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100);
    for forbidden in [
        "raw_content",
        "task_write",
        "command_commit",
        "effect_authority",
        "pbl_no_match_permission",
        "relationship_authority",
    ] {
        let request = mutate(valid.clone(), |object| {
            object.insert(forbidden.to_owned(), json!(true));
        });
        assert!(compose_f8_handoff(&request, &history, &owner_source, &[]).is_err());
    }
}

#[test]
fn wp4_rejects_owner_rewrite_phantom_history_stale_intent_and_watermark() {
    let intent1 = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let intent2 = derive_candidate(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&intent1),
        101,
        'b',
        std::slice::from_ref(&intent1),
    );
    let history = vec![intent1.clone(), intent2.clone()];
    let owner_source = trusted_owner_commitments();

    let stale = handoff_request(&intent1, &history, Some("PROPOSE_F8_HANDOFF"), 100);
    assert_eq!(
        compose_f8_handoff(&stale, &history, &owner_source, &[]).unwrap_err(),
        HandoffError::IntentCandidateMismatch
    );

    let valid = handoff_request(&intent2, &history, Some("PROPOSE_F8_HANDOFF"), 100);
    let mut rewritten_owner = owner_source.clone();
    rewritten_owner[0].commitment_revision = 2;
    assert_eq!(
        compose_f8_handoff(&valid, &history, &rewritten_owner, &[]).unwrap_err(),
        HandoffError::OwnerCommitmentMismatch
    );

    let phantom = mutate(valid.clone(), |object| {
        object.insert(
            "intent_candidate_ref".to_owned(),
            json!("candidate:SYNTHETIC_TEST:phantom:1"),
        );
    });
    assert!(compose_f8_handoff(&phantom, &history, &owner_source, &[]).is_err());

    let above_owner_watermark = handoff_request(
        &intent2,
        &history,
        Some("PROPOSE_F8_HANDOFF"),
        101,
    );
    assert_eq!(
        compose_f8_handoff(&above_owner_watermark, &history, &owner_source, &[]).unwrap_err(),
        HandoffError::OwnerCommitmentMismatch
    );
}

#[test]
fn wp5_adapts_the_exact_handoff_into_the_existing_execute_command_frame() {
    let candidate = formed_handoff();
    let submission = synthetic_f3_home_intent_submission(&candidate).unwrap();
    assert!(submission.command_id.starts_with("command:SYNTHETIC_TEST:home-intent:"));
    assert_eq!(submission.command_id.len(), "command:SYNTHETIC_TEST:home-intent:".len() + 64);
    assert_eq!(submission.request_fingerprint, agents_os_resident::canonical::fingerprint::sha256_hex(&submission.request_bytes));
    assert!(!submission.runtime_usable);

    let frame = parse_request(&submission.request_bytes, MethodId::ExecuteCommand).unwrap();
    assert_eq!(frame.request_id, submission.command_id);
    let validated = validate_submission(&frame.payload).unwrap();
    assert_eq!(validated.command_type_id, HOME_INTENT_COMMAND_TYPE_ID);
    assert_eq!(validated.command_id, submission.command_id);
    assert_eq!(validated.canonical_command_fingerprint, submission.command_fingerprint);
}

#[test]
fn wp5_f3_alone_commits_and_exactly_replays_the_home_intent_command() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) = v2_kernel_with_formed_handoff(root.path(), "m0b-wp5");
    let boundary = CommandBoundary::synthetic(&kernel);
    let submission = synthetic_f3_home_intent_submission(&handoff).unwrap();

    let before = kernel.ledger_counts().unwrap();
    let first = boundary
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(first.disposition, Disposition::Committed);
    assert_eq!(
        first.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "HOME_INTENT_COMMAND_COMMITTED_SYNTHETIC"
    );
    let after = kernel.ledger_counts().unwrap();
    assert_eq!(after.inbox_commands, before.inbox_commands + 1);
    assert_eq!(after.replay_rows, before.replay_rows + 1);
    assert_eq!(after.events, before.events + 1);
    assert_eq!(after.facts, before.facts);
    assert_eq!(after.pointers, before.pointers);
    assert_eq!(after.outbox_intents, before.outbox_intents);

    let replay = boundary
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(replay.canonical_bytes, first.canonical_bytes);
    assert_eq!(kernel.ledger_counts().unwrap(), after);
    kernel.shutdown().unwrap();
}

#[test]
fn wp5_exact_replay_survives_a_later_intent_head_advance() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) = v2_kernel_with_formed_handoff(root.path(), "m0b-wp5-replay-head");
    let submission = synthetic_f3_home_intent_submission(&handoff).unwrap();
    let first = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(first.disposition, Disposition::Committed);

    let intent1 = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let intent2 = derive_candidate(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&intent1),
        103,
        'b',
        std::slice::from_ref(&intent1),
    );
    assert_eq!(
        kernel
            .commit_home_candidate(
                intent2,
                HomeHeadExpectation::Exact {
                    revision: 1,
                    fingerprint: intent1.candidate_fingerprint,
                },
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );
    let before_replay = kernel.ledger_counts().unwrap();
    let replay = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(replay.canonical_bytes, first.canonical_bytes);
    assert_eq!(kernel.ledger_counts().unwrap(), before_replay);
    kernel.shutdown().unwrap();
}

#[test]
fn wp6_candidate_and_handoff_replay_survive_a_later_intent_head_advance() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) =
        v2_kernel_with_formed_handoff(root.path(), "m0b-wp6-delayed-replay");
    let intent1 = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    let intent2 = derive_candidate(
        "intent",
        2,
        "INTENT_CANDIDATE",
        Some(&intent1),
        103,
        'b',
        std::slice::from_ref(&intent1),
    );
    assert_eq!(
        kernel
            .commit_home_candidate(
                intent2,
                HomeHeadExpectation::Exact {
                    revision: 1,
                    fingerprint: intent1.candidate_fingerprint.clone(),
                },
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );

    let before_replays = kernel.ledger_counts().unwrap();
    assert_eq!(
        kernel
            .commit_home_candidate(
                intent1,
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    assert_eq!(
        kernel
            .commit_home_handoff(handoff.clone(), "intent", HomeCommitFault::None)
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    assert_eq!(kernel.ledger_counts().unwrap(), before_replays);
    assert!(
        kernel
            .commit_home_handoff(handoff, "other-intent", HomeCommitFault::None)
            .is_err()
    );
    assert_eq!(kernel.ledger_counts().unwrap(), before_replays);
    kernel.shutdown().unwrap();
}

#[test]
fn wp5_f3_treats_the_handoff_event_watermark_as_a_lower_bound() {
    let root = tempfile::tempdir().unwrap();
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp5-lower-bound",
        b"m0b-wp5-lower-bound-nonce",
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root.path(), ownership))
        .unwrap();
    kernel.migrate_synthetic_ledger_v2().unwrap();
    let intent = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        101,
        'a',
        &[],
    );
    kernel
        .commit_home_candidate(
            intent.clone(),
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .unwrap();
    let history = vec![intent.clone()];
    let handoff = compose_f8_handoff(
        &handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100),
        &history,
        &trusted_owner_commitments(),
        &[],
    )
    .unwrap()
    .candidate
    .unwrap();
    kernel
        .commit_home_handoff(handoff.clone(), "intent", HomeCommitFault::None)
        .unwrap();
    let submission = synthetic_f3_home_intent_submission(&handoff).unwrap();
    let response = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(response.disposition, Disposition::Committed);
    kernel.shutdown().unwrap();
}

#[test]
fn wp6_rejects_fully_resigned_nonsynthetic_candidate_refs_before_persistence() {
    let root = tempfile::tempdir().unwrap();
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp6-ref-boundary",
        b"m0b-wp6-ref-boundary-nonce",
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root.path(), ownership))
        .unwrap();
    kernel.migrate_synthetic_ledger_v2().unwrap();
    let baseline = kernel.ledger_counts().unwrap();
    let valid = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );

    let mut forged_source = valid.clone();
    forged_source.source_subject_ref = "subject:PRODUCTION:session:1".to_owned();
    resign_materialized_candidate(&mut forged_source);
    let source_error = kernel
        .commit_home_candidate(
            forged_source,
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .unwrap_err();
    assert!(
        source_error
            .to_string()
            .contains("Home candidate is not exact canonical F7 evidence"),
        "unexpected source rejection: {source_error}"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), baseline);

    let mut forged_creator = valid.clone();
    forged_creator.creator_assessment_ref = "assessment:PRODUCTION:creator:1".to_owned();
    resign_materialized_candidate(&mut forged_creator);
    let creator_error = kernel
        .commit_home_candidate(
            forged_creator,
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .unwrap_err();
    assert!(
        creator_error
            .to_string()
            .contains("Home candidate is not exact canonical F7 evidence"),
        "unexpected creator rejection: {creator_error}"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), baseline);

    let mut smuggled_source = valid.clone();
    smuggled_source.source_subject_ref =
        "subject:PRODUCTION:case:SYNTHETIC_TEST:leak".to_owned();
    resign_materialized_candidate(&mut smuggled_source);
    assert!(kernel
        .commit_home_candidate(
            smuggled_source,
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .is_err());
    assert_eq!(kernel.ledger_counts().unwrap(), baseline);

    let mut smuggled_creator = valid;
    smuggled_creator.creator_assessment_ref =
        "assessment:PRODUCTION:case:SYNTHETIC_TEST:leak".to_owned();
    resign_materialized_candidate(&mut smuggled_creator);
    assert!(kernel
        .commit_home_candidate(
            smuggled_creator,
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .is_err());
    assert_eq!(kernel.ledger_counts().unwrap(), baseline);
    kernel.shutdown().unwrap();

    let connection = rusqlite::Connection::open(root.path().join(SYNTHETIC_DATABASE_FILENAME))
        .unwrap();
    let persisted_candidates: i64 = connection
        .query_row("SELECT COUNT(*) FROM home_candidate_revision", [], |row| row.get(0))
        .unwrap();
    assert_eq!(persisted_candidates, 0);
}

#[test]
fn wp6_schema_v2_candidate_handoff_and_replay_are_atomic_and_low_disclosure() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) = v2_kernel_with_formed_handoff(root.path(), "m0b-wp6");
    let replay_candidate = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'a',
        &[],
    );
    assert_eq!(
        kernel
            .commit_home_candidate(
                replay_candidate,
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    assert_eq!(
        kernel
            .commit_home_handoff(
                handoff.clone(),
                "intent",
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    kernel.shutdown().unwrap();

    let database = root.path().join(SYNTHETIC_DATABASE_FILENAME);
    let connection = rusqlite::Connection::open_with_flags(
        &database,
        rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
    )
    .unwrap();
    let counts: (i64, i64, i64, i64) = connection
        .query_row(
            "SELECT (SELECT COUNT(*) FROM home_candidate_revision),(SELECT COUNT(*) FROM home_candidate_head),(SELECT COUNT(*) FROM home_handoff_link),(SELECT COUNT(*) FROM event)",
            [],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
        )
        .unwrap();
    assert_eq!(counts, (1, 1, 1, 3));
    let quick: String = connection
        .query_row("PRAGMA quick_check", [], |row| row.get(0))
        .unwrap();
    let foreign_keys: i64 = connection
        .query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| row.get(0))
        .unwrap();
    assert_eq!(quick, "ok");
    assert_eq!(foreign_keys, 0);
    let forbidden = [
        "raw_content",
        "conversation_text",
        "thought_text",
        "private_memory",
        "provider_response",
        "credential",
        "token",
        "cookie",
        "secret",
    ];
    let mut statement = connection
        .prepare(
            "SELECT CAST(canonical_bytes AS TEXT) FROM home_candidate_revision UNION ALL SELECT CAST(canonical_bytes AS TEXT) FROM home_handoff_link UNION ALL SELECT CAST(canonical_bytes AS TEXT) FROM event",
        )
        .unwrap();
    let rows: Vec<String> = statement
        .query_map([], |row| row.get(0))
        .unwrap()
        .collect::<Result<_, _>>()
        .unwrap();
    for row in rows {
        let lower = row.to_ascii_lowercase();
        for pattern in forbidden {
            assert!(!lower.contains(pattern), "stored forbidden pattern {pattern}");
        }
    }
    drop(statement);
    drop(connection);
    let writable = rusqlite::Connection::open(&database).unwrap();
    writable.pragma_update(None, "foreign_keys", "ON").unwrap();
    assert!(writable
        .execute(
            "UPDATE home_candidate_revision SET payload_commitment=?1 WHERE candidate_id='intent' AND candidate_revision=1",
            ["ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"],
        )
        .is_err_and(|error| error.to_string().contains("home_candidate_revision_immutable")));
    assert!(writable
        .execute(
            "DELETE FROM home_handoff_link WHERE handoff_id='home-intent' AND handoff_revision=1",
            [],
        )
        .is_err_and(|error| error.to_string().contains("home_handoff_link_immutable")));
}

#[test]
fn wp6_candidate_and_handoff_same_revision_rewrites_fail_without_partial_rows() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) = v2_kernel_with_formed_handoff(root.path(), "m0b-wp6-rewrite");
    let mut rewritten_candidate = derive_candidate(
        "intent",
        1,
        "INTENT_CANDIDATE",
        None,
        100,
        'b',
        &[],
    );
    assert!(matches!(
        kernel.commit_home_candidate(
            rewritten_candidate.clone(),
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("same Home candidate revision")
    ));
    rewritten_candidate.candidate_fingerprint = handoff.handoff_candidate_fingerprint.clone();
    assert!(kernel
        .commit_home_candidate(
            rewritten_candidate,
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .is_err());
    let mut rewritten_handoff = handoff.clone();
    rewritten_handoff.minimum_trusted_event_sequence = 99;
    assert!(kernel
        .commit_home_handoff(rewritten_handoff, "intent", HomeCommitFault::None)
        .is_err());
    kernel.shutdown().unwrap();
}

#[test]
fn wp5_invalid_or_inactive_home_intent_never_writes_a_command() {
    let submission = synthetic_f3_home_intent_submission(&formed_handoff()).unwrap();
    let inactive = CommandBoundary::inactive()
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(inactive.disposition, Disposition::ContractNotActive);

    let mut value: Value = serde_json::from_slice(&submission.request_bytes).unwrap();
    value["payload"]["canonical_command"]["command_payload"]["raw_content"] =
        json!("forbidden");
    let invalid = canonicalize_json(&serde_json::to_vec(&value).unwrap()).unwrap();
    let root = tempfile::tempdir().unwrap();
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp5-reject",
        b"m0b-wp5-reject-nonce",
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root.path(), ownership))
        .unwrap();
    kernel.initialize_ledger_v1().unwrap();
    let before = kernel.ledger_counts().unwrap();
    let rejected = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &invalid)
        .unwrap();
    assert_eq!(rejected.disposition, Disposition::Rejected);
    assert_eq!(
        rejected.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "INVALID_HOME_INTENT_COMMAND"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), before);
    kernel.shutdown().unwrap();
}

#[test]
fn wp5_schema_valid_home_intent_on_v1_is_low_disclosure_and_zero_write() {
    let submission = synthetic_f3_home_intent_submission(&formed_handoff()).unwrap();
    let root = tempfile::tempdir().unwrap();
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp5-v1-source-unavailable",
        b"m0b-wp5-v1-source-unavailable-nonce",
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root.path(), ownership))
        .unwrap();
    assert_eq!(kernel.initialize_ledger_v1().unwrap().version, 1);
    let before = kernel.ledger_counts().unwrap();
    let rejected = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(rejected.disposition, Disposition::Rejected);
    assert_eq!(
        rejected.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "INVALID_HOME_INTENT_COMMAND"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), before);
    kernel.shutdown().unwrap();
}

#[test]
fn wp5_schema_valid_but_unresolved_home_intent_is_low_disclosure_and_zero_write() {
    let root = tempfile::tempdir().unwrap();
    let (kernel, handoff) =
        v2_kernel_with_formed_handoff(root.path(), "m0b-wp5-unresolved-source");
    let payload = SyntheticHomeIntentPayload {
        handoff_candidate_ref: "handoff:SYNTHETIC_TEST:phantom:1".to_owned(),
        handoff_candidate_revision: handoff.handoff_candidate_revision,
        handoff_candidate_fingerprint: handoff.handoff_candidate_fingerprint,
        intent_candidate_ref: handoff.intent_candidate_ref,
        intent_candidate_revision: handoff.intent_candidate_revision,
        intent_candidate_fingerprint: handoff.intent_candidate_fingerprint,
        owner_commitment_set_fingerprint: handoff.owner_commitment_set_fingerprint,
        canonical_candidate_history_fingerprint: handoff
            .canonical_candidate_history_fingerprint,
        minimum_trusted_event_sequence: handoff.minimum_trusted_event_sequence,
    };
    let command_id = payload.command_id().unwrap();
    let submission = home_intent_submission_value(&payload).unwrap();
    let request = request_bytes(MethodId::ExecuteCommand, &command_id, submission).unwrap();
    let before = kernel.ledger_counts().unwrap();
    let rejected = CommandBoundary::synthetic(&kernel)
        .invoke(MethodId::ExecuteCommand, &request)
        .unwrap();
    assert_eq!(rejected.disposition, Disposition::Rejected);
    assert_eq!(
        rejected.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "INVALID_HOME_INTENT_COMMAND"
    );
    assert!(!String::from_utf8(rejected.canonical_bytes)
        .unwrap()
        .contains("phantom"));
    assert_eq!(kernel.ledger_counts().unwrap(), before);
    kernel.shutdown().unwrap();
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
    let smuggled_production_refs = [
        "observation_id",
        "session_ref",
        "source_subject_ref",
        "creator_assessment_ref",
    ]
    .map(|field| {
        mutate(observation("DISCARD"), |object| {
            object.insert(
                field.to_owned(),
                json!("session:PRODUCTION:case:SYNTHETIC_TEST:leak"),
            );
        })
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
    for smuggled in smuggled_production_refs {
        assert!(reduce_nonpromotion(&smuggled).is_err());
    }
    assert!(reduce_nonpromotion(&uppercase_hash).is_err());
    assert!(reduce_nonpromotion(&zero_revision).is_err());
}

#[test]
fn wp6_activates_only_the_explicit_synthetic_schema_v2_migration() {
    assert_eq!(schema::SCHEMA_VERSION, 1);
    assert_eq!(schema::M0B_SCHEMA_V2_TARGET_VERSION, 2);
    assert_eq!(
        schema::M0B_SCHEMA_V2_MIGRATION_STATUS,
        "WP6_SYNTHETIC_MIGRATION_ACTIVE"
    );
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
    assert!(schema::m0b_schema_v2_migration_sql().is_some());
}

fn wp7_life_stream_candidate() -> HomeCandidateRevision {
    let observed = decode_synthetic_observation(
        &observation("PROPOSE_LIFE_STREAM_CANDIDATE"),
    )
    .unwrap();
    let proposal = canonicalize_json(
        &serde_json::to_vec(&json!({
            "candidate_id": "life-stream",
            "candidate_revision": 1,
            "created_event_sequence": 20,
            "creator_assessment_fingerprint": observed.creator_assessment_fingerprint,
            "creator_assessment_ref": observed.creator_assessment_ref,
            "payload_commitment": observed.payload_commitment,
            "predecessor_candidate_fingerprint": null,
            "predecessor_candidate_ref": null,
            "predecessor_candidate_revision": null,
            "semantic_class": "LIFE_STREAM_CANDIDATE",
            "source_subject_fingerprint": observed.source_subject_fingerprint,
            "source_subject_ref": observed.source_subject_ref,
            "source_subject_revision": observed.source_subject_revision
        }))
        .unwrap(),
    )
    .unwrap();
    derive_candidate_revision(&proposal, &[]).unwrap().candidate
}

fn wp7_integrated_run(root: &std::path::Path) -> M0BIntegratedWitness {
    for choice in ["EPHEMERAL_ONLY", "DISCARD", "REMAIN_IN_SESSION"] {
        let decision = reduce_nonpromotion(&observation(choice)).unwrap();
        assert_eq!(decision.result, "NO_PROMOTION");
        assert_eq!(decision.canonical_writes.total(), 0);
    }
    assert_eq!(
        decode_synthetic_observation(&observation("PROPOSE_LIFE_STREAM_CANDIDATE"))
            .unwrap()
            .explicit_branch_choice,
        SessionBranchChoice::ProposeLifeStreamCandidate
    );

    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp7",
        b"m0b-wp7-deterministic-nonce",
    )
    .unwrap();
    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).unwrap();
    assert_eq!(kernel.migrate_synthetic_ledger_v2().unwrap().version, 2);

    let life = wp7_life_stream_candidate();
    assert_eq!(
        kernel
            .commit_home_candidate(
                life.clone(),
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );

    let intent = reduce_explicit_promotion(
        &promotion_request(
            &life,
            Some("PROPOSE_INTENT_CANDIDATE"),
            Some("intent"),
            Some(100),
            20,
        ),
        std::slice::from_ref(&life),
    )
    .unwrap()
    .derived_candidate
    .unwrap();
    assert_eq!(
        kernel
            .commit_home_candidate(
                intent.clone(),
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );

    let mut history = vec![intent.clone(), life.clone()];
    let memory = reduce_explicit_promotion(
        &promotion_request(
            &life,
            Some("PROPOSE_MEMORY_CANDIDATE"),
            Some("memory"),
            Some(101),
            20,
        ),
        &history,
    )
    .unwrap()
    .derived_candidate
    .unwrap();
    assert_eq!(
        kernel
            .commit_home_candidate(
                memory.clone(),
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );
    history.push(memory);

    let handoff = compose_f8_handoff(
        &handoff_request(&intent, &history, Some("PROPOSE_F8_HANDOFF"), 100),
        &history,
        &trusted_owner_commitments(),
        &[],
    )
    .unwrap()
    .candidate
    .unwrap();
    assert_eq!(
        kernel
            .commit_home_handoff(handoff.clone(), "intent", HomeCommitFault::None)
            .unwrap(),
        HomeCommitObservation::FirstCommitted
    );

    let submission = synthetic_f3_home_intent_submission(&handoff).unwrap();
    let boundary = CommandBoundary::synthetic(&kernel);
    let committed = boundary
        .invoke(MethodId::ExecuteCommand, &submission.request_bytes)
        .unwrap();
    assert_eq!(committed.disposition, Disposition::Committed);

    let before_rejection = kernel.ledger_counts().unwrap();
    let mut invalid: Value = serde_json::from_slice(&submission.request_bytes).unwrap();
    invalid["payload"]["canonical_command"]["command_payload"]["raw_content"] =
        json!("fixed-rejection-control");
    let invalid = canonicalize_json(&serde_json::to_vec(&invalid).unwrap()).unwrap();
    let rejected = boundary.invoke(MethodId::ExecuteCommand, &invalid).unwrap();
    assert_eq!(rejected.disposition, Disposition::Rejected);
    assert_eq!(kernel.ledger_counts().unwrap(), before_rejection);

    let ambiguous_request = canonicalize_json(
        br#"{"environment":"SYNTHETIC_TEST","interface_version":"agents-os.m0b.f3-ambiguous-control.v0.1","request_id":"command:SYNTHETIC_TEST:ambiguous-home-intent"}"#,
    )
    .unwrap();
    let ambiguous_response = canonicalize_json(
        br#"{"disposition":"INDETERMINATE","external_call_count":0,"runtime_usable":false}"#,
    )
    .unwrap();
    let ambiguous = TerminalIntake {
        command_id: "command:SYNTHETIC_TEST:ambiguous-home-intent".to_owned(),
        command_type_id: HOME_INTENT_COMMAND_TYPE_ID.to_owned(),
        command_type_revision: 1,
        request_fingerprint: agents_os_resident::canonical::fingerprint::sha256_hex(
            &ambiguous_request,
        ),
        request_bytes: ambiguous_request,
        response_fingerprint: agents_os_resident::canonical::fingerprint::sha256_hex(
            &ambiguous_response,
        ),
        response_bytes: ambiguous_response,
    };
    kernel.terminal_indeterminate_intake(ambiguous).unwrap();

    let witness = kernel.m0b_integrated_witness().unwrap();
    assert_eq!(witness.synthetic_session_observation_count, 4);
    assert_eq!(witness.synthetic_life_stream_candidate_count, 1);
    assert_eq!(witness.synthetic_memory_candidate_count, 1);
    assert_eq!(witness.synthetic_intent_candidate_count, 1);
    assert_eq!(witness.synthetic_handoff_count, 1);
    assert_eq!(witness.synthetic_f3_committed_count, 1);
    assert_eq!(witness.synthetic_f3_rejected_control_count, 1);
    assert_eq!(witness.synthetic_f3_indeterminate_count, 1);
    assert_eq!(witness.real_occurrence_count, 0);
    assert!(!witness.runtime_usable);
    kernel.shutdown().unwrap();
    witness
}

#[test]
fn wp7_two_clean_runs_and_restart_are_byte_deterministic_without_promotion() {
    const FIXED_ROOT: &str =
        "81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80";
    let first_root = tempfile::tempdir().unwrap();
    let second_root = tempfile::tempdir().unwrap();
    let first = wp7_integrated_run(first_root.path());
    let second = wp7_integrated_run(second_root.path());
    assert_eq!(first.root_fingerprint, FIXED_ROOT);
    assert_eq!(first, second);

    let database_root = first_root.path();
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:m0b-wp7",
        b"m0b-wp7-deterministic-nonce",
    )
    .unwrap();
    let restarted = ResidentKernel::start(ResidentKernelConfig::synthetic(
        database_root,
        ownership,
    ))
    .unwrap();
    let counts_before = restarted.ledger_counts().unwrap();
    let restart_witness = restarted.m0b_integrated_witness().unwrap();
    assert_eq!(restart_witness, first);
    assert_eq!(restarted.ledger_counts().unwrap(), counts_before);
    restarted.shutdown().unwrap();
}

#[test]
fn wp0_preserves_historical_methods_while_local_owner_additions_stay_closed() {
    let source = include_str!("../src/lib.rs");
    let historical_command_exports = [
        "execute_command",
        "execute_query",
        "claim_outbox",
        "acknowledge_outbox",
        "reconcile",
    ];
    let lifecycle_exports = ["activate_runtime", "runtime_status", "shutdown_runtime"];
    let local_owner_exports = [
        "prepare_local_owner_proposal",
        "submit_local_owner_consent",
        "execute_local_owner_query",
        "invalidate_local_owner_proposal",
    ];
    // P2-A..P2-H canonical runtime surface: MMR mutation exports added by the
    // accepted P1/P2 implementation and promoted by Controlled Integration.
    let mmr_mutation_exports = [
        "prepare_mmr_mutation",
        "submit_mmr_mutation_consent",
        "query_mmr_mutation_core",
    ];
    let presence_exports = ["query_presence_context", "seal_provider_attempt"];
    for export in historical_command_exports
        .into_iter()
        .chain(lifecycle_exports)
        .chain(local_owner_exports)
        .chain(mmr_mutation_exports)
        .chain(presence_exports)
    {
        let marker = format!("#[napi(js_name = \"{export}\")]");
        assert_eq!(
            source.matches(&marker).count(),
            1,
            "missing or duplicate {export}"
        );
    }
    assert_eq!(
        source.matches("#[napi(js_name = ").count(),
        historical_command_exports.len()
            + lifecycle_exports.len()
            + local_owner_exports.len()
            + mmr_mutation_exports.len()
            + presence_exports.len()
    );
}
