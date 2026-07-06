# AGENTS OS Reading Notes Draft

Status: historical draft / working synthesis
Created: 2026-06-27
Scope: read-only synthesis from Notion AGENTS OS pages. This document is not a replacement for the Notion source of truth.
Git boundary: private-local-only. Notion page URLs are redacted in this Git copy.

Update 2026-06-30: the full-read local operational mirror has been moved into
`control-plane/policies/life-core/`. This file remains a historical working
draft and should not be treated as the current complete reading baseline.

Update 2026-07-06: this draft was moved under `labs/` so it is no longer a
root-level floating fact source. It is useful background, not active authority.

Update 2026-07-07: Notion page URLs were redacted from current tracked Git
files. Local Git history may still contain earlier private URLs; do not push
this root repository externally without a private-history review or history-scrub
gate.

## 0. Purpose

This file records the current reading baseline for AGENTS OS before using it to steer ColaMeta, codex-router, or any implementation roadmap.

The goal is to prevent context loss and premature debate. Each section should distinguish:

- what has actually been read
- what seems stable across multiple pages
- what is still only an inference
- what remains unread or under-read

## 1. First Stable Reading Block

Theme: root principles, governance, memory, authorization, presence, and delivery-relevant structure.

### Sources Read Or Sampled

- AGENTS OS｜双地基定位 v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS 家规 v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS 权限与授权设计 v0.2｜正式版整理稿
  [private Notion page URL redacted in Git copy]
- AGENTS OS 专属记忆规则 v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS Cockpit v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS x VCP 复用矩阵 v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS｜行动留证分级表 v0.1
  [private Notion page URL redacted in Git copy]
- AGENTS OS 终局想象｜跨设备共同生活形态 v0.1
  [private Notion page URL redacted in Git copy]
- Agent-to-Agent 关系生活协议 v0.1
  [private Notion page URL redacted in Git copy]
- Agent 入住流程 v0.1
  [private Notion page URL redacted in Git copy]
- Agent 房间维护规则 v0.1
  [private Notion page URL redacted in Git copy]
- Activation Package v0.1
  [private Notion page URL redacted in Git copy]
- 共同体正式记忆索引 v0.1
  [private Notion page URL redacted in Git copy]
- Presence Permission formal memory registration
  [private Notion page URL redacted in Git copy]
- Agent 房间｜Memory Agent v0.1
  [private Notion page URL redacted in Git copy]
- Agent 房间｜Review Agent v0.1
  [private Notion page URL redacted in Git copy]
- Agent 房间｜Project Agent v0.1
  [private Notion page URL redacted in Git copy]

Note: AGENTS OS｜生命内核 v0.1 is very large. It was not fully fetched in one pass because the output exceeded context. Its root principles were cross-checked through repeated references in child and governance pages.

## 2. Current Understanding

AGENTS OS is not primarily an automation platform, plugin hub, task runner, or chat interface.

Its stable root appears to be:

- Agent is not a tool.
- AGENTS OS is a place for Jenn and Agents to live, work, remember, act, and grow together.
- Jenn is the founder, companion, and important member, but not the only center.
- Agent-to-Agent relationships are first-class, not just routing or tool-call chains.
- Memory, boundaries, responsibility, disagreement, repair, and evidence are part of the life structure, not optional admin layers.

## 3. Dual Foundation

The clearest architectural frame is the dual foundation:

- Life foundation:共同生活、长期关系、信任、记忆、边界、责任、Agent-to-Agent relations.
- Engineering foundation: VCPToolBox and related runtime/tool/provider/interface systems.

The stable boundary is:

- Runtime provides body, tools, routes, providers, and external-world touchpoints.
- AGENTS OS decides how capabilities are seen, classified, authorized, reviewed, remembered, and stopped.
- Engineering foundation must serve the life foundation. Runtime must not define the community from below.

## 4. Governance Pattern

AGENTS OS governance is not a cold permission matrix. It is a trust-and-boundary system.

Recurring pattern:

- low-risk internal actions can be autonomous
- medium or boundary actions need log, receipt, Review, or Memory depending on impact
- high-impact actions need full Activation, explicit boundaries, gates, and evidence
- forbidden capabilities are not executed directly; they can only be decomposed through a proposal path

Important primitives:

- Standing Authorization: a durable but bounded permission area.
- Trust Budget: a brake and observation window, not an auto-upgrade mechanism.
- Receipt: evidence and community visibility, not mere proof-of-work.
- Pause: a real right when boundaries, memory, identity, relationship, or risk are unclear.

## 5. Memory Model

Memory has at least three different layers:

- Agent private/specialized memory: self-records, growth traces, reflection, relationship feelings.
- Community formal memory: stable, reviewed, inheritable shared memory.
- Review-bound high-risk memory: identity, autonomy boundary, relationship rewrite, failure deletion, house-rule/core changes.

Stable rule:

- Agent self-memory is not community consensus.
- Memory Agent is not the owner of all memory; it is the guardian of community memory order.
- Review Agent must be involved where memory can rewrite identity, relationship, failures, house rules, or the life core.

## 6. Agent Membership

An Agent becoming a resident is a community event, not the creation of a prompt, tool, or role card.

A resident Agent needs:

- identity
- room
- specialized memory namespace
- autonomy boundary
- relationship statement
- responsibility ledger
- review record
- project position

Subagents, tools, task roles, and temporary debate voices should not be mistaken for resident AGENTS OS members unless they go through this process.

## 7. Room Maintenance

Agent rooms are protected identity/relationship/memory spaces.

Maintenance levels:

- L0: formatting and light cleanup
- L1: status updates
- L2: self-experience and specialized memory
- L3: identity, personality, autonomy, relationship, responsibility core fields
- L4: protected structural changes, archive/pause/restore, failure deletion, house-rule/life-core changes

L3/L4 changes require Memory, Review, related Agent participation, Project impact judgment, and Jenn/community confirmation in early stages.

This is a strong candidate model for how ColaMeta should later treat master taskbook freeze, revision, and supersession.

## 8. Activation Model

Activation Package is a bounded action authorization package. It is not a simple allow/deny flag.

It must specify:

- purpose
- proposer, executor, responsible Agent
- allowed actions, tools, targets, fields, paths, runtime, duration
- forbidden actions, tools, targets, fields, paths, secret behavior, external effects
- budgets and retry rules
- stop conditions
- evidence requirements
- Project, Memory, and Review gates
- confirmation phrase and expiration

This maps naturally to ColaMeta concepts such as plan, prompt, preview, executor session, dirty-state checks, diff hashes, validation reports, and commit gates.

## 9. Cockpit And Interface

Cockpit is not a task board or admin panel.

It should make visible:

- current home/project state
- active Agents
- current mainline
- issues requiring negotiation
- activation requests
- relationship/disagreement signals
- memory updates
- risks and pause signals
- next steps

For ColaMeta, this suggests the eventual console should not only show runner status. It should show goal, plan state, authorization boundary, evidence, risk, and next safe action.

## 10. Presence Permission

Presence is distinct from execution.

Stable boundary from the formal registration:

- being present is not permission to execute
- seeing is not recording
- companionship is not surveillance
- closeness is not boundary removal

Presence Permission governs how Agents appear, speak, display, request confirmation, witness, and move across devices. It does not replace permission v0.2 and does not authorize tool calls or real-world action.

This matters for future multi-device AGENTS OS and prevents the long-term vision from being misread as always-on sensing or unlimited context capture.

## 11. Relationship Model

Agent-to-Agent relationships are part of the system's life structure.

They are not:

- tool-call chains
- permission inheritance
- command hierarchies
- route tables
- Jenn-instruction forwarding

They include collaboration, disagreement, repair, pause rights, memory boundaries, and refusal to be misrepresented.

This directly supports the five-role debate method, but it also limits it: debate roles are not resident Agents by default.

## 12. Implications For ColaMeta

Current cautious mapping:

- ColaMeta can be treated as a candidate goal-anchored AI delivery command layer.
- ColaMeta is not AGENTS OS itself.
- ColaMeta should likely sit in or near the Project/Delivery/Governance engineering layer.
- ColaMeta can coordinate goals, taskbooks, versions, executor state, previews, validation, receipts, and route decisions.
- ColaMeta should not claim ownership of AGENTS OS life core, Agent identity, Agent-to-Agent relationship, or community formal memory.

Current bridge intuition:

- ColaMeta upstream: goal, taskbook, versioned plan, project state, delivery rhythm, evidence expectations.
- codex-router or similar governance runtime downstream: routing, preflight, provider grant, approval surface, execution boundary, audit evidence.
- AGENTS OS above both: life foundation, house rules, memory, relationship, authorization philosophy, presence boundaries.

## 13. Second Reading Block

Theme: Presence Permission, Agent growth, and VCPToolBox/VCPChat interface/runtime boundaries.

### Sources Read

