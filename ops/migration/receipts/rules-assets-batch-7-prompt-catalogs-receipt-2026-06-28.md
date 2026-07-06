# Batch 7 Receipt: Prompt Catalogs

Status: completed local prompt-catalog patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 7 local prompt-catalog file
placement patch. It is not a general migration authorization, not authorization
to activate, install, source, import, apply, or execute any prompt, not
authorization to change Codex, agent, reviewer, operator, memory, room, harness,
or runtime behavior, and not authorization for secret, private-state, remote,
branch, push, release, deploy, background execution, or permission-expansion
actions.

## Authorization Wording

User requested:

```text
授权执行 Batch 7 补丁：创建 4 个 prompt catalog 目标文件，并补 Batch 7 receipt。
```

## Source Files Read

| Source file | SHA-256 | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | `bf1cf95d12f54211fa9461a20454d66a5f7abf5145df647105f73fee095b8d55` | Adapted as target-native root prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | `7bed9fed366787d3d0c5c6cd37b033ecdc8bb5aace5a2280b2d75fedca796148` | Adapted as agent prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | `f830684fa454ae406cccf372f5954c3811b0666a72d1c4ab029cbe43107aea6e` | Adapted as Codex prompt catalog README. |

All three included source hashes matched the Batch 7 patch plan immediately
before target creation.

## Listed-Only Names And Directories

| Listed-only item | Source catalog | Handling |
| --- | --- | --- |
| `review/` | Root prompt README | Recorded as reference-only; directory not created. |
| `templates/` | Root prompt README | Recorded as reference-only; directory not created. |
| `MEMORY_AGENT.md` | Agent prompt README | Recorded as reference-only; prompt file not created. |
| `REVIEW_AGENT.md` | Agent prompt README | Recorded as reference-only; prompt file not created. |
| `PROJECT_AGENT.md` | Agent prompt README | Recorded as reference-only; prompt file not created. |
| `METIS.md` | Agent prompt README | Recorded as reference-only; prompt file not created. |
| `AGENT_OS_OPERATOR.md` | Agent prompt README | Recorded as reference-only; prompt file not created. |
| `CODEX_MASTER_PROMPT.md` | Codex prompt README | Recorded as reference-only; prompt file not created. |
| `CODEX_REPO_AUDITOR.md` | Codex prompt README | Recorded as reference-only; prompt file not created. |
| `CODEX_EXTENSION_EXTRACTOR.md` | Codex prompt README | Recorded as reference-only; prompt file not created. |
| `CODEX_VCP_SYNC_AUDITOR.md` | Codex prompt README | Recorded as reference-only; prompt file not created. |
| `CODEX_NO_SECRET_RULES.md` | Codex prompt README | Recorded as reference-only; prompt file not created. |

## Target Directories Created

| Target directory | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/` | Created for prompt catalog guidance. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/` | Created for agent prompt catalog guidance. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/` | Created for Codex prompt catalog guidance. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/` | Created for reference-only listed prompt names. |

## Target Files Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/README.md` | Created as prompt catalog index; not active prompt authority. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/README.md` | Created as agent prompt catalog index; not identity, memory, room, or permission activation. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/README.md` | Created as Codex prompt catalog index; not active Codex operating authority. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/legacy-listed-prompts.md` | Created as reference-only evidence of listed-but-unobserved prompt names and directories. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-7-prompt-catalogs-receipt-2026-06-28.md` | Created as receipt for this local patch. |

## Files And Directories Explicitly Skipped

| Skipped target | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/review/` | Listed by source README but not observed as a source directory. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/templates/` | Listed by source README but not observed as a source directory. |
| Agent prompt files named in source README | Listed by source README but not observed as source files. |
| Codex prompt files named in source README | Listed by source README but not observed as source files. |
| Private prompts, private memory, `AGENTS.override.md`, runtime prompts, extension-specific prompt assets | Outside Batch 7 scope and not authorized. |

## Non-Activation And Non-Authorization Checks

| Check | Result |
| --- | --- |
| Root catalog boundary | Target root README states prompt catalogs are guidance only and not authorization to activate, install, source, import, apply, or execute prompts. |
| Agent catalog boundary | Target agent README states it is not authorization to activate identity, grant permissions, read memory, or change agent behavior. |
| Codex catalog boundary | Target Codex README states it is not authorization to change active Codex behavior, execute work, modify repositories, or run prompts. |
| Legacy reference boundary | Target legacy reference says listed names are not active prompts, migrated prompt files, or authorization to create prompts later. |
| Validation command boundary | Target catalogs do not include copy-ready validation script commands. |
| Governance boundary | Target catalogs point to `governance/SECURITY_BOUNDARIES.md` as authority. |

## Validation Run

| Check | Result |
| --- | --- |
| Pre-existing target check | Four target files and this receipt were absent before creation. |
| Source hash check | Three included source README hashes matched the Batch 7 patch plan. |
| Target file list check | `control-plane/prompts/` contains the four planned target files and no extra prompt files. |
| Listed-only absence check | Listed-only prompt files were not created under `agents/` or `codex/`. |
| Missing directory absence check | `control-plane/prompts/review/` and `control-plane/prompts/templates/` were not created. |
| Live-secret pattern scan | No live-secret patterns were found in the four target prompt catalog files. |
| Authority-risk wording check | Authority-risk terms appear only in non-authorization, forbidden, boundary, or reference-only context. |
| Validation-command scan | No copy-ready validation script command was found in the target files. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Prompt activation or prompt tooling | Batch 7 is catalog-only and does not authorize activation. |
| Validation scripts | Batch 7 does not authorize script execution. |
| Private prompt or private memory review | Private prompt and memory material are outside scope. |
| Runtime prompt validation | Runtime prompts were not observed and are outside scope. |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Catalogs could be mistaken as active prompt authority. | Every target file states non-authorization or reference-only boundaries. |
| Listed-only prompt names could be mistaken as migrated files. | `legacy-listed-prompts.md` records that source and target prompt files were not observed or created. |
| Future prompt migration may involve private memory or identity behavior. | Target files state those require separate review, authorization, and receipt. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, source hashes, direct content checks, and pattern scans. |

## Rollback Path

If this Batch 7 prompt-catalog patch must be rolled back, remove only the files
created by this receipt after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/legacy-listed-prompts.md
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-7-prompt-catalogs-receipt-2026-06-28.md
```

Remove prompt directories only if they are empty after those files are removed.
Do not remove `control-plane/`, existing migration documents, receipts, or any
source files under `A:\AGENTS_OS_Workspace`.
