# Phase 8 Parser/Semantic Review Gate Plan

Date: 2026-06-28

Status: plan only.

This document plans the first Phase 8 gate: parser/semantic review. It uses
Phase 7 static evidence as input and decides what can be preflighted next
without executing runtime, loader, package scripts, tests, builds, or remote
actions.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-8-scope-plan-2026-06-28.md` | `304573f6d5a38455e06aa134448468e92a25a9309017ad78a15021563e086f3a` | Opens Phase 8 with parser/semantic review first. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-phase-7-closeout-receipt-2026-06-28.md` | `2a9884d9e23ca865155883d4313773682c317649789c51b45f8cdadc2d10fcfb` | Confirms Phase 7 static read-only closeout. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-evidence-review-closeout-receipt-2026-06-28.md` | `a364279d65fc813f33082e354274cd5de9575b602d830ea7d3439e6ba1e81dff` | Confirms static boundary evidence accepted with limits. |
| `ops/migration/inventory/phase-7-runtime-loader-limited-content-read-evidence-2026-06-28.md` | `cae14ba07918d251130514dba0da47a33da69f3ab8d8b3ba3f9002e6d8cf1138` | Provides bounded text findings from five admitted files. |

## Gate Objective

Plan a parser/semantic review path that separates:

- evidence-only semantic review from existing Phase 7 findings
- structured JSON parse-only checks for small JSON files
- deferred YAML parse/semantic review
- deferred lockfile review
- behavior validation gates that require execution

## Candidate Decisions

| Candidate | Proposed next handling | Reason |
| --- | --- | --- |
| `runtime/README.md` | Evidence-only semantic review from Phase 7 content evidence. | Markdown was already read within cap; no parser needed. |
| `execution/README.md` | Evidence-only semantic review from Phase 7 content evidence. | Markdown was already read within cap; no parser needed. |
| `governance/codex-router/README.AGENTS_OS.md` | Evidence-only semantic review from Phase 7 content evidence. | Markdown was already read within cap; governance authority risk must remain labeled. |
| `governance/codex-router/package.json` | JSON parse-only preflight candidate. | Small JSON file already read within cap; parse can validate structure without executing scripts. |
| `governance/codex-router/tsconfig.json` | JSON parse-only preflight candidate. | Small JSON file already read within cap; parse can validate structure without running typecheck. |
| `governance/codex-router/routing-policy.yaml` | Deferred to YAML-specific read/parse gate. | Previously deferred due line cap and parse/semantic separation. |
| `governance/codex-router/package-lock.json` | Deferred to lockfile-specific gate. | Lockfile content read remains deferred. |
| `governance/codex-router/AGENTS.md` | Deferred to revised-cap or section-scoped gate. | Exceeds current line cap. |
| `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md` | Deferred to revised-cap or section-scoped gate. | Exceeds current line cap. |
| `governance/codex-router/README.md` | Deferred to revised-cap or section-scoped gate. | Exceeds current line cap. |

## Future Preflight Scope

The next preflight may confirm:

- this plan hash
- Phase 8 scope plan hash
- Phase 7 closeout/evidence hashes
- future parser/semantic evidence and receipt target absence
- that `package.json` and `tsconfig.json` hashes still match Phase 7 metadata
- local JSON parser availability
- command boundary: parse JSON only, no package script execution, no build,
  no typecheck, no tests

The next preflight must not parse the files yet unless explicitly recorded as a
parse-only evidence step after preflight.

## Future Evidence Tracks

If preflight passes, parser/semantic review can split into two evidence tracks:

| Evidence track | Allowed evidence | Not allowed |
| --- | --- | --- |
| Evidence-only semantic review | Review Phase 7 static findings and classify boundary claims. | No new file reads required; no behavior acceptance. |
| JSON parse-only evidence | Parse `package.json` and `tsconfig.json` to confirm syntactic JSON structure and top-level key classes. | No script execution, dependency install, build, typecheck, tests, or semantic acceptance. |

## Red Lines

Stop if:

- any input hash drifts
- future evidence/receipt targets already exist
- JSON parser is unavailable
- parsing would execute code or evaluate package scripts
- semantic review tries to accept runtime, loader, router, package scripts, tests,
  build, typecheck, or consumer integration
- the scope expands to YAML, lockfile, hidden surfaces, deferred Markdown files,
  runtime code, or router source code without a separate gate

## Acceptance Boundary

This plan can only support parser/semantic preflight. It cannot grant:

- parse evidence collection without preflight
- semantic acceptance
- script execution
- runtime behavior acceptance
- loader behavior acceptance
- governance router acceptance
- full consumer integration acceptance

## Result

Parser/semantic review gate planning is complete. The next safe step is a
preflight that confirms inputs, targets, JSON parser availability, and command
boundaries without parsing files yet.

Marker:

```text
PHASE_8_PARSER_SEMANTIC_REVIEW_GATE_PLAN_CREATED_PARSE_PREFLIGHT_ONLY_NO_EXECUTION
```
