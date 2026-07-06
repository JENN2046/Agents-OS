# Phase 2 Batch 11 Registry Consumer Readiness Check Plan - 2026-06-28

Status: patch plan only; no readiness report created and no consumers changed.

Notice: This plan is not migration authorization, not consumer integration
authorization, not authorization to execute validation scripts, not authorization
to create maintenance/sync helpers, not authorization to change executable bits,
and not authorization for remote, branch, push, release, deploy, secret,
private-state, log, cache, or runtime actions.

## Goal

Plan a local, read-only Batch 11 evidence check for the newly authoritative
registry file:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
```

The check should answer:

1. Which files currently claim or imply registry consumer behavior?
2. Which files actually reference the new registry path?
3. Which references became stale after Batch 10 created the authority registry?
4. What remains unverified before any future consumer patch?

## Inputs Already Observed

| Evidence | Path | SHA-256 | Observed fact |
| --- | --- | --- | --- |
| Batch 11 candidate selection | `ops/migration/plans/phase-2-batch-11-candidate-selection-2026-06-28.md` | `0ffe55a68a5c394d0108008b344a6e986a90e66b33d2e273a3aea4ba361d2320` | Selects registry consumer/readiness check and defers maintenance/sync helper planning. |
| Batch 10 receipt | `ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md` | `89754a412029a868afe43274a6382392610e4440aabc5533fb22d66654c098f6` | Records that registry consumer integration remains separate. |
| Authority registry | `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | YAML parses; top-level keys are `workspace`, `layers`, `repositories`, `security`; 11 layers and 6 repositories. |
| Registry README | `control-plane/registry/README.md` | `255d71dffedcbc9415a4f8f62abe70d8d34f3d72eea2055001cc6a278793cc56` | Declares expected consumers and still contains Batch 1-era future-authority wording. |
| Workspace validator | `ops/validation/validate-workspace.sh` | `daab2f5ebdcb89d52c39f2c4162edf17079ea607d64ddceba6d7155366c3c87f` | Lists the registry path as a deferred warning path; not executed. |

## Planned Scope

If later authorized, Batch 11 should create exactly these local evidence files:

| Planned file | Purpose |
| --- | --- |
| `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md` | Read-only consumer/readiness evidence table. |
| `ops/migration/receipts/rules-assets-batch-11-registry-consumer-readiness-receipt-2026-06-28.md` | Receipt for the evidence file creation and validation results. |

No consumer file should be modified in this batch.

## Files To Inspect As Evidence

### Authority And Prior-Batch Evidence

| Evidence area | Files | Check |
| --- | --- | --- |
| Batch 10 boundary | `ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md` | Confirm consumer integration was deferred and remote/sync helpers remained outside scope. |
| Batch 11 selection | `ops/migration/plans/phase-2-batch-11-candidate-selection-2026-06-28.md` | Confirm selected direction, guardrails, and deferred maintenance/sync candidate. |
| Authority registry | `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Confirm existence, hash stability, YAML parse, layer/repository counts, and security authorization flags. |

### Declared Registry Consumers

| Evidence area | Files | Check |
| --- | --- | --- |
| Registry README interface claims | `control-plane/registry/README.md` | Extract declared `used_by` consumers and identify stale wording that still says authority files are future or Batch 1-deferred. |
| Control-plane runbook reference | `control-plane/runbooks/add-new-extension.md` | Check whether registry registration wording still says the canonical registry is pending migration. |
| Prompt catalogs | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` | Check for registry path references, consumer claims, or instructions that could be mistaken for active authority. |
| Governance index surfaces | `governance/README.md`, `governance/SECURITY_BOUNDARIES.md` | Check whether governance claims to consume registry data or imposes constraints on registry use. |
| Extension index surfaces | `extensions/README.md` and migrated registry examples | Check whether extension registration references authority registry or examples-only material. |

### Actual Reference Search

Use read-only searches to classify references, not to change files:

| Search target | Patterns | Classification |
| --- | --- | --- |
| Migrated control-plane and ops surfaces | `WORKSPACE_REGISTRY.yaml`, `control-plane/registry` | Actual local references to the authority registry. |
| Governance and extension surfaces | `WORKSPACE_REGISTRY.yaml`, `control-plane/registry`, `registry` near `consumer`, `loader`, `policy`, or `provider` | Possible consumer claims or unrelated registry terminology. |
| Migration docs | `Registry consumer integration`, `consumer/readiness`, `maintenance/sync` | Boundary and prior-decision evidence only; do not count migration docs as active consumers. |

