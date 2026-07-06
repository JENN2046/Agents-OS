# Boundaries And Authorizations

Date: 2026-06-30
Status: boundary_plan_v0.1_adjusted_2026-06-30

## 0. Package Boundary

This package authorizes no implementation.

It only defines future boundaries.

## 1. Permission Levels

Use the AGENTS OS permission language:

```text
A0  Read / see
A1  Light self-maintenance
A2  Housekeeping with log / receipt
A3a Low-impact real action under standing authorization
A3b Medium-impact real action under explicit trial authorization
A3c High-impact action with full gate + Jenn confirmation
A4  Forbidden / proposal path only
```

## 2. Default Forbidden For Future Work

```text
secret reading
private-state reading
provider/auth config modification
validation script execution without exact authorization
package script execution without exact authorization
broad npm test / smoke / canary without explicit gate
runtime probe without object-list and Review
git push
git tag
release
deploy
history rewrite
destructive delete
bulk move/rename/overwrite
external write
Notion write unless explicitly requested
Memory write unless explicitly requested and gated
```

## 3. Future Authorization Requirements

### Local Documentation Patch

Likely level:

```text
A2
```

Requires:

```text
scope
target files
receipt
review if touching governance/permissions/memory/identity
```

### Contract Draft Patch

Likely level:

```text
A2
```

Requires:

```text
contract names
allowed example data
forbidden private data
review owner
receipt
```

### codex-router Code Change

Likely level:

```text
A3a or A3b depending on behavior
```

Requires:

```text
repository reality check
branch plan
test plan
risk classification
receipt
no direct main work
```

### Validation Script Run

Likely level:

```text
A3a
```

Requires:

```text
exact command
working directory
scope
expected output
redaction policy
failure behavior
receipt path
```

### VCPToolBox Read-Only Probe

Likely level:

```text
A0/A1 if truly public/local read-only, but only after object-list and Review
```

Requires:

```text
target/object list
excluded targets
stop conditions
Review pass
receipt template
no secret/private/provider/plugin/shell/login objects
```

### VCPToolBox Runtime Execution

Likely level:

```text
A3b/A3c or A4 proposal path depending on capability
```

Requires:

```text
Activation Package
budget
stop conditions
Review Gate
Memory Gate if memory related
Project Gate
Jenn confirmation for high-impact actions
```

## 4. Stop Conditions

Stop immediately if future work encounters:

```text
.env / config.env / secret value
token / api_key / password / cookie / authorization header
provider/auth configuration
browser login state
private raw memory
state-private content without explicit authorization
unknown runtime object that may contain private data
required shell execution not already authorized
required plugin/provider call not already authorized
unexpected external write
request to bypass review or permission gates
```

## 5. Risk Register

| Risk | Severity | Reason | Mitigation |
|---|---|---|---|
| Notion plan stays disconnected from local files | high | AGENTS OS remains vision-only | Phase 1-2 local reports/contracts |
| Local contracts become bureaucracy | medium | Skeleton can swallow home | Keep contracts tied to Loop/Cockpit use |
| codex-router becomes whole AGENTS OS | medium | Governance repo is only one layer | Keep dual foundation and interface/memory plans |
| codex-router state-only head is mistaken for validated source | medium | Current head and validated source are intentionally split | Read state-sync record before alignment |
| migration map pending statuses are mistaken for current truth | medium | Some paths are present while map still says pending | Add reconciliation task before implementation |
| VCPToolBox probe starts too early | high | Runtime may expose secret/provider/shell paths | A0 target/object list first |
| Validation scripts overclaim safety | high | Scripts may expose paths or miss requirements | Exact authorization + redacted receipts |
| Historical ops/migration receipts become live authority | medium | Old heavy evidence remains valid but future mode changed | Use project index and state cards |
| Agent localization grants implicit permissions | high | Identity docs may be mistaken for runtime activation | Explicit non-activation status |
| Cockpit becomes UI before data | medium | Pretty interface hides missing evidence | Data cards first |
| Private memory leaks into repo | critical | Violates core boundary | state-private denied, fake examples only |

## 6. Authorization Labels For Future Plans

Use these labels in future plan headers:

```text
plan_only
read_only
local_doc_patch
contract_draft_patch
validation_preflight
validation_exact_run_requested
runtime_a0_target_list
runtime_probe_requested
implementation_requested
external_write_requested
forbidden_proposal_only
```