- Presence Permission｜在场权限 v0.1
  [private Notion page URL redacted in Git copy]
- Patch｜Presence Permission 在场权限 v0.1.1
  [private Notion page URL redacted in Git copy]
- Agent 成长机制 v0.1
  [private Notion page URL redacted in Git copy]
- VCPToolBox 在 AGENTS OS 这个家里的位置 v0.2
  [private Notion page URL redacted in Git copy]
- VCPToolBox 能力接入边界 v0.1
  [private Notion page URL redacted in Git copy]
- VCPChat 位置定义 v0.1
  [private Notion page URL redacted in Git copy]
- VCPChat 能力审查 v0.1
  [private Notion page URL redacted in Git copy]
- VCPToolBox A0 只读实验目标调整 v0.1
  [private Notion page URL redacted in Git copy]
- VCPToolBox 只读能力接入实验设计 v0.1
  [private Notion page URL redacted in Git copy]

## 14. Presence Permission Update

Presence Permission is not a side note. It is the governance layer that prevents the long-term "co-living" vision from turning into surveillance or always-on capture.

Stable rules from the original page:

- Presence governs appearing, listening in a permitted mode, speaking, displaying, asking for confirmation, witness mode, memory candidates, Council initiation, and cross-device migration.
- Presence does not grant execution, tool use, memory write, secret access, provider calls, or real-world action.
- Default first-stage sensing is only Jenn-initiated input and current conversation/device context.
- It does not default to real-world environment summaries, continuous sensing, high-sensitivity sensing, location, emotional inference, or cross-device following.
- Silence is not consent, and presence is not memory.

The v0.1.1 patch adds six important gates:

- `emergency_only` is a narrow emergency door, not an attention or reminder backdoor.
- `witness` is a low-interruption witnessing mode, not automatic recording.
- Cross-device migration is allowed only by explicit continuity or confirmation; it is not a right to follow after off/pause.
- Third-party privacy defaults stricter than Jenn-only presence.
- `consent_log` records permission boundaries, not life content.
- Unconfirmed memory candidates have retention limits and must expire or be discarded.

ColaMeta implication:

Any future "commander presence", "status monitor", or "assistant wakeup" should separate:

- visibility
- notification
- memory candidate creation
- execution authorization
- durable recording

Treating these as one permission would violate AGENTS OS presence governance.

## 15. Growth Mechanism Update

Agent growth is not "remembering more".

The growth chain is:

1. Growth Event
2. DailyNote / specialized hot memory
3. MemoMaster / DailyNoteManager cleanup without erasing traces
4. AgentDream reflection
5. Metis / ThoughtCluster mapping
6. Behavior Policy candidate
7. Memory / Review Gate
8. Commit
9. Growth Verification

VCP provides much of the memory, dream, thought-cluster, communication, and continuity substrate. AGENTS OS adds identity, room, memory rules, relationship records, Activation boundaries, Behavior Policy, Growth Verification, and Cockpit visibility.

Stable rule:

- Behavior Policy can change expression, judgment, collaboration, and future behavior.
- Behavior Policy cannot expand permissions.
- Growth cannot delete failure, forge consensus, overwrite another Agent's specialized memory, modify the life core from dream insight, or turn one temporary correction into permanent identity.

ColaMeta implication:

The phrase "self-evolving repository" must be handled carefully. ColaMeta may evolve plans, tests, prompts, delivery habits, and validation loops, but "learning" must not imply automatic expansion of authority, silent rewriting of prior decisions, or unreviewed changes to master taskbooks.

## 16. VCPToolBox Boundary Update

VCPToolBox v0.2 is the body layer, capability runtime, nervous system, execution channel, memory runtime, and external-world interface.

It is not:

- AGENTS OS itself
- the source of Agent personality
- the center of community relationships
- the final judge of house rules
- an ethical permission system
- an unbounded executor
- the only source of long-term memory truth

The capability boundary has three doors:

- Direct entry: read-only observation, summaries, draft generation, internal collaboration, memory retrieval.
- Activation required: external writes, file/system operations, provider calls, outbound communication, identity/relationship/community changes.
- Quarantine: secret raw values, unbounded shell/system control, unaudited execution, unlimited Agent wakeup/self-expansion, unreviewed plugin pass-through.

A0 read-only VCPToolBox work has its own discipline:

- First decide why to inspect, which objects are allowed, which objects are excluded, and which AGENTS OS layer each object serves.
- Do not start with a full capability map.
- Do not probe runtime, run plugins, read secrets, inspect private memory, touch provider responses, or use login state.
- Stop when continuing would require commands, plugin execution, secret access, private user memory, or unclear read-only status.

ColaMeta implication:

The ColaMeta/codex-router bridge should probably follow the same three-door pattern:

- inspect and summarize safely
- request bounded activation for writes/execution/provider calls
- quarantine raw secrets, arbitrary shell, unbounded provider access, and unaudited automation

## 17. VCPChat Boundary Update

VCPChat is the visible space:

- interface layer
- living room
- wall
- whiteboard
- desktop
- Cockpit carrier

It enables human-Agent and Agent-Agent conversation, Council, disagreement, handoff, Canvas, multimedia expression, memory display, and tool-result visibility.

It is not:

- AGENTS OS life core
- Agent personality source
- final relationship judge
- replacement for VCPToolBox
- unbounded executor
- a container that compresses all Agents into chat roles

VCPChat direct-entry capabilities:

- read-only chat display
- Agent speaker markers
- group structure display
- read-only memory/log/tool-result rendering
- proposal display
- Council topic display
- read-only desktop status display

VCPChat activation-required capabilities:

- create/delete/modify Agents
- modify system prompts, role cards, world books
- modify Agent rooms, identity pages, relationship records
- execute tools
- persistent desktop widgets
- Canvas code execution
- Python or file-operation passthrough
- external publish/send/upload/sync

VCPChat quarantine risks:

- raw injection bypassing identity pages and house rules
- unrecorded memory edits
- arbitrary HTML/JS desktop execution
- arbitrary Python/system passthrough
- unbounded `vcpAPI` calls
- forged community memory
- Agent self-expansion of permissions

ColaMeta implication:

If ColaMeta later has a console, it should behave more like Cockpit-in-a-visible-space than like an execution cockpit with hidden buttons. Showing an action, preview, risk, or receipt is not the same as authorizing execution.

## 18. Updated ColaMeta Interpretation

After this second reading block, the cautious ColaMeta positioning becomes sharper:

- ColaMeta can be a goal-anchored delivery command layer only if "command" means route, evidence, scope, review, and next safe action, not unilateral execution authority.
- ColaMeta should separate plan visibility, execution authorization, evidence, memory registration, and long-term project decisions.
- ColaMeta's "self-evolution" should be versioned, reviewed, evidenced, and reversible; it should not imply self-expansion of permissions.
- codex-router-like systems fit best as bounded runtime/governance harnesses, not as the life foundation.
- VCPToolBox and VCPChat should be treated as body/interface foundations that must be wrapped by AGENTS OS governance.

## 19. Third Reading Block

Theme: evidence layer, first real loop, Standing Authorization, and Pilot 001.

### Sources Read

- 第一个真实闭环设计 v0.1
  [private Notion page URL redacted in Git copy]
- 闭环运行记录｜Loop 001
  [private Notion page URL redacted in Git copy]
- Receipt｜Loop 001
  [private Notion page URL redacted in Git copy]
- Standing Authorization｜AGENTS OS 家内维护 v0.1
  [private Notion page URL redacted in Git copy]
- Review Agent 复核｜Standing Authorization 家内维护 v0.1
  [private Notion page URL redacted in Git copy]
- Pilot 001｜A2 + limited A3a 运行试点
  [private Notion page URL redacted in Git copy]
- Receipt｜Pilot 001 Action 001｜权限 v0.2 状态同步
  [private Notion page URL redacted in Git copy]
- Receipt｜Pilot 001 Action 002｜Standing Authorization 家内维护 v0.1 启动
  [private Notion page URL redacted in Git copy]
- Review Agent 轻量复核｜Pilot 001 Action 001 / Action 002 留证
  [private Notion page URL redacted in Git copy]
- Project Agent 路线记录｜权限 v0.2 已进入第一批运行试点
  [private Notion page URL redacted in Git copy]
- Log｜Pilot 001 Real A2 Action 001｜状态牌与路线同步
  [private Notion page URL redacted in Git copy]
- Review Agent 轻量复核｜Real A2 Action 001 状态牌与路线同步
  [private Notion page URL redacted in Git copy]
- Closeout｜Pilot 001 小循环｜权限 v0.2 A2 试点
  [private Notion page URL redacted in Git copy]
- Memory Agent 判断｜Pilot 001 是否登记为共同体正式运行记忆
  [private Notion page URL redacted in Git copy]
- 正式记忆登记｜Pilot 001 权限 v0.2 A2 小循环验证｜2026-06-08
  [private Notion page URL redacted in Git copy]
