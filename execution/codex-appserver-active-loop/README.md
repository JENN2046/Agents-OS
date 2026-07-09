# Codex App Server Active Event Loop

This project contains the local MVP plan and implementation workspace for the Codex App Server Active Event Loop.

Current status: hardened synthetic Codex-to-Codex message channel is frozen by CEA-028 as a minimal communication channel. It supports single-turn Worker <-> Reviewer communication, two-round dialogue, and three-role Worker / Reviewer / Verifier routing identities. The channel transmits, routes, correlates, and records messages; it does not implement governance, role authority, workspace policy, or AGENTS.md interpretation. Phase 8 real-repository read-only pilot remains blocked by restricted-readable-root schema support.

## Intake Package

- Source archive: `archive/intake/codex_appserver_active_loop_fixed_plan_taskbook.zip`
- Extracted docs: `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/`
- Primary execution taskbook: `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/03_CODEX_EXECUTION_TASKBOOK.md`
- Commander review: `docs/commander/2026-07-07-review-and-tasking.md`
- Commander task queue: `data/jobs/commander_task_queue_2026-07-07.json`
- Phase 8 authorization brief: `docs/commander/2026-07-07-phase8-readonly-real-repo-authorization-brief.md`
- Phase 8 authorization package: `data/jobs/phase8_readonly_real_repo_authorization_2026-07-07.json`
- Latest Phase 8 pilot closeout: `data/reports/phase8_readonly_pilot_20260707152026.json`
- Latest source review package: `data/review-packages/source-review-20260707153000/codex-appserver-active-loop-source-review-20260707153000.zip`
- CEA-009 server request response patch: `data/reports/cea-009_server_request_response_patch.json`
- CEA-010 restricted read root recalibration: `data/reports/cea-010_restricted_read_root_recalibration.json`
- CEA-011 safe repo snapshot pilot: `data/reports/cea-011_safe_repo_snapshot_pilot.json`
- CEA-012 context ledger pilot: `data/reports/cea-012_context_ledger_pilot.json`
- CEA-013 context promotion gate: `data/reports/cea-013_context_promotion_gate.json`
- CEA-014 promotion approval receipt: `data/reports/cea-014_promotion_approval_receipt.json`
- CEA-015 prompt packet compiler dry run: `data/reports/cea-015_prompt_packet_compiler.json`
- CEA-016 snapshot-bound Worker prep: `data/reports/cea-016_snapshot_bound_worker_prep.json`
- CEA-017 snapshot-bound Reviewer pilot: `data/reports/cea-017_snapshot_bound_reviewer_pilot.json`
- CEA-018 end-to-end safe review loop: `data/reports/cea-018_e2e_safe_review_loop.json`
- CEA-019 E2E evidence verification gate: `data/reports/cea-019_e2e_evidence_verification_gate.json`
- CEA-020 Phase 8 schema gate: `data/reports/cea-020_phase8_schema_gate.json`
- CEA-021 snapshot review package publisher: `data/reports/cea-021_snapshot_review_package_publisher.json`
- CEA-022 Commander closeout readiness matrix: `data/reports/cea-022_commander_closeout_readiness_matrix.json`
- CEA-023 Codex-to-Codex message bus MVP: `data/reports/cea-023_codex_to_codex_message_bus_mvp.json`
- CEA-024 Message Bus hardening: `data/reports/cea-024_message_bus_hardening.json`
- CEA-025 Multi-turn Codex dialogue: `data/reports/cea-025_multi_turn_codex_dialogue.json`
- CEA-026 Multi-role Codex channel: `data/reports/cea-026_multi_role_codex_channel.json`
- CEA-027 Channel minimalism and AGENTS.md delegation: `data/reports/cea-027_channel_minimalism_agentsmd_delegation.json`
- CEA-028 Channel freeze and closeout: `data/reports/cea-028_channel_freeze_closeout.json`
- Channel freeze manifest: `data/reports/channel_freeze_manifest.json`
- Safe snapshot design: `docs/SAFE_REPO_SNAPSHOT.md`
- Codex-to-Codex message bus: `docs/CODEX_CHANNEL_MESSAGE_BUS.md`
- Channel boundary: `docs/CHANNEL_BOUNDARY.md`
- Context ledger design: `docs/CONTEXT_LEDGER.md`
- Context promotion gate: `docs/CONTEXT_PROMOTION_GATE.md`
- Promotion approval receipt: `docs/PROMOTION_APPROVAL_RECEIPT.md`
- Prompt packet compiler: `docs/PROMPT_PACKET_COMPILER.md`
- Snapshot-bound Worker prep: `docs/SNAPSHOT_BOUND_WORKER_PILOT.md`
- End-to-end safe review loop: `docs/E2E_SAFE_REVIEW_LOOP.md`
- E2E evidence verification gate: `docs/E2E_EVIDENCE_VERIFICATION_GATE.md`
- Phase 8 schema gate: `docs/PHASE8_SCHEMA_GATE.md`
- Snapshot review package publisher: `docs/SNAPSHOT_REVIEW_PACKAGE_PUBLISHER.md`
- Commander closeout readiness matrix: `docs/COMMANDER_READINESS_MATRIX.md`

## Commander Boundary

This repository is the only write target for the MVP implementation.

Managed Worker and Reviewer sessions must stay read-only during MVP execution. Restricted readable roots are an intended safety boundary, but the current local App Server generated schema does not expose `readableRoots`; do not treat `cwd` as an equivalent guarantee.

Do not use Workspace Agents API, Responses API, browser automation, WebSocket transport, `thread/shellCommand`, `command/exec`, `process/*`, `full_access`, or `dangerFullAccess`.

Do not commit, push, deploy, release, tag, read secrets, or access real repositories during MVP smoke.

## Channel Freeze

The Codex-to-Codex Message Bus is a minimal communication channel. It only transmits, routes, correlates, and records messages. It does not implement governance, role authority, workspace policy, or AGENTS.md interpretation.

- CEA-023 proved single-turn communication.
- CEA-024 hardened delivery integrity.
- CEA-025 proved multi-turn communication.
- CEA-026 proved multi-role routing identities.
- CEA-027 froze channel minimalism and AGENTS.md delegation.
- CEA-028 freezes the communication channel as complete for the current line.

Message Bus transmits information. It does not interpret authority.

## Project Scaffold

This project has moved past scaffold and now contains the MVP synthetic loop implementation, schema artifacts, evidence, and follow-up review packages.

Required scripts:

- `npm run build`
- `npm run context:annex`
- `npm run context:approve`
- `npm run context:pilot`
- `npm run context:promote`
- `npm run reviewer:live`
- `npm run safe-review:e2e`
- `npm run safe-review:verify`
- `npm run phase8:schema-gate`
- `npm run review-package:publish`
- `npm run commander:closeout`
- `npm run channel:smoke`
- `npm run channel:multiturn`
- `npm run channel:multirole`
- `npm run test`
- `npm run test:unit`
- `npm run snapshot`
- `npm run smoke`
- `npm run validate`
- `npm run validate:live`
- `npm run worker:live`
- `npm run worker:prepare`

`npm run smoke` runs the real App Server synthetic Worker/Reviewer loop. It does not authorize real repository review.
`npm run validate` runs build and unit tests only. `npm run validate:live` is the explicit live gate that also runs smoke.
