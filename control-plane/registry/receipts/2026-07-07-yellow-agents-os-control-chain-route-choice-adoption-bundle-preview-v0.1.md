# Receipt: AGENTS OS Control Chain Route Choice Adoption Bundle Preview v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Risk class: yellow

## What Changed

- Added Control Chain `route-choice-adoption-bundle-preview`.
- Added tests for the bundle preview path and invalid-input non-write behavior.
- Registered the command in the Control Chain README and manifest.
- Updated local governance state and registry evidence for docctl cleanliness.
- Kept the real Active Work Queue unchanged except for governance evidence
  status text.

## Changed Files

```text
CURRENT_STATE.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-control-chain-route-choice-adoption-bundle-preview-v0.1.md
control-plane/registry/receipts/2026-07-07-yellow-agents-os-control-chain-route-choice-adoption-bundle-preview-v0.1.md
control-plane/registry/reviews/2026-07-07-yellow-agents-os-control-chain-route-choice-adoption-bundle-preview-v0.1.review.md
execution/agents-os-control-chain/README.md
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
```

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-adoption-bundle-preview --confirmation-text "[fixture]" --json
result=PASS

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/test-control-chain.py
result=PASS cases=29 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py validate --json
result=PASS

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-dashboard/dashboard.py validate --json
result=PASS last_completed=control_chain_route_choice_adoption_bundle_preview_v0.1

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate --json
result=PASS closed_count=31

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml --json
result=PASS checked_documents=340 pass=340 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml --json
result=PASS checked_registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status --json
result=PASS documents=382 scanned_files=403 score=100

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor --json
result=PASS documents=382 scanned_files=403 warn=0 fail=0

git diff --check
result=PASS

temporary fixture directory cleanup check
result=PASS no_residual_agents-os-route-choice-e2e_or_control-chain-test_directories

secret-shape scan on exact changed files
result=PASS no_matches
```

## Side Effects

```text
preview_only=true
confirmation_text_included=false
raw_confirmation_text_output=false
raw_template_output=false
real_queue_write_performed=false
workspace_route_state_modified=false
active_queue_modified=false
write_performed=false
queue_write_authorized=false
queue_promotion_authorized=false
route_auto_selection_authorized=false
route_adoption_authorized=false
execution_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
memory_write_authorized=false
external_write_authorized=false
```