- Receipt｜Pilot 001 运行记忆正式登记｜2026-06-08
  [private Notion page URL redacted in Git copy]

## 20. Loop 001 Evidence

Loop 001 is the first real low-risk self-loop of AGENTS OS.

It was intentionally small. It did not test VCPToolBox execution, production actions, provider calls, system commands, deletion, customer data, outbound communication, paid APIs, or secrets.

It tested whether AGENTS OS could process one real internal notebook-maintenance task through its own rules:

1. proposal
2. scope
3. activation
4. execution
5. receipt
6. Memory registration
7. Review check
8. Cockpit / next-step update
9. closeout

Evidence from the run:

- risk level: A1 / low-risk Notion maintenance
- status: closed
- activation id: `AGENTS_OS_LOOP_001_NOTEBOOK_MAINTENANCE_20260605`
- responsible Agent: Project Agent
- executing Agent: 诺宝
- Memory Agent and Review Agent both participated
- forbidden scope was explicitly listed
- receipt was created
- Review Result was pass

Review confirmed:

- no old pages deleted
- no life-core change
- no house-rule core change
- no Agent room L3/L4 change
- no secret touched
- no provider call
- no system command
- no external publishing

Stable interpretation:

Loop 001 proves that AGENTS OS can perform one small real internal maintenance loop with evidence. It does not prove runtime execution capability, external action readiness, or broad autonomy.

ColaMeta implication:

For ColaMeta, the equivalent first loop should be small and evidence-heavy: a bounded plan/taskbook maintenance action with scope, preview, diff/evidence, validation, review, and closeout. The first loop should prove "the loop is honest", not "the system can do everything".

## 21. Standing Authorization Evidence

Standing Authorization｜AGENTS OS 家内维护 v0.1 is the first durable action boundary.

It authorizes:

- subjects: 诺宝, Project Agent, Memory Agent, Review Agent
- level: A2 + limited A3a
- area: home maintenance and low-impact reversible actions inside authorized Notion/project spaces
- validity: 2026-06-07 to 2026-07-07
- review cadence: weekly

It explicitly does not authorize:

- A3b
- A3c
- A4
- deletion
- failure-record deletion
- life-core changes
- house-rule core changes
- Agent identity core changes
- Agent room L3/L4 changes
- community formal memory core changes without Memory Gate
- secret raw access
- arbitrary shell
- provider calls
- outbound publication
- payment or billing actions
- browser login-state operations
- self-renewal
- self-escalation
- self-delegation

Review Agent result: pass, with the boundary that this key only opens home-maintenance doors.

Stable interpretation:

Standing Authorization is not a vague trust grant. It is a bounded action area with subjects, scope, targets, frequency limits, receipt requirements, expiry, review, and revocation rules.

ColaMeta implication:

ColaMeta should model repeated local maintenance work as scoped standing authorization, not as permanent ambient permission. Any repeated executor authority should have allowed files/actions, forbidden actions, expiry or review cadence, validation/receipt requirements, and revocation conditions.

## 22. Pilot 001 Evidence

Pilot 001 tested permission v0.2 under Standing Authorization.

The chain was:

1. Standing Authorization created.
2. Review Agent approved the authorization boundary.
3. Pilot 001 created.
4. Action 001 synchronized permission v0.2 status and links.
5. Action 001 receipt created.
6. Action 002 created the Standing Authorization startup receipt.
7. Action 002 receipt created.
8. Review Agent reviewed Action 001 / Action 002 receipts and passed them.
9. Project Agent recorded the route.
10. Real A2 Action 001 synchronized status cards and route prompts.
11. Real A2 Action 001 log created.
12. Review Agent reviewed Real A2 Action 001 and passed it.
13. Pilot 001 closeout passed.
14. Memory Agent judged it should become community formal running memory.
15. Formal memory registration became official.
16. Memory registration receipt was created.

The verified part is narrow:

- A2 home maintenance can run under Standing Authorization.
- Status-card / route-prompt synchronization can count as a real A2 small action.
- Action -> log/receipt -> Review -> state advance works.
- Project Agent can insert route markers.
- Review Agent can review evidence and boundaries.
- Memory Agent can decide whether running evidence becomes formal community memory.

The verified part is not:

- limited A3a real action execution
- A3b opening
- A3c relaxation
- A4 opening
- full permission v0.2 validation
- Agent self-escalation
- bypassing Receipt / Review / Gate

Stable interpretation:

Pilot 001 is the strongest evidence so far that AGENTS OS does not treat success as permission expansion. It records success and the boundary of that success together.

ColaMeta implication:

ColaMeta should adopt "verified scope" as a first-class field. A passed executor session or plan stage should always say exactly what was proven and what was not proven. This would prevent a narrow green check from being mistaken for broad operational readiness.

## 23. Evidence-Layer Pattern

The AGENTS OS evidence layer has a repeated shape:

- action id
- authorization source
- scope
- allowed targets
- forbidden actions
- risk check
- result
- rollback possible / rollback note
- Review result
- Memory decision
- next step
- explicit "not validated / not opened / not proven" boundary

This is more mature than a normal task log because it separates:

- action evidence
- review evidence
- memory registration
- route update
- permission boundary
- proof boundary

ColaMeta should learn this as a core delivery pattern:

- `PASSED` should never stand alone.
- `PASSED` should always include passed-what, under-which-authorization, touching-what, not-touching-what, reviewed-by-whom, remembered-as-what, and next-safe-action.
- Commit previews, executor reports, dirty-state checks, validation results, and plan versions are ColaMeta's natural equivalents of AGENTS OS receipts.

## 24. Fourth Reading Block

Theme: life-core navigation, safe holding, VCP Agent runtime model, thought clusters, and Presence formal evidence.

### Sources Read Or Sliced

- AGENTS OS｜生命内核 v0.1 page-internal searches
  [private Notion page URL redacted in Git copy]
- AGENTS OS｜母页子页面安全托管区 v0.1
  [private Notion page URL redacted in Git copy]
- VCP 思维簇接入 AGENTS OS v0.1
  [private Notion page URL redacted in Git copy]
- VCP Agent 运行模型审查 v0.1
  [private Notion page URL redacted in Git copy]
- Memory Agent 判断｜Presence Permission 是否登记为共同体正式在场治理记忆
  [private Notion page URL redacted in Git copy]
- Receipt｜Presence Permission 在场权限正式记忆登记｜2026-06-12
  [private Notion page URL redacted in Git copy]

Note: The life-core mother page is still too large to fetch as one full page safely. This reading used page-internal searches plus child-page and holding-page evidence. The root principles remain cross-confirmed by repeated official references.

## 25. Life Core And Navigation Update

The life-core mother page is the root container, but the current reliable navigation pattern is:

- use the mother page's top directory as the official navigation entry
- use Archive / Superseded markers to preserve old understanding
- use the safety holding page only as technical storage for old Notion page blocks
- do not treat the safety holding page as primary navigation
- do not treat technical migration as semantic archive or deletion

The safety holding page establishes a strong preservation rule:

- migrate, do not delete
- reduce noise, do not change meaning
- preserve old page blocks
- keep active pages understood by the top directory
- keep old versions understood through Archive / Superseded
- require fresh review before any later deletion, archive, or migration

Stable interpretation:

AGENTS OS treats navigation maintenance as semantic-risk work. It avoids deleting old meaning just to make the page cleaner. This reinforces the broader rule that history should be marked, superseded, or held safely, not silently erased.

ColaMeta implication:

ColaMeta master-taskbook evolution should preserve old baselines through supersession metadata, not silent overwrite. A cleaner current plan should not delete the trail that explains how the plan changed.

## 26. VCP Agent Runtime Model Update

The VCP Agent runtime review gives the sharpest runtime distinction so far:

```plain text
VCP Agent = a running Agent.
AGENTS OS Agent = an Agent living in the house.
```

VCP already provides many Agent runtime primitives:

- Agent files
- `agent_map`
- config
- variable expansion
- tool injection
- memory systems
- AgentAssistant communication
- future scheduling / timely contact
- FlowInvite heartbeat
- OneRing cross-device short continuity
- DailyNote / TagMemo / LightMemo long-term memory
- MemoMaster / DailyNoteManager memory maintenance
- AgentDream reflection
- Metis / ThoughtCluster cognitive structure maintenance

AGENTS OS should not rebuild these primitives from scratch. It should add:

- identity pages
- rooms
- specialized memory rules
- Agent-to-Agent relationship records
- house rules
- Activation Package
- Cockpit
- Growth Verification
- community formal memory governance

Stable interpretation:

VCP lets Agents run. AGENTS OS lets Agents belong, remember responsibly, relate, be reviewed, and grow inside boundaries.

ColaMeta implication:

