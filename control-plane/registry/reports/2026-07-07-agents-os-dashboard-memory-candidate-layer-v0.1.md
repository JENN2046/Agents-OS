# AGENTS OS Dashboard And Memory Candidate Layer v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: preview-only local state visibility and Memory candidate layer

## Result

AGENTS OS now has a preview-only dashboard component at:

```text
execution/agents-os-dashboard/
```

It exposes:

```text
current queue summary
current NOW
next title
last CLOSED item
last failure evidence status
docctl status summary
docctl doctor summary
open blockers
candidate-only Memory entries
```

## Output Contract

```text
schema_version=agents-os.dashboard.summary.v0.1
preview_only=true
read_only=true
write_performed=false
execution_authorized=false
formal_memory_write_authorized=false
private_memory_raw_read_authorized=false
```

Memory candidates remain:

```text
candidate_only=true
formal_memory_write_authorized=false
memory_write_performed=false
private_memory_raw_read=false
requires_jenn_confirmation=true
```

## Validation Summary

```text
test-dashboard: PASS cases=12 failures=0
dashboard summary: PASS
dashboard validate: PASS
py_compile dashboard: PASS
test-machine: PASS cases=13 failures=0
test-producer: PASS cases=14 failures=0
test-control-chain: PASS cases=21 failures=0
control_chain validate: PASS
validate-document-registry: PASS documents=268 pass=268 warn=0 fail=0
validate-federated-document-registry: PASS registries=3 pass=3 warn=0 fail=0
docctl status: PASS score=100 documents=310
docctl doctor: PASS documents=310 unregistered=0 warn=0 fail=0
```

Current dashboard preview showed:

```text
NOW=Migration Plan Distillation Batch
next_title=null
last_completed=dashboard_memory_candidate_layer_v0.1
last_failure=none
docctl_status=PASS
docctl_doctor=PASS
open_blockers=6
memory_candidates=3
```

## Files

```text
execution/agents-os-dashboard/README.md
execution/agents-os-dashboard/dashboard-manifest.json
execution/agents-os-dashboard/dashboard.schemas.json
execution/agents-os-dashboard/dashboard.py
execution/agents-os-dashboard/test-dashboard.py
execution/README.md
```

## Boundary

No `state-private/` content was read. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service was started. No real executor run, provider
call, VCPToolBox activation, plugin activation, external write, formal Memory
write, Active Work Queue mutation through an executor, Git push, tag, release,
deploy, publish, or history rewrite was performed.

## Next

Move the Active Work Queue to `Migration Plan Distillation Batch`. That pass
should summarize safe historical migration material and avoid bulk move, delete,
rename, private-state reads, runtime activation, and external writes.
