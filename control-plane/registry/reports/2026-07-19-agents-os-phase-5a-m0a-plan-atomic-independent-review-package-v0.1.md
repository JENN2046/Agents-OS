# AGENTS OS Phase 5A M0-A Plan Atomic Independent Review Package v0.1

Date: 2026-07-19
Owner: Jenn
Review unit: `PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_ATOMIC_BUNDLE`
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## Canonical manifest

```text
control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: 01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef
```

```yaml
subjects: 4
workspace_authority_inputs: 21
external_VCPToolBox_inputs: 6
author_evidence: 1
declared_total: 32
partial_review: forbidden
```

## Review request

Perform a fresh full atomic hash-bound independent review. The author
self-review is evidence only. Read and hash every input, including the six
VCPToolBox files fixed at commit
`555b3b538f6eb736e530c2912de678c5941f9985`, and execute every manifest command.

The central question is:

> Does this four-subject unit leave a decision-complete, buildable M0-A plan
> that preserves every F1-F6 authority boundary, keeps VCPToolBox core and the
> current runtime untouched, prevents synthetic evidence from becoming runtime
> authority, and still requires a second Jenn decision before any code or
> database is created?

Independently attack at least:

1. change source ownership from external package to VCPToolBox core or an
   unbound copied directory;
2. enable `plugin-manifest.json` or make plugin discovery possible before the
   implementation and activation gates;
3. add a sixth N-API method, a filesystem path, SQL, callback, credential or
   provider handle to a frame;
4. introduce a second SQLite connection, read pool, JavaScript writer, sidecar,
   network transport or hidden retry;
5. remove an F1-F6 traceability row or leave a favorable behavior without a
   negative, replay and crash case;
6. implement F7/F8 Home behavior in M0-A or treat F8 durability as runtime
   authority;
7. let relationship, role, operating lane, urgency, history or PBL no-match
   alter effect authority;
8. allow `UNKNOWN` to return to an executable queue automatically;
9. let plan freeze automatically authorize WP0, dependency installation,
   SQLite creation or VCPToolBox startup;
10. push source to a public fork or use the existing dirty VCPToolBox worktree.

Review the cross-subject composition, not only each file in isolation. Any
undefined owner, incompatible version, contradictory lifecycle, untestable
crash invariant or implementation choice left to the coder is a finding.

## Author-side fixed claims

```yaml
four_subject_hashes_fixed: true
YAML_subjects_parse: 3/3
F1_through_F6_traceability_rows: 6/6
NAPI_method_count: 5
Rust_ledger_thread_count: 1
SQLite_authoritative_connection_count: 1
VCPToolBox_core_diff_expected: 0
enabled_plugin_manifest_count: 0
Rust_or_JavaScript_source_created: 0
SQLite_database_created: 0
runtime_activation_count: 0
provider_call_count: 0
real_effect_count: 0
terminal_outcome: NOT_IMPLEMENTED
```

These are author claims, not independent conclusions.

## Critical ownership model

```text
extensions/agents-os-resident/           source authority
        |
        | deterministic hash-bound materialization
        v
VCPToolBox/Plugin/AGENTSOSResident/       blocked install overlay
        |
        | future separately authorized activation only
        v
same VCPToolBox Node process + Rust N-API
```

The source is external to VCPToolBox core but the eventual native module is
in-process. No Rust daemon, sidecar or parallel control system is allowed.

## Allowed result and governance

Allowed independent results are exactly `PASS_NO_BLOCKER` or `BLOCK`.
`PASS_NO_BLOCKER` does not freeze the plan. Jenn must atomically accept and
freeze the complete four-subject unit. Even that freeze does not start
implementation; a second exact Jenn implementation decision is mandatory.

```yaml
Phase_5A_started: true
Phase_5A_mode: PLAN_CLOSURE_ONLY
Phase_5A_plan_frozen: false
Phase_5A_implementation_started: false
implementation_authorized: false
dependency_installation_authorized: false
database_creation_authorized: false
VCPToolBox_change_or_start_authorized: false
plugin_enablement_authorized: false
runtime_activation_authorized: false
provider_or_effect_execution_authorized: false
```
