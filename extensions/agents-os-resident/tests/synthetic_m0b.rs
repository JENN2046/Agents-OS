use agents_os_resident::{home, ledger::schema};

#[test]
fn wp0_fixes_the_home_module_layout_without_activating_it() {
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
        "WP0_LAYOUT_ONLY"
    );
    assert_eq!(home::candidate::IMPLEMENTATION_STATUS, "WP0_LAYOUT_ONLY");
    assert_eq!(home::handoff::IMPLEMENTATION_STATUS, "WP0_LAYOUT_ONLY");
    assert!(!home::session_boundary::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::candidate::CANONICAL_WRITE_AUTHORIZED);
    assert!(!home::handoff::COMMAND_COMMIT_AUTHORIZED);
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
