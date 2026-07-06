# Receipt: AGENTS OS Control Chain Route Choice Template Readiness v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Risk class: yellow

## What Changed

- Added a Control Chain `route-choice-template-readiness` command.
- Wired Control Chain validation to require passing Task Producer route-choice
  template coverage.
- Preserved A-E route template readiness as summary-only metadata.
- Kept raw template output, route selection, queue mutation, queue promotion,
  execution, provider call, service start, executor run, external write, and
  Memory write unauthorized.
- Updated local governance state and registry evidence for docctl cleanliness.

## Changed Files

```text
CURRENT_STATE.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-control-chain-route-choice-template-readiness-v0.1.md
control-plane/registry/receipts/2026-07-07-yellow-agents-os-control-chain-route-choice-template-readiness-v0.1.md
control-plane/registry/reviews/2026-07-07-yellow-agents-os-control-chain-route-choice-template-readiness-v0.1.review.md
execution/agents-os-control-chain/README.md
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
```

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-template-readiness --json
result=PASS

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/test-control-chain.py
result=PASS cases=27 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py validate --json
result=PASS

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py route-choice-template-coverage --json
result=PASS

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-dashboard/dashboard.py validate --json
result=PASS last_completed=control_chain_route_choice_template_readiness_v0.1

PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate --json
result=PASS closed_count=29

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml --json
result=PASS checked_documents=334 pass=334 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml --json
result=PASS checked_registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status --json
result=PASS documents=376 scanned_files=397 score=100

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor --json
result=PASS warn=0 fail=0

git diff --check
result=PASS

secret-shape scan on exact changed files
result=PASS no_matches
```

## Side Effects

```text
route_selected=false
route_auto_selection_authorized=false
active_queue_modified=false
queue_write_authorized=false
queue_promotion_authorized=false
execution_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
memory_write_authorized=false
external_write_authorized=false
raw_template_output=false
```
