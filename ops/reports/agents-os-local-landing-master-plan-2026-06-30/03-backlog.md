# Planned Backlog

Date: 2026-06-30
Status: backlog_plan_v0.1_adjusted_2026-06-30

## 0. Backlog Rule

Each task below is a planned task, not an executed task. The presence of a task
does not authorize implementation.

Status values:

```text
planned
partially_satisfied_by_reality_adjustment
needs_scope
needs_authorization
blocked_until_prior_phase
```

## 0A. Reality Adjustment Delta

The 2026-06-30 local survey changes the next backlog order. The workspace
already has significant governance and migration evidence, so the next work is
not more broad planning. The next work is compact state surfacing and
reconciliation.

Immediate adjusted sequence:

```text
1. accept the local reality adjustment as the current planning baseline
2. create or plan a global project index
3. define project state-card locations for active and placeholder projects
4. reconcile _MIGRATION_MAP.md pending statuses against actual local presence
5. roll up ops/migration evidence into a short current-state surface
6. draft only missing minimal contracts after the state surface is stable
```

## 1. Phase 1: Reality Stabilization

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P1-001 | Write current workspace state report | `ops/reports/current-workspace-state-YYYY-MM-DD.md` | Captures real dirs, empty scaffolds, nested repo state, forbidden areas | Read-only survey + report write |
| P1-002 | Write open gaps report | `ops/reports/agents-os-open-gaps-YYYY-MM-DD.md` | Separates Notion-ready, local-ready, missing, deferred | Report only |
| P1-003 | Create repo/scaffold matrix plan | report section or standalone doc | Lists runtime/extensions/domains/labs/memory/execution status | No clone/fetch |
| P1-004 | Registry consistency review plan | report only | Notes metadata-only registry rule and pending repos | No registry patch |
| P1-005 | Accept local reality adjustment | `07-local-reality-adjustment-2026-06-30.md` | Records current facts and adjusted sequence | Report only |
| P1-006 | Plan global project index | `ops/migration/project-index.md` plan or report section | Lists project path, status, state card, risk, next action | No state mutation |
| P1-007 | Plan project state-card locations | report section | Defines state card path for codex-router and placeholder projects | No project edits |
| P1-008 | Reconcile migration map statuses | reconciliation plan | Separates present, absent, pending, reference-only | No clone/fetch/pull |
| P1-009 | Roll up ops/migration evidence | short rollup report | Summarizes active decisions and Phase 10/11 limits | No receipt rewrite |
| P1-010 | Record codex-router source/head split | alignment note | Distinguishes `f04b369` validated source from `f8a7fe7` current state-only head | No package script |

## 2. Phase 2: Contract Drafting

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P2-001 | Draft Receipt contract | contract draft | Has fields, status, forbidden content, fake example | No validator run |
| P2-002 | Draft TaskEnvelope contract | contract draft | Maps request/scope/risk/authorization/receipt | No codex-router patch |
| P2-003 | Draft CapabilityCard contract | contract draft | Covers source, side effects, secret risk, permission level | No VCP probe |
| P2-004 | Draft ActivationPackage contract | contract draft | Covers allowed/forbidden/stop/receipt/gates | No activation execution |
| P2-005 | Draft StandingAuthorization contract | contract draft | Covers scope, expiry, revocation, forbidden self-expansion | No permission grant |
| P2-006 | Draft AgentIdentityCard and AgentRoomCard contracts | contract drafts | Covers identity, room, memory, boundary, responsibility | No agent activation |
| P2-007 | Draft CockpitCard contract family | contract draft | Seven cards with source and update rules | No UI |
| P2-008 | Draft Growth contracts | contract drafts | GrowthEvent, BehaviorPolicyCandidate, GrowthVerification | No memory write |

## 3. Phase 3: Foundation Agent Localization

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P3-001 | Plan Nobao local card | agent card draft plan | Mirrors Notion identity without new permission | Plan/doc only |
| P3-002 | Plan Memory Agent local card | agent card draft plan | Includes memory-status boundaries | No private memory |
| P3-003 | Plan Review Agent local card | agent card draft plan | Includes pause/review boundary | No enforcement code |
| P3-004 | Plan Project Agent local card | agent card draft plan | Includes current-thread/next-step ownership | No task runner |
| P3-005 | Plan first relation cards | relation card examples | Covers Nobao-Memory, Nobao-Review, Review-Project | Fake examples only |