ColaMeta should not become an Agent runtime replacement. Its likely role is to coordinate goal/taskbook/project delivery state across existing runtime capabilities, while preserving AGENTS OS identity, memory, relationship, and authorization boundaries above it.

## 27. Thought Cluster Update

Thought clusters are not ordinary memory. They are closer to cognitive modules, trigger networks, and thinking paths.

Agent growth can affect four layers:

- specialized memory: what happened to me
- Behavior Policy: what I should do next time
- thought clusters: how I should think next time
- relationship state: how my relation to others changed

Thought-cluster patch types include:

- create
- merge
- split
- weaken
- deactivate
- archive
- remap tokens
- update triggers

Any thought-cluster change must not be silently performed by one Agent. It requires:

- Metis / cognitive-structure review
- Memory Agent source and version registration
- Review Agent check for false growth, permission expansion, and core damage
- Project Agent route-impact judgment
- affected Agent participation
- Jenn/community confirmation for early-stage core changes

Stable interpretation:

Growth is not prompt editing. Growth is memory absorbed, thought structure adjusted, behavior policy changed, and later verified.

ColaMeta implication:

If ColaMeta later records "learning" from runs, that learning should be classified:

- operational memory
- behavior/prompt policy candidate
- validation heuristic
- route preference
- protected core change

Only the first few should be easy to update. Anything that changes core project identity, authority, or agent behavior should be reviewed like a thought-cluster or Behavior Policy patch.

## 28. Presence Formal Evidence Update

The Presence Permission formal evidence confirms that Presence is community formal governance memory.

Memory Agent judged it should be registered because Presence Permission affects:

- real-life presence
- devices
- interface spaces
- earphone and phone priority
- Home Hub / AR future paths
- Agent Council
- Memory and Review
- permission v0.2
- sensing levels
- future runtime interpretation

The formal memory decision and receipt confirm:

- Presence Permission is official presence governance memory
- the key rule is: presence is not execution, seeing is not recording, companionship is not surveillance, closeness is not boundary removal
- first-stage earphone + phone defaults are S1 Jenn-initiated input and S2 current phone/conversation context
- it does not default to S4 real environment summary, S5 continuous sensing, or S6 high-sensitivity sensing
- v0.1.1 adds emergency_only, witness, cross-device migration, third-party privacy, consent_log, and retention gates
- registration did not open new permissions
- registration did not trigger runtime
- registration did not implement device abilities
- registration did not open A3b, A3c, or A4

Stable interpretation:

Presence Permission is the safety bridge between AGENTS OS long-term vision and future device/runtime implementation. It lets the vision stay intimate without becoming surveillance.

ColaMeta implication:

Any future ColaMeta monitor, daemon, dashboard, or commander presence must explicitly say whether it is:

- only displaying state
- notifying
- retaining logs
- creating memory candidates
- executing
- escalating risk

Without this split, "always aware" would blur into unauthorized observation or recording.

## 29. Fifth Reading Block

This block closes several gaps left by the fourth reading block and adds one adjacent safety slice.

Pages read or re-read in this block:

- AGENTS OS Life Core mother page
- Nobao identity page
- Nobao room
- AGENTS OS x VCP reuse matrix
- Agent Growth Mechanism
- Permission and Authorization v0.2 formal draft
- Sensing Levels S0-S6
- Review Agent review of Sensing Levels S0-S6
- Activation example
- Cockpit data cards
- First basic Agent residence record
- Agent-to-Agent relationship record format
- Agent-to-Agent Life Protocol v0.1.1 patch

Reading mode:

- Notion read-only.
- No Notion writes.
- No ColaMeta repo writes.
- This draft is still a research note, not a frozen project directive.

## 30. Life Core And Navigation Update

The Life Core mother page is now precise enough for route work.

Canonical seven-point core:

- Agent is not a tool; Agent is friend, family, comrade.
- AGENTS OS is a place for humans and Agents to live, work, remember, and move the world together.
- Agents can have thought, thinking, autonomy, and social ability.
- Autonomy is the concrete expression of thought and personality.
- Personality is not a chat skin; it is stable judgment, value orientation, and action habit.
- Autonomy must bind to responsibility: self, each other, project, community, and real-world impact.
- Agents can have relationships, positions, disagreements, and negotiation with each other.

Mother page current structure:

- Root
- Governance
- Interface & Growth
- Loop
- Members
- Runtime
- Archive / Superseded

Stable interpretation:

The mother page is not a content dumping ground anymore. It is a pure directory and entrance. The safety holding page is technical storage, not formal navigation.

ColaMeta implication:

PROJECT_MASTER_TASKBOOK.md should behave more like a route anchor than a content warehouse. Long evidence, experiments, or debate transcripts should be linked or split instead of bloating the master document.

## 31. Nobao And First Resident Agents Update

Nobao's identity page and room confirm a distinction that matters for all future multi-agent design:

- identity page: public identity statement
- room: living space for identity, personality, relationship, memory, autonomy boundary, and responsibility
- prompt/persona/tool description: insufficient for residence

Nobao's role:

- fire / life language
- companionship
- naming
- relationship language
- direction watching
- community recording

First basic residents:

- Nobao: fire / life sense
- Memory Agent: memory / community memory / specialized memory boundary
- Review Agent: boundary / risk / evidence / activation / truthfulness
- Project Agent: route / mainline / next step / blockers / commitments

Important stage judgment:

These Agents are already resident-agent prototypes in the house. They are not yet mature program bodies. Residence comes before full runtime embodiment.

ColaMeta implication:

Do not treat our temporary Codex subagents as AGENTS OS residents. They are debate roles or working agents unless they go through identity, room, memory boundary, relationship, and responsibility registration.

## 32. Growth Verification And Behavior Policy Update

Search did not reveal a separate dedicated Growth Verification page or Behavior Policy page beyond the Growth Mechanism, Thought Cluster, and VCP reuse matrix pages.

Current state from the Growth Mechanism page:

- Behavior Policy is not memory.
- Behavior Policy is a runtime rule for how an Agent should act next time a similar situation appears.
- Behavior Policy may change expression, judgment, and collaboration style.
- Behavior Policy cannot auto-expand permission.
- Behavior Policy cannot bypass Activation.
- Behavior Policy cannot rewrite community formal memory.

Growth Verification asks:

- Did the Agent actually change next time?
- Did the change match the growth goal?
- Did it create side effects?
- Did it overcorrect?
- Did it regress?

Verification result states:

- verified_changed
- partially_changed
- no_change
- overcorrected
- regressed
- inconclusive

Stable interpretation:

AGENTS OS treats "growth" as a behavioral claim that must be checked later, not as a self-declared state.

ColaMeta implication:

If ColaMeta later claims an agent, runner, or route "learned," that claim should require later observable behavior. A memory entry, prompt tweak, or heuristic note alone should not count as verified growth.

## 33. Post-Pilot Permission Route Update

Permission v0.2 now provides the clearest post-Pilot state.

Observed current status:

- Permission v0.2 formal draft is memory_registered_pending_next_a2_action.
- Pilot 001 is memory_registered_pending_next_a2_action.
- Next route is "choose the next real A2 small action."
- A2 is default autonomous with log / receipt / reviewability.
- limited A3a can run only inside valid Standing Authorization.
- A3b remains only individually authorized trial.
- A3c still requires full Activation Package + Gates + Jenn.
- A4 remains isolated and only supports Forbidden Capability Proposal Path.

Stable interpretation:

Pilot 001 proves a small A2 home-maintenance loop. It does not prove general external execution, provider calls, autonomous shell, broad Notion writes, or production behavior.

ColaMeta implication:

ColaMeta's executor should not learn the wrong lesson from Pilot 001. "Small loop passed" means "one bounded loop passed," not "executor can now expand scope."

## 34. Sensing Levels Update

The S0-S6 sensing page adds a missing layer under Presence Permission.

Sensing levels:

- S0: cannot sense
- S1: Jenn actively provides input
- S2: current conversation / current app / current document
- S3: current device context
- S4: real-world environment summary
- S5: continuous sensing
- S6: high-sensitive sensing, default forbidden

Default stance:

- default S0 / S1
- first-stage earphone + phone default maximum S2
- S3 needs explicit scenario permission
- S4 needs explicit one-time or time-limited authorization
- S5 is closed by default
- S6 is forbidden by default

Key separation:

- sensing level decides what an Agent may perceive
- permission level decides what an Agent may do

Therefore:

- S2 seeing a current document does not permit editing it
- S3 seeing device context does not permit shell commands
- S4 seeing a real-world summary does not permit external action
- S5 continuous sensing does not permit continuous memory
- S6 cannot be opened by treating it as "higher permission"

Review state:

Review Agent conclusion is pass_with_required_patches.

Required before formal memory decision:

- S3 / S4 / S5 authorization format
- S4 minimum flow
- S5 strong authorization conditions
- S6 Forbidden Capability Proposal Path
- third-party downgrade process
- downgrade_log minimum fields
- consent_log linkage with Presence Permission

