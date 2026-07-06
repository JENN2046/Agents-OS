# AGENTS OS ColaMeta Global Registry Mode Update Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for updating the ColaMeta global
project registry entry for `AGENTS_OS_Workspace` from `source-only` to
`managed`.

This package is not execution authorization by itself. It is the narrow
confirmation material for a single global registry mode update.

## Current Facts

Workspace-local ColaMeta Runner state already exists:

```text
/home/jenn/AGENTS_OS_Workspace/.colameta/plan.json
/home/jenn/AGENTS_OS_Workspace/.colameta/state.json
/home/jenn/AGENTS_OS_Workspace/.colameta/todolist.json
/home/jenn/AGENTS_OS_Workspace/.colameta/decisions.json
/home/jenn/AGENTS_OS_Workspace/.colameta/memory.md
```

The local Runner state is intentionally narrow:

```text
.colameta/memory.md is empty
no ColaMeta service was started
no executor ran
no provider call happened
no auth/token/cookie/session state was changed
```

Latest recorded ColaMeta project mode:

```text
project_name: AGENTS_OS_Workspace
project_root: /home/jenn/AGENTS_OS_Workspace
project_mode: source-only
global_registry_not_modified_by_managed_promotion: true
```

Current connector state remains unusable for this step:

```text
HTTP 401
code: token_expired
```

The connector token state is acknowledged and must not be fixed, bypassed, or
used by this registry mode update.

## What This Step Would Change

The action target is limited to one global ColaMeta registry file:

```text
/home/jenn/.config/colameta/project-registry.json
```

The intended data change is limited to the `AGENTS_OS_Workspace` project record:

```text
project_name: AGENTS_OS_Workspace
project_root: /home/jenn/AGENTS_OS_Workspace
mode before: source-only
mode after: managed
```

The implementation must preserve all unrelated registry records and all
unrelated fields in the `AGENTS_OS_Workspace` record.

## Evidence Writes For The Execution Step

If Jenn later confirms execution, the registry update step should also leave
local governance evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-global-registry-mode-update-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-global-registry-mode-update-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

These evidence writes are local governance records only. They do not expand the
global registry action target.

## What It Must Not Do

This step does not authorize:

```text
starting ColaMeta service
changing auth/token/cookie/session state
modifying provider configuration
modifying runtime configuration
running ColaMeta executor
making provider calls
modifying /home/jenn/AGENTS_OS_Workspace/.colameta/plan.json
modifying /home/jenn/AGENTS_OS_Workspace/.colameta/state.json
modifying /home/jenn/AGENTS_OS_Workspace/.colameta/memory.md
modifying WORKSPACE_REGISTRY.yaml
writing formal AGENTS OS Memory content
reading state-private/
reading, printing, copying, or summarizing secrets/tokens/cookies/credentials
printing raw /home/jenn/.config/colameta/project-registry.json content
external writes other than the single confirmed registry file update
commit / push / tag
release / deploy / publish
Delivery State accepted
ReviewDecision
GateEvent
bulk move / delete / rename
```

## Preflight Before Global Registry Update

Before execution, check the smallest necessary facts:

```text
1. /home/jenn/.config/colameta/project-registry.json exists.
2. It is valid JSON.
3. Exactly one AGENTS_OS_Workspace record is present.
4. The record points to /home/jenn/AGENTS_OS_Workspace.
5. The current mode is source-only, or the step reports no-op if already managed.
6. The proposed diff changes only the mode field for AGENTS_OS_Workspace.
7. No auth/token/cookie/session/provider secret-like fields are read, printed, or changed.
8. .colameta/memory.md remains empty.
9. No executor has run.
10. The connector token_expired state is acknowledged but not used.
```

If any preflight check differs from this package, stop and prepare a revised
confirmation package.

## Reporting Boundary

The execution report may print only redacted structural facts:

```text
project_name
project_root
mode_before
mode_after
changed_field_count
validation result
```

It must not print the raw registry file, unrelated project records, tokens,
headers, cookies, credentials, session material, provider raw responses, or
private memory.

## Rollback Boundary

Rollback is a separate global registry write action. Do not run it unless Jenn
confirms rollback after seeing the actual update result.

Expected rollback scope, if the update changed only the expected field:

```text
set AGENTS_OS_Workspace project mode from managed back to source-only
leave all unrelated project records unchanged
leave all unrelated fields unchanged
```

Rollback must not:

```text
use git reset --hard
use git clean -fd
touch state-private/
touch WORKSPACE_REGISTRY.yaml
touch auth/token/cookie/session/provider config
start service
run executor
make provider calls
perform unrelated external writes
```

## Validation After Global Registry Update

After a confirmed execution, run local validation that does not use the expired
connector token:

```text
python3 - <<'PY'
import json
from pathlib import Path
path = Path('/home/jenn/.config/colameta/project-registry.json')
data = json.loads(path.read_text(encoding='utf-8'))

records = []

def walk(node):
    if isinstance(node, dict):
        names = {node.get('project_name'), node.get('name'), node.get('id')}
        roots = {node.get('project_root'), node.get('root'), node.get('path')}
        if 'AGENTS_OS_Workspace' in names or '/home/jenn/AGENTS_OS_Workspace' in roots:
            records.append(node)
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)

walk(data)
assert len(records) == 1
record = records[0]
mode = record.get('project_mode', record.get('mode'))
assert mode == 'managed'
print('global_registry_mode_update_structural_check=PASS project_name=AGENTS_OS_Workspace mode=managed')
PY
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

Manual checks:

```text
ColaMeta global registry shows AGENTS_OS_Workspace as managed
.colameta/memory.md remains empty
no service was started
no executor ran
no auth/provider/runtime config changed
no provider call happened
no connector token/header/cookie was printed
```

## Exact Confirmation Text

To execute the global registry mode update, use this exact confirmation shape:

```text
确认执行 AGENTS OS ColaMeta global registry mode update v0.1。
允许最小读取并修改 /home/jenn/.config/colameta/project-registry.json，
只把 AGENTS_OS_Workspace 对应记录的 project mode 从 source-only 更新为
managed，并保持其他项目记录和其他字段不变。

允许为这次 global registry mode update 写入对应本地 receipt/review evidence，
并只为保持 docctl doctor clean 而更新 document registry 和 federated document registry。

不启动服务、不改 auth/token/cookie/session、不改 provider/runtime 配置、
不跑 executor、不做 provider 调用、不修改 .colameta/plan.json、
不修改 .colameta/state.json、不写 .colameta/memory.md 内容、不改
WORKSPACE_REGISTRY.yaml、不写正式 AGENTS OS Memory 内容、不读 state-private/、
不读或输出 logs/token/config raw content、不做其他外部写入、不 commit/push/tag、
不发布、不部署、不做 bulk move/delete/rename。
```

Until Jenn confirms this exact execution scope, the global ColaMeta registry
must remain unchanged.