Current shallow reference evidence outside migration docs:

| File | Observed reference |
| --- | --- |
| `control-plane/registry/README.md` | Declares `used_by: ops validators, Codex prompts, extension loader, governance layer`. |
| `ops/validation/validate-workspace.sh` | Lists `control-plane/registry/WORKSPACE_REGISTRY.yaml` as a deferred warning path. |
| `control-plane/runbooks/add-new-extension.md` | Says registry registration is pending separately authorized migration of the registry file. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Records its own `authority_path`. |

## Readiness Questions To Answer

| Question | Required evidence | Expected output |
| --- | --- | --- |
| Is the registry authority file present and parseable? | Hash, YAML parse, top-level keys, layer count, repository count. | `ready`, `needs review`, or `blocked`. |
| Did Batch 10 leave consumer integration separate? | Batch 10 receipt lines for unvalidated consumer integration. | Boundary statement in evidence table. |
| Are declared consumers real current consumers or aspirational claims? | README `used_by` claim plus actual reference search. | Classify each as `observed reference`, `declared only`, or `not observed`. |
| Did Batch 10 make any wording stale? | Registry README and add-new-extension runbook wording. | List stale wording candidates, without editing them. |
| Does the workspace validator need a future patch? | Static read of `ops/validation/validate-workspace.sh`; no execution. | Note whether registry remains a deferred warning despite now existing. |
| Are examples still separated from authority? | Registry README plus `control-plane/registry/examples/*.yaml`. | Confirm examples-only boundary remains intact. |
| Is any remote/sync helper implicated? | Absence check for `ops/maintenance/sync-upstream-vcp.sh`; prior decisions. | Confirm maintenance/sync remains deferred. |

## Explicit Non-Goals

- Do not update `control-plane/registry/README.md`.
- Do not update `control-plane/runbooks/add-new-extension.md`.
- Do not update `ops/validation/validate-workspace.sh`.
- Do not update prompts, governance files, extension files, loaders, or examples.
- Do not execute validation scripts.
- Do not create or modify `ops/maintenance/sync-upstream-vcp.sh`.
- Do not create root or governance copies of `WORKSPACE_REGISTRY.yaml`.
- Do not change executable bits.
- Do not run Git remote, branch, push, release, deploy, network, destructive,
  copy, move, or sync actions.
- Do not print secret values or file contents from secret-like files.

## Strict Preflight Before Evidence Patch

| Check | Expected result |
| --- | --- |
| Target evidence file absence | `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md` does not exist. |
| Target receipt absence | `ops/migration/receipts/rules-assets-batch-11-registry-consumer-readiness-receipt-2026-06-28.md` does not exist. |
| Batch 11 selection hash stability | Candidate selection hash remains `0ffe55a68a5c394d0108008b344a6e986a90e66b33d2e273a3aea4ba361d2320`. |
| Batch 10 receipt hash stability | Batch 10 receipt hash remains `89754a412029a868afe43274a6382392610e4440aabc5533fb22d66654c098f6`. |
| Registry hash stability | Registry hash remains `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d`. |
| Registry YAML parse | YAML parses with the expected top-level keys. |
| Consumer files read-only | Planned evidence patch does not modify consumer files. |
| Live-secret scan | Planned evidence and receipt contain no live-secret patterns. |
| Command-risk scan | Planned evidence and receipt contain no copy-ready remote, branch, destructive, sync, or validator-execution commands. |
| Maintenance/sync absence | `ops/maintenance/sync-upstream-vcp.sh` remains absent. |

## Planned Validation After Evidence Patch

Use static checks only:

| Validation | Method |
| --- | --- |
| Evidence file exists | File existence and SHA-256 hash. |
| Receipt exists | File existence and SHA-256 hash. |
| Consumer files unchanged | Recheck hashes for registry README, workspace validator, add-new-extension runbook, and prompt/governance/extension index files included in the evidence table. |
| Registry parse remains valid | YAML parse of `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| No secret-like content | Pattern scan of the new evidence and receipt files. |
| No risky command text | Pattern scan for remote, branch, destructive, sync, and validator-execution commands in new evidence and receipt files. |

## Authorization Needed For Next Step

Before creating the evidence file and receipt, request explicit authorization for:

```text
Authorize Batch 11 evidence patch: create the registry consumer/readiness evidence file and receipt only; do not modify consumers.
```

That authorization still would not allow script execution, consumer edits,
maintenance/sync helper creation, remote actions, or executable-bit changes.
