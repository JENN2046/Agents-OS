# Decision Receipt: AGENTS OS automation uplift v0.1

Date: 2026-07-05
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: absorb the remaining automation specialization clauses from `codex副本.md` into AGENTS OS local governance.

## Decision

The workspace root `AGENTS.md` now absorbs the automation-strengthening parts of
`/mnt/c/Users/51529/Downloads/codex副本.md` that were not fully covered by the
engineering absorption pass:

```text
Read-Only Closure
AGENTS OS-specific Red hard stops
scoped file moves as Yellow instead of blanket P3
expanded safe push conditions
PR merge removed from default automatic action
Memory taxonomy
A0/A1/A2/A3 automation classes
G1-G8 automation route index
```

A longer workspace-local automation rulebook was created at:

```text
governance/automation/AGENTS_OS_AUTOMATION_RULEBOOK.md
```

## Reason

The previous root `AGENTS.md` had strong Nobao authority and a working
Green/Yellow/Red model, but it still carried too much confirmation gravity for
bounded local work. This decision makes AGENTS OS closer to the global L3
default-advance behavior while keeping P3 strict.

## Boundary

This decision does not weaken P3. It does not authorize secrets access, raw
private memory reads, provider raw response exposure, service startup that uses
secrets or exposes public endpoints, real provider execution, real Codex CLI
execution, real workspace-write execution, auth/provider/runtime configuration
changes, deployment, release, package publish, force push, tag, production
database writes, irreversible external writes, or PR merge into protected /
shared / governance-critical / production / release / mainline branches.

This decision does not modify global `~/.codex/AGENTS.md`.

## Changed Files

```text
AGENTS.md
governance/automation/AGENTS_OS_AUTOMATION_RULEBOOK.md
control-plane/registry/decisions/2026-07-05-agents-os-automation-uplift-v0.1.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

## Validation

```text
validation_status=passed
validate-document-registry=PASS documents=204 pass=204 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_doctor=PASS registries=3 documents=246 scanned_files=292 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl_status=PASS score=100 eligible_95=True warn=0 fail=0
```
