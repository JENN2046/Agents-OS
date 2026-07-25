# AGENTS OS Phase 5D M0-D Actual Object-Only Source Run Decision Package v0.3

Date: 2026-07-25
Owner: Jenn
Agent steward: Nobao
Status: DRAFT_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
Terminal outcome: NOT_EXECUTED

## 1. Narrow successor purpose

R3 preserves immutable R1/R2 evidence and closes only R2's three independent
review blockers: scanner verify-before-execute, signal-safe terminal commit,
and closed no-follow fixture mode. It is not an execution decision.

## 2. R3 executable subjects

    R3_start_decision_sha256: 0ddac25b83277637c56ab1be750e9751ee8b2e45b100302864dec793b5f7ff0d
    amendment_sha256: 22d03bee4337141de6e8973cf6d0b03a6060c30536d33c413aecf1ae25005575
    runner_sha256: 3bf99381e9c4b3e4413abfa799dbad676ae864e173dbe0eeef15ce829d02e5f0
    fixture_builder_sha256: f30b8f1f03354c51f8b5dea6f8a4daca0c5a493721a5bd757671f7fd28dde746
    fixture_sha256: 1c78df56c9a4627ea6844616a2529879cc1eb058d984c0a54f69423356181256
    validator_sha256: cf28f801abc3db9e133904da4d729ce40c50c4ba9f03d335b5d151841d186601
    inherited_scanner_sha256: 82bb5693a650e0f4a415b0158933b3c5414a28f2fe6640344fce5d44ec3f9b35

The R3 runner does not load a scanner at import. Actual mode first verifies the
closed R3 manifest and every source hash through no-follow regular descriptors;
only then can it compile the already verified inherited scanner bytes.

SIGINT, SIGTERM and SIGHUP stay blocked for the complete actual-mode lifetime.
The final pending-signal check is the terminal linearization point. A pending
signal at or before it turns the result into `BLOCKED_INTERRUPTED_OR_SIGNALLED`.
Only after that point may a success receipt be written; the process exits while
the catchable signal mask remains installed, with no post-receipt unmasking.

Fixture mode is exactly `--fixture`, with no positional path. It reads only the
literal R3 fixture via no-follow regular-file validation.

## 3. What creation and review do not authorize

    actual_object_only_source_run_authorized: false
    VCPToolBox_Git_command_count: 0
    VCPToolBox_worktree_or_checkout: false
    Host_plugin_runtime_database_provider_or_authentication: false
    private_Memory_state_private_sensing_or_effect: false
    commit_push_PR_merge_release_deploy_publish_tag_or_force_push: false

## 4. Required review gate

R3 must receive `PASS_NO_BLOCKER` from a fresh full atomic independent review
before any freeze package or Section 6 decision exists. A reviewer must execute
the fixed offline commands, verify all manifest inputs, prove scanner
substitution has no top-level side effect, test fixed fixture rejection of an
extra symlink argument, and use subprocess probes for pending terminal signals.

## 5. Jenn decision surface

### A. Do not execute yet

Keep the R3 package at the independent-review gate. No VCPToolBox Git command,
temporary run root, receipt, scanner execution in actual mode, Host operation,
or runtime path may occur.

### B. Future decision only after review and freeze

A later, separate Jenn execution decision must bind this R3 manifest SHA-256,
the fresh independent review SHA-256, and the exact runner SHA-256. It cannot
be inferred from this draft or from an author self-review.