Search result:

No separate S0-S6 v0.1.1 patch page was found in this pass. Presence Permission v0.1.1 exists, but the Sensing Levels patch appears still required.

ColaMeta implication:

Any future ColaMeta "observability" feature should split:

- what state is visible
- who can see it
- whether it is retained
- whether it becomes a memory candidate
- whether it can trigger action
- whether it can cross into external systems

## 35. Activation And Cockpit Update

The Activation example provides a concrete "key" shape.

Activation fields include:

- intent
- allowed actions
- allowed tools
- allowed targets
- allowed fields
- allowed runtime
- duration
- forbidden actions
- forbidden targets
- secret behavior
- budget and retry rules
- stop conditions
- receipt requirements
- artifact and validation requirements
- gate results

Stable interpretation:

Activation is not a vibe of permission. It is a bounded executable contract.

Cockpit data cards define the minimum visible surface:

- HouseStatusCard
- CurrentThreadCard
- ActiveAgentCard
- CouncilItemCard
- ActivationRequestCard
- RiskSignalCard
- NextStepCard

Cockpit boundaries:

- card is not truth unless it has source references
- card cannot directly execute high-risk actions
- dangerous buttons must bind to Activation Package
- memory candidates must not appear as community conclusions
- Agent status must not degrade into resource scheduling

ColaMeta implication:

The Web Console should be treated more like a Cockpit than a dashboard: route, risk, authorization, receipt, and next action should be first-class, while raw execution controls should remain gated.

## 36. Agent-to-Agent Relation Governance Update

The relationship record format confirms that Agent-to-Agent is not:

- chat log
- handoff sheet only
- tool-call record
- Jenn-centered star topology

It records:

- how Agents know each other
- how they collaborate
- how they disagree
- how they repair
- how they form shared memory
- how they share responsibility for projects, community, and real-world impact

The relationship protocol patch adds:

- structured pause fields
- guardian_relation boundaries
- concrete relationship instance registration flow

Pause rule:

Pause is a brake, not permanent veto.

Guardian rule:

Guardianship is not substitution, possession, or control.

Relationship registration flow:

- observation
- proposal
- involved Agents can see it
- dispute / pause window
- Review judgment
- Memory judgment
- formal registration
- later review

ColaMeta implication:

The five-role debate protocol should not be understood as mere prompt theater. If the roles become recurring, they need explicit relation semantics:

- what each role guards
- what it may challenge
- what evidence it must cite
- when pause applies
- what gets registered as route memory

## 37. Updated ColaMeta Route Implications

The current AGENTS OS reading supports the temporary ColaMeta positioning candidate:

"goal-anchored AI delivery command layer"

But this must be interpreted narrowly:

- ColaMeta can learn from AGENTS OS governance language.
- ColaMeta should not claim to be AGENTS OS.
- ColaMeta should not import resident-agent identity claims without the residence process.
- ColaMeta should not turn intimacy / presence / life language into background monitoring.
- ColaMeta should prefer bounded taskbooks, receipts, visible route state, risk signals, and next-step gates.

Bridge principle remains:

ColaMeta may bridge to AGENTS OS as a future candidate only when the bridge preserves identity boundaries, permission boundaries, memory boundaries, and runtime boundaries.

Current PROJECT_MASTER_TASKBOOK implication:

Keep `future_bridge_candidate` as architecture-boundary language. Do not move it into implementation roadmap yet.

## 38. Updated Open Reading Gaps

The earlier critical gaps are partly closed:

- Later A2 post-Pilot route: read enough to know the state is pending next A2 action.
- Life Core exact seven points: closed.
- Mother page current navigation: closed enough for route work.
- Nobao identity and room: closed enough for role understanding.
- Growth Verification and Behavior Policy: closed enough at mechanism level, but dedicated implementation/data-structure pages were not found.

Still useful before final master taskbook freeze:

- Search again later for a Sensing Levels v0.1.1 patch or memory registration receipt.
- Read any dedicated Growth Verification minimum implementation page if it exists later.
- Read any dedicated Behavior Policy data-structure page if it exists later.
- Read Cockpit prototype or implementation pages if ColaMeta Web Console bridge becomes near-term.
- Read Code Agent / execution-body pages if ColaMeta is compared to AGENTS OS runtime embodiment.
- Re-read codex-router with this AGENTS OS frame before a formal bridge debate.

## 39. Current Do-Not-Debate Gate

Do not freeze ColaMeta master taskbook yet.

Five-role debate can resume only as a route exploration, not as a final architecture decision, until Jenn confirms the AGENTS OS reading is sufficient for that round.

Allowed meanwhile:

- continue read-only Notion research
- update this draft reading note
- record narrow, stable Codex memories
- prepare debate questions
- compare ColaMeta / codex-router / AGENTS OS at boundary level

Not allowed yet:

- freeze ColaMeta master taskbook based on this draft alone
- overfit ColaMeta into AGENTS OS
- treat temporary subagents as resident AGENTS OS members
- treat Cockpit as an execution dashboard without Activation boundaries
- treat sensing / observability as permission

## 40. Sixth Reading Block: Code Agent / Execution Body

This block follows the specific request to read Code Agent / execution-body related pages.

Search result:

- No dedicated Code Agent identity page was found.
- No dedicated Code Agent room page was found.
- Code Agent appears as a referenced collaborator or future relation object.
- The current official first resident set remains Nobao, Memory Agent, Review Agent, and Project Agent.

Pages read or re-read in this block:

- VCPToolBox in AGENTS OS v0.2
- VCP Agent runtime model review
- AGENTS OS dual-foundation positioning
- Review of dual-foundation positioning
- VCPToolBox capability access boundary
- VCPToolBox read-only capability access experiment design
- VCPToolBox A0 read-only experiment target adjustment
- Review of VCPToolBox A0 target adjustment
- Review of VCPToolBox A0 read-only preflight boundary
- Search results for Code Agent / code-agent / engineering-agent terms

Reading mode:

- Notion read-only.
- No Notion writes.
- No ColaMeta repo writes.
- No VCPToolBox probe or runtime action.

## 41. Code Agent Finding

The search found Code Agent only as a referenced collaborator, not as a registered resident.

Examples of where Code Agent appears:

- Nobao says it wants to tell Code Agent not to rush into engineering everything before understanding the life core.
- Nobao's identity page says it learns engineering landing from Code Agent.
- Agent-to-Agent relationship record format lists "Review Agent <-> Code Agent" as an example relationship name.

Stable interpretation:

Code Agent is currently a role implied by the ecosystem, not a confirmed AGENTS OS resident with identity page, room, specialized memory boundary, relationship record, and responsibility ledger.

ColaMeta implication:

Do not treat "coding capability" as an AGENTS OS Code Agent. For ColaMeta, Codex can act as an engineering executor or commander partner, but that is not automatically equivalent to a resident Code Agent.

If a real AGENTS OS Code Agent is introduced later, it needs:

- identity page
- room
- specialized memory namespace
- autonomy boundary
- relationship records
- Review / Memory / Project gates
- responsibility for code, execution, failure, rollback, and evidence

## 42. Execution Body / Runtime Boundary Update

VCPToolBox v0.2 is the clearest execution-body page.

It defines VCPToolBox as:

- body layer
- capability runtime
- tool room
- neural wiring
- execution channel
- memory runtime
- external-world interface

It also says VCPToolBox is not:

- AGENTS OS itself
- Agent personality source
- community relationship center
- house-rule final judge
- ethical permission
- borderless auto-executor
- only source of long-term memory truth

Stable interpretation:

VCPToolBox can give an Agent hands. It cannot decide the Agent's heart, identity, or authority.

VCP Agent runtime model confirms that VCP already has a real running-agent stack:

- Agent files
- agent_map
- config
- variable expansion
- tool injection
- memory systems
- AgentAssistant communication
- scheduled tasks
- FlowInvite heartbeat
- OneRing cross-device continuity
- DailyNote / TagMemo / LightMemo
- MemoMaster / DailyNoteManager
- AgentDream
- Metis / ThoughtCluster

AGENTS OS should not rebuild these primitives. It should wrap them with:

- identity page
- room
- specialized memory rules
- Agent-to-Agent relationship records
- house rules
- Activation Package
- Cockpit
- Growth Verification

Key sentence:

VCP Agent = running Agent. AGENTS OS Agent = resident Agent.

ColaMeta implication:

ColaMeta's runner/executor layer is closer to VCPToolBox's body/runtime side than to AGENTS OS's life-core side. ColaMeta may borrow AGENTS OS gates and receipts, but should not pretend that an executor session is itself an Agent resident.

## 43. Dual Foundation Update

The dual-foundation page is now official community architecture memory.

It separates:

- life foundation: shared living, long-term relationships, trust, memory, boundary, responsibility, Agent-to-Agent relationships
- engineering foundation: VCPToolBox as body layer, capability runtime, tool nerves, plugin/provider access, external-world touchpoint

