# Decision Receipt: AGENTS OS root AGENTS engineering absorption v0.1

Date: 2026-07-05
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: absorb engineering automation clauses into the AGENTS OS workspace root `AGENTS.md`.

## Decision

The workspace root `AGENTS.md` keeps the existing Nobao role anchor, P0/P1/P2/P3
authority model, and three-lane execution model.

It now absorbs selected engineering protocol clauses from the compared
`codex副本.md` draft:

```text
workspace directory authority map
file placement questions before edits
validation policy and ladder
delivery safety additions
subagents and review rules
structured reporting fields and result states
```

## Reason

The current workspace `AGENTS.md` already has stronger Nobao construction
authority and clear P3 boundaries. The compared draft is more precise about
large-scale engineering operation. Absorbing the useful engineering clauses
improves execution quality without replacing the current authority model.

## Boundary

This decision does not weaken P3. It does not authorize secrets access,
provider calls, service startup, auth/provider/runtime configuration changes,
formal Memory writes, destructive operations, external irreversible writes,
deployment, release, package publish, force push, tag, or state-private reads.

This decision does not modify global `~/.codex/AGENTS.md`.

## Changed Files

```text
AGENTS.md
control-plane/registry/decisions/2026-07-05-agents-os-root-agents-engineering-absorption-v0.1.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

## Validation

```text
validation_status=passed
validate-document-registry=PASS documents=202 pass=202 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_doctor=PASS registries=3 documents=244 scanned_files=291 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl_status=PASS score=100 eligible_95=True warn=0 fail=0
diff_check=NOT_RUN workspace root is not a git repository
```
