# Batch 4 Receipt: Security Boundary Authority

Status: completed local authority-document patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 4 local patch. It is not a
general migration authorization, not authorization for `SECURITY.template.md`,
not authorization for root or control-plane duplicate security-boundary files,
and not authorization for runbooks, scripts, active config, registry files,
private state, logs, cache, or runtime artifacts.

## Authorization Wording

User requested:

```text
授权执行 Batch 4 authority 补丁：创建 governance/SECURITY_BOUNDARIES.md，并把高风险路径中的 harness 从 execution/ 改为 governance/，完成后补 receipt。
```

## Source File Read

| Source file | Use |
| --- | --- |
| `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | Source for canonical governance security-boundary authority. |
| `ops/migration/plans/phase-2-batch-4-security-boundary-authority-patch-plan-2026-06-28.md` | Batch 4 scope, reconciliation, checks, and receipt requirements. |
| `ops/migration/decisions/target-layer-reconciliation-2026-06-27.md` | Authority for `Codex_Autonomous_Work_Harness` target-layer reconciliation. |

## Target File Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | Created as canonical workspace security-boundary authority under governance. |

## Reconciliation Performed

| Source value | Target value | Reason |
| --- | --- | --- |
| `execution/Codex_Autonomous_Work_Harness/` | `governance/Codex_Autonomous_Work_Harness/` | Prior target-layer decision resolved the harness as governance/rules material. |

Additional target-native wording was added to state the authoritative location
and clarify that allowed template file patterns do not authorize active local
configuration files or real secret values.

## Receipt File Created

| Receipt file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-4-security-boundary-authority-receipt-2026-06-28.md` | Receipt for this Batch 4 authority patch. |

## Files Explicitly Skipped

| Skipped file or family | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/SECURITY_BOUNDARIES.md` | Root duplicate was rejected because it creates drift risk. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/policies/SECURITY_BOUNDARIES.md` | Control-plane duplicate was rejected; this is governance authority. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | Security template is a later batch after authority exists. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Template source is not part of this authority patch. |
| `WORKSPACE_REGISTRY.yaml` | Registry authority belongs to a separate registry batch. |
| Runbooks and scripts | They require separate review and were not run. |
| Active config, private state, logs, cache, runtime artifacts | Outside security-boundary authority scope. |

## Validation Run

| Check | Result |
| --- | --- |
| Target pre-existence check before patch | `governance/SECURITY_BOUNDARIES.md` was absent before creation. |
| Duplicate authority pre-existence check | Root and control-plane duplicate authority paths were absent before creation. |
| Source existence check | Source file existed and size was recorded as 1832 bytes. |
| Target existence check | `governance/SECURITY_BOUNDARIES.md` exists after patch. |
| Duplicate absence check | Root `SECURITY_BOUNDARIES.md` and `control-plane/policies/SECURITY_BOUNDARIES.md` were not created. |
| Security template absence check | `control-plane/templates/security/SECURITY.template.md` was not created. |
| Section presence check | Absolute rules, private state, git, runtime, permission levels, high-risk areas, and risk report format are present. |
| High-risk path reconciliation check | `governance/Codex_Autonomous_Work_Harness/` is present and `execution/Codex_Autonomous_Work_Harness/` is absent. |
| Live-secret pattern scan | No live-secret patterns were found in the target file. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Source or migrated validator scripts | Batch 4 plan says not to run validator scripts in this batch. |
| Security template validation | Security template was excluded from this authority patch. |
| Runbook validation | Runbooks were excluded from this authority patch. |
| Registry validation | Registry files were excluded from this authority patch. |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Runtime and domain high-risk path examples may need future reconciliation as later repository migrations proceed. | Current target preserves source high-risk examples except for the already decided harness path. |
| Security template still needs migration. | Template patch is intentionally deferred until after this authority file exists. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, direct content checks, path reconciliation checks, and live-secret scanning. |

## Rollback Path

If this Batch 4 authority patch must be rolled back, remove only the files
created by this receipt after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-4-security-boundary-authority-receipt-2026-06-28.md
```

Do not remove `governance/` or unrelated governance files.
