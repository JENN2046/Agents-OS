# Decision Receipt: AGENTS OS three-lane execution model v0.1

Date: 2026-07-03
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: reduce local AGENTS OS operating friction by replacing micro-gates with three execution lanes.

## Decision

AGENTS OS local work now defaults to three lanes:

```text
Green Fast Lane
Yellow Work Batch
Red Hard Stop
```

Green work is local, reversible, and outside P3. It should be done directly
with nearest useful validation and a concise final report. It should not create
confirmation packages.

Yellow work has real but bounded local side effects. It should be batched under
one scope with one compact evidence trail, not split into repeated micro-gates.

Red work is P3. It still stops for Jenn's explicit current authorization. If a
package contains `Exact Confirmation Text`, shorthand is not enough unless Jenn
explicitly says she is confirming that exact text.

## Reason

The previous flow protected boundaries but became too heavy for local project
deployment. The new model keeps P3 strict while making ordinary local work fast
again.

## Changed Files

```text
AGENTS.md
control-plane/registry/GOLDEN_PATHS.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

## Boundary

This decision does not weaken P3. It does not authorize secrets access, provider
calls, service startup, auth/provider/runtime configuration changes, formal
Memory writes, destructive operations, external irreversible writes, deployment,
release, package publish, force push, tag, or state-private reads.

## Validation

```text
validation_status=passed
validate-document-registry=PASS documents=197 pass=197 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_doctor=PASS registries=3 documents=239 scanned_files=286 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl_status=PASS score=100 eligible_95=True warn=0 fail=0
```
