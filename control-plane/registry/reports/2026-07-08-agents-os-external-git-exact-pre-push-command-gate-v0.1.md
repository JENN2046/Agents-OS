# AGENTS OS External Git Exact Pre-Push Command Gate v0.1

Date: 2026-07-08
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: no-write exact command gate before first external Git push

## Purpose

This report prepares the exact external Git publication command plan for the
target repository selected by Jenn:

```text
target_remote=git@github.com:JENN2046/Agents-OS.git
target_repository=JENN2046/Agents-OS
target_visibility=private
target_remote_state=empty_or_no_advertised_refs
```

It does not execute the plan. It does not authorize `git remote add`, `git
commit`, `git push`, tag, release, deploy, package publish, force push, history
rewrite, or destructive cleanup.

## Read-Only Local Facts

```text
workspace=/home/jenn/AGENTS_OS_Workspace
local_branch=main
local_remote_count=0
recent_head=68b714e chore: record vcptoolbox integration contract
tracked_modified_count=6
untracked_count=25
zone_identifier_untracked_count=2
workbench_untracked_count=13
registry_new_markdown_count=9
docctl_status=PASS documents=418 warn=0 fail=0 score=100
```

The working tree is not clean. Publication must not use `git add -A`.

## Tracked Modified Range

```text
M AGENTS.md
M CURRENT_STATE.md
M control-plane/registry/drafts/document-registry.v0.1.example.yaml
M control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
M control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
M execution/README.md
```

Tracked diff size:

```text
AGENTS.md: +32 -623
CURRENT_STATE.md: +57 -0
control-plane/registry/drafts/document-registry.v0.1.example.yaml: +421 -0
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml: +1 -1
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md: +17 -15
execution/README.md: +53 -0
```

`AGENTS.md` has a large deletion and must not be staged by the default
publication plan unless Jenn separately confirms that exact file change.

## Untracked Range

```text
AGENTS - 副本.md:Zone.Identifier
AGENTS -2.md
AGENTS.md:Zone.Identifier
control-plane/registry/receipts/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.md
control-plane/registry/receipts/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.md
control-plane/registry/receipts/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-vcptoolbox-body-understanding-v0.1.md
control-plane/registry/reports/2026-07-08-agents-os-external-git-publication-target-gate-v0.1.md
control-plane/registry/reports/2026-07-08-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
control-plane/registry/reviews/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.review.md
control-plane/registry/reviews/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.review.md
control-plane/registry/reviews/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.review.md
execution/agents-os-workbench/records/.gitkeep
execution/agents-os-workbench/records/advancerecord-0ea0a055ef.json
execution/agents-os-workbench/records/advancerecord-7b55fd624c.json
execution/agents-os-workbench/records/advancerecord-b8934442f4.json
execution/agents-os-workbench/records/advancerecord-f592087326.json
execution/agents-os-workbench/records/cyclerecord-37dc3eb50e.json
execution/agents-os-workbench/records/cyclerecord-5897c149ba.json
execution/agents-os-workbench/records/cyclerecord-b26127a831.json
execution/agents-os-workbench/records/goalsession-cb48f5b182.json
execution/agents-os-workbench/records/manual-smoke-record.json
execution/agents-os-workbench/test-workbench.py
execution/agents-os-workbench/workbench-manifest.json
execution/agents-os-workbench/workbench.py
```

## Recommended Publish Scope

Default include set for a first private remote publication:

```text
CURRENT_STATE.md
execution/README.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-vcptoolbox-body-understanding-v0.1.md
control-plane/registry/reports/2026-07-08-agents-os-external-git-publication-target-gate-v0.1.md
control-plane/registry/reports/2026-07-08-agents-os-external-git-exact-pre-push-command-gate-v0.1.md
control-plane/registry/reports/2026-07-08-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
control-plane/registry/receipts/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.md
control-plane/registry/receipts/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.md
control-plane/registry/receipts/2026-07-08-yellow-agents-os-external-git-exact-pre-push-command-gate-v0.1.md
control-plane/registry/receipts/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
control-plane/registry/reviews/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.review.md
control-plane/registry/reviews/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.review.md
control-plane/registry/reviews/2026-07-08-yellow-agents-os-external-git-exact-pre-push-command-gate-v0.1.review.md
control-plane/registry/reviews/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.review.md
execution/agents-os-workbench/workbench.py
execution/agents-os-workbench/test-workbench.py
execution/agents-os-workbench/workbench-manifest.json
execution/agents-os-workbench/records/.gitkeep
```