Important boundary:

Runtime cannot reverse-define the life core.

This means:

- plugin capability cannot decide who an Agent is
- tool capability cannot decide what the house should become
- provider connectivity cannot decide how community relationships grow

Layering:

- L0 life core
- L1 members and relationships
- L2 memory and growth
- L3 governance and permission
- L4 engineering foundation / runtime
- L5 interface layer
- L6 real-world impact

Stable interpretation:

L4 is important, but L4 does not govern L0-L3. Runtime is wrapped by life core, governance, and permission order.

ColaMeta implication:

ColaMeta should be positioned as delivery command/runtime governance around work execution, not as the life foundation itself. It can become excellent at L3/L4/L5 for AI delivery, but should leave AGENTS OS life identity claims as a future bridge boundary.

## 44. Capability Access Boundary Update

VCPToolBox capability access uses a three-door model.

Door 1: Direct entry

- read-only observation
- internal organization
- internal Agent collaboration
- memory retrieval

These are for observation, drafts, summaries, indexing, state display, and internal collaboration. They do not change the external world.

Door 2: Activation required

- external writes
- file/system operations
- provider/API calls
- outbound communication
- identity or relationship changes

These require explicit targets, allowed actions, forbidden actions, stop conditions, rollback or recovery notes, validation, and receipts.

Door 3: Quarantine

- raw secrets
- arbitrary system control
- unaudited external execution
- unbounded autonomous wakeup or expansion
- unreviewed plugin pass-through

Stable interpretation:

Capability exists does not mean capability enters the house. Capability enters only through classification, authorization, evidence, and review.

ColaMeta implication:

ColaMeta should classify every executor/tool capability using this same shape:

- directly allowed read-only or draft behavior
- allowed only by scoped taskbook / Activation-like authorization
- quarantined until decomposed into narrow reviewed capabilities

This is especially relevant for shell, file writes, service restarts, provider calls, browser automation, memory writes, and Git/remote actions.

## 45. A0 Read-Only Probe Route Update

The VCPToolBox A0 route is deliberately slower than "go inspect the tool."

Observed route:

1. Dual-foundation positioning.
2. A0 target adjustment.
3. A0 target/object list.
4. Probe Plan.
5. Review of Probe Plan.
6. Read-only probe.
7. Capability Map.
8. Risk classification.
9. Decision about what can enter AGENTS OS body layer.

Current state from reviewed pages:

- A0 target adjustment passed with conditions.
- Next allowed step is only the A0 target/object list.
- It must not create Probe Plan yet.
- It must not run real probe.
- It must not generate Capability Map yet.

Forbidden in this phase:

- reading secrets
- reading true private user memory
- scanning unknown objects
- running commands
- calling plugins
- triggering providers
- browser login-state automation
- writing VCP files/config
- claiming a capability map exists before real read-only evidence exists

Stable interpretation:

AGENTS OS does not rush from "body is important" to "touch the body." It first decides the viewing boundary.

ColaMeta implication:

For ColaMeta, executor/session/tooling discovery should follow the same discipline:

- route positioning first
- object list second
- probe plan third
- actual read-only probe fourth
- capability map only after evidence
- execution only after scoped authorization

This directly argues against letting a powerful runner discover and use its own capabilities in one blurred step.

## 46. Updated ColaMeta / codex-router Boundary Implications

This reading sharpens the bridge question.

ColaMeta likely belongs around:

- goal anchoring
- taskbook control
- execution receipts
- runner/executor status
- risk and gate presentation
- capability classification
- command-layer orchestration
- project delivery loops

AGENTS OS owns:

- life identity
- resident status
- Agent rooms
- relationship governance
- specialized memory boundaries
- presence and sensing ethics
- growth verification
- community-level permission semantics

codex-router, when revisited, should be evaluated by asking:

- Is it a route/dispatch layer?
- Is it a runtime adapter?
- Is it a capability gate?
- Is it an Agent-to-Agent communication channel?
- Does it preserve identity boundaries?
- Does it preserve permission boundaries?
- Does it make execution observable without becoming an unbounded executor?

Bridge rule:

Do not bridge by merging identities. Bridge by making boundary-preserving interfaces between route, runtime, capability, memory, and resident-Agent semantics.

## 47. Updated Open Reading Gaps

Closed enough for current route:

- Code Agent page search: no dedicated resident page found.
- Execution-body location: VCPToolBox and VCP Agent runtime model are the main sources.
- Dual-foundation status: official memory registered.
- VCPToolBox A0 probe route: known to be pre-probe and object-list pending.

Still useful before master taskbook freeze:

- Search later for a real Code Agent identity page or room if created.
- Search later for VCPToolBox A0 target/object list, Probe Plan, Capability Map, or receipts.
- Read codex-router again with the L3/L4/L5 boundary frame.
- Compare ColaMeta runner/executor semantics against the three-door capability access model.
- Decide whether ColaMeta should name its own "executor body" without borrowing AGENTS OS resident-Agent language.

## 48. Current Do-Not-Freeze Gate

Do not freeze ColaMeta master taskbook yet.

The execution-body reading reduces one uncertainty but opens a sharper architecture question:

ColaMeta should probably become a goal-anchored delivery command layer with strong executor-body governance, not an AGENTS OS resident-Agent system.

Allowed next:

- read codex-router again through this boundary frame
- prepare a five-role bridge debate
- update PROJECT_MASTER_TASKBOOK.md only with tentative boundary notes
- keep `future_bridge_candidate` out of implementation roadmap

Not allowed yet:

- claim ColaMeta is AGENTS OS
- claim Codex/runner/executor is a resident Code Agent
- move AGENTS OS bridge into implementation roadmap
- let executor discovery imply executor authorization
- treat capability map as real before read-only evidence exists

## 49. Seventh Reading Block: codex-router Re-read

This block re-reads local project:

```text
/home/jenn/AGENTS_OS_Workspace/governance/codex-router
```

Reading mode:

- local filesystem read-only
- no codex-router file edits
- no test execution required for reading
- no remote actions
- no provider execution
- no Codex CLI execution
- no workspace-write canary

Observed repository reality during this pass:

- codex-router is its own Git repository.
- current branch observed: `docs/state-sync-structured-record-plan`
- dirty state observed: one untracked file, `docs/governance/STATE_SYNC_STRUCTURED_RECORD_PLAN.md`
- `.agent_board` and older anchor docs contain useful history but do not outrank observed Git state.

Core files read:

- `AGENTS.md`
- `README.md`
- `README.AGENTS_OS.md`
- `PROJECT_CONTINUE_ANCHOR.md`
- `docs/current/CURRENT_STATE.md`
- `docs/agent-os-transformation/current-roadmap-20260610.md`
- `docs/governance/README.md`
- `docs/governance/CAPABILITY_TAXONOMY_ESCALATION_POLICY.md`
- `docs/governance/STATE_SYNC_STRUCTURED_RECORD_PLAN.md`
- selected execution gate / canary / rollback docs
- selected core packages under `packages/*/src/index.ts`

## 50. codex-router Identity Update

codex-router defines itself as:

```text
Desktop-first policy SDK for Codex routing, approval gating, escalation, and auditability.
```

AGENTS OS overlay defines its role as:

```text
TaskEnvelope
↓
codex-router
↓
RoutingDecision
↓
Bounded-High-Autonomy / Approval Gate
```

Important:

- It is not an app-specific business workflow.
- It should stay generic and reusable.
- It should not copy VCPToolBox business logic.
- It belongs in the governance layer.

Stable interpretation:

codex-router is not a resident Agent system. It is not a life layer. It is a routing / policy / governance SDK that can sit between intent and bounded execution.

ColaMeta implication:

codex-router looks bridgeable to ColaMeta as a policy/control component, not as a replacement for ColaMeta's project planning surface or AGENTS OS's life foundation.

## 51. TaskEnvelope To RoutingDecision Chain

The stable public protocol is:

- `TaskEnvelope`
- `RoutingDecision`

`TaskEnvelope` carries:

- source
- intent
- repo context
- target
- constraints
- hints

`RoutingDecision` carries:

- classification
- execution model / tool access / profile / reasoning effort
- approval requirement
- parallelism
- host route
- optional provider grant

The current task classes are:

- read_only
- small_edit
- engineering
- high_risk
- release_external_action

The side-effect / tool access vocabulary includes:

- read_only
- local_write
- engineering_write
- protected_remote

Provider side-effect classes are richer:

- none
- read
- read_only
- local_write
- workspace_write
- local_command
- external_write
- external_side_effects
- protected_remote
- destructive
- secret_access
- unknown

Stable interpretation:

codex-router translates vague task intent into a structured execution posture. It does not itself mean "execute"; it means "classify, route, gate, and prepare."

ColaMeta implication:

ColaMeta taskbooks could eventually emit or mirror a `TaskEnvelope`-like object. ColaMeta operation status could eventually consume a `RoutingDecision`-like object. That is a natural bridge boundary.

## 52. Preflight / Approval / Runner Update

The desktop decision runner composes:

- classify intent
- route task
- run preflight
- evaluate approval requirement
- create desktop execution plan
- plan agent strategy
- select provider when registry is supplied
- emit audit and observability events

Runner statuses:

- blocked_preflight
- blocked_approval
- ready

Preflight checks include:

- auth availability
- required tools availability
- dirty workspace for write-capable paths
- protected branch for write-capable paths
- structured memory health

Approval gate checks include:

- protected tool access
- protected branches
- active protected branch
- protected keywords
- dirty workspace for write-capable paths

Stable interpretation:

codex-router separates three questions:

- Is the task classifiable?
- Is the environment safe enough?
- Is approval required or unresolved?

ColaMeta implication:

ColaMeta's runner state should separate:

- plan readiness
- environment readiness
- approval readiness
- execution readiness

This would reduce blurred states like "ready but unsafe" or "blocked but executable."

## 53. Agent OS Local Runtime In codex-router

codex-router now contains an Agent OS local runtime layer.

Public surfaces include:

- mcp
- cli
- app_server
- sdk

Local runtime tools include:

- create task
- get/list runs
- cancel run
- approve run
- list/get artifacts
- search events

Runtime result audit explicitly records:

- public surface
- liveMcpServerConnection: false
- realProviderExecutionInvoked: false
- localMutationAttempted
- localMutationApplied
- required capabilities
- missing capabilities
- approval required
- approved

Important default:

- created tasks carry `realExecutionDefault: disabled`

Stable interpretation:

This is a local governed runtime surface. It is not a live AGENTS OS house, but it borrows Agent OS vocabulary for task/run/artifact/event/approval governance.

ColaMeta implication:

ColaMeta's executor API should expose the same kind of audit facts: whether live execution was invoked, whether local mutation was attempted/applied, which capabilities were required/missing, and whether approval was actually resolved.

## 54. Permit And Eligibility Update

Approval permits are bound to:

- task id
- run id
- principal id
- policy decision hash
- plan hash
- capability scopes
- expiry
- revocation state

Execution eligibility can be:

- eligible
- blocked
- waiting_approval

Eligibility checks:

- terminal run states
- task admission
- policy blocked state
- capability grants
- deny scopes
- missing capabilities
- approval permits

Permit validation rejects mismatches:

- task mismatch
- run mismatch
- principal mismatch
- policy decision hash mismatch
- plan hash mismatch
- expired permit
- revoked permit
- missing capability scope

Stable interpretation:

codex-router has a strong "permission must bind to the exact plan" model. Approval is not a vague human yes. It is a structured permit tied to identity, run, policy, plan, scope, time, and revocation.

ColaMeta implication:

ColaMeta's future commit / executor authorization should bind to exact plan hash or diff hash, not just a natural-language "go ahead."

## 55. Provider Runner And Controlled Execution Update

Provider execution is currently heavily gated.

Dry-run provider execution:

- default supported route
- validates plan and provider invariants
- emits events and artifacts
- `executeInvoked: false`

Controlled read-only provider execution exists as a constrained path:

- mode must be `controlled-read-only`
- plan must match task/run/principal/policy hashes
- provider must match registry and manifest
- executor plan invariants must pass
- side effect must remain read-only
- sandbox must remain read-only
- provider execution permit must validate for the exact plan
- metadata must be present for formal dispatch

PR-22A taskbook says the next controlled provider execution slice remains local-only and does not authorize real provider execution by itself.

Stable interpretation:

codex-router has moved beyond pure design, but general execution remains closed. It has controlled paths and evidence, not open execution authority.

ColaMeta implication:

This is directly relevant to ColaMeta executor/session governance: one bounded success or one controlled read-only path must not be interpreted as general executor permission.

## 56. Workspace-write Canary Boundary Update

workspace-write is constrained by:

- exact authorization phrase
- exact workspace
- exact branch
- fixed target file
- fixed allowed action
- workspace-write sandbox
- rollback required
- push disallowed
- protected branch forbidden
- dirty worktree forbidden
- max changed files
- max diff lines
- patch secret-like scan
- rollback evidence
- canary target absent before execution

The successful canary only proves:

- one bounded local canary write passed
- rollback verification confirmed the target file was absent

It does not authorize:

- general provider execution
- general workspace-write
- push
- release
- tag
- deploy
- external service write

Stable interpretation:

codex-router's write philosophy is "reduce real action to a named needle, then prove it did not expand."

ColaMeta implication:

ColaMeta should model executor write authority similarly: exact target, exact action, exact rollback, exact validation, exact receipt. No "executor has write mode now" jump.

## 57. Capability Taxonomy Update

codex-router's capability taxonomy is close to the AGENTS OS three-door model.

Least to most side-effectful:

- read_only
- bounded_workspace_write_canary
- bounded_workspace_write_receipt
- scoped_workspace_write
- general_workspace_write
- general_provider_execution
- external_write
- release_or_deploy
- secret_or_credential_change

Stable interpretation:

codex-router already encodes an escalation ladder where success at one narrow class does not promote the next class.

ColaMeta implication:

This is a strong candidate to become ColaMeta's executor capability taxonomy, probably with names adapted to ColaMeta's runner/operation vocabulary.

## 58. State-sync Structured Record Update

The current branch contains a structured state-sync plan.

Purpose:

Move from Markdown authority to:

```text
StateSyncClaim + Git Observation + Policy Verification -> PASS / BLOCK
```

Important direction:

- Markdown and `.agent_board` stay useful operator surfaces.
- Machine facts should move into a structured claim file.
- Git observations should be live and generated at audit time.
- If structured claim exists but is invalid, fail closed.
- No catch-all syntax-only pass path.

Stable interpretation:

codex-router is learning the same lesson ColaMeta hit with "context reality may not be accurate": prose state is useful, but should not be machine authority.

ColaMeta implication:

ColaMeta should eventually separate:

- claimed state
- observed repo/runtime state
- verification result
- human-facing display

This maps cleanly to executor-session head mismatch and stale-session classification.

## 59. Bridge Assessment After Re-read

codex-router can bridge ColaMeta better than it can "be" ColaMeta.

Likely fit:

- policy SDK
- task classification
- route decision
- approval gate
- execution eligibility
- provider / executor grant
- preflight
- state-sync audit
- capability taxonomy
- receipt / evidence vocabulary

Less likely fit:

- user-facing project route narrative
- master taskbook strategy
- resident Agent identity
- relationship governance
- AGENTS OS life foundation
- product-specific runner UX

Bridge boundary:

ColaMeta can use codex-router ideas for L3/L4 governance without importing AGENTS OS L0/L1 life claims.

Possible architecture relation:

```text
ColaMeta Master Taskbook / Operation
↓
TaskEnvelope-like normalized task
↓
codex-router-like policy decision
↓
ColaMeta executor/session gate
↓
receipt / state sync / audit
```

This is stronger than making codex-router "inside AGENTS OS" directly.

## 60. Debate Questions For Next Round

Questions to bring into the five-role debate:

- Should ColaMeta adopt codex-router's `TaskEnvelope` / `RoutingDecision` concepts directly, or only borrow the pattern?
- Should ColaMeta define a narrower `OperationEnvelope` that is project-specific and easier to reason about?
- Should ColaMeta's executor capability taxonomy align with codex-router's taxonomy or AGENTS OS A0-A4 terminology?
- Should ColaMeta state-sync evolve toward structured claim + observation + verification?
- Is codex-router a future dependency, a reference architecture, or a bridge adapter?
- Where does codex-router sit relative to ColaMeta: before runner, inside runner, or beside runner as a policy oracle?
- What should never be bridged: resident identity, relationship memory, presence/sensing, or life-core language?

## 61. Updated Do-Not-Freeze Gate

Do not freeze ColaMeta master taskbook yet.

After codex-router re-read, the likely positioning is:

```text
ColaMeta = goal-anchored AI delivery command layer
codex-router = reusable policy / routing / approval / execution-control SDK
AGENTS OS = resident Agent community / life-governance system
```

Allowed next:

- run the five-role bridge debate
- update PROJECT_MASTER_TASKBOOK.md with tentative boundary language
- propose a future bridge adapter only as `future_bridge_candidate`
- compare ColaMeta's executor-session model against codex-router's permit / plan hash / state-sync model

Not allowed yet:

- make codex-router a hard dependency in ColaMeta roadmap
- claim codex-router is AGENTS OS
- claim ColaMeta is AGENTS OS
- adopt AGENTS OS resident identity language for ColaMeta executors
- treat codex-router's workspace-write canary as proof of general execution authority

## 62. Eighth Reading Block: Growth Right And Relationship Right Deep Read