## 4. Phase 4: Runtime Source Boundary And VCPToolBox A0 Target/Object List

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P4-001 | Draft target/object list | VCPToolBox A0 object-list doc | Lists object categories, reason, allowed/excluded | No runtime read |
| P4-002 | Draft excluded object list | section in same doc | Explicitly excludes env/config/secrets/private memory/provider/login/shell | No secret access |
| P4-003 | Draft stop conditions | section in same doc | Stop if secret/provider/plugin/shell/login/private data required | Plan only |
| P4-004 | Draft readonly receipt template | receipt template | Supports later proof without path leaks | No validation run |
| P4-005 | Draft Review Agent A0 questions | review checklist | Ensures target list cannot become probe | Plan only |
| P4-006 | Draft runtime source-boundary plan | source-boundary doc | Explains clone/fetch/probe authorization requirements because runtime/VCPToolBox is absent | No clone/fetch |
| P4-007 | Draft missing-runtime risk note | report section | Prevents A0 object-list from pretending local runtime exists | Plan only |

## 5. Phase 5: codex-router Alignment

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P5-001 | Map TaskEnvelope to codex-router | alignment doc | Identifies existing concepts and gaps | No code change |
| P5-002 | Map Activation to permit/profile | alignment doc | Shows possible routing and approval relation | No branch change |
| P5-003 | Map Receipt to evidence/audit | alignment doc | Shows audit event and evidence candidate links | No test run |
| P5-004 | Map resident-agent roles | alignment doc | Review/Memory/Project roles mapped to packages/concepts | No runtime identity |
| P5-005 | Define future implementation branch plan | branch plan | States branch rules, tests, non-main work | No git action |
| P5-006 | Map state-sync authority to AGENTS OS state cards | alignment doc | Uses structured state-sync record without making Markdown authoritative | No state-sync script |
| P5-007 | Map Phase 10/11 evidence limits | alignment doc | Carries forward what is and is not granted | No test run |

## 6. Phase 6: Cockpit Data MVP

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P6-001 | Draft HouseStatusCard plan | card contract | Has source_refs, review owner, update trigger | No UI |
| P6-002 | Draft CurrentThreadCard plan | card contract | Tracks phase, active item, next items, not_doing | No live state |
| P6-003 | Draft ActiveAgentCard plan | card contract | Tracks agent status, room refs, risks | No agent runtime |
| P6-004 | Draft CouncilItemCard plan | card contract | Tracks relation/dispute/council items | No messaging |
| P6-005 | Draft ActivationRequestCard plan | card contract | Tracks gates, risk, receipt requirement | No activation |
| P6-006 | Draft RiskSignalCard plan | card contract | Tracks stop condition and Review judgment | No enforcement |
| P6-007 | Draft NextStepCard plan | card contract | Limits next steps and evidence | No task execution |

## 7. Phase 7: Validation And Evidence

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P7-001 | Draft validation authorization template | template doc | Includes scope, cwd, expected output, redaction, receipt | No script run |
| P7-002 | Draft no-secrets redaction policy | policy doc | Counts/redacted summaries preferred | No secret scan |
| P7-003 | Draft workspace validation preflight plan | plan doc | Explains what validation would prove and not prove | No command |
| P7-004 | Draft validation receipt template | template doc | Records command, scope, output policy, result | No command |
| P7-005 | Draft lightweight gate card template | template doc | Matches active lightweight governance decision | No command |
| P7-006 | Draft project phase rollup template | template doc | Matches multi-project governance mode | No command |

## 8. Phase 8: First Local Loop Candidate

| ID | Task | Output | Acceptance | Boundary |
|---|---|---|---|---|
| P8-001 | Select first local low-risk loop | loop proposal | One small contract/report task only | Needs Jenn continuation |
| P8-002 | Draft loop scope | loop scope | allowed/forbidden/receipt/review clear | Plan only until authorized |
| P8-003 | Draft loop closeout criteria | closeout plan | mirrors Loop 001 grammar | No execution |

## 9. Parking Lot

These are intentionally later:

```text
VCPToolBox clone/fetch/probe
Bounded-High-Autonomy migration
Codex_Autonomous_Work_Harness migration
VCPChat interface prototype
Photo_Studio_OS local landing
Jenn extension activation
codex-router implementation branch
validation script execution
private memory system
cross-device presence runtime
```