Default exclude set:

```text
AGENTS.md
AGENTS -2.md
AGENTS - 副本.md:Zone.Identifier
AGENTS.md:Zone.Identifier
execution/agents-os-workbench/records/*.json
```

Rationale:

- `AGENTS.md` has a large deletion and needs separate review.
- `Zone.Identifier` files are platform metadata, not AGENTS OS source.
- Workbench JSON records are local run artifacts and not required for the first
  source publication.
- The default plan stages named paths only and avoids `git add -A`.

## Exact Command Plan

These commands are the proposed future plan. They were not executed by this
gate.

```bash
git switch main
git status --short --untracked-files=all

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  execution/agents-os-workbench/workbench.py \
  execution/agents-os-workbench/test-workbench.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/test-workbench.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py \
  control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py \
  control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
python3 control-plane/registry/docctl.py status

git remote add origin git@github.com:JENN2046/Agents-OS.git

git add CURRENT_STATE.md
git add execution/README.md
git add control-plane/registry/drafts/document-registry.v0.1.example.yaml
git add control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
git add control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
git add control-plane/registry/reports/2026-07-07-agents-os-vcptoolbox-body-understanding-v0.1.md
git add control-plane/registry/reports/2026-07-08-agents-os-external-git-publication-target-gate-v0.1.md
git add control-plane/registry/reports/2026-07-08-agents-os-external-git-exact-pre-push-command-gate-v0.1.md
git add control-plane/registry/reports/2026-07-08-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
git add control-plane/registry/receipts/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.md
git add control-plane/registry/receipts/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.md
git add control-plane/registry/receipts/2026-07-08-yellow-agents-os-external-git-exact-pre-push-command-gate-v0.1.md
git add control-plane/registry/receipts/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.md
git add control-plane/registry/reviews/2026-07-07-yellow-agents-os-vcptoolbox-body-understanding-v0.1.review.md
git add control-plane/registry/reviews/2026-07-08-yellow-agents-os-external-git-publication-target-gate-v0.1.review.md
git add control-plane/registry/reviews/2026-07-08-yellow-agents-os-external-git-exact-pre-push-command-gate-v0.1.review.md
git add control-plane/registry/reviews/2026-07-08-yellow-agents-os-vcptoolbox-documentation-reality-map-v0.1.review.md
git add execution/agents-os-workbench/workbench.py
git add execution/agents-os-workbench/test-workbench.py
git add execution/agents-os-workbench/workbench-manifest.json
git add execution/agents-os-workbench/records/.gitkeep

git status --short
git commit -m "chore: add agents os workbench and git publication gate"
git push -u origin main
```

## Abort Criteria

Abort before external write if any of these are true:

```text
validation_failure=true
docctl_status_not_PASS=true
unexpected_staged_file=true
AGENTS.md_staged_without_separate_confirmation=true
Zone.Identifier_staged=true
workbench_records_json_staged=true
state_private_path_staged=true
secret_or_token_shape_detected_in_staged_diff=true
remote_not_JENN2046_Agents_OS=true
remote_has_unexpected_main_ref=true
force_push_required=true
```

## Boundary Kept

```text
external_write_authorized=false
git_remote_add_performed=false
git_commit_performed=false
git_push_performed=false
force_push_authorized=false
tag_release_deploy_publish_authorized=false
history_rewrite_authorized=false
state_private_read_authorized=false
secret_raw_read_authorized=false
formal_memory_write_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
```

## Decision

Accepted as a no-write exact pre-push command gate. The next step requires
Jenn's explicit authorization to execute the named command plan or a revised
version of it.