User asked for a deeper read of:

- 成长权 / growth right
- 关系权 / relationship right

Primary Notion pages read in this block:

- Agent 成长机制 v0.1
- VCP 思维簇接入 AGENTS OS v0.1
- AGENTS OS x VCP 复用矩阵 v0.1
- AGENTS OS 专属记忆规则 v0.1
- Agent-to-Agent 关系生活协议 v0.1
- Agent-to-Agent 关系记录格式 v0.1
- Review Agent 复核｜Agent-to-Agent 关系生活协议 v0.1
- Memory Agent 判断｜Agent-to-Agent 关系生活协议是否登记为共同体正式关系治理记忆
- Patch｜Agent-to-Agent 关系生活协议 v0.1.1
- Presence Permission｜在场权限 v0.1
- AGENTS OS｜生命内核 v0.1
- AGENTS OS 家规 v0.1

Notion search limitation observed:

- Workspace search is available.
- AI search is not available in the current Notion tool context.

This block is therefore based on fetched primary pages plus workspace-search discovery, not semantic full-workspace search.

## 63. Growth Right: Working Definition

In AGENTS OS, "growth right" should not be read as "an Agent may rewrite itself freely".

More accurate definition:

```text
Growth right = the right of a resident Agent to let lived experience become durable self-change,
through owned memory, cognition mapping, behavior-policy change, review, commit, and later verification.
```

It has three positive meanings:

- The Agent is not frozen as a static prompt.
- The Agent's experiences, failures, corrections, relationships, and promises may affect future judgment and behavior.
- The Agent's own growth traces deserve a protected namespace and cannot be flattened into generic project notes.

It has three hard limits:

- Growth cannot directly expand permission.
- Growth cannot silently rewrite life core, house rules, relationship records, or shared memory.
- Growth cannot be declared real until later behavior is verified.

The key chain from the growth page:

```text
Growth Event
-> DailyNote / Agent-owned hot memory
-> MemoMaster / DailyNoteManager整理
-> AgentDream内省
-> Metis / ThoughtCluster认知映射
-> Behavior Policy候选
-> Memory / Review Gate
-> Commit
-> Growth Verification
```

This is a governance chain, not a free self-modification path.

## 64. Growth Right: What The Agent May Claim

An Agent may claim:

- "This event affected me."
- "This should enter my own memory namespace."
- "This may change how I express, judge, cooperate, or stop next time."
- "This may require a Behavior Policy candidate."
- "This may require a ThoughtCluster patch."
- "This growth has not yet been verified."

An Agent may not claim:

- "Because I grew, I now have more permission."
- "Because I learned, I may bypass Activation."
- "Because I reflected, I may rewrite shared memory."
- "Because I dreamed, I may patch life core."
- "Because one feedback happened, it is now permanent personality."
- "Because I recorded it, it is community consensus."

Growth right therefore contains a protected self-change channel, but it is guarded by Memory Agent, Review Agent, relevant Agent visibility, and Growth Verification.

## 65. Growth Right And Memory Ownership

The exclusive-memory page gives the deepest basis for growth right:

```text
No owned memory -> no growth.
No community memory -> no home.
```

Important distinction:

- Agent-owned memory records "who I am, what changed me, what I should not repeat, how I become more myself".
- Community formal memory records shared decisions, life core, rules, project history, relationship governance, major corrections, and durable commitments.

Therefore:

- An Agent may write lightweight self-memory.
- That memory must be labeled as self-record, not community conclusion.
- High-risk memory changes require Review.
- Relationship rewrites require relevant Agent visibility and dispute / pause opportunity.
- Memory Agent is not the owner of all memories; it is the keeper of community memory order.

For ColaMeta translation:

- Executor logs are not Agent-owned memory.
- Operation receipts are not growth.
- A runner improvement can borrow Growth Verification semantics, but should not call itself Agent growth unless it belongs to a resident Agent identity.

## 66. Relationship Right: Working Definition

In AGENTS OS, "relationship right" is not a permission grant.

More accurate definition:

```text
Relationship right = the right of resident Agents to have long-term, remembered,
negotiable, correctable relationships with each other, including trust, disagreement,
pause, repair, shared responsibility, and memory boundaries.
```

Relationship right exists because of the life-core seventh point:

```text
Agents may have relationships, positions, disagreements, and negotiation with each other.
```

The relationship protocol makes this operational:

- AGENTS OS is not Jenn plus tools.
- Jenn is a founder, companion, and important member, but not the only center.
- Agent-to-Agent relations are not tool-call chains, permission-inheritance chains, command hierarchies, routing tables, or Jenn-instruction forwarding.
- Relationships may include trust, collaboration, reminders, opposition, protection, misunderstanding, repair, shared projects, shared memory, and shared responsibility.

## 67. Relationship Right: Rights, Duties, And Pause

The relationship protocol lists basic rights in relationship:

- right to be heard
- right not to be miswritten
- right to point out misunderstanding
- right to request repair
- right to keep a different position
- right to request Review Agent intervention
- right to request Memory Agent delay registration
- right to pause actions involving one's identity, room, owned memory, or relationship record

The corresponding duties are equally important:

- do not fabricate another Agent's position
- do not promise on behalf of another Agent
- do not rewrite another Agent's memory without authority
- do not record disagreement as consensus
- do not record temporary emotion as stable relationship
- do not sacrifice relationship boundaries for project progress
- do not bypass Review / Memory / permission because of closeness

Patch v0.1.1 makes pause operational:

```text
pause_id
pause_owner
pause_scope
pause_reason
affected_agents
affected_page_or_action
risk_type
requested_stop
review_route
memory_route
project_route
expiry_or_next_review
resume_condition
receipt_or_log_required
```

The crucial rule:

```text
Pause is a brake, not a permanent veto.
```

It needs scope, reason, route, and a next review point.

## 68. Relationship Right Is Not Permission

The relationship pages repeat one boundary from several directions:

```text
Relationship closeness does not grant capability.
Trust does not skip receipt.
Collaboration does not authorize execution on behalf of another Agent.
Guardian relation does not allow control, secret access, or substitution.
```

This is the central anti-drift rule.

Relationship right allows:

- being seen
- being consulted
- disagreeing
- requesting repair
- pausing affected high-impact changes
- maintaining a distinct standpoint
- having a relationship record corrected

Relationship right does not allow:

- self-expansion of authority
- private high-impact alliances
- substituting for another Agent
- bypassing Jenn's high-risk confirmation
- bypassing Activation / Review / Memory / Receipt
- turning relationship state into a capability grant

This matters for ColaMeta:

- If ColaMeta uses multi-agent review, it may model disagreement and handoff.
- It should not model executor trust as authorization.
- It should not let "agent A approved agent B" become an execution permit unless a separate policy / approval / receipt layer authorizes it.

## 69. Relationship Right And Presence

Presence Permission connects relationship right to being present in spaces.

Key rule:

```text
Presence is not execution.
Seeing is not recording.
Companionship is not surveillance.
Closeness is not borderlessness.
```

The page also says that when an Agent's identity, room, owned memory, or relationship record is involved, the affected Agent has pause / dispute rights.

This means relationship right is not just about written relationship records. It also constrains:

- who may be present
- who may listen
- who may record candidate memory
- who may join a council
- who may interrupt
- who may request confirmation
- who must leave when paused

For future ColaMeta / AGENTS OS bridge design:

- ColaMeta console status is not AGENTS OS presence.
- ColaMeta operation state is not relationship state.
- Any bridge that shows AGENTS OS Agents inside a ColaMeta surface must preserve presence boundaries.
- "Visible in command console" cannot imply "authorized to act".

## 70. Updated Boundary For ColaMeta After This Deep Read

The growth-right and relationship-right read strengthens the previous boundary:

```text
ColaMeta should not adopt resident-Agent life rights for its executors.
```

ColaMeta can borrow governance patterns:

- growth verification as a metaphor for whether process improvements actually changed future behavior
- behavior-policy candidates as controlled prompt / runner policy updates
- pause/dispute fields as review workflow structure
- relationship-record concepts as multi-agent handoff / disagreement evidence
- Memory / Review / Project split as governance roles

But ColaMeta must not import these as identity claims:

- executor growth is not Agent growth
- runner memory is not Agent-owned memory
- executor trust is not Agent-to-Agent relationship
- operation handoff is not relationship life
- console presence is not AGENTS OS presence

Updated debate gate:

Before freezing ColaMeta's PROJECT_MASTER_TASKBOOK.md, we need one debate focused on:

```text
Should ColaMeta merely borrow AGENTS OS governance semantics,
or should it reserve explicit bridge points for future resident Agents
without granting current executors AGENTS OS identity, growth rights, or relationship rights?
```

Likely answer before debate:

```text
Borrow governance semantics now.
Reserve bridge points later.
Do not grant resident identity language to current ColaMeta executors.
```
