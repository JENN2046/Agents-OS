# Decision Record: AGENTS OS Resident Operating Architecture v0.1

```yaml
decision_id: decision-agents-os-resident-operating-architecture-2026-07-12
date: 2026-07-12
status: accepted
implementation_status: not_started
owner: Jenn
agent_steward: Nobao
scope:
  - AGENTS OS runtime topology
  - resident coordination model
  - Goal health and critical work frontier
  - Goal Task Run Validation Event semantics
  - canonical global task ledger
  - state and event persistence
  - Goal and Task execution budget
  - Goal and Task execution deadline
  - Task priority
  - Task Dependency v0.1
  - Task Scheduling Architecture Boundary v0.1
  - ArtifactRef boundary
  - VCPToolBox integration boundary
  - Rust implementation boundary
acceptance_basis: Jenn selected and accepted the recorded choices one by one in the current architecture discussion
amendments:
  - date: 2026-07-12
    decision: Goal lifecycle, outcome, authority, and task-count plan progress accepted by Jenn
  - date: 2026-07-12
    decision: Task State Transition Contract v0.4-final accepted by Jenn
  - date: 2026-07-12
    decision: Layered required Validation set composition and authority accepted by Jenn
  - date: 2026-07-12
    decision: ValidationRequirement and Validation attempt relationship accepted by Jenn
  - date: 2026-07-12
    decision: Required Validation set commitment-boundary freeze rule accepted by Jenn
  - date: 2026-07-12
    decision: Frozen Validation Set Extension Contract accepted by Jenn
  - date: 2026-07-12
    decision: Requirement Waiver Contract accepted by Jenn
  - date: 2026-07-12
    decision: Required Validation Revalidation and Evidence Reuse Contract accepted by Jenn
  - date: 2026-07-12
    decision: ArtifactRef boundary accepted by Jenn; Artifact is not a sixth core object in v0.1
  - date: 2026-07-12
    decision: GoalHealthProjection, Critical Work Frontier, and HARD_BLOCKER v0.1 accepted by Jenn
  - date: 2026-07-12
    decision: Goal Health RISK v0.1 reason-code registry accepted by Jenn
  - date: 2026-07-12
    decision: RISK v0.1 Validation remediation gap corrected by Jenn
  - date: 2026-07-12
    decision: Goal Health EVIDENCE_GAP v0.1 reason-code registry accepted by Jenn
  - date: 2026-07-12
    decision: Goal and Task Budget v0.1 accepted by Jenn
  - date: 2026-07-12
    decision: Goal and Task Deadline v0.1 accepted by Jenn after final consistency review
  - date: 2026-07-12
    decision: Task Priority v0.1 accepted by Jenn after two consistency reviews
  - date: 2026-07-12
    decision: Task Dependency v0.1 accepted by Jenn after three-stage design review and final freeze review
  - date: 2026-07-12
    decision: Task Dependency sync adds CURRENT_FRONTIER_REQUIRED_COMPLETION_ASSURANCE_INVALIDATED to HARD_BLOCKER v0.1
  - date: 2026-07-12
    decision: Task Dependency sync adds COMPLETION_ASSURANCE_RESOLUTION_ACTIVE to RISK v0.1
  - date: 2026-07-13
    decision: Jenn selected and accepted Task Scheduling Architecture Boundary v0.1 using rolling time planning, current-fact event-driven task selection, and atomic execution admission
  - date: 2026-07-13
    decision: Scheduling, Time, and Capacity v0.1 proposed-final package recorded for Jenn review; no contained v0.1 contract or Resource Scheduling v0.2 design accepted by this record update
pending_amendments:
  - amendment_id: scheduling-time-capacity-v0.1-r1
    date: 2026-07-13
    status: pending_Jenn_freeze_decision
    source: control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
    effect_before_acceptance: none
    acceptance_unit:
      id: R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE
      members:
        - source document Sections 3-9
        - this document Section 2.1 pending R1 amendment overlay
      partial_freeze_permitted: false
    scope:
      - Calendar host start-authority semantics
      - Deadline hard new start-authority cutoff terminology and fence
      - RUN_ATTEMPTS evidence-based settlement
      - immutable complete RUN_ATTEMPTS Budget authority binding
      - complete Task and Goal RUN_ATTEMPTS late-positive correction set
      - dependency assurance in time projections
      - pure resource-unconstrained SchedulePlan
      - TaskForecastBoundary constraint-owner partition
      - semantic forecast fingerprints independent of read and storage identity
      - virtual-service fairness baseline
      - deterministic fairness transition and batch-endpoint reduction
      - zero Duration and timing observation policy
    implementation_authorized: false
runtime_execution_authorized: false
runtime_source_change_authorized: false
active_config_access_authorized: false
secret_access_authorized: false
permission_expansion_granted: false
```

## 1. 一句话决议

**AGENTS OS 以后常驻在 VCPToolBox 这具后端身体里，由 Nobao 作为唯一常驻主协调者；
VCPChat 是桌面主前端，VCPMobile 是移动端。VCPToolBox 内新增独立边界的
`AGENTSOSResident`，由它持有全局任务总账和确定性身份连续性。**

实现上采用：

```text
VCPToolBox 内唯一 JavaScript hybridservice Resident
+ Rust N-API 确定性内核
+ SQLite 单一权威写入
+ Current State / Event / Inbox / Outbox 同事务协调
```

不采用：

```text
Workbench 成为执行内核
codex-router 吞并 AGENTS OS 全部 runtime 和 state
另建一个与 VCPToolBox 平行的常驻控制系统
默认再启动一个 Rust sidecar 进程
让 VCPChat 或 VCPMobile 直接访问总账数据库
把一次 Run 成功误当成 Task 或 Goal 完成
```

## 2. 本文件的权威范围

本文件是当前讨论后，AGENTS OS 未来运作方式的综合架构基线。

它负责记录：

```text
已经由 Jenn 明确选定的架构
各对象的权威关系
已经冻结的状态集合和完成规则
VCP 三端的正式角色
Rust 与 JavaScript 的实现边界
哪些内容仍未决定
```

它不替代以下专项决议：

```text
control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md
control-plane/registry/decisions/2026-07-03-three-lane-execution-model-v0.1.md
```

前者继续负责高权限、TaskPermit、设备身份和 host enforcement 的专项原则；后者继续负责
Green / Yellow / Red 执行分区。

如果旧计划、报告或草案与本文件的已确定架构冲突：

```text
旧文件中的源码事实仍可作为证据
旧文件中的冲突建议由本决议取代
```

### 2.1 Pending R1 amendment overlay

The following synchronization is a reviewable amendment proposal, not an accepted change. Before Jenn explicitly
freezes R1, the already accepted clauses below remain historical authority and this overlay grants no runtime,
database, reducer, migration, or activation permission.

The proposed scheduling contracts and this overlay form one acceptance unit. If Jenn freezes the complete
`R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`, the following terms replace their older parent wording as one atomic amendment:

```yaml
acceptance_unit:
  id: R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE
  members:
    - control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md Sections 3-9
    - this document Section 2.1 pending R1 amendment overlay
  partial_freeze_permitted: false
  member_amendment_keeps_complete_bundle_pending: true
  effect_before_Jenn_freeze: none

pending_parent_replacements:
  normative_pending_source: this_Section_2_1_only
  rendered_mirrors_outside_Section_2_1_are_authoritative_before_freeze: false
  historical_accepted_wording_remains_authoritative_before_freeze: true
  effective_transition: all_targets_replace_together_only_when_Jenn_freezes_complete_bundle
  targets:
    - Section_10_5_create_run_candidate_and_commitment_mapping
    - Section_10_15_1_atomic_admission_commitment_wording
    - Section_10_15_4_effectful_Validation_and_atomic_persistence_wording
    - Section_11_Run_commitment_provenance
    - Section_14_create_run_Outbox_atomicity_wording
    - Section_23_pending_R1_acceptance_tests
    - Appendix_pending_r1_scheduling_amendment

create_run_work_subject_and_commitment:
  TASK_EXECUTION:
    no_current_candidate: NONE_EXPECTED
    current_candidate: authorized_REJECT_FOR_NEW_EXECUTION_then_clear_exact_candidate_result_and_completion_support
    commitment: allocate_new_EXECUTION_ADMISSION_only_when_absent_or_inputs_changed_else_reuse_current_immutable_unchanged
  EFFECTFUL_VALIDATION:
    candidate_disposition: PRESERVE_FOR_EFFECTFUL_VALIDATION
    requires: exact_current_result_candidate_commitment_frozen_Validation_Set_Requirement_revision_validator_execution_contract
    candidate_mutation_or_supersession_for_executor_need: forbidden
    commitment: reuse_exact_current_CANDIDATE_ADOPTION_unchanged
  newly_allocated_commitment: same_transaction_as_Run_reservations_Event_permit_Outbox
  reused_commitment: preexisting_byte_identical_no_write_on_success_or_rollback

run_commitment_provenance:
  TASK_EXECUTION: exact_EXECUTION_ADMISSION_TaskCommitmentSnapshot
  EFFECTFUL_VALIDATION: exact_current_CANDIDATE_ADOPTION_TaskCommitmentSnapshot
  one_exact_phase_correct_snapshot_per_Run: required

calendar_and_deadline:
  canonical_schema_mappings:
    HARD_NEW_EXECUTION_CUTOFF: HARD_NEW_START_AUTHORITY_CUTOFF
    effective_new_execution_cutoff: effective_new_start_authority_cutoff
    effective_new_execution_cutoff_utc_ms: effective_new_start_authority_cutoff_utc_ms
    HardNewExecutionCutoffReached: HardNewStartAuthorityCutoffReached
    DEADLINE_NEW_EXECUTION_PROHIBITED: DEADLINE_NEW_START_AUTHORITY_PROHIBITED
    start_not_after_utc_ms: start_authority_commit_before_utc_ms
    checks_start_not_after: checks_start_authority_commit_before
  canonical_deadline_kind: HARD_NEW_START_AUTHORITY_CUTOFF
  effective_boundary_field: effective_new_start_authority_cutoff
  effective_boundary_value_field: effective_new_start_authority_cutoff_utc_ms
  deadline_snapshot_effective_boundary_field: effective_new_start_authority_cutoff_utc_ms
  reached_event: HardNewStartAuthorityCutoffReached
  task_blocker_reason: DEADLINE_NEW_START_AUTHORITY_PROHIBITED
  task_permit_field: start_authority_commit_before_utc_ms
  host_capability_field: checks_start_authority_commit_before
  calendar_purpose: NEW_START_AUTHORITY_ALLOWED
  canonical_fence: calendar_start_authority_fence
  effective_boundary_formula: earliest_current_HARD_NEW_START_AUTHORITY_CUTOFF_or_HARD_ACTIVE_EXECUTION_STOP_CUTOFF_across_self_and_current_ancestors
  cutoff_controls: Rust_commit_of_one_time_host_start_authority
  cutoff_does_not_claim: remote_physical_process_started
  start_authority_compliance_evidence:
    fact: HostWorkAcceptanceFact_ACCEPTED
    requirement: committed_by_Rust_before_effective_new_start_authority_cutoff_utc_ms
    binds: run_permit_execution_epoch_host_fence_and_current_calendar_start_authority_fence
    host_timestamp_can_grant_retroactive_compliance: false
  physical_start_evidence:
    fact: HostWorkStartDispositionFact_STARTED_or_stronger_authenticated_execution_fact
    requirement: binds_exact_HostWorkAcceptanceFact_and_same_execution_epoch
    HostWorkAcceptanceFact_alone_is_sufficient: false
  legacy_run_start_evidence_split:
    old_field: run_start_evidence
    authority_compliance_field: start_authority_compliance_evidence
    physical_start_field: physical_start_evidence
    one_field_may_not_represent_both_facts: true
  accepted_before_cutoff:
    run_state: LEASED
    authority: bounded_nonrenewable_one_time_start_authority
    physical_start_evidence: still_required
  start_authority_expires_at: min_host_start_grace_allocation_lease_when_enforced_active_stop_cutoff_when_present
  ordinary_calendar_close_revokes_committed_authority: false
  active_stop_or_dynamic_fence_may_revoke: true

run_attempts:
  create_run: reserve_every_applicable_Task_and_Goal_envelope
  authority_binding:
    record: RunAttemptsBudgetAuthorityBinding
    formal_core_object: false
    cardinality: exactly_one_per_Run_and_execution_epoch
    created_with_reservations: same_Rust_SQLite_transaction
    canonical_members: complete_sorted_Task_and_Goal_RUN_ATTEMPTS_envelope_revision_reservation_set
    member_fields: budget_scope_scope_id_envelope_id_envelope_revision_reservation_id_dimension_units
    member_units: 1
    immutable_member_set_fingerprint: required
    immutable_authority_binding_fingerprint: required
    references_commitment_snapshot: exact_immutable_task_commitment_snapshot_id
    commitment_snapshot_reverse_Run_specific_binding: forbidden
    cross_bound_to: Run_every_member_reservation_TaskPermit_admission_Event_Outbox
    later_expected_set_source: immutable_authority_binding_only
    surviving_rows_or_current_envelopes_may_infer_expected_set: false
    missing_duplicate_or_corrupt_binding: INDETERMINATE_no_partial_compensation_Task_fenced
    fail_closed_scope_basis: immutable_expected_scopes_union_observed_conflicting_scopes_or_independently_reconstructable_cross_refs
  HostWorkAcceptanceFact_ACCEPTED: complete_bound_set_remains_RESERVED
  HostWorkStartDispositionFact_STARTED_or_stronger_positive_execution_evidence: complete_bound_set_SETTLED_exactly_once
  authoritative_no_execution_proof: complete_bound_set_RELEASED
  possible_execution_or_conflicting_evidence: complete_unsettled_bound_set_UNKNOWN_full_occupancy_no_auto_retry
  allocation_or_transport_ack_is_attempt: false
  late_positive_execution_after_RELEASED:
    trigger: authenticated_same_execution_epoch_STARTED_or_stronger_positive_execution_evidence
    applicable_reservation_set:
      scopes: every_bound_Task_and_Goal_RUN_ATTEMPTS_reservation_for_the_original_Run
      source: exact_immutable_RunAttemptsBudgetAuthorityBinding_only
      completeness: required
      ordering: canonical_sorted
      set_fingerprint: required
      correction_atomicity: all_or_nothing_in_one_correction_transaction
      missing_duplicate_or_conflicting_member: BUDGET_CORRECTION_SET_INDETERMINATE
      indeterminate_disposition: fail_closed_no_partial_compensation
    transition: every_applicable_RELEASED_reservation_to_SETTLED_exactly_once
    correction_event: RunAttemptsReleaseContradictedByPositiveExecution
    accounting: settle_each_applicable_actual_RUN_ATTEMPTS_unit_without_partial_compensation_or_double_counting
    immutable_history: preserve_prior_release_event_and_late_execution_fact
    prior_run_terminal_state: REJECTED_unchanged_never_reopened_as_UNKNOWN_or_nonterminal
    prior_no_execution_assurance: CONTRADICTED
    run_and_effect_history: reconcile_to_actual_observed_execution_through_independent_late_effect_reconciliation
    reconciliation_uses_existing_objects_only: true
    correction_transaction:
      no_new_run_fence: raised_atomically
      successor_scan: every_later_execution_epoch_and_current_candidate_result_validation_binding
      one_nonterminal_execution_run_invariant: preserved
      multiple_nonterminal_successors: ledger_integrity_conflict_fence_stop_query_all
    successor_disposition:
      QUEUED_proven_never_dispatched: supersede_permit_and_outbox_then_reject
      QUEUED_dispatch_uncertain: UNKNOWN_query_and_reconciliation
      LEASED_RUNNING_WAITING: fence_pause_stop_query_reconcile
      terminal_successor: preserve_terminal_state_and_quarantine_candidate_result_evidence_validation_completion
      no_successor: retain_fence_and_reconcile_historical_execution_and_effects
    task_projection:
      late_STARTED_physical_execution_possibly_active:
        applicability: nonterminal_Task_without_current_UNKNOWN_or_current_nonterminal_successor_determining_state
        state: ACTIVE
        activity_kind: COORDINATING
        coordination_subtype: LATE_EFFECT_RECONCILIATION
        required_context: reconciliation_id_owner_next_action_activity_deadline
        narrow_priority_exception: overrides_ordinary_unsafe_effect_BLOCKED_projection_only_while_addressable_stop_query_is_unfinished
        does_not_override: current_Run_UNKNOWN_forces_Task_BLOCKED
      physical_execution_stopped_effect_influence_unresolved:
        nonterminal_state: BLOCKED
        context: existing_unresolved_effect_blocking_context
      already_terminal_Task:
        state: unchanged
        automatic_reopen: forbidden
        assurance: challenge_affected_completion_candidate_result_validation_and_Goal_dependency_support
    new_formal_Task_state: false
    capacity: quarantine_and_reconcile_under_existing_contradictory_receipt_rules
    new_run: forbidden
    automatic_retry: forbidden
    replay:
      accounting_identity: run_execution_epoch_authority_binding_expected_and_observed_sets_outcome_and_complete_correction_or_gap_set
      correction_fingerprint_excludes_itself: true
      evidence_identity: run_execution_epoch_and_positive_fact
      later_stronger_positive_fact: enrich_existing_reconciliation_without_second_compensation

planning:
  SchedulePlanProjection: pure_resource_unconstrained_time_forecast
  ordering_capacity_and_admission_observation: separate_surfaces
  completion_boundary_requires: effective_current_or_pinned_CONFIRMED_assurance
  Task_DONE_alone_means_zero_duration: false
  assurance_only_change_stales_time_projection: true
  TaskForecastBoundarySnapshot:
    formal_core_object: false
    authority: read_only_Rust_reducer_input
    forecast_constraint_owner_partition:
      complete_current_constraint_refs: required
      owners:
        - dependency_geometry
        - active_duration_geometry
        - active_work_release
        - completion_release
      membership: exact_kind_compatible_disjoint_and_complete
      coverage: COMPLETE_or_INDETERMINATE
      partition_fingerprint: required
      duplicate_missing_or_basis_mismatch: INDETERMINATE_no_aggregate_TASK_DONE
    dependency_owned_active_hold: DELEGATED_TO_DEPENDENCY_GEOMETRY
    zero_active_work_rule: active_duration_owner_empty_and_zero_basis_refs_exactly_match_completion_release_owner
    projection_binding: SchedulePlan_and_TimeCriticalPath_bind_the_same_partition_fingerprint
    fingerprint_semantics:
      includes: Task_lifecycle_completion_state_phase_canonical_constraint_refs_owner_sets_Dependency_and_Duration_bases_release_zero_alignment_evidence_policy
      excludes: row_snapshot_projection_IDs_aggregate_CAS_versions_read_or_reducer_watermarks_materialization_timestamps
      source_Event_sequence_allowed_only_when: explicitly_named_immutable_domain_source_or_current_pointer
      source_current_pointer_event_sequence_is_read_watermark: false
      rebuild_with_same_semantics_at_new_read_barrier: byte_identical_fingerprint

fairness:
  accounting: checked_u128_virtual_service_passes
  new_or_reactivated_account_origin: at_least_current_system_virtual_service
  zero_based_catch_up_burst: forbidden
  service_charge_boundary: successful_local_admission
  service_charge_is_RUN_ATTEMPTS: false
  exact_rules_source: scheduling_time_capacity_R1_Sections_3_through_9
  assignment_transition:
    flags: fixed_ordinal_derived_from_exact_before_and_after_inputs
    composite_floor: checked_max_of_every_applicable_existing_source_and_target_floor
    same_account_work_request_revision: preserve_continuous_lineage_floor
    complete_input_set_and_fingerprint: required
  lineage_head_transition:
    change_flags: canonical_fixed_ordinal_including_HEAD_COMPARATOR_INPUT_CHANGED
    trigger_flags: canonical_complete_set
    materialization_context: separate_from_semantic_trigger_flags
    transition_identity_binds_flags: true
  simultaneous_boundary_batch:
    identity: boundary_batch_id_and_fingerprint
    reducer_semantics: compare_complete_pre_semantic_set_to_final_post_semantic_set
    per_lineage_intermediate_Event_changes_episode_or_system_state: false
    swap_cycle_or_many_to_one_may_fabricate_EMPTY: false
  canonical_input_sets:
    Focus_Expedite_Deadline_urgency_refs_and_set_fingerprints: complete
    Focus_and_Expedite_reduction: OR_over_complete_current_set
    Deadline_urgency_driver: canonical_from_complete_current_set
  backoff:
    rejection_reason_codes: fixed_registry_order_complete_set
    reason_set_fingerprint: required
    same_reason_identity: complete_reason_set_not_caller_selected_scalar

duration:
  zero_triple: allowed_only_with_ZERO_ACTIVE_WORK_PROVEN_and_positive_evidence
  compatible_cumulative_PARTIAL_observation_stales_base_estimate: false
  estimate_range_exhausted: remaining_projection_UNAVAILABLE_until_explicit_new_estimate

resource_scheduling_v0_2:
  source: control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
  included_in_v0_1_acceptance: false
  status: preserved_design_draft_not_proposed_for_acceptance_with_deferred_known_gaps
```

Until acceptance, every exact schema and validation rule is reviewed from the R1 source document; this summary cannot
be used as a substitute gate. No Section or overlay fragment in this revision can be frozen separately. After acceptance,
the mappings above replace the old names together: the old names remain
readable historical aliases only and may not be emitted by new canonical records. The replacement does not rewrite old
Events, infer physical start from host acceptance, or grant a new execution authority.

## 3. 正式运行拓扑

```text
Jenn
  -> 通过 VCPChat / VCPMobile 与 AGENTS OS 交互

VCPToolBox
  -> AGENTS OS 后端身体与常驻宿主
  -> 模型、工具、插件、记忆智能和执行能力宿主
  -> 托管 AGENTSOSResident 生命周期

VCPChat
  -> 桌面主前端
  -> 人类交互面
  -> 受治理的桌面执行宿主

VCPMobile
  -> 移动端
  -> 通知、在场、批准和受限设备能力节点
  -> 不成为全局事实权威
```

其他系统的定位：

```text
Codex Desktop / Codex CLI / ColaMeta executor
  -> 按任务召回的实际执行宿主或工作流执行器

codex-router
  -> 可复用的治理、协议、许可、调度与恢复能力候选
  -> 不是 AGENTS OS 全部 runtime 的当然所有者

Workbench
  -> 操作入口、流程外壳、兼容适配和只读投影视图
  -> 不是 canonical task ledger
```

AGENTS OS 是这些部件之上的共同体和全局目标，不被任何单个仓库吞并。

## 4. VCPToolBox 集成边界

采用：

> AGENTS OS 住在 VCPToolBox 内部，随 VCPToolBox 常驻，但保持独立模块边界。

具体含义：

```text
AGENTSOSResident 由 VCPToolBox 启动、检查、关闭和恢复
优先使用现有 service / hybridservice / plugin / route / lifecycle 扩展点
业务状态机、总账和 Nobao 身份连续性不散落进 VCPToolBox 核心文件
只有权限拦截等无法从模块完成的能力，才修改 VCPToolBox 核心
核心修改必须是最小、通用、可维护的 hook
核心 hook 不包含 AGENTS OS 具体业务规则
```

必须避免：

```text
重写 VCPToolBox
让 AGENTS OS 业务逻辑侵入 server.js 和 Plugin.js 各处
为了方便而复制第二套插件系统、模型系统或记忆系统
把 upstream checkout 变成无法继续跟踪的私有大改 fork
```

运行时住在 VCPToolBox 内部，不等于所有源码必须与 VCPToolBox core 混在一起。最终源码
放置和发布方式仍需在实施前单独冻结。

## 5. Nobao 与 Agent 层级

正式采用：

```text
Nobao
  -> 唯一常驻主协调者
  -> Jenn 面前的统一长期身份
  -> 理解目标、维护上下文、组织任务、召回 Agent、处理冲突和最终汇总

Long-Lived Domain Agent
  -> 重要领域可以拥有长期逻辑 Agent
  -> 在领域章程和已分配目标内维护专业连续性
  -> 不取代 Nobao 的全局协调权

Temporary Worker
  -> 为具体 Task / Run 临时创建或召回
  -> 完成限定执行后释放
  -> 不因执行一次任务获得长期身份或全局权力
```

### 5.1 身份连续性

所有身份连续性由 VCPToolBox 内的确定性常驻服务维持，而不是依赖一个永不结束的模型
会话。

```text
Nobao 是逻辑身份
模型调用是 Nobao 使用的思考引擎
AGENTSOSResident 保存稳定身份、对象 ID、状态、关系、权限、恢复点和事件
```

确定性服务负责：

```text
身份 ID
对象关系
状态和版本
权限与 lease
幂等与恢复
可核验历史
```

Nobao 负责：

```text
理解 Jenn 真正想要什么
澄清模糊目标
判断优先级
拆解和组织工作
选择 Agent / Worker
处理领域冲突
形成最终结论
```

## 6. Goal 生命周期、权威与计划进度

正式采用：

```text
Jenn
  -> 掌握顶层 Goal 的最终变更权、结束权和放弃权

Nobao
  -> 在 Jenn 已确认的顶层 Goal 下，自主创建和维护 Subgoal
  -> 判断 Subgoal 的拆分、顺序、暂停、恢复和完成建议
```

当 Jenn 对顶层 Goal 的表达仍然模糊时：

```text
Nobao 不擅自把模糊愿望伪装成已经确定的目标
Nobao 与 Jenn 继续讨论
逐渐明确目标边界、成功标准、限制条件和不做什么
在澄清过程中保留 Goal 候选，而不是启动无限扩张的执行
```

这里的“候选”不增加 `CANDIDATE` 状态。原始想法先作为 Event 进入系统；只要已经值得作为
Goal 讨论，就建立 `Goal(CLARIFYING)`。

### 6.1 生命周期与结果分离

正式采用两个字段，不再把过程状态和最终结果混在同一个枚举中：

```yaml
goal_lifecycle:
  - CLARIFYING
  - READY
  - ACTIVE
  - PAUSED
  - COMPLETION_REVIEW
  - CLOSED

goal_outcome:
  - null
  - ACHIEVED
  - ABANDONED
  - UNACHIEVABLE
  - SUPERSEDED
```

生命周期含义：

| lifecycle | 含义 |
|---|---|
| `CLARIFYING` | Jenn 已表达意图，但目标、边界或成功标准仍不够清楚 |
| `READY` | Goal 已经讲清楚并值得做，但还没有正式推进 |
| `ACTIVE` | 正在通过 Subgoal 和 Task 推进 |
| `PAUSED` | Goal 仍有效，但暂时不推进；必须记录原因和恢复条件 |
| `COMPLETION_REVIEW` | Nobao 判断成功标准可能已经满足，等待最终确认 |
| `CLOSED` | Goal 生命周期已经结束，必须同时具有非空 outcome |

结果含义：

| outcome | 含义 |
|---|---|
| `ACHIEVED` | Goal 自己的成功标准已经满足 |
| `ABANDONED` | 最终权威决定不再追求该 Goal |
| `UNACHIEVABLE` | 证据证明在当前约束下无法满足成功标准 |
| `SUPERSEDED` | 被一个更准确或更新的 Goal 取代 |

强制不变量：

```text
lifecycle != CLOSED  -> outcome 必须为 null
lifecycle == CLOSED  -> outcome 必须为 ACHIEVED / ABANDONED / UNACHIEVABLE / SUPERSEDED
Goal 不使用 FAILED 作为最终结果
```

### 6.2 核心转移

已冻结的基础转移：

```text
CLARIFYING -> READY
READY -> ACTIVE
READY -> PAUSED
ACTIVE -> PAUSED
PAUSED -> ACTIVE
ACTIVE -> COMPLETION_REVIEW
COMPLETION_REVIEW -> ACTIVE
COMPLETION_REVIEW -> CLOSED + ACHIEVED
任意非 CLOSED -> CLOSED + ABANDONED / UNACHIEVABLE / SUPERSEDED
```

`CLOSED` 不得自动重新开启。顶层 Goal 只有 Jenn 可以明确要求重新开启；重新开启的目标状态
必须根据当时目标是否仍清晰决定，并追加 Event，不得删除原关闭历史。

### 6.3 顶层 Goal 与 Subgoal 权限

顶层 Goal：

```text
Jenn
  -> 最终修改成功标准
  -> CLOSED
  -> 选择最终 outcome
  -> 明确重新开启

Nobao
  -> 维护 CLARIFYING 讨论
  -> 在目标已经清楚后整理为 READY
  -> 根据真实推进切换 ACTIVE / PAUSED
  -> 提交 COMPLETION_REVIEW
  -> 不能自行关闭顶层 Goal
```

如果 Jenn 一开始已经把目标、边界和成功标准表达得足够清楚，Nobao 可以直接登记为
`READY`，不需要制造额外形式确认。

Subgoal：

```text
Nobao
  -> 可以创建
  -> 可以在已允许生命周期状态间推进
  -> 可以设置 outcome 并关闭
  -> 不能通过 Subgoal 改写顶层 Goal 的方向或成功标准
```

### 6.4 BLOCKED 不是 Goal 生命周期

某个 Task 被卡住，不表示 Goal 生命周期已经改变。

```yaml
goal_lifecycle: ACTIVE
goal_health: BLOCKED
```

`BLOCKED` 属于只读 `GoalHealthProjection`，不加入 Goal lifecycle。任何调用方都不得直接
`set_goal_health`；Rust core 只能根据当前 canonical facts、当前 plan revision 和本节规则生成投影。
Goal health 描述“Goal 是否仍有完成路径”，不是“是否还有任何零散工作可做”。因此 Goal health 为
`BLOCKED` 时，非关键 Task 仍可继续推进，但当前条件下 Goal 无法到达成功。

#### 6.4.1 两层 GoalHealthProjection

正式采用：

```yaml
GoalHealthProjection:
  applicability: NOT_ACTIVE | ACTIVE
  assessment: null | HEALTHY | ATTENTION_REQUIRED | BLOCKED | INSUFFICIENT_EVIDENCE
  reason_codes: []
  critical_frontier_status: UNAVAILABLE | PARTIAL | COMPLETE
  based_on:
    plan_revision:
    event_sequence:
    assessed_at:
```

`assessment` 只在 `applicability = ACTIVE` 时计算。非 `ACTIVE` Goal 一律为 `NOT_ACTIVE`，不把
`CLARIFYING`、`READY`、`PAUSED`、`COMPLETION_REVIEW` 或 `CLOSED` 伪装成健康问题。

确定性判定顺序：

```text
Goal lifecycle != ACTIVE
  -> applicability = NOT_ACTIVE；assessment 不计算

存在当前 HARD_BLOCKER，且 critical_frontier_status != COMPLETE
  -> ATTENTION_REQUIRED
  -> CONFIRMED_CRITICAL_BLOCKER + FRONTIER_INCOMPLETE

成功标准、路线结构或当前事实不足
  -> INSUFFICIENT_EVIDENCE

critical_frontier_status == COMPLETE
且任一必要 success criterion 的全部可替代路线被阻断
  -> BLOCKED

critical_frontier_status == COMPLETE
且存在风险、可修复关键问题或某些路线受阻但仍有替代路线
  -> ATTENTION_REQUIRED

其余
  -> HEALTHY
```

强制不变量：

```text
HEALTHY / BLOCKED -> critical_frontier_status 必须为 COMPLETE
BLOCKED -> 必须能列出被阻断的必要 success criterion 和全部受阻路线
ATTENTION_REQUIRED / INSUFFICIENT_EVIDENCE -> reason_codes 不得为空
assessment != HEALTHY -> 必须能定位受影响的 success criterion / frontier member
```

#### 6.4.2 Critical Work Frontier 与路线表达式

v0.1 使用 `Critical Work Frontier`，不伪造依赖 duration、deadline 和资源估算的传统单一
`critical_path`。每个未满足的必要 Goal success criterion 使用以下最小路线表达式：

```text
criterion
  -> ANY_OF route_groups

route_group
  -> ALL_OF frontier_members
```

计算规则：

```text
一个 ALL_OF route_group 中任一必要 member 有活动 HARD_BLOCKER
  -> 该 route_group 被阻断

一个 criterion 的全部 ANY_OF route_groups 都被阻断
  -> 该必要 criterion 被阻断

任一必要 criterion 被阻断
  -> GoalHealthProjection = BLOCKED
```

一个路线被阻断但仍有替代 route group 时，Goal 只能是 `ATTENTION_REQUIRED`，不能进入
`BLOCKED`。

前沿完整度：

```text
UNAVAILABLE
  -> 无法建立 success criterion 与路线关系

PARTIAL
  -> 仍有未覆盖的必要 criterion、未声明的 ALL_OF / ANY_OF，或事实不够当前

COMPLETE
  -> 每个未满足的必要 criterion 都有明确路线表达式
  -> 每个 frontier member 都绑定当前、可核对的 canonical fact
```

Critical Work Frontier 是 projection 输入与计划语义，不增加正式领域对象。frontier member 的当前
canonical fact 必须覆盖该 Task 自身以及其 completion commitment 所固定的 dependency ancestry。
`INVALIDATED` 是当前、可核对的完整负面事实：frontier 仍可为 `COMPLETE`，但该 member 所在路线被
HARD_BLOCKER 截断。`INDETERMINATE` 一定表示事实不足；`CHALLENGED` 只有在准确 challenge facts 与正式
impact-review 或 remediation resolution path 都 current 时才可作为“完整但待处理”的风险事实，否则同样令 frontier
`PARTIAL / UNAVAILABLE`，不得伪装成证据完整。
`Task Scheduling Architecture Boundary v0.1` 已冻结以下分工：`SchedulePlanProjection` 与
`TimeCriticalPathProjection` 都是无执行权的只读派生结果，不能替代 Critical Work Frontier，也不能改变
`plan_progress`、GoalHealthProjection 或 Goal closure。时间投影不存在、过期或尚缺已接受输入时，只影响
时间投影自身的可用性；不得令已经能够从逻辑事实完整建立的 Critical Work Frontier 变成
`PARTIAL / UNAVAILABLE`。

预测可能迟到不等于 Section 10.12 的 Deadline 已经到期，也不得冒充
`SOFT_DEADLINE_TARGET_MISSED`、HARD_BLOCKER 或 Task lifecycle fact。传统时间关键路径的精确算法仍须等待
`Duration Estimate v0.1`、`Calendar v0.1` 和时间关键路径专项合同冻结；考虑 capacity 竞争的
`ResourceScheduleProjection` 继续延后。Deadline、Budget 与已冻结的 Task Dependency 只提供约束和前置关系，
不足以自行推导传统时间关键路径。

#### 6.4.3 HARD_BLOCKER v0.1 白名单

`HARD_BLOCKER` 只证明某个当前 frontier member 或 route group 不能继续；Goal 是否 `BLOCKED`
仍由 Section 6.4.2 的完整路线表达式计算。v0.1 只允许：

```text
UNRECONCILED_UNKNOWN_EFFECT_ON_CURRENT_FRONTIER
  -> 当前 generation 的前沿 Run 存在 UNKNOWN 或未核对副作用

CURRENT_FRONTIER_HARD_TASK_BLOCKER
  -> 当前前沿 Task 为 BLOCKED
  -> blocker_context 由 Rust policy 白名单分类为 HARD

CURRENT_FRONTIER_REQUIRED_TASK_TERMINAL
  -> 当前计划必要 Task 为 FAILED / CANCELLED
  -> 该 Task 是当前 ALL_OF route group 的必要 member

CURRENT_FRONTIER_REQUIRED_COMPLETION_ASSURANCE_INVALIDATED
  -> 当前计划必要 Task 可以仍为 DONE，但其准确 completion ref 已不可逆 INVALIDATED
  -> 该 completion ref 是当前 ALL_OF route group 的必要 member support

REQUIRED_AUTHORIZATION_ROUTE_DENIED_OR_REVOKED
  -> 当前必要路线的授权被明确拒绝或撤销

REQUIRED_POLICY_ROUTE_DENIED
  -> 当前 policy bundle 明确禁止必要路线

REQUIRED_EXTERNAL_DEPENDENCY_CURRENTLY_UNAVAILABLE
  -> 当前有效的权威事实证明必要外部依赖不可用
```

同一个 frontier member 若已有更具体代码，不得再重复生成
`CURRENT_FRONTIER_HARD_TASK_BLOCKER`。Agent 不得自行填写 `blocker_class = HARD`，也不得扩展
reason code；code 与 class 的映射由版本化 Rust policy registry 决定。

明确不得直接产生 `HARD_BLOCKER`：

```text
授权 PENDING、尚未申请或等待 Jenn 决策
普通 WAITING / PAUSED / READY
一次或多次 Validation FAILED
Validation ERROR / INCONCLUSIVE
completion assurance 仅为 CHALLENGED / INDETERMINATE
尚未选择 host 或尚未申请 permit
没有回复、没有查询或状态未知
无证据的 Agent 判断
裸 ArtifactRef
```

这些事实只有符合 Section 6.4.5 白名单时才进入 `RISK`；其余按 Section 6.4.6 进入
`EVIDENCE_GAP`，或先形成合规的结构化 Task blocker。
`NO_COMPLIANT_EXECUTION_PATH_CONFIRMED` 不进入 v0.1；必须等 host capability inventory 与 permit
路径合同冻结后再评估。

#### 6.4.4 Reason 实例、当前性与失效

Goal health reason 是投影条目，不增加正式领域对象。每个硬阻塞实例至少绑定：

```yaml
reason_registry_version:
reason_code:
affected_success_criterion:
affected_route_group:
affected_frontier_member:
goal_spec_revision:
plan_revision:
affected_task_lifecycle_generation: optional
affected_task_completion_epoch: optional
affected_result_revision: optional
affected_completion_ref_id: optional
affected_assurance_version: optional
source_fact_refs:
source_event_sequence:
observed_at:
valid_until: optional
review_at: optional
currentness_mode:
resolution_condition:
```

`source_fact_refs` 必须指向当前 Task / Run / Validation / permit / host Receipt 或受权事实 Event。
`ArtifactRef` 只能作为这些正式事实的低披露证据附件，不能单独证明硬阻塞。

`currentness_mode` 只允许：

```text
UNTIL_RECONCILED
UNTIL_CANONICAL_STATE_CHANGE
UNTIL_PLAN_REVISION
UNTIL_POLICY_REVISION
TIME_BOUND
```

`TIME_BOUND` 事实必须具有 `valid_until` 或 `review_at`。事实到期后不得直接消失并让 Goal 变为
`HEALTHY`；在取得新事实前应转成 `EVIDENCE_GAP` 并重新计算健康。

#### 6.4.5 RISK v0.1 白名单

`RISK` 表示当前仍有至少一条可行完成路线，但已有事实表明路线正在变差、需要修复，或者 Goal 可能无法
按现有计划满足成功标准。`RISK` 只能产生 `ATTENTION_REQUIRED`，无论数量多少都不得自动升级为
`HARD_BLOCKER` 或 `BLOCKED`；只有出现 Section 6.4.3 白名单中的新 canonical fact，路线才算被截断。

v0.1 只允许：

```text
ALTERNATIVE_ROUTE_REDUCED
  -> 某个必要 criterion 的部分 route_group 已被 HARD_BLOCKER 截断
  -> 至少仍有一条替代 route_group 可行

COMPLETION_ASSURANCE_RESOLUTION_ACTIVE
  -> 当前 frontier member 的 completion assurance 为 CHALLENGED，但不是 INVALIDATED / INDETERMINATE
  -> 已有精确绑定 challenge set 的 linked DependencyImpactReview Task，或 REMEDIATION_REQUIRED 对应 remediation Task
  -> resolution_status 为 PLANNED / ACTIVE / EVIDENCE_READY，且 owner、next review 与 resolution condition current
  -> resolution route 未被 HARD_BLOCKER 截断；resolution Task 为 DONE 时只可对应 EVIDENCE_READY
  -> 若关联 UNKNOWN、resolution route 终结或事实不再 current，则结束本 RISK 并按 HARD_BLOCKER / EVIDENCE_GAP 重算

REQUIRED_VALIDATION_FAILURE_REMEDIATION_REQUIRED
  -> 当前必要 Validation 已 FAILED
  -> remediation_status: MISSING | PLANNED | ACTIVE
  -> 直到出现当前有效 PASSED、Requirement revision 被合法替换或 Task 合法终结才结束
  -> ERROR / INCONCLUSIVE 不进入此项

GOAL_CRITERIA_UNMET_AT_PLAN_100
  -> 当前 plan_progress 已到 100%
  -> 一个或多个 Goal success criteria 仍未满足

CRITICAL_FRONTIER_PROGRESS_SUSPENDED
  -> 当前关键前沿 Task 已 PAUSED
  -> 或存在未收口的 PAUSE / CANCEL Control Intent
  -> 尚未形成 terminal Task 或 HARD_BLOCKER

SOFT_BUDGET_TARGET_EXCEEDED
  -> 当前适用 SOFT_TARGET 的 consumed + reserved 已超过 limit
  -> 不阻止 Run，不自动升级为 HARD_BLOCKER

SOFT_DEADLINE_TARGET_MISSED
  -> 当前 Deadline revision 的 SOFT_COMPLETION_TARGET 已到期
  -> Task 尚未在到期前进入 DONE，或 Goal 尚未在到期前以 ACHIEVED 进入 CLOSED
  -> 只有影响当前 Goal 成功标准或必要路线时才进入 Goal Health
  -> 不阻止 Run，不自动升级为 HARD_BLOCKER

EVIDENCE_BACKED_DOMAIN_RISK_ACTIVE
  -> Nobao 或获授权 Domain Agent 提交有证据、作用范围和复查时间的领域风险
```

明确不得直接产生 `RISK`：

```text
普通 WAITING
一次 Run FAILED
Agent 空闲
进度主观看起来慢
尚未申请 permit 或尚未选择 host
没有 deadline 合同时的延期判断
没有 budget 合同时的成本判断
没有证据的直觉判断
```

权限：

```text
Rust core
  -> 根据 canonical facts 自动导出除 EVIDENCE_BACKED_DOMAIN_RISK_ACTIVE 外的所有白名单项

Nobao
  -> 可以提交和解决 EVIDENCE_BACKED_DOMAIN_RISK_ACTIVE

Domain Agent
  -> 可以在授权领域内提出风险
  -> 只有 scope policy 明确允许，或 Nobao 接受后才成为 ACTIVE

Worker
  -> 只能提交事实，不能声明 Goal risk
```

风险实例沿用 Section 6.4.4 的 plan、generation、source、currentness 和 resolution 字段，并至少增加：

```yaml
risk_code:
affected_success_criterion:
affected_route_group: optional
affected_frontier_member: optional
source_fact_refs:
raised_by:
accepted_by: optional
goal_spec_revision:
plan_revision:
affected_task_lifecycle_generation: optional
affected_task_completion_epoch: optional
affected_result_revision: optional
observed_at:
review_at:
expires_at: optional
resolution_condition:
mitigation_task_ref: optional
resolution_task_ref: optional
resolution_task_lifecycle_generation: optional
resolution_task_spec_revision: optional
resolution_status: optional_PLANNED_ACTIVE_EVIDENCE_READY
challenge_set_fingerprint: optional
```

`review_at` 必填。达到 `review_at` 或 `expires_at` 后仍未复查的风险，不得直接消失并让 Goal 变为
`HEALTHY`；在取得新事实前转入 `EVIDENCE_GAP`。风险对应路线真正被截断时，结束该 RISK，并根据新
canonical fact 产生对应 `HARD_BLOCKER`。风险被证伪或 mitigation 完成时追加解决 Event，不删除历史。

#### 6.4.6 EVIDENCE_GAP v0.1 白名单

`EVIDENCE_GAP` 表示系统缺少、无法验证或无法统一解释某个判断 Goal 健康所必需的当前事实。它不是
风险、失败或阻塞；无论持续多久、数量多少，都不得自动升级为 `RISK`、`HARD_BLOCKER` 或
`BLOCKED`。

`FRONTIER_INCOMPLETE` 是派生汇总代码：

```text
critical_frontier_status == UNAVAILABLE | PARTIAL
  -> FRONTIER_INCOMPLETE
```

它不能单独存在，必须同时列出至少一个未被抑制的具体根原因。v0.1 根原因只允许：

```text
GOAL_SUCCESS_CRITERIA_INCOMPLETE
  -> ACTIVE Goal 的成功标准缺失、未版本化、相互冲突或不足以判断达成

CURRENT_PLAN_UNAVAILABLE
  -> ACTIVE Goal 没有当前有效 plan_revision
  -> 或当前计划无法解析出有效叶子 Task

CRITERION_ROUTE_MAPPING_INCOMPLETE
  -> 必要 criterion 没有完整 ANY_OF route_groups
  -> route_group 没有完整 ALL_OF frontier_members
  -> 或 member 归属无法证明

CURRENT_REQUIRED_FACT_MISSING
  -> projection contract 明确要求某个事实现在必须存在
  -> 已跨过 fact_required_at_event
  -> 当前 plan / lifecycle / result revision 仍匹配
  -> 没有合法 PENDING / WAITING 解释其缺失

CANONICAL_FACT_RECONCILIATION_REQUIRED
  -> 同一权威链中的 Event、Receipt 或 projection input 无法一致归约
  -> 必须绑定 conflicting_fact_refs

REQUIRED_VALIDATION_RESULT_INCONCLUSIVE
  -> 当前 health 判断依赖的 required Validation 为 ERROR 或 INCONCLUSIVE
  -> PENDING 不进入此项
  -> 关联 Run 存在 UNKNOWN 时改用 HARD_BLOCKER，不生成此 gap

REQUIRED_EVIDENCE_UNAVAILABLE_OR_UNVERIFIABLE
  -> 必需 ArtifactRef 无法解析、digest 不匹配、访问不足或完整性无法证明
  -> 若正式 Validation 已因此进入 INCONCLUSIVE，只保留 Validation gap

TIME_BOUND_HEALTH_FACT_STALE
  -> HARD_BLOCKER、RISK 或外部可用性事实超过 valid_until / review_at
  -> 尚未取得新的当前事实

DEADLINE_TIME_AUTHORITY_UNCERTAIN
  -> 当前 Deadline 判断所需的 Rust wall-clock 无法读取、明显倒退或无法通过当前 time policy 校验
  -> 不得猜测 Deadline 已到期或尚未到期
  -> Hard Deadline 适用时由独立 fail-closed time gate 阻止新增执行授权

BUDGET_ACCOUNTING_UNRECONCILED
  -> usage receipt、price schedule 或 reservation settlement 无法核对
  -> 外部 effect 本身 UNKNOWN 时由 HARD_BLOCKER 取代，不生成此 gap

HEALTH_POLICY_VERSION_UNAVAILABLE
  -> health policy、reason registry 或 reducer contract 版本缺失、不受支持或无法校验
  -> 由 Rust 内置 fail-closed fallback 识别，不依赖缺失的外部 registry
```

`CURRENT_REQUIRED_FACT_MISSING` 不能把尚未到产生阶段的未来结果伪装成 gap，必须额外绑定：

```text
expected_fact_contract_version
fact_required_at_event
expected_source
```

抑制顺序：

```text
HEALTH_POLICY_VERSION_UNAVAILABLE
  -> 使用内置 fallback projection
  -> 抑制所有依赖该 policy 的细分 gap

GOAL_SUCCESS_CRITERIA_INCOMPLETE
  -> 抑制依赖这些 criteria 的 route mapping gap

CURRENT_PLAN_UNAVAILABLE
  -> 抑制该计划下的 route mapping 和 member fact gap

DEADLINE_TIME_AUTHORITY_UNCERTAIN
  -> 抑制依赖当前时间判断的 Deadline miss 与 DeadlineReached 细分结论
  -> 不抑制独立存在的 UNKNOWN、Control Intent 或 host capability 事实

REQUIRED_VALIDATION_RESULT_INCONCLUSIVE
  -> 关联 UNKNOWN Run 时由具体 HARD_BLOCKER 取代
  -> 已表达证据不可用原因时，抑制重复的 evidence gap
```

policy fallback 必须由 Rust binary 内置，最小输出固定为：

```yaml
applicability: ACTIVE
assessment: INSUFFICIENT_EVIDENCE
critical_frontier_status: UNAVAILABLE
reason_codes:
  - HEALTH_POLICY_VERSION_UNAVAILABLE
  - FRONTIER_INCOMPLETE
```

权限：

```text
Rust core
  -> 唯一 projection derivation authority
  -> 根据 canonical facts 导出和清除 EVIDENCE_GAP

Jenn / Nobao / Domain Agent / Worker
  -> 可以补充事实、修订计划、修正成功标准或提交证据
  -> 不得直接声明 evidence sufficient
  -> 不得直接 dismiss EVIDENCE_GAP 或 set Goal health
```

Gap 是投影条目，不是新的正式对象，也不是可修改的 canonical record。真正写入 ledger 的是补充事实、
reconciliation Event、Goal / plan revision 和证据更新。

每个 gap 实例至少绑定：

```yaml
gap_registry_version:
gap_code:
affected_success_criterion: optional
affected_route_group: optional
affected_frontier_member: optional
expected_fact_contract_version: optional
fact_required_at_event: optional
expected_source: optional
last_known_fact_ref: optional
conflicting_fact_refs: optional
goal_spec_revision:
plan_revision:
affected_task_lifecycle_generation: optional
affected_task_completion_epoch: optional
affected_result_revision: optional
affected_completion_ref_id: optional
affected_assurance_version: optional
detected_event_sequence:
detected_at:
resolution_condition:
```

归约与解决：

```text
FRONTIER_INCOMPLETE + 至少一个具体 gap + 没有已确认 HARD_BLOCKER
  -> INSUFFICIENT_EVIDENCE

FRONTIER_INCOMPLETE + 已确认 HARD_BLOCKER
  -> ATTENTION_REQUIRED
  -> CONFIRMED_CRITICAL_BLOCKER + FRONTIER_INCOMPLETE

新 canonical fact 修复 gap
  -> projection 重新计算并保留历史事实

gap 后来被证明为实际阻塞
  -> 只有匹配 HARD_BLOCKER 白名单时才生成 blocker
```

明确禁止：

```text
gap 持续很久或数量很多 -> 自动变成 RISK / BLOCKED
Jenn 接受未知 -> 把 health 标为 HEALTHY
缺少尚未到期的未来结果 -> 生成 gap
裸 ArtifactRef -> 直接证明 gap 已解决
人工删除 gap -> 绕过 projection
```

本节冻结两层 projection、Critical Work Frontier、`HARD_BLOCKER v0.1`、`RISK v0.1` 和
`EVIDENCE_GAP v0.1`。

### 6.5 计划完成进度

Goal 和 Subgoal 增加 `plan_progress`，但它的正式名称和语义是“当前计划完成进度”，不是
“Goal 成功程度”。

```text
plan_progress = 当前计划版本中 DONE 的叶子 Task 数 / 当前计划版本的叶子 Task 总数
```

所有计划 Task 初始等权，不按预计时间、难度或 token 数加权。

```yaml
plan_progress:
  type: derived_projection
  basis: equal_weight_current_plan_leaf_tasks
  only_DONE_counts: true
  plan_revision_required: true
  may_decrease_after_revision: true
  reaches_100_does_not_close_goal: true
```

Task 状态计数规则：

```yaml
READY: 0
ACTIVE: 0
WAITING: 0
PAUSED: 0
BLOCKED: 0
VERIFYING: 0
DONE: 1
FAILED: 0
CANCELLED: 0
```

只有 `DONE` 增加已完成数。`VERIFYING` 尚未通过全部 required Validation，不能提前计入。

如果一个计划 Task 被继续拆成 Child Task：

```text
父 Task 不再作为当前计划计数单元
只计算当前计划中的叶子 Child Task
父 Task 和 Child Task 不得同时计数
```

如果当前计划没有正式 Task：

```text
plan_progress = null
显示“尚未形成计划”
不显示伪造的 0%
```

### 6.6 Plan Revision

Nobao 可以根据新事实修改实现计划，但每次增加、移除、替换或继续拆分计划 Task，都必须
形成新的 `plan_revision` 并追加 Event：

```yaml
plan_revision: integer
reason: required
added_task_ids: []
removed_task_ids: []
replaced_task_ids: []
created_by: Nobao
```

因此百分比可以诚实下降。例如：

```text
revision 3: 8 / 10 = 80%
revision 4: 8 / 12 = 66%
```

这表示对真实工作量的认识发生变化，不得通过冻结或平滑百分比掩盖。

`CANCELLED` Task 不会自动从分母消失。必须通过新 plan revision 说明它为什么不再需要、
是否被替代，以及删除是否影响 Goal 成功标准。

```text
只改变执行方法或任务拆法
  -> Nobao 可以自主修订计划

降低或改变顶层 Goal 成功标准
  -> 属于 Jenn 的顶层 Goal 最终变更权
```

### 6.7 100% 的含义

```text
plan_progress == 100%
不等于
Goal outcome == ACHIEVED
```

正确流程：

```text
全部当前计划叶子 Task DONE
  -> plan_progress = 100%
  -> Nobao 重新检查 Goal success criteria
  -> 满足时进入 COMPLETION_REVIEW
  -> 顶层 Goal 由 Jenn 决定 CLOSED + ACHIEVED
```

如果计划已经 100%，但 Goal 成功标准仍未满足：

```text
Goal 保持 ACTIVE
Nobao 创建新的 plan_revision
```

推荐投影和显示：

```yaml
plan_progress:
  revision: 4
  completed: 8
  total: 12
  percent: 66
  active: 2
  verifying: 1
  blocked: 1
  calculated_from: current_leaf_tasks
```

```text
计划进度 66% · 8/12
进行中 2 · 验证中 1 · 阻塞 1
```

百分比向下取整，只有 `completed == total` 时才能显示 `100%`。Plan revision 和 Task
membership 是 canonical fact；百分比和各状态数量由只读 projection 计算，不作为独立
可随意写入的事实。

#### 6.7.1 Dependency assurance 与 Goal closure

`plan_progress` 只回答当前计划叶子 Task 做完了多少，不回答这些完成事实现在是否仍足以支持
Goal 成功标准。Task Dependency v0.1 因此不修改 Section 6.5 的计数规则，而是增加按当前
Goal、plan revision 和 membership 计算的只读支持投影：

```yaml
GoalPlanMemberSupportProjection:
  goal_id:
  plan_revision:
  membership_id:
  task_id:
  completion_ref_id:
  assessment: SUPPORTED | REVIEW_REQUIRED | UNSUPPORTED | INSUFFICIENT_EVIDENCE
  based_on_completion_assurance_version:
  based_on_event_sequence:
```

`GoalClosureEvidenceChallenge` 是从 completion assurance、plan membership 和 Event 导出的稳定 challenge
reference，不是第六个对象，也不是可直接写入的状态。它至少绑定 Goal / plan / membership、准确
completion ref、assurance version、root reason refs 和 detected Event sequence；解决状态只能由 underlying
canonical facts 重算。它让已关闭 Goal 的历史支持问题保持可见，但 closure gate 始终直接同步读取 canonical
assurance，不信任该 projection。

```yaml
GoalClosureEvidenceChallengeProjection:
  challenge_ref:
  goal_id:
  goal_spec_revision:
  plan_revision:
  membership_id:
  completion_ref_id:
  assurance_version:
  assessment: CHALLENGED | INVALIDATED | INDETERMINATE
  root_reason_refs: []
  status: OPEN | RESOLVED | SUPERSEDED_BY_EXPLICIT_PLAN
  detected_event_sequence:
  resolved_or_superseded_event_sequence: optional
```

Rust 按上述 canonical tuple 生成稳定 `challenge_ref`。underlying assurance 不再非 `CONFIRMED` 时进入
`RESOLVED`；新 plan 只有显式记录旧 challenge、replacement route / evidence 与 authority 后才可进入
`SUPERSEDED_BY_EXPLICIT_PLAN`。Projection rebuild 只能重放这些事实，不能自动清除、接受或创建执行权。

允许并必须诚实表达：

```text
plan_progress = 100%
Goal completion eligibility = false
```

`CLOSED + ACHIEVED` 使用同步 Rust gate，而不是信任异步投影。当前选择的 route group 必须完整，
每个必要 member 必须为 `DONE`，对应 completion ref 和全部 pinned dependency ancestry 必须为
`CONFIRMED`，且不存在未解决的 `GoalClosureEvidenceChallenge`。

```text
CHALLENGED + current impact-review 或 remediation resolution path
  -> closure eligibility = false
  -> member support = REVIEW_REQUIRED
  -> COMPLETION_ASSURANCE_RESOLUTION_ACTIVE
  -> ATTENTION_REQUIRED

CHALLENGED 但没有 current resolution path，或 INDETERMINATE
  -> closure eligibility = false
  -> member support 为 REVIEW_REQUIRED / INSUFFICIENT_EVIDENCE
  -> ACTIVE Goal 只能按准确根因映射既有 EVIDENCE_GAP：
     CANONICAL_FACT_RECONCILIATION_REQUIRED、CURRENT_REQUIRED_FACT_MISSING、
     REQUIRED_EVIDENCE_UNAVAILABLE_OR_UNVERIFIABLE 或 HEALTH_POLICY_VERSION_UNAVAILABLE
  -> 不允许生成一个未在白名单中的泛化 dependency reason

INVALIDATED
  -> 产生 CURRENT_FRONTIER_REQUIRED_COMPLETION_ASSURANCE_INVALIDATED
  -> 当前 route group 被截断

替代路线仍存在
  -> ALTERNATIVE_ROUTE_REDUCED
  -> ATTENTION_REQUIRED

该必要 criterion 的全部路线都被白名单 HARD_BLOCKER 截断
  -> BLOCKED
```

Plan revision 可以建立真正的新路线，但不能通过删除 edge 或 member 静默清除旧挑战。新路线必须明确
记录 `superseded_challenge_refs`、replacement route、replacement completion evidence、success criteria
revision 和 authority。降低或改变顶层 Goal 成功标准仍由 Jenn 决定。

顶层 Goal 已经 `CLOSED + ACHIEVED` 后出现新 challenge，不自动 reopen 或修改 outcome；系统追加持续
可见的 closure evidence review，由 Jenn 决定。Subgoal 仍由 Nobao 在既定权限内处理。

## 7. 任务进入与创建权

正式采用 Nobao 控制的分层任务入口。

### 7.1 Jenn

Jenn 可以直接创建：

```text
顶层 Goal
顶层 Task
方向性、跨领域或 Jenn-only 决策对象
```

### 7.2 Nobao

Nobao 可以在已确认目标和权限范围内自主创建：

```text
顶层 Task
跨领域 Task
Subgoal
Child Task
澄清、验证、恢复和收尾 Task
```

Nobao 可以根据新事实重新排序、暂停、恢复或拆分 Task，但不能越过 Jenn 对顶层 Goal 的
最终权威。

### 7.3 Domain Agent

长期领域 Agent 可以：

```text
在已分配 Parent Task 下创建 Child Task
在领域章程允许范围内创建 Green Task
提出跨领域 Task Candidate
```

长期领域 Agent 不可以自行把跨领域候选升级为正式全局 Task。

### 7.4 Temporary Worker

Temporary Worker：

```text
不能创建正式全局 Task
可以回传 follow-up candidate、发现、风险和建议
```

### 7.5 Deterministic Automation

确定性自动化只可以从已登记的 Green Rule 创建正式 Task。任何自动派生必须具有：

```text
parent_task_id 或明确 domain charter
deduplication key
数量限制
深度限制
预算或时间限制
可追踪的创建原因
```

所有进入系统的重要输入先获得 Event ID。Event 不自动等于 Task。

## 8. Canonical Global Task Ledger

正式采用：

```text
VCPToolBox.AGENTSOSResident.GlobalTaskLedger
```

它是 AGENTS OS 全局任务生命周期的唯一权威写入者。

现有 VCPToolBox 部件的定位：

| 现有部件 | 正式角色 | 不再被视为什么 |
|---|---|---|
| `VCPTaskAssistant` | 调度和任务派发适配器 | canonical global ledger |
| `routes/taskScheduler.js` | 定时触发适配器 | Goal / Task 生命周期权威 |
| `AgentAssistant` | Agent 通讯与执行适配器 | durable Run recovery system |
| Dashboard / Workbench | 只读投影和操作入口 | 状态写入权威 |

采用：

```text
Single Authority Per Fact Class
+ One Canonical Global Task Ledger
+ Derived Read-Only Projections
```

这不表示所有子系统状态都必须塞进同一数据库。它表示同一种事实只能有一个权威写入者。

## 9. 正式领域对象

已冻结的核心对象：

```yaml
objects:
  - Goal
  - Task
  - Run
  - Validation
  - Event
```

完成规则：

```yaml
completion_rule:
  Run_success: does_not_complete_Task
  Validation_pass: may_complete_Task
  Tasks_completed: does_not_automatically_complete_Goal
  Goal_success_criteria_met: may_complete_Goal
```

大白话解释：

```text
Run 只说明某次尝试发生了什么
Validation 说明结果是否满足要求
Task 只有在全部必需 Validation 通过后才有资格 DONE
一组 Task 做完，不自动证明 Goal 已实现
Goal 是否成功，要重新检查 Goal 自己的成功标准
```

`TaskDependencySpecRevision`、`DependencySetSnapshot`、`PinnedDoneBinding`、
`TaskCommitmentSnapshot`、completion-reference assurance 和 fence 都是 Task-owned、Event-backed
合同记录或可重建投影，不增加第六个正式领域对象。它们的 canonical 写入仍属于 Task aggregate 与
Rust core；不能被 UI、host 或异步 projection 当作独立状态权威。

### 9.1 ArtifactRef 边界

`Artifact` 在 v0.1 **不是**第六个正式领域对象。核心对象仍严格保持 Goal、Task、Run、Validation、Event
五个。`ArtifactRef` 是可嵌入这些对象的不可变、受类型约束的引用值，不拥有独立 aggregate、状态机、
全局生命周期或由 GlobalTaskLedger 管理的权限表。

`ArtifactRef` 至少包含：

```text
artifact_id（存储方提供的 opaque stable handle）
artifact_kind
content_digest + algorithm（内容可寻址时必填）
storage_authority
provenance / producer reference
sensitivity classification
retention_policy_ref
```

`artifact_id` 和任何 locator 都必须是低披露 handle；不得把绝对本机路径、登录 URL、签名 URL、token、
cookie、secret、原始私人记忆、完整 prompt、原始 provider response 或原始敏感日志写入 ledger、Event、
Outbox、Receipt 或模型上下文。内容本身永远留在其 `storage_authority`，例如 VCPToolBox 受治理存储、
对应 host 或未来独立 artifact service。

任何作为 Validation evidence、证据复用来源或 Task 完成守卫的 `ArtifactRef` 必须具有可校验的
`content_digest + algorithm`；只有 opaque handle 而没有完整性证明的引用，最多可用于非权威展示或定位，
不得单独支持 `PASSED` 或 `DONE`。

权威边界如下：

```text
artifact bytes、可用性、访问控制、保留和删除
  -> 对应 storage_authority

ArtifactRef 与 Goal / Task / Run / Validation / Event 的语义关联
  -> AGENTSOSResident Rust core
```

Rust core 只校验 ref 的结构、digest、分类和所属命令的权限，并把不可变 ref 与其拥有的领域事实同事务
写入；它不保存 blob、不解析敏感内容、不负责下载、不自行清理 artifact，也不因 ref 被引用而取得存储
访问权。storage_authority 也不能借由 artifact 更新直接改写 Task / Goal canonical state。

如果完成所需的证据 ArtifactRef 无法解析、digest 不匹配或访问条件不足，历史引用仍保留，但相关
Validation 不得伪造为 `PASSED`；应按其验证合同进入 `INCONCLUSIVE` 或让 Task 保持 / 进入 `BLOCKED`。

只有出现独立 artifact 生命周期、跨 Task 所有权、独立 ACL、保留 / legal hold、复制去重、跨设备同步或
独立检索治理等真实需求时，才可通过新的 ADR 评估是否将 Artifact 升格为正式对象。不得仅因引用字段增加
就自动升格。

## 10. Task 状态

### 10.1 正式状态集合

已冻结且不再增加过渡状态：

```text
READY
ACTIVE
WAITING
PAUSED
BLOCKED
VERIFYING
DONE
FAILED
CANCELLED
```

`NEW`、`PAUSING`、`CANCELLING` 不进入 Task 状态集合。创建是 Command；异步暂停和取消
由 Control Intent 表达。

状态分为：

```text
普通状态：READY / ACTIVE / WAITING / PAUSED / BLOCKED / VERIFYING
终态：DONE / FAILED / CANCELLED
```

### 10.2 Command、Fact 与唯一写入者

任何调用方都不得提交 `set_state` 或直接写总账。

```text
Command
  -> 表达 Jenn、Nobao、Domain Agent 或系统策略希望系统执行什么
  -> 使用 command_id、actor 和 expected_aggregate_version

Fact / Receipt
  -> 表达 host、Run、Validation 或外部副作用实际上发生了什么
  -> 使用稳定 source_id / receipt_id 和对象 epoch 去重
  -> 不要求匹配 Task 当前 aggregate_version

Rust reducer
  -> 接纳 Command 或 Fact
  -> 执行权限、CAS、幂等和机械不变量检查
  -> 确定性推导 Task 状态
  -> 在同一事务中更新 Current State、追加 Event、写入 Outbox
```

Rust core 是唯一状态写入者，但不是所有语义决定的主体。`FAILED` 等现实判断仍由有权限的
Jenn 或 Nobao 提交，Rust 只验证权限、证据结构、版本和机械安全条件。

### 10.3 Task 当前投影的版本边界

Task 当前投影至少区分：

```yaml
aggregate_version: optimistic_concurrency_and_task_projection_version
task_spec_revision: task_scope_and_completion_criteria
result_revision: current_candidate_result
validation_set_revision: current_validation_requirements
validation_set_snapshot_id: null_or_current_frozen_validation_membership
dependency_revision: current_dependency_spec
dependency_set_snapshot_id: null_or_current_frozen_dependency_membership_and_bindings
commitment_revision: current_task_commitment_revision
lifecycle_generation: increment_on_every_reopen
completion_epoch: increment_once_on_every_reopen_or_successful_dependency_recommit
execution_epoch: increment_on_every_new_run
phase_checkpoint: READY | ACTIVE | VERIFYING
activity_kind: null | COORDINATING | DISPATCHING | EXECUTING | RECONCILING_RESULT
active_control_intent_id: null_or_current_intent
active_dependency_fence_ref: null_or_current_fence
current_execution_commitment_id: null_or_current_execution_snapshot
current_candidate_commitment_id: null_or_current_candidate_snapshot
current_completion_commitment_id: null_or_current_completion_snapshot
unresolved_risk: false_by_default
last_event_id: current_projection_alignment
```

Run 和 Validation 使用各自的 object version。全局 Event sequence 与对象 version 分离。

旧 generation 或旧 epoch 的 Run、Validation、permit、intent、effect 和 receipt 可以作为历史
事实保留，但默认不得推进当前 Task。

### 10.4 普通状态转移矩阵

```text
READY      -> ACTIVE | WAITING | PAUSED | BLOCKED
ACTIVE     -> READY | WAITING | PAUSED | BLOCKED | VERIFYING
WAITING    -> READY | ACTIVE | PAUSED | BLOCKED
PAUSED     -> READY | ACTIVE | WAITING | BLOCKED | VERIFYING
BLOCKED    -> READY | ACTIVE | WAITING | PAUSED | VERIFYING
VERIFYING  -> READY | ACTIVE | PAUSED | BLOCKED
```

这些箭头是通过 reducer 守卫后可能形成的最终结果，不是调用方可以立即赋值的 API。

状态推导优先级：

```text
已正式终结
  -> 对应终态

存在 QUEUED / LEASED / RUNNING / WAITING 的执行 Run
  -> ACTIVE
  -> blocker、fence 或 Control Intent 仍照常记录和收口，但不得把真实活动执行伪装成 BLOCKED

存在 UNKNOWN、unsafe effect 或未解除 blocker
  -> BLOCKED

暂停请求已经安全完成
  -> PAUSED

wake condition 尚未满足
  -> WAITING

其他情况
  -> phase_checkpoint 对应的 READY / ACTIVE / VERIFYING
```

安全阻塞不得被 `PAUSED` 遮盖。已阻塞 Task 收到暂停请求时仍显示 `BLOCKED`；blocker 解除后，
如果暂停仍有效，才进入 `PAUSED`。

Context 最低不变量：

```text
WAITING 需要有效 waiting_context、wake condition 和 timeout policy
BLOCKED 需要有效 blocking_context、blocker、owner、解除条件和 next review
PAUSED 需要有效 pause_context、暂停原因和恢复条件
进入 READY / ACTIVE / VERIFYING 时必须同步 phase_checkpoint
Context resolve / clear 与状态变化在同一事务中完成
```

### 10.5 Task 与 Run 强不变量

v0.1 采用：

```text
一个 Task 同时最多一个非终态执行 Run
并行执行必须拆成子 Task
Run QUEUED / LEASED / RUNNING / WAITING 时，Task 必须是 ACTIVE
VERIFYING 和终态不得存在非终态执行 Run
Run UNKNOWN 强制 Task BLOCKED，并禁止新 Run 和自动重试
dependency fence 出现时，已有非终态 Run 的 Task 仍保持 ACTIVE，先 fence 新副作用并收口 Run
```

> **Pending R1 replacement mirror:** Section 2.1 proposes replacing the historical `create_run` candidate and
> commitment mapping below with work-subject-specific `TASK_EXECUTION` / `EFFECTFUL_VALIDATION` rules. This mirror has
> no effect before Jenn freezes the complete R1 bundle; the historical accepted wording below remains authoritative.

创建 Run 时，在同一事务中：

```text
确认没有非终态 Validation、活动 Control Intent、UNKNOWN 或未核对 effect
若存在 current candidate，create_run 必须显式提交 candidate_disposition = REJECT_FOR_NEW_EXECUTION、reason 与 authority
追加 CandidateRejectedByNewExecution
清除 result_revision、current_candidate_commitment_id 与 current_completion_commitment_id
旧 PASSED 因不再匹配 current result 而失去当前裁决权，历史仍保留
冻结或读取当前 Validation Set 与 Dependency Set
同步重算全部直接和传递 completion-reference assurance
创建或复用当前 DependencyClosureSnapshot
创建绑定 Validation Set、Dependency Set 与 closure 的当前 EXECUTION_ADMISSION TaskCommitmentSnapshot
增加 execution_epoch
创建绑定 execution commitment snapshot 的 Run QUEUED
签发绑定 epoch、dependency closure、assurance version 和 fence generation 的 permit
Task 进入或保持 ACTIVE
写入使用稳定 effect_id 的 Outbox dispatch intent
```

业务守卫失败时只提交 Inbox rejection 与必要的精确 fence / blocker，不得留下 Run、permit、reservation、
commitment pointer 或 Outbox 半成品；数据库 / CAS 技术冲突则整体 rollback / retry。Priority selection 只提供
选择依据，不能代替这里的同步依赖 gate。

没有 current candidate 时，`candidate_disposition` 必须为 `NONE_EXPECTED`；有 current candidate 时缺少
`REJECT_FOR_NEW_EXECUTION` 或权限一律拒绝。该 disposition 只能由 Jenn 或在既定 Goal / Task spec 内的
Nobao 决定；Domain Agent 只能 proposal，Worker / executor 不能拒绝验收对象。`VERIFYING -> ACTIVE` 只能走上述原子路径。v0.1 不允许为了
所谓 closure-only Run 保留旧 candidate；无副作用复查使用 Validation，需要执行的新工作拆成新 Run 或新 Task。
新 Run 后即使产出内容 digest 相同，也必须形成新的 result revision；旧证据只能按 Section 12.6 重新判断复用。
`create_run` 与 `complete_task` 使用同一 Task CAS，不能同时保留旧完成资格和新执行权。

`Run SUCCEEDED` 只说明一次尝试成功。只有当前候选结果已经形成、计划内执行已经结束、没有
未解决 Run 时，Nobao 或受权策略才可请求进入 `VERIFYING`。

`ACTIVE` 暂时没有 Run 时，必须具有 `activity_kind`、下一动作和 deadline；超时只能重新评估为
`READY`、`WAITING` 或 `BLOCKED`，不得自动 `FAILED`。

这里的 activity deadline 是当前协调活动的 timeout context，不自动等同于 Section 10.12 的
`DeadlineConstraint`。两者同时存在时分别判断，activity timeout 不能放宽 Hard Deadline。

### 10.6 Control Intent

Control Intent 是 Event-backed operational record，不增加正式领域对象数量。Task 投影只保存
当前活动 intent ID。

```yaml
intent:
  intent_id: stable_unique_id
  kind: PAUSE | CANCEL
  targets:
    runs: []
    validations: []
    permits: []
    effects: []
  status: REQUESTED | ACKNOWLEDGED | RECONCILING | COMPLETED | REJECTED | SUPERSEDED
```

强制规则：

```text
每个 Task 同时最多一个活动 intent
CANCEL 可以原子取代 PAUSE
PAUSE 不得覆盖 CANCEL
dependency fence 可以创建或复用 PAUSE intent，但不得取代既有 CANCEL
被取代 intent 的迟到回执仍须入账
活动 CANCEL 阻止普通转换、新 Run、完成和失败
暂停和取消必须先撤销许可、停止执行并核对副作用，再由 reducer 最终收口
最后一个相关回执到达时，reducer 在同一事务中尝试 finalize
崩溃窗口由可重入 finalizer 和启动恢复扫描补齐
```

### 10.7 终态命令

`DONE`：

```text
只能从 VERIFYING 产生
由 reducer 在所有完成守卫满足后确定性完成
Run SUCCEEDED 不得直接完成 Task
主观接受权必须建模为 HUMAN_ACCEPTANCE Validation
Requirement waiver 不等于 PASSED，且仍须服从 Section 12.5 的完成资格守卫
旧 PASSED 不因 reopen 或上下文变化自动继承；证据复用须服从 Section 12.6
current COMPLETION_ASSESSMENT snapshot 必须与 Task、result、Validation decision 和 dependency closure 一致
全部直接和传递 completion-reference assurance 必须为 CONFIRMED
```

`FAILED`：

```text
由 Nobao 或 Jenn 提交 determine_task_failure
一次 Run 失败、重试耗尽或 Validation ERROR 不能独立导致 FAILED
Rust core 不自行声称现实中已经“无路可走”
```

`CANCELLED`：

```text
正常路径必须先完成停止、permit fencing 和副作用 reconciliation
取消表示明确不再执行，不等于失败
```

所有终态默认要求：

```text
没有活动或未收口 Control Intent
没有当前 epoch 非终态 Run / Validation
所有执行与验证 permit 已撤销或 fenced
没有 UNKNOWN
没有未核对 completion-blocking effect
```

其中 current completion commitment 与 dependency closure 的同步通过只属于 `DONE` 守卫，不属于
`FAILED / CANCELLED` 守卫。失败和取消必须能够在 dependency 失效时完成安全收口；它们仍要求相应 actor
authority、停止确认、permit fencing、UNKNOWN 处理和副作用 reconciliation。

如果 `UNKNOWN` 永远无法核对，只有 Jenn 可以明确执行未决风险接受：

```yaml
command: accept_unresolved_effect_risk
allowed_terminal_state: CANCELLED_only
unresolved_risk: true
```

这不是把 UNKNOWN 伪装成确定结果。未知事实和风险记录必须永久保留，该 Task 永远不得由此转成
`DONE`。

### 10.8 Reopen

`reopen_task` 必须：

```text
增加 lifecycle_generation
增加 completion_epoch
增加 aggregate_version
隔离旧 permit、Run、Validation、intent、effect 和 receipt
默认不继承旧 PASSED Validation 的当前裁决权
```

从 `DONE` reopen 时还必须提交：

```yaml
prior_completion_disposition: PRESERVED | INVALIDATED | UNCERTAIN
reason:
basis_refs: []
```

该 disposition 只描述 source 的指定历史 completion ref，不替任何 consumer 判断最终影响。

```text
PRESERVED
  -> 必须具有正面 evidence 和 actor authority

INVALIDATED
  -> 必须具有证伪依据
  -> 对旧 completion ref 不可逆

UNCERTAIN
  -> 必须记录具体未知项
  -> 对旧 completion ref fail-closed
```

当前命令缺少 disposition 时拒绝；旧数据或恢复中无法取得 disposition 时按 `UNCERTAIN`。Disposition
与后续 resolution 都通过 append-only Event 表达，不原地改写历史。`PRESERVED` 只可能维持既有
PinnedDoneBinding 的支持，不让 reopened Task 继承自己的旧 Validation，也不允许新的 consumer 在 source
当前非 `DONE` 时绑定旧完成。

任何 reopen 都不得复活旧 permit、lease、Run、Validation、Outbox intent 或 Control Intent。新执行权必须
重新绑定当前 lifecycle generation、completion epoch、TaskCommitmentSnapshot、dependency fence generation
和 plan membership。

每次 reopen 在同一事务中先执行：

```text
current_execution_commitment_id = null
current_candidate_commitment_id = null
current_completion_commitment_id = null
validation_set_snapshot_id = null
dependency_set_snapshot_id = null
result_revision = null（除非本事务随后采用 REOPENED_PRIOR_RESULT）
```

采用 `REOPENED_PRIOR_RESULT` 时，本事务随后设置新的 current execution / candidate pointer，保持
current completion pointer 为 null，设置新冻结的 Validation / Dependency Set snapshot IDs，并把采用的历史
result revision 重新登记为本 epoch 的 current candidate。普通 READY / WAITING / PAUSED / BLOCKED reopen
则保持三个 commitment pointer 与两个 set snapshot pointer 为空，直到新的 commitment。

默认目标：

```text
DONE      -> VERIFYING
FAILED    -> READY / WAITING / PAUSED / BLOCKED
CANCELLED -> READY / WAITING / PAUSED / BLOCKED
```

Reopen 不直接进入 `ACTIVE`。激活必须另行创建 Run，或登记带下一动作和 activity deadline 的受限协调活动。
`DONE -> VERIFYING` 只有在同一 reopen 事务中重新冻结当前 Validation / Dependency、创建新
EXECUTION_ADMISSION snapshot，并以 `REOPENED_PRIOR_RESULT` 创建 current CANDIDATE_ADOPTION snapshot
时成立。无法安全采用旧 result 时不得留下无 candidate 的 `VERIFYING`；命令必须明确落到
`READY / WAITING / PAUSED / BLOCKED` 后再形成新 candidate。
旧证据只有在后续 Validation 合同允许、输入完全匹配且追加 `evidence_carry_forward` Event 时才能
跨 completion epoch 复用。

### 10.9 Actor authority 与进度

```text
Jenn
  -> 最高 Task 决定权
  -> 唯一未决风险接受权

Nobao
  -> 在既定 Goal 成功标准内管理 Task 生命周期
  -> 可以提交失败判断、取消和重开

Domain Agent
  -> 默认只能在授权范围内请求普通转换
  -> 默认不能决定失败、取消或重开

Worker / executor
  -> 只能提交 Run 事实

Validator
  -> 只能提交 Validation 事实

VCPChat / VCPMobile
  -> 只能发送命令和读取投影

Rust core
  -> 唯一写入者、reducer 和机械守卫
```

只有 `DONE` 计入 Goal 的 Task 计划进度。`FAILED` 和 `CANCELLED` 保持为 `0`，直到新的
`plan_revision` 明确替换或移除。涉及顶层 Goal 成功标准变化时仍由 Jenn 决定。

### 10.10 明确留给后续专项合同

Task Scheduling 的总架构边界已在 Section 10.15 冻结。本节不提前冻结：

```text
Outbox claim / lease / retry / dead-letter 精确 schema
Control Intent 数据表精确 schema
reason code 完整枚举
Duration Estimate v0.1 的字段、估算语义、currentness 和学习规则
Calendar v0.1 的 timezone、窗口、例外、物化和恢复语义
Capacity v0.1 的 pool、unit、host availability、claim、allocation、lease 和 fencing
Eligibility reason、effective-order、aging、公平性、backoff 和 stable tie-break 精确 policy
Atomic Admission and Recovery v0.1 的 effectful Validation mapping、host rejection 和恢复细节
TimeCriticalPathProjection 的精确 schema、算法、currentness 和多路径语义
ResourceScheduleProjection 与任何 solver / resource-leveling policy
preemptive scheduling v0.2+
Domain Agent delegation 精确 schema
Dashboard projection 和移动端同步合同
```

这些名字只确定后续合同边界，不表示其 schema、authority、inheritance、算法或 persistence 已被接受。
后续合同必须服从本节和 Section 10.15，不得反向改变九个状态及其核心语义。

v0.1 明确不采用：

```text
同一 Task 多执行 Run 并行
调用方直接 set_state
旧 Validation 默认跨 reopen 复用
UNKNOWN 自动重试
使用 Task aggregate_version 拒绝真实迟到回执
使用 PAUSED 隐藏 BLOCKED
```

### 10.11 Budget v0.1

> **Pending R1 synchronization:** Section 2.1 proposes that `RUN_ATTEMPTS` stays `RESERVED` at
> `HostWorkAcceptanceFact(ACCEPTED)`, becomes `SETTLED` only on canonical positive execution evidence, becomes `RELEASED` on
> authoritative no-execution proof, and becomes `UNKNOWN` when execution may have occurred. A later authenticated
> same-epoch positive execution fact atomically corrects the complete bound Task/Goal `RUN_ATTEMPTS` reservation set from
> `RELEASED` to `SETTLED` exactly once; a missing or conflicting member performs no partial correction and leaves Budget
> accounting fail-closed. The correction preserves the old Run as terminal `REJECTED`, contradicts the prior no-execution assurance, and opens an independent late-effect
> reconciliation. The correction transaction raises a no-new-Run fence and scans every later execution epoch plus its
> candidate, result, evidence, and Validation completion bindings. A late `STARTED` that may still be physically active
> is the narrow projection exception when no current Run `UNKNOWN` or nonterminal successor already determines state: a
> nonterminal Task remains `ACTIVE` with `activity_kind=COORDINATING`,
> `coordination_subtype=LATE_EFFECT_RECONCILIATION`, owner, next action, and activity deadline while stop/query is
> unfinished; only after physical execution has stopped does unresolved effect influence project that Task `BLOCKED`.
> A terminal Task stays terminal and only its affected assurance/support is challenged. No branch creates a Run,
> authorizes automatic retry, or weakens the one-nonterminal-Run invariant. This proposal has no effect until Jenn
> freezes R1.

Budget 是 Goal / Task 拥有的版本化执行合同，不是权限、permit 或 provider 调用授权。它不增加正式领域
对象；`BudgetEnvelope` 是 Goal / Task spec 中的不可变合同记录，`BudgetReservation` 是 Rust 管理的
基础设施记录。

v0.1 只支持四个独立维度：

```text
RUN_ATTEMPTS
MODEL_TOKENS
WALL_CLOCK_MS
MONEY_MICRO_UNITS
```

钱、时间、token 和尝试次数不得换算为一个总分。CPU、内存、磁盘、网络和 tool-call 次数延后到 host
capability 合同成熟后再评估。

Envelope 最低合同：

```yaml
BudgetEnvelope:
  envelope_id:
  scope: GOAL | TASK
  scope_id:
  dimension:
  mode: SOFT_TARGET | HARD_CAP
  limit: integer
  unit:
  currency: optional
  price_schedule_ref: optional
  budget_revision:
  created_by:
  reason:
```

所有 limit 必须是非负整数。`MONEY_MICRO_UNITS` 必须使用整数与明确 currency，不得使用浮点数；需要
provider 定价时必须绑定版本化 `price_schedule_ref`。缺失或不可验证的价格合同不能被猜测。

模式：

```text
SOFT_TARGET
  -> 可以继续 reservation 和执行
  -> consumed + reserved 超过 limit 时产生 RISK
  -> 不自动阻止 Run

HARD_CAP
  -> create_run 前必须完整 reservation
  -> 无法预留时不得创建 Run 或签发 permit
  -> 耗尽不自动令 Task FAILED / CANCELLED
```

Reservation 最低合同：

```yaml
BudgetReservation:
  reservation_id:
  run_id:
  effect_id: optional
  envelope_id:
  dimension:
  reserved_amount:
  consumed_amount:
  status: RESERVED | SETTLED | RELEASED | UNKNOWN
  idempotency_key:
  created_at:
  settled_at: optional
```

流程：

```text
计算本次 Run 每个维度的最大授权消耗
-> 检查 Task 和所有适用 Goal envelopes
-> 在 create_run 同一 SQLite transaction 中写入 reservation
-> Run / provider / host 使用 reservation_id
-> 可信 host / metering receipt 返回实际消耗
-> SETTLED 实际值并释放未使用额度
```

Task budget 与 Goal budget 同时存在时，每个适用 envelope 都必须允许 `HARD_CAP` reservation；同一维度
的 effective availability 取所有适用硬上限中最严格的剩余额度。Task cap 总和可以高于 Goal cap，真正
运行时仍由 Goal pool 原子约束，避免预分配大量闲置额度。

统一计量公式：

```text
consumed_total
  -> 只统计已 SETTLED 的实际消耗

reserved_total
  -> 只统计尚未 SETTLED / RELEASED 的保留额度
  -> UNKNOWN 按完整 reserved_amount 占用

remaining
  -> limit - consumed_total - reserved_total
```

同一用量不得同时计入 `consumed_total` 和 `reserved_total`。SETTLED 时原 reservation 从 outstanding
reserved 中移除，再计入实际 consumed。

崩溃与不确定性：

```text
Run 创建后、执行前崩溃
  -> reservation 保留
  -> 只有确认未派发后才能 RELEASED

执行后、usage receipt 前崩溃
  -> reservation = UNKNOWN
  -> 不自动释放
  -> 不自动重试付费或有副作用的操作

可信 receipt 晚到
  -> 按 reservation_id / receipt_id 幂等结算
```

执行结果已知但 metering 无法核对时，进入 budget evidence gap。外部副作用本身是否发生无法确定时，仍按
既有 Run / effect `UNKNOWN` 规则处理，不能用 budget gap 降级安全状态。

实际消耗意外超过 reservation 时，真实消耗仍必须入账，相关 envelope 进入 `OVER_CAP` projection，并
阻止后续新 Run；不得截断、丢弃或伪造 receipt。

Budget revision 不改写历史：

```text
new limit >= consumed + reserved
  -> 正常生效

new limit < consumed + reserved
  -> 允许记录新 limit
  -> envelope = OVER_CAP
  -> 阻止新 reservation
  -> 不取消已经发生的消耗或有效 reservation
```

权限：

```text
Jenn
  -> 可以设置和修改顶层 Goal 的所有预算
  -> 唯一可以增加真实货币 HARD_CAP

Nobao
  -> 可以在 Jenn 已批准的 Goal budget 内设置 Task / Subgoal cap
  -> 可以重新分配未消费额度
  -> 不能增加父级总预算

Domain Agent
  -> 只能在明确授权额度内提出或收紧 Task budget

Worker
  -> 不能修改 budget
  -> 不能自行声明权威 monetary / token consumption

可信 execution host / metering adapter
  -> 提交低披露 usage receipt

Rust core
  -> 唯一 reservation、settlement、remaining 和 OVER_CAP 计算权威
```

Budget 永远不授予额外权限。存在货币额度不等于允许真实 provider 调用、越过 P3、读取 secret 或执行
外部副作用。所有 provider、permit、host 和 authorization gate 仍独立生效。

Goal health 映射：

```text
SOFT_TARGET 的 consumed + reserved 超过 limit
  -> RISK: SOFT_BUDGET_TARGET_EXCEEDED

HARD_CAP 无法 reservation
  -> Task BLOCKED
  -> CURRENT_FRONTIER_HARD_TASK_BLOCKER subtype: BUDGET_HARD_CAP_EXHAUSTED

usage / price / receipt 无法核对，且不存在外部 effect UNKNOWN
  -> EVIDENCE_GAP: BUDGET_ACCOUNTING_UNRECONCILED
```

`SOFT_BUDGET_TARGET_EXCEEDED` 加入 `RISK v0.1`；`BUDGET_ACCOUNTING_UNRECONCILED` 加入
`EVIDENCE_GAP v0.1`。二者继续服从各自 registry 的证据、当前性、抑制和不得自动升级规则。

最终不变量：

```text
没有成功 HARD_CAP reservation
  -> 不创建 Run
  -> 不签发 permit
  -> 不派发外部工作

priority 和 deadline 永远不能越过 HARD_CAP
```

### 10.12 Deadline v0.1

> **Pending R1 synchronization:** Section 2.1 proposes renaming `HARD_NEW_EXECUTION_CUTOFF` to
> `HARD_NEW_START_AUTHORITY_CUTOFF` and defining the boundary as Rust's commitment of bounded one-time host start
> authority, not proof of remote physical start. The same atomic amendment renames the effective boundary fields,
> Deadline Event, blocker reason, permit field, host capability field, and Deadline snapshot field listed in Section
> 2.1. The existing subsection text remains historical accepted wording until Jenn freezes R1.

Deadline 是 Goal / Task 拥有的版本化运行合同，不是第六个正式领域对象，也不是调度器、Run timeout、
lease expiry、WAITING timeout、health `review_at` 或 `WALL_CLOCK_MS` budget。它只表达完成目标、禁止新执行
或停止活动执行的绝对时间边界。

`DeadlineConstraint` 是不可变合同记录；同一 scope、同一种 kind 最多一个当前 revision：

```yaml
DeadlineConstraint:
  deadline_id:
  scope: GOAL | TASK
  scope_id:
  kind: SOFT_COMPLETION_TARGET | HARD_NEW_EXECUTION_CUTOFF | HARD_ACTIVE_EXECUTION_STOP_CUTOFF
  deadline_at_utc_ms:
  display_timezone: optional
  deadline_revision:
  authority_mode: JENN_LOCKED | NOBAO_MANAGED
  created_by:
  reason:
  effective_from_event_sequence:
```

`deadline_at_utc_ms` 必须是 Rust 支持范围内的非负 UTC Unix milliseconds。`display_timezone` 只用于 UI
显示，不能改变 canonical instant；VCPChat、VCPMobile、JavaScript adapter 或 host 提交的本地时间都没有
裁决权。旧 revision 始终保留，不得原地修改。

#### 10.12.1 精确完成与截止边界

v0.1 使用半开边界：

```text
Rust transaction time < deadline_at_utc_ms
  -> 尚未越过 Deadline

Rust transaction time >= deadline_at_utc_ms
  -> 已越过 Deadline
```

Soft completion 是否按时，只看 GlobalTaskLedger 的权威完成 Event：

```text
Task
  -> DONE Event 在边界前提交，才算按时完成

Goal
  -> CLOSED + outcome ACHIEVED Event 在边界前提交，才算按时完成
  -> ABANDONED / UNACHIEVABLE / SUPERSEDED 不算按时完成
```

host 声称工作较早完成、客户端较早点击或 artifact 较早生成，都不能代替 Task `DONE` 或 Goal
`CLOSED + ACHIEVED`。非 ACTIVE Goal 仍服从 `GoalHealthProjection.applicability = NOT_ACTIVE`；历史
Deadline Event 可以保留，但不得伪装成 ACTIVE health。

#### 10.12.2 三种 Deadline

```text
SOFT_COMPLETION_TARGET
  -> 希望所属 Goal / Task 在边界前完成
  -> 到期只产生 Event 和可能的 RISK
  -> 不建立执行 fence，不阻止 Run

HARD_NEW_EXECUTION_CUTOFF
  -> 到期后禁止开始新的执行
  -> 已由权威 host 在边界前接受的 Run 可以继续
  -> 不要求停止已开始的 Run

HARD_ACTIVE_EXECUTION_STOP_CUTOFF
  -> 包含 HARD_NEW_EXECUTION_CUTOFF 的全部效果
  -> 同时撤销继续执行的权限，并要求停止、fence 和 reconciliation
```

Run “已经开始”必须由匹配当前 `run_id`、permit、execution epoch 和 host fence epoch 的权威 host
acceptance Fact 证明，而且该 Fact 必须在边界前由 Rust transaction 接纳并写入 ledger。host 自报的
`accepted_at`、迟到 Receipt 或客户端时间不得反向取得“截止前已开始”资格；未来若允许可信远端时间证明，
必须另行冻结 attestation 合同。`create_run`、`QUEUED`、`LEASED`、Outbox `CLAIMED` 或仅由 Agent 声称开始
都不算。

#### 10.12.3 时间权威

Rust core 是 Deadline 时间判断的唯一权威。每个 Deadline-sensitive transaction 只采样一次 wall-clock，
并把使用的时间与 `time_policy_revision` 写入相关 Event。JavaScript timer 只能请求重新评估，不能直接产生
Deadline fact 或修改 fence。

初始 time policy 至少维护：

```yaml
TimeAuthorityProjection:
  state: TRUSTED | UNCERTAIN
  last_observed_utc_ms:
  policy_revision:
  clock_regression_tolerance_ms:
  detected_event_sequence: optional
```

`clock_regression_tolerance_ms` 是版本化 Rust policy，调用方不得覆盖。monotonic clock 只用于同一次进程
启动内的等待与 timer 安排，不能跨重启证明绝对时间。

```text
wall-clock 无法读取或超出容差地倒退
  -> TimeAuthorityProjection = UNCERTAIN
  -> 不产生虚假的 DeadlineReached 或 Soft miss
  -> 有 Hard Deadline 时 fail closed，禁止新执行授权
  -> 有活动 HARD_ACTIVE_EXECUTION_STOP_CUTOFF 时发起预防性 PAUSE
  -> EVIDENCE_GAP: DEADLINE_TIME_AUTHORITY_UNCERTAIN

wall-clock 向前跳过 Hard Deadline
  -> 按已经到期处理并建立 sticky fence
  -> 后续把时钟调回不能自动恢复权限
```

预防性 PAUSE 不等于证明 Deadline 已到；时间重新可信后必须重新归约。若执行已经因该 PAUSE 被中断，
不得在没有显式恢复命令和完整安全重检的情况下自动续跑。

#### 10.12.4 继承与有效边界

Soft target 只评价其直接所属的 Goal / Task，不自动复制到后代。Hard Deadline 按当前 Goal ancestry 与
Task membership 递归约束后代：

```text
effective_new_execution_cutoff
  -> self 与所有 current ancestors 中
     HARD_NEW_EXECUTION_CUTOFF 和 HARD_ACTIVE_EXECUTION_STOP_CUTOFF 的最早值

effective_active_stop_cutoff
  -> self 与所有 current ancestors 中
     HARD_ACTIVE_EXECUTION_STOP_CUTOFF 的最早值
```

父级 projection 可以异步传播，但不能成为执行 gate 的权威。每次 `create_run`、permit、dispatch 和
effectful Validation gate 都必须从 canonical current relationship 与 Deadline revisions 重新计算。Task
移入已经到期的 Hard scope 时，scope fence 必须先于任何新执行权限生效。

#### 10.12.5 原子检查与 Run snapshot

以下路径必须在推进前调用 Rust deadline reducer：

```text
Resident startup recovery，且发生在 readiness 之前
create_run
首次 permit 签发
Outbox claim
dispatch authorization
host permit acceptance
effectful Validation 启动
Deadline revision / retirement
Goal ancestry 或 Task membership 变化
```

领域事务先以同一 `now` 物化已经到期的 Deadline Event 与 scope fence，再判断原 Command。Run 创建时至少
记录：

```yaml
deadline_snapshot:
  source_deadline_revisions: []
  effective_new_execution_cutoff_utc_ms: optional
  effective_active_stop_cutoff_utc_ms: optional
  deadline_fence_epoch:
  time_policy_revision:
```

TaskPermit 至少携带独立的 `start_not_after_utc_ms` 与 `stop_not_after_utc_ms`。签发时检查不能替代 host
在接受 permit 和发生副作用前的本地 enforcement check。host clock 只能执行其 capability contract，不能
写入 ledger 的 Deadline projection 或反向改变 Rust transaction time。

Run lease 与执行授权分离。越过 `HARD_NEW_EXECUTION_CUTOFF` 后，边界前已接受的同一 Run 可以续 lease，
但必须保持相同 run、executor、execution epoch、effect scope 和 permit；不得借续 lease 签发新 permit、
扩大 effect 或越过 `effective_active_stop_cutoff`。

#### 10.12.6 Soft target 到期

同一个 `deadline_id + deadline_revision` 最多产生一次 `SoftCompletionTargetMissed` Event。到期时只记录
canonical miss，不直接修改 Task 状态、不阻止 Run，也不完成或关闭对象。

```text
当前 revision 到期且所属对象未按 Section 10.12.1 完成
  -> SoftCompletionTargetMissed

miss 影响当前 Goal success criterion 或必要 route
  -> RISK: SOFT_DEADLINE_TARGET_MISSED

miss 只属于非关键 Task
  -> 保留局部 Deadline projection，不改变 Goal Health
```

当前 RISK 在对象按规则完成、Deadline 合法修订 / retirement 或当前 plan 不再依赖该路线后结束；历史 miss
Event 永不删除。Task `FAILED / CANCELLED` 或 Goal 非 `ACHIEVED` 终结时，由更具体 lifecycle / route 事实
决定 Goal Health，不重复用 Soft risk 遮盖终态。该 RISK 仍须按 Section 6.4.5 带有由版本化 health policy
生成的 `review_at`；没有当前复查不得直接回到 `HEALTHY`。

#### 10.12.7 Hard new-execution cutoff

同一个 Hard revision 到期时，Rust 幂等追加 `HardNewExecutionCutoffReached`，并建立 scope start fence：

```text
禁止创建新 Run 和 retry Run
禁止派发尚未被 host 接受的 Run
禁止新增会产生 Task 结果或外部副作用的执行
禁止新增 effectful Validation
不撤销边界前已经被 host 接受的 Run
```

确定未派发 / 未接受的 Run 可以归约为 `REJECTED`。请求可能已到达 host 但 acceptance 无法确定时，Run
进入 `UNKNOWN`，不得因“可能只是没开始”而自动重试。

Deadline fence 本身不是 Task blocker，也不得直接把有活动 Run 的 Task 从 `ACTIVE` 改成 `BLOCKED`。
只有当前、版本化的 plan / Requirement / execution commitment 证明 Task 必须新增执行才能推进，且不存在
合规 closure-only 路线时，才形成 Rust policy 白名单 subtype：

```text
DEADLINE_NEW_EXECUTION_PROHIBITED
```

无结构化承诺时，Agent 的主观判断或一次试探性 `create_run` 拒绝不足以证明 HARD blocker。健康判断需要该
事实但事实尚未形成时，使用 `CURRENT_REQUIRED_FACT_MISSING`，不得伪造路线已经截断。

#### 10.12.8 Hard active-execution stop

`HARD_ACTIVE_EXECUTION_STOP_CUTOFF` 到期时，Rust 在 scope 层先原子完成：

```text
追加 HardActiveExecutionStopCutoffReached
提升 deadline fence epoch
阻止所有后续新 Run、permit 和 dispatch
撤销或 fence 当前执行 permit
为活动执行写入可重试 Outbox stop intent
```

Goal scope 可以有多个后代 Task。scope fence 必须在一个权威事务中立即生效；逐个 Task 的停止与
reconciliation 可以通过幂等、有界批次继续，不能为了等待批处理而留下新派发窗口。

Deadline 使用现有 `PAUSE` Control Intent，不使用 `CANCEL`，因为停止执行不等于取消 Task：

```text
没有活动 Control Intent
  -> 创建 initiator = SYSTEM_POLICY、cause = DEADLINE_HARD_STOP 的 PAUSE intent

已有 PAUSE
  -> 追加 DeadlineBoundToControlIntent Event，不创建第二个 intent

已有 CANCEL
  -> 保留 CANCEL 优先级，追加 Deadline fence 与关联 Event，不创建 PAUSE
```

停止请求、AbortSignal、发送 signal 或 Outbox `ACKED` 都不等于已经停止。只有 host final Receipt 与副作用
reconciliation 能收口 intent。无法确认时必须进入 `UNKNOWN`。

#### 10.12.9 Run 结果与迟到事实

Deadline 只限制授权，不改写现实：

```text
能够证明 host 从未接受
  -> Run REJECTED

host 确认按 Deadline stop request 停止
  -> Run CANCELLED

Run 违反自己的独立 runtime timeout contract
  -> Run TIMED_OUT

host 是否接受、继续执行或产生副作用无法确定
  -> Run UNKNOWN

可信 SUCCEEDED / FAILED Receipt 晚到
  -> 按真实事实和原 epoch 幂等入账
```

Task / Goal Deadline 本身不得把 Run 伪装成 `TIMED_OUT`。若可信事实证明 host 在 permit 已因 Deadline
失效后仍执行，必须记录 `DeadlineAuthorityViolation`，保留真实 Run 结果，并把相关 effect 视为
completion-blocking，直到 policy-required reconciliation / Validation 完成。

#### 10.12.10 Validation 与 closure-only 路线

Hard Deadline 到期后仍允许系统安全收尾：

```text
接收迟到 Fact / Receipt
UNKNOWN reconciliation
可重入 finalizer
纯 ledger reducer 与 projection
不创建 Run / permit、不改变 candidate result、effect_class = NONE 的 Validation
HUMAN_ACCEPTANCE
合法的 EVIDENCE_CARRY_FORWARD_REVIEW
```

已经在边界前由 host 接受的 effectful Validation Run，按对应 Hard kind 的 Run 规则继续或停止。到期后不得
新建会调用 provider / external host、产生副作用、修改 candidate result 或扩大结果范围的 Validation。

活动 Deadline fence 不会自动废掉既有 PASSED，也不自动阻止 `VERIFYING` 或 `DONE`。如果全部完成守卫可以
通过 closure-only 路线满足，Task 可以在截止后合法完成；若已生成
`DEADLINE_NEW_EXECUTION_PROHIBITED` blocker，必须先由新 canonical fact 证明 closure 路线成立并清除
blocker。

#### 10.12.11 Host 能力门禁

Host capability contract 至少必须表达：

```yaml
deadline_enforcement:
  checks_start_not_after: true | false
  checks_stop_not_after: true | false
  supports_permit_fencing: true | false
  supports_addressable_stop: true | false
  emits_terminal_stop_receipt: true | false
  supports_idempotent_status_query: true | false
  accepts_late_receipts: true | false
  capability_revision:
```

`HARD_NEW_EXECUTION_CUTOFF` 路线至少需要可靠的 start check、permit fencing 与 acceptance / status 事实。
`HARD_ACTIVE_EXECUTION_STOP_CUTOFF` 路线需要上列全部能力，或一个能够提供等价安全保证的版本化 host
contract。仅调用 `AbortController.abort()`、发送 `SIGTERM / SIGKILL` 或本地 Promise reject 都不能证明
停止完成。

尚未选择 host 或 capability 事实尚未到要求阶段时，不得生成 HARD blocker；需要该事实时使用
`CURRENT_REQUIRED_FACT_MISSING`。只有所有当前允许的执行路线都被 canonical capability facts 证明不能
满足 Hard Stop，且没有合规替代路线时，才形成 Rust policy 白名单 subtype：

```text
DEADLINE_HARD_STOP_ENFORCEMENT_UNAVAILABLE
```

VCPToolBox 当前实现不能被整体声明为满足 Hard Stop；每个 direct service、child process、distributed
executor 和 provider adapter 必须分别验证。本决议不启用或修改这些 runtime 路径。

#### 10.12.12 Revision、fence 与恢复

Deadline revision Command 至少绑定：

```yaml
command_id:
actor:
expected_scope_aggregate_version:
base_deadline_revision: optional_for_create
operation: CREATE | REVISE | RETIRE
reason:
```

Deadline revision 增加 scope aggregate version、deadline revision 和 Event sequence，但单纯改变时间不增加
`task_spec_revision`、`result_revision` 或 `validation_set_revision`，也不使无关 Validation evidence 失效。
若同时改变 Task scope 或 Goal success criteria，仍必须走对应 spec / plan revision。

`deadline_id` 在 revision 间保持稳定。Task `DONE / FAILED / CANCELLED` 或 Goal `CLOSED` 后，不接受新的独立
CREATE / REVISE / RETIRE；历史合同保持不变。对象 reopen / reactivate 后可以按当前 authority 创建新
revision，但未处理的旧 Deadline 与 fence 仍立即适用。

把任一种 Deadline 创建或修订到当前时间或过去时，必须在同一事务中立即物化对应 Soft miss 或 Hard
crossing Event；Hard kind 同时建立 scope fence。到期后延长或 retirement 不删除旧 Event，也不自动解除
已经触发的 fence。

`DeadlineFence` 是 Event-backed operational record，不增加正式对象：

```yaml
DeadlineFence:
  fence_id:
  scope:
  scope_id:
  source_deadline_id:
  source_deadline_revision:
  fence_kind: START | STOP
  fence_epoch:
  status: ACTIVE | RELEASED
  triggered_event_sequence:
  released_by: optional
  released_event_sequence: optional
```

`ReleaseDeadlineFence` 必须使用 scope CAS，并同时满足：

```text
触发 fence 的 Deadline 已合法 revision / retirement，且当前不再到期
没有其他适用且已到期的 Hard Deadline
TimeAuthorityProjection = TRUSTED
没有 UNKNOWN、未核对副作用或未收口 Control Intent
actor 具有触发来源相同或更高的 authority
重新检查 dependency、budget、permit、host、P3 和当前 plan
```

释放 fence 只恢复“可以重新评估”的资格，不创建 Run、不自动恢复旧 Run、不直接改变 Task 状态。Task 可以
在 fence 仍 ACTIVE 时通过合法 closure-only 路线进入终态并保留该历史 fence；若以后 reopen，则必须先处理
当前仍适用的 Deadline 与 fence。

#### 10.12.13 Actor authority

```text
Jenn
  -> 设置、修改和 retirement 顶层 Goal Deadline
  -> 设置任意 JENN_LOCKED Deadline
  -> 可以管理所有下级 Deadline

Nobao
  -> 在当前 Goal 与父级 Hard boundary 内管理 Subgoal / Task 的 NOBAO_MANAGED Deadline
  -> 不能放宽、retire 或 release Jenn / ancestor 的 Hard constraint

Domain Agent
  -> 只能在授权领域提出 Deadline proposal
  -> v0.1 不直接提交 revision 或 release fence

Worker / executor / UI
  -> 不能修改 Deadline 或 release fence
  -> 只能提交事实或转发有 actor identity 的 Command

Rust core
  -> 唯一 revision、time judgment、effective cutoff、fence 和 projection 写入者
```

Nobao 触发的 `NOBAO_MANAGED` fence 可以由 Nobao 或 Jenn 在全部守卫满足后释放；Jenn / ancestor 来源的
fence 只能由 Jenn 或该来源明确定义的更高权威处理。Deadline 不授予任何 provider、secret、host、P3
或外部副作用权限。

#### 10.12.14 Goal Health 映射

```text
当前 Soft target miss 影响 Goal criterion 或必要路线
  -> RISK: SOFT_DEADLINE_TARGET_MISSED

当前 Deadline 判断的时间权威不可信
  -> EVIDENCE_GAP: DEADLINE_TIME_AUTHORITY_UNCERTAIN

当前必要执行 commitment 已被 start fence 确定禁止，且无 closure 路线
  -> Task blocker subtype: DEADLINE_NEW_EXECUTION_PROHIBITED

所有允许路线被证明无法执行要求的 Hard Stop
  -> Task blocker subtype: DEADLINE_HARD_STOP_ENFORCEMENT_UNAVAILABLE
```

两个 Task blocker subtype 只有在 affected Task 属于当前 Critical Work Frontier 且 Rust policy 将其分类为
HARD 时，才可通过 `CURRENT_FRONTIER_HARD_TASK_BLOCKER` 影响 Goal Health。Deadline fence、Soft miss、host
尚未选择、time uncertainty 或 Agent 判断本身都不得直接声称 Goal `BLOCKED`。

Deadline reason 至少绑定 `deadline_id`、`deadline_revision`、scope、Goal / plan / affected Task revisions、
crossing Event sequence、source fact refs 和 resolution condition。Deadline revision 过期后，旧 reason 失去
当前裁决权但保留历史。

#### 10.12.15 最终不变量

```text
Deadline 不自动完成、失败、取消或 reopen Task / Goal
Run SUCCEEDED 仍不自动完成 Task
Hard cutoff 不直接覆盖活动 Run 所要求的 Task ACTIVE 不变量
Deadline fence 不自动等于 Task blocker
priority 不能越过 Hard Deadline
Deadline 不能越过 dependency、budget、permit、host 或 P3
timer 未触发不能成为继续执行的理由
停止请求不等于已经停止
Deadline revision 不改写历史 miss、violation、fence 或 Receipt
每个 deadline_id + deadline_revision + crossing kind 最多一个 crossing Event
```

### 10.13 Task Priority v0.1

Task Priority 只表达一个 Task 相对于其他普通、已具备执行资格 Task 的基础服务等级。它不表达安全紧急、
Jenn 当前 focus、临时 expedite、Deadline urgency、Critical Work Frontier、执行许可或抢占权。

旧 Active Work Queue 的 `NOW / NEXT` 是 operator / compatibility surface，不是 canonical Task Priority；
VCPToolBox 的 time scheduler 与 `codex-router` task graph 当前也没有可直接继承的 Priority authority。

#### 10.13.1 固定等级

v0.1 只允许四级：

```text
HIGH
  -> 延迟会明显损害当前 Goal 的既定计划
  -> 优先获得普通执行容量
  -> 不代表安全事件、立即执行或允许抢占

NORMAL
  -> 默认计划工作
  -> 没有充分理由提高或降低时采用

LOW
  -> 明确可以让位于普通计划工作
  -> 仍必须获得公平服务

BACKGROUND
  -> 维护、探索或机会性工作
  -> 主要使用剩余或公平份额容量
  -> 不等于永不执行
```

固定顺序为：

```text
HIGH > NORMAL > LOW > BACKGROUND
```

Rust 可以在内置 policy 中使用固定 ordinal 比较，但协议、数据库外部 API 与调用方只能提交枚举；不得提交
`P0 / P1`、0—100、浮点 score、自由文本等级或调用方自定义 comparator。

#### 10.13.2 Task-owned contract

Priority 不是新正式领域对象，而是 Task 拥有的不可变版本化合同：

```yaml
TaskPriorityContract:
  priority_id:
  task_id:
  priority_policy_version: task-priority.v0.1
  base_priority_class: HIGH | NORMAL | LOW | BACKGROUND
  priority_revision:
  authority_mode: JENN_LOCKED | NOBAO_MANAGED

  basis_type: SYSTEM_DEFAULT | JENN_EXPLICIT | GOAL_PLAN | DECOMPOSITION | REPRIORITIZATION
  basis_refs: []
  reason:

  context_fingerprint_contract_version: priority-context.v0.1
  context_binding:
    task_spec_revision:
    goal_bindings:
      - goal_id:
        criterion_bindings:
          - criterion_id:
            criterion_revision:
        plan_membership_refs:
          - route_group_id:
            frontier_member_id:
            membership_revision:

  priority_context_fingerprint:
  decided_by:
  effective_from_event_sequence:
```

强制规则：

```text
priority_id 在 revision 间保持稳定
每个 Task 恰好一个 current Priority revision
旧 revision 永远保留，不原地修改或删除
Task 创建时未声明 Priority -> Rust 在同一事务中持久化 NORMAL
SYSTEM_DEFAULT 的 authority_mode 固定为 NOBAO_MANAGED
非 SYSTEM_DEFAULT 的 basis_refs 不得为空
context_binding 与 fingerprint 由 Rust 从 canonical facts 生成，调用方不得覆盖
```

Task 创建与初始 Goal / plan membership 在同一事务中形成时，初始 Priority 直接绑定最终初始 context。Task
先独立创建、以后才加入 Goal / plan 时，按 Section 10.13.5 进入 `REVIEW_REQUIRED`。

#### 10.13.3 多 Goal context

v0.1 不假设一个 Task 只能服务一个 Goal：

```text
standalone Task
  -> goal_bindings 可以为空

shared Task
  -> 可以具有多个 goal_bindings
  -> 仍只有一个全局 base_priority_class
  -> Jenn / Nobao 必须综合全部 Goal basis 作出一次全局决定
```

结构化 binding 必须规范化：

```text
goal_bindings
  -> 按 goal_id 排序并去重

criterion_bindings
  -> 按 criterion_id + criterion_revision 排序并去重

plan_membership_refs
  -> 按 route_group_id + frontier_member_id + membership_revision 排序并去重
```

Priority 不绑定整个全局 `plan_revision`。`plan_membership_refs` 只保存该 Task 自己的 Goal criterion route /
frontier membership；无关 Task 或无关 plan member 的变化不能让本 Task Priority 失去当前性。后续 plan / dependency
合同必须提供稳定、版本化的 membership identity，不得退化成按自然语言比较。

#### 10.13.4 Context fingerprint

`priority-context.v0.1` 固定使用：

```text
input
  -> task_id + 完整规范化 context_binding

encoding
  -> UTF-8 canonical JSON

object keys
  -> lexical order

arrays
  -> 使用 Section 10.13.3 的稳定业务键排序

duplicates
  -> reject

numbers
  -> integers only；不允许 float、NaN 或 Infinity

digest
  -> SHA-256 lowercase hex
```

Rust 在 Priority Command 的同一事务中：

```text
读取 canonical Task / Goal / criterion / Task-specific plan membership
-> 构造 context_binding
-> canonicalize
-> 计算 priority_context_fingerprint
-> 写入 Priority revision、Task projection 与 Event
```

调用方提供的 context、digest 或排序只能作为请求提示，不能成为权威值。

#### 10.13.5 Context currentness

Priority 当前投影至少为：

```yaml
TaskPriorityProjection:
  declared_class: HIGH | NORMAL | LOW | BACKGROUND | null
  context_status: CURRENT | REVIEW_REQUIRED
  scheduling_class: HIGH | NORMAL | LOW | BACKGROUND
  reason_codes: []
  based_on_priority_revision:
  stored_context_fingerprint:
  current_context_fingerprint:
  detected_event_sequence: optional
```

Priority projection reason 不是 Goal Health reason，也不增加新正式对象。v0.1 只允许：

```text
TASK_SCOPE_CHANGED
GOAL_BINDING_CHANGED
CRITERION_BINDING_CHANGED
PLAN_MEMBERSHIP_CHANGED
PRIORITY_POLICY_CHANGED
PRIORITY_POLICY_UNAVAILABLE
```

归约：

```text
stored fingerprint == current fingerprint，且 policy 兼容
  -> context_status = CURRENT
  -> scheduling_class = declared_class

fingerprint 不同，或 policy 没有明确兼容声明
  -> context_status = REVIEW_REQUIRED
  -> declared_class 保留历史
  -> scheduling_class = NORMAL
```

`declared_class = null` 只用于 Rust 无法解析未来 policy 的历史等级。原始合同和 Event 仍保留，但未知值不能
进入 comparator。

以下变化要求复查：

```text
Task spec revision 改变
Goal binding 增加、删除或替换
criterion identity / revision 改变
本 Task 的 plan membership 改变
Priority policy 语义变化且没有兼容映射
```

以下变化本身不使 Priority 失去当前性：

```text
无关 Task 或无关 plan member 变化
Run / Validation 状态变化
Deadline 到期
Goal Health 变化
普通 PAUSE / WAITING
未改变 Task scope 与 Goal / plan context 的 reopen
```

`REVIEW_REQUIRED` 不阻塞 Task、不改变 Task state、不产生 Goal Health reason，也不能由调用方直接 clear。Jenn
或 Nobao 必须提交新的 `ReviseTaskPriority`；即使等级不变，也生成新 revision 并绑定当前 context。
`JENN_LOCKED` 进入 `REVIEW_REQUIRED` 后只能由 Jenn 确认或修订。

#### 10.13.6 Basis authority guards

```text
SYSTEM_DEFAULT
  -> 只能由 Rust 在 Task 创建事务中产生
  -> class 必须为 NORMAL
  -> 必须是初始 revision
  -> basis_refs 可以为空

JENN_EXPLICIT
  -> actor 必须是 Jenn
  -> 必须引用 Jenn Command Event

GOAL_PLAN
  -> canonical 决策者只能是 Jenn 或 Nobao
  -> 必须引用 Goal、criterion 与 Task-specific plan membership

DECOMPOSITION
  -> canonical 决策者只能是 Jenn 或 Nobao
  -> 只用于子 Task 初始 Priority
  -> 必须引用 parent Task 与 decomposition Event

REPRIORITIZATION
  -> canonical 决策者只能是 Jenn 或 Nobao
  -> 必须引用上一 Priority revision 与新的判断依据
  -> context confirmation 即使 class 不变，也使用此类型
```

Domain Agent proposal 可以进入 `basis_refs`，但不能成为 `decided_by`。Lock / Unlock 使用
`JENN_EXPLICIT`，同时引用上一 Priority revision 与 Jenn Command Event。Rust 只验证 actor、引用、版本和
结构，不声称能判断自然语言中的现实重要性。

#### 10.13.7 Command、权限与 Jenn lock

Priority Command 最低合同：

```yaml
command_id:
actor:
task_id:
expected_task_aggregate_version:
base_priority_revision:
operation: REVISE | LOCK | UNLOCK
new_base_priority_class: optional
basis_type:
basis_refs: []
reason:
```

Rust 使用当前 canonical facts 自行捕获 context，不信任 Command 中的 fingerprint。

```text
Jenn
  -> 可以设置、确认、锁定和解锁任何非终态 Task Priority

Nobao
  -> 可以管理非终态 Task 的 NOBAO_MANAGED Priority
  -> 可以确认 context 或修订 class
  -> 不能修改或解除 JENN_LOCKED

Domain Agent
  -> 只能提交 proposal

Worker / executor / Validator / UI
  -> 不能写 Priority
  -> UI 只能转发带真实 actor identity 的 Command

Rust core
  -> 唯一默认值、revision、context currentness、CAS 和 projection 写入者
```

Lock lifecycle：

```text
LockTaskPriority
  -> Jenn-only
  -> 创建新 revision
  -> authority_mode = JENN_LOCKED
  -> 可以保持或同时修改 class

UnlockTaskPriority
  -> Jenn-only
  -> 创建新 revision
  -> authority_mode = NOBAO_MANAGED
  -> 默认保持原 class，除非 Jenn 同时修改
```

Lock / Unlock 不改变 Task state、不影响活动 Run，也不绕过 context currentness。

#### 10.13.8 Selection snapshot 与竞态

Priority 与普通 scheduling selection 必须由 Rust 单写入顺序关闭竞态。每次 selection 至少内嵌：

```yaml
TaskPrioritySelectionSnapshot:
  selection_id:
  task_id:
  task_aggregate_version_observed:
  lifecycle_generation:
  priority_id:
  priority_revision:
  priority_policy_version:
  declared_class:
  context_status:
  scheduling_class:
  priority_context_fingerprint:
  dependency_revision_observed:
  dependency_set_snapshot_id: null_if_precommit
  dependency_assessment_mode: PRECOMMIT_NEW_BINDING | POSTCOMMIT_EXISTING_BINDING
  dependency_assessment_freshness: CURRENT | STALE | EVALUATING
  dependency_assessment_outcome: SATISFIED | WAITING | INTERVENTION_REQUIRED | INDETERMINATE
  dependency_input_fingerprint:
  selected_at_event_sequence:
```

它是 scheduling Event 的不可变内嵌值，不是新领域对象、capacity claim、reservation 或 permit。
`Task Scheduling Architecture Boundary v0.1` 继续复用它作为唯一 canonical selection record；不得另建平行的
`DispatchSelectionSnapshot` 或第二套 selection authority。Eligibility 与 Effective ordering 是 Rust 在
selection 时执行的确定性归约，不因此获得领域状态写入权。

```text
Priority revision 先提交
  -> selection 必须使用新 revision

Selection 先提交
  -> snapshot 保持历史有效
  -> 后续 Priority revision 不取消、不抢占 selection 或活动 Run

Task reopen
  -> lifecycle_generation 增加
  -> 旧 selection 永远不能创建新 Run

Task aggregate version 在 selection 后改变
  -> create_run 与其他执行 gate 必须重新检查当前事实
```

selection 后 Task 的 dependency、Deadline、Budget、permit、host、P3 或状态改变时，后续 gate 仍可拒绝；
Priority snapshot 不授予执行资格。

未来 Duration、Calendar、Capacity 与 effective-order 专项合同可以通过兼容版本增加 selection 的观察引用，
但本轮不接受这些字段。任何旧 selection、stale planning projection 或旧 lifecycle generation 都不得创建
Run；`create_run` 必须重新读取当前 canonical facts。

Priority selection 只应选择 dependency assessment 为 `CURRENT + SATISFIED` 的 Task，但该字段只是选择时
证据。`create_run`、permit、dispatch、effectful Validation、candidate adoption 与 `complete_task` 仍须在
Rust 写事务中重新读取 canonical dependency facts 和 immutable assurance closure。异步 assessment 或旧
selection 不得成为执行授权。

首次 commitment 前 selection 不创建或冻结 DependencySetSnapshot，`dependency_set_snapshot_id = null`；
它只记录当前 revision、assessment 和 input fingerprint。已有 current commitment 时才记录对应 set snapshot
ID。无论是否为 null，`create_run` 都必须在自己的事务中完成正式冻结与同步 closure gate。

#### 10.13.9 Priority 适用范围

Priority 只排序多个已经具备资格的 Task 对普通 worker / executor 容量的竞争，包括：

```text
新 execution Run
普通 effectful Validation Run
需要 worker / executor 容量的普通 closure work
```

以下已冻结的安全义务不进入普通 Priority 比较：

```text
Fact / Receipt 接纳
UNKNOWN reconciliation
Deadline stop
活动 Control Intent 收口
lease / crash recovery
ledger integrity recovery
```

它们不获得一个可由角色填写的“超级 Priority”；只是既有安全合同要求系统先收口。具体 control lane 与容量
仍由 scheduling 合同表达。

#### 10.13.10 生命周期与继承

```text
Priority revision
  -> 增加 Task aggregate version、priority revision 和 Event sequence
  -> 不增加 task_spec_revision、result_revision 或 validation_set_revision
  -> 不废掉 Validation evidence
  -> 不改变 Task state
  -> 不取消或抢占活动 Run

Task DONE / FAILED / CANCELLED
  -> 独立 Priority revision、Lock、Unlock 被拒绝

Task reopen
  -> 默认保留 Priority
  -> context 未变时仍 CURRENT
  -> context 改变时 REVIEW_REQUIRED
```

父 Task、Goal 或 Critical Work Frontier 不自动传播或改写 Priority。拆出子 Task 时默认 `NORMAL`；Nobao 可以
显式复制父级 class，但必须为子 Task 建立自己的 `DECOMPOSITION` basis 和 Priority contract。Deadline、
Validation / Run failure、Goal Health、等待时长和 Agent 主观判断也不能静默改写 base class。

#### 10.13.11 Rust 内置 policy fallback

Rust binary 必须内置：

```yaml
supported_policy: task-priority.v0.1
ordering:
  - HIGH
  - NORMAL
  - LOW
  - BACKGROUND

fallback:
  context_status: REVIEW_REQUIRED
  scheduling_class: NORMAL
  reason_codes:
    - PRIORITY_POLICY_UNAVAILABLE
```

```text
stored policy 可解析且存在明确兼容映射
  -> 正常归约

stored policy 不受支持或 comparator 不可用
  -> 使用 Rust 内置 NORMAL fallback
  -> 拒绝普通 Priority mutation
  -> 等待正式 migration / recovery 合同

policy 语义改变且没有兼容映射
  -> PRIORITY_POLICY_CHANGED
  -> REVIEW_REQUIRED
```

Policy 故障不能阻止 Fact / Receipt、UNKNOWN reconciliation、Deadline stop、Control Intent finalizer 或
ledger recovery。

#### 10.13.12 Priority 与 Scheduling Architecture Boundary

以下内容不进入 Priority v0.1：

```text
Jenn focus
temporary expedite
eligible-wait aging
跨 Goal 公平份额
BACKGROUND 最低服务保证
连续高优先任务上限
stable tie-break
并发容量
```

Scheduling 可以计算临时 effective selection order，但不得回写或伪造 `base_priority_class`。Priority v0.1
只能作为 scheduling 的一个输入，不能独立决定“下一项一定是谁”。Jenn focus、Deadline urgency、Critical
Work Frontier 或预测时间也不能静默改写 base Priority。

普通 scheduling v0.1 已明确为 `NON_PREEMPTIVE`：新的 selection、Priority revision 或 planning projection
只影响尚未开始的工作，不自动暂停、取消、替换或终止活动 Run。未来任何 preemptive scheduling 都属于
v0.2+ 专项合同。Deadline hard stop、Jenn / Nobao 的既有 Control Intent、dependency fence、P3 和 host
safety stop 继续服从各自合同，不属于 scheduling preemption。

#### 10.13.13 最终不变量

```text
Priority 不授予权限
Priority 不改变 Task 状态、进度或完成资格
Priority 不覆盖 dependency、Deadline、Budget、permit、host 或 P3
Priority 不自动抢占活动 Run
Priority 不自动继承
Priority context 变化不静默沿用极端等级
Priority selection 必须绑定实际使用的 revision 与 lifecycle_generation
REVIEW_REQUIRED 使用 NORMAL，不伪造旧等级仍然适用
普通 Priority 不压过既有安全收口义务
NOW / NEXT 不等于 canonical Priority
```

### 10.14 Task Dependency v0.1

Task Dependency v0.1 正式采用 `PINNED_DONE_EVENT`。它表达一个 Task 在正式承诺时，要求另一个
Task 已经完成，并把那一次不可修改的完成事实固定下来。它不持续追踪 source 的最新状态，也不声称
dependent 消费了 source 结果内容。

#### 10.14.1 范围与非目标

v0.1 只允许：

```text
同一 Goal 当前计划内的 Task
两个 endpoint 都只属于该 Goal 的当前计划，不是多 Goal shared Task
ALL_OF
PINNED_DONE_EVENT
```

Task dependency 是 Task-owned、版本化、不可变快照合同，不是第六个正式领域对象。v0.1 明确不采用：

```text
跨 Goal dependency
以 shared Task endpoint 形成的隐性跨 Goal dependency
ANY_OF dependency
FOLLOW_CURRENT
结果内容或 Artifact slice dependency
任意 predicate / boolean expression DSL
冻结后为当前 generation 增删 edge
dependency 自动传播 Priority、Deadline、Budget、权限或 Goal ancestry
自动 reopen、重跑、补偿或级联修改 Task 状态
```

替代路线继续由 Goal 的 `ANY_OF route_groups` 表达。结果血缘、cross-Goal owner / consumer、
`PINNED_VALIDATED_RESULT` 和冻结后 extension 留给新的后续合同。

Priority v0.1 允许一个 Task 具有多个 `goal_bindings`，但 Task Dependency v0.1 的安全范围更窄：任何 endpoint
只要同时服务多个当前 Goal membership，就拒绝建立 edge。需要共享工作时，先为当前 Goal 建立专属
consumer / wrapper Task；不得让一个 Goal 中 source completion 的 challenge 静默改变另一个 Goal。

#### 10.14.2 Dependency spec 与 edge

```yaml
TaskDependencySpecRevision:
  task_id:
  dependency_revision:
  dependency_policy_version: task-dependency.v0.1
  edges:
    - edge_id:
      edge_revision:
      kind: PINNED_DONE_EVENT
      prerequisite_task_id:
      dependent_task_id:
      goal_id:
      plan_membership_refs: []
      basis_refs: []
      decided_by:
  dependency_spec_fingerprint:
  fingerprint_contract_version:
  effective_from_event_sequence:
```

强制规则：

```text
dependent_task_id 必须等于 spec.task_id
prerequisite 与 dependent 必须在 edge.goal_id 的同一当前计划中具有可核对 membership
prerequisite 与 dependent 都不得具有 edge.goal_id 之外的当前 Goal membership
edge_id + edge_revision 全局唯一
task_id + dependency_revision 唯一
self-edge 拒绝
同一 spec 中重复 edge 拒绝
任何直接或间接 cycle 拒绝
edge kind 只能是 PINNED_DONE_EVENT
任何 Task 仍被 current dependency spec、snapshot 或 binding 引用时，为它增加第二个当前 Goal membership 的 Command 拒绝
```

Edge 使用稳定 identity；冻结前的增删改通过新的 `dependency_revision` 表达，旧 revision 永远保留。
Rust 根据规范化 edge、Goal 和稳定 plan membership refs 生成 spec fingerprint。调用方提供的 digest 只能
作为请求提示，不能覆盖 Rust 计算结果。

Fingerprint 必须记录 algorithm、canonicalization contract version、authority 和 sensitivity。Rust 只能
组合 ledger 已有的低披露 ID、revision、Event ref 和允许进入 ledger 的 digest；不得读取 artifact bytes、
raw prompt、secret、private memory 或 provider raw response。敏感 composite fingerprint 只能保存在内部
canonical storage；公共 projection 和模型上下文使用 opaque handle。

如果恢复或 legacy 数据发现 endpoint 已经具有多个当前 Goal membership，assessment 必须进入
`INDETERMINATE` 并建立 fence；不得假装该 edge 仍符合 v0.1。需要共享工作时必须先通过新 plan revision
建立 Goal 专属 wrapper / replacement Task，再解除旧引用，不能直接修改已 commitment endpoint。

#### 10.14.3 Phase-aware DependencyAssessment

```yaml
DependencyAssessment:
  task_id:
  mode: PRECOMMIT_NEW_BINDING | POSTCOMMIT_EXISTING_BINDING
  freshness: CURRENT | STALE | EVALUATING
  outcome: SATISFIED | WAITING | INTERVENTION_REQUIRED | INDETERMINATE
  dependency_revision:
  observed_dependency_revision:
  dependency_spec_fingerprint:
  dependency_set_snapshot_id: null_for_precommit
  dependency_input_fingerprint:
  observed_input_fingerprint:
  assessed_at_event_sequence:
```

归约：

```text
PRECOMMIT_NEW_BINDING
  -> 尚无 current DependencySetSnapshot
  -> 每个 prerequisite 当前必须为 DONE
  -> 待绑定的 completion ref 必须就是 source current completion ref，且 assurance = CONFIRMED
  -> 全部满足时 SATISFIED

PRECOMMIT_NEW_BINDING 中存在仍可通过正常推进进入 DONE 的非终态 prerequisite
  -> WAITING

PRECOMMIT_NEW_BINDING 中存在 FAILED / CANCELLED prerequisite
  -> INTERVENTION_REQUIRED

POSTCOMMIT_EXISTING_BINDING
  -> 必须有 current immutable DependencySetSnapshot 与完整 PinnedDoneBindings
  -> 不重新要求 source 当前 state = DONE
  -> 每条准确 bound completion ref 与 effective closure assurance 全部 CONFIRMED
  -> SATISFIED

任一模式中引用损坏、证据冲突、policy 不可用、binding mismatch 或 assurance 无法判断
  -> INDETERMINATE
```

当 PRECOMMIT source 当前为 DONE，或 POSTCOMMIT 已有准确 binding 时，assurance 使用完整归约表：

| Assurance | PRECOMMIT_NEW_BINDING | POSTCOMMIT_EXISTING_BINDING |
|---|---|---|
| `CONFIRMED` | `SATISFIED`，允许同事务建立新 binding | `SATISFIED` |
| `CHALLENGED` | `INDETERMINATE`，不得建立 binding | `INTERVENTION_REQUIRED`，绑定 impact review / remediation owner 与 resolution condition |
| `INVALIDATED` | `INTERVENTION_REQUIRED`，不得建立 binding | `INTERVENTION_REQUIRED`，旧 binding 不再支持正式 gate |
| `INDETERMINATE` | `INDETERMINATE`，不得建立 binding | `INDETERMINATE` |

多条 edge 采用 fail-closed 合并优先级：`INDETERMINATE` 高于 `INTERVENTION_REQUIRED`，其后是 `WAITING`，
全部 edge 都 `SATISFIED` 才为 `SATISFIED`。`WAITING` 只来自 PRECOMMIT source 尚可正常推进的非终态状态；
POSTCOMMIT 不因 source 当前 lifecycle 产生 `WAITING`。

Source reopen 后，只有 `prior_completion_disposition` 及后续 assurance 决定既有 binding 是否继续支持；source
当前非 `DONE` 本身不把 `POSTCOMMIT_EXISTING_BINDING` 降为 `WAITING`。`PRESERVED` 且 effective closure
全部 confirmed 时 postcommit assessment 可以恢复 `SATISFIED`。这不允许新 consumer 或 recommit 绑定历史
ref：所有新 binding 一律重新进入 `PRECOMMIT_NEW_BINDING` 的 source current-DONE 守卫。

`WAITING` 对应 canonical wake condition。`INTERVENTION_REQUIRED` 和 `INDETERMINATE` 对应有 owner、
resolution condition 与 next review 的 Task blocker；它们不自动令 Task `FAILED`。

`dependency_revision` 只描述 declared edge set。Assessment fingerprint 必须包含 mode 与
`dependency_set_snapshot_id`。Source 状态、completion assurance 或 evidence 改变时，
下游 revision 不一定变化，因此 assessment 还必须比较 `dependency_input_fingerprint`。无关 Task、无关
plan member 或无关 edge 的变化不得令本 Task assessment 失去当前性。

Assessment、reverse index 与 impact projection 均为可重建 read model，不是 permit 或 canonical gate
结果。正式动作必须按 Section 10.14.7 同步重算。

#### 10.14.4 PinnedDoneBinding 与 immutable provenance

下游首次跨越 commitment boundary 时，每条 edge 生成：

```yaml
PinnedDoneBinding:
  binding_id:
  edge_id:
  edge_revision:
  dependency_spec_fingerprint:
  prerequisite_task_id:
  source_completion_ref_id:
  source_lifecycle_generation:
  source_completion_epoch:
  source_result_revision:
  source_completion_commitment_snapshot_id:
  source_done_event_id:
  source_assurance_version:
  source_fence_generation:
  source_fact_versions: []
  goal_id:
  plan_membership_refs: []
  bound_at_event_sequence:
```

`completion_ref_id` 是 Rust 为下列不可变 tuple 生成的稳定 opaque identity：

```text
task_id
+ lifecycle_generation
+ completion_epoch
+ COMPLETION_ASSESSMENT TaskCommitmentSnapshot ID
+ DONE Event ID
```

调用方不得自选、复用或仅按 task_id 猜测它。相同 tuple 只能有一个 ID；任一组成字段不同就是不同
completion ref。该 ID 只用于准确定位一次历史完成，不携带结果内容或新的执行权限。

首次 binding 必须满足：

```text
source 当前 Task state == DONE
source completion ref assessment == CONFIRMED
source CompletionCommitmentSnapshot、result、Validation decision 和 DONE Event 一致
source DONE Event sequence 早于 dependent commitment
```

即使旧 completion 后来被确认 `PRESERVED`，新的 consumer 也不能在 source 当前非 `DONE` 时绑定它。
`PRESERVED` 只可能维持已有 binding 的支持。零 edge Task 仍生成明确的空
`DependencySetSnapshot`，证明该次 commitment 已完成 dependency 检查。

传递 assurance 只沿不可修改的历史闭包计算：

```text
CompletionCommitmentSnapshot
  -> DependencySetSnapshot
  -> PinnedDoneBinding
  -> source CompletionCommitmentSnapshot
  -> source snapshot 的 PinnedDoneBindings
```

不得以 source 当前 DependencySpec、current commitment pointer、current plan 或最新 result 替换历史
闭包。唯一允许终止某个受挑战上游分支的是 Section 10.14.8 定义的、当前有效且精确绑定该 binding 与
upstream completion ref 的 `UNAFFECTED` provenance resolution cut；该 cut 作为新的 assurance evidence
进入闭包，不修改或删除原 binding。闭包缺失、引用 identity mismatch、未知 schema、非法 Event 顺序或形成环时，一律
`INDETERMINATE` 并拒绝正式 gate。

`CHALLENGED / INDETERMINATE` 可以沿 assurance 闭包传播并阻止下游 gate；`INVALIDATED` 结论、
reopen、重跑、补偿和 Task 状态变化必须逐 Task、逐 completion ref 决定。传递 challenge 不等于
传递生命周期 mutation。

#### 10.14.5 Completion reference assurance 与 fence

Event 与不可变 spec / snapshot / fact row 是 canonical。Rust 在同一事务中维护以下可重建当前投影：

```yaml
CompletionReferenceAssuranceState:
  completion_ref_id:
  assurance_version:
  fence_generation:
  reducer_contract_version:
  last_fact_event_id:
  last_fact_event_sequence:
  assessment: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE
  active_reason_refs: []
```

确定性归约顺序：

```text
存在不可逆证伪事实
  -> INVALIDATED

存在未解决反证或明确 uncertainty
  -> CHALLENGED

事实、引用、policy 或 reducer 无法完整判断
  -> INDETERMINATE

其余
  -> CONFIRMED
```

强制规则：

```text
INVALIDATED 对准确 completion ref 是吸收态
CHALLENGED / INDETERMINATE 均阻止正式 gate
PRESERVED 只能解决它对应的 uncertainty，不能覆盖其他反证
每个 reason 必须绑定 reason_code、source_fact_refs、authority 和 Event sequence
任一 assurance fact、resolution、evidence、artifact、waiver、time 或 policy 变化增加 assurance_version
进入非 CONFIRMED 时增加 fence_generation
fence_generation 单调递增，永不减少
```

会触发 assurance 重算的事实至少包括：

```text
source reopen disposition
Validation evidence 被证伪
ArtifactRef 缺失、digest mismatch 或访问不足
result reference 损坏
waiver 到期、撤销或 policy 失效
evidence freshness 到期
reducer / policy / canonicalization contract 不可用
completion snapshot 损坏或 canonical facts 无法一致归约
```

没有自然 Event 的时间到期必须在正式 gate 中使用 Rust 权威 `as_of` 和当前 time policy 重算。临时
不可访问或事实不足通常形成 `CHALLENGED / INDETERMINATE`；只有确切证伪才形成 `INVALIDATED`。

#### 10.14.6 Phase-specific TaskCommitmentSnapshot

```yaml
TaskCommitmentSnapshot:
  commitment_snapshot_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  task_spec_revision:
  commitment_revision:
  phase: EXECUTION_ADMISSION | CANDIDATE_ADOPTION | COMPLETION_ASSESSMENT
  parent_snapshot_id: optional
  supersedes_snapshot_id: optional
  dependency_set_snapshot_id:
  dependency_closure_snapshot_id:
  validation_set_snapshot_id:
  candidate_origin: null | RUN_RESULT | DIRECT_RESULT_ADOPTION | REOPENED_PRIOR_RESULT
  candidate_origin_event_id: optional_by_phase
  run_id: optional_by_candidate_origin
  result_revision: optional_by_phase
  completion_validation_decision_refs: []
  completion_waiver_refs: []
  created_event_sequence:
```

Task projection 分别保存 current execution、candidate 和 completion pointer。阶段不变量：

```text
EXECUTION_ADMISSION
  -> candidate_origin、candidate_origin_event_id、run_id 与 result_revision 为空
  -> dependency_set_snapshot_id、dependency_closure_snapshot_id 与 validation_set_snapshot_id 必填

CANDIDATE_ADOPTION
  -> candidate_origin、candidate_origin_event_id 与 result_revision 必填
  -> RUN_RESULT 时 run_id 必填且必须属于当前 execution snapshot
  -> DIRECT_RESULT_ADOPTION / REOPENED_PRIOR_RESULT 时 run_id 必须为空
  -> dependency set、current closure 与 Validation Set 必填
  -> parent 必须是当前 generation / completion epoch 的有效 execution snapshot

COMPLETION_ASSESSMENT
  -> dependency set、current closure、Validation、result、准确 completion decision evidence refs 必填
  -> parent 必须是当前 candidate snapshot
```

```text
task_id + lifecycle_generation + completion_epoch + commitment_revision 唯一
每个 phase snapshot 的 task_spec_revision 必须等于创建时 current Task spec
每创建一个 TaskCommitmentSnapshot 都分配该 Task 的下一个单调 commitment_revision
同一事务创建多个 phase 时按 EXECUTION_ADMISSION -> CANDIDATE_ADOPTION -> COMPLETION_ASSESSMENT 连续分配
相同 Inbox command_id 的幂等重放返回原 snapshots，不再次增加 revision
每个 phase 最多一个 current snapshot
superseded snapshot 永不重新 current
supersedes 只能指向同 phase
parent 只能按 EXECUTION -> CANDIDATE -> COMPLETION
同一个 snapshot 内不同 Task / lifecycle generation / completion epoch 或无 lineage 的 dependency、Validation、result 不得拼接
DependencyClosureSnapshot 的 task、generation、completion epoch、phase 和 set snapshot 必须与 commitment 完全匹配
```

Phase snapshot 表达各阶段当时的 current envelope，所以 child 可以在同一 Task / generation / epoch 内绑定比
parent 更新的 Validation Set 或 assurance closure，但必须有 `ValidationSetExtended`、assurance Event 或 policy
revision 的可核对 lineage；不得拿无关 set 或 result 拼接。Candidate refresh 必须保持 result / origin / Run
provenance 完全不变。活动 Run 始终受自己的 execution snapshot 约束，后续 phase 演进不得回写其 permit。

`DIRECT_RESULT_ADOPTION` 只允许 Jenn 或 Nobao 在既定 Task spec 内，把已有、低披露、完整性可校验的结果
引用登记为 candidate；它不签发执行权、不证明结果正确，也不跳过 required Validation。`REOPENED_PRIOR_RESULT`
只允许 DONE reopen 后在新 completion epoch 中明确采用同一历史 result revision，并创建新的 execution 与
candidate commitment；旧 Validation 和 permit 仍不继承。任何没有 current candidate 的 Task 都不得启动
结果验收 Validation、进入 `VERIFYING` 或 `DONE`。

`candidate_origin_event_id` 不接受任意历史 Event：

```text
RUN_RESULT
  -> 必须是本次 candidate transaction 的 RunResultAdopted Event
  -> Event 中的 run_id、execution_epoch、result_revision 与 snapshot 完全匹配

DIRECT_RESULT_ADOPTION
  -> 必须是本次受权 Command 产生的 DirectResultAdopted Event
  -> Event 中的 actor、Task、result revision 与完整性引用完全匹配

REOPENED_PRIOR_RESULT
  -> 必须是本次 TaskReopened Event
  -> Event 同时固定 prior result identity、新 lifecycle generation 与新 completion epoch
```

任一 origin、Event kind 或 identity mismatch 都拒绝整个事务。

Validation Set、assurance version、fence generation 或 closure policy 改变，而同一 result / origin 仍可保留时，
正式 Validation start 或 `complete_task` 不得把新 closure 与旧 candidate 临时拼接。Rust 必须在外层 Command
事务中执行不可独立调用的 `candidate commitment refresh`：

```text
确认 Task / lifecycle generation / completion epoch、result revision 与 candidate origin 完全不变
确认没有非终态 Run / Validation、活动 Control Intent、UNKNOWN 或未核对 effect
确认 current Validation Set 与 Dependency Set pointers
同步重算全部 assurance；只接受 CURRENT + SATISFIED + effective closure CONFIRMED
创建当前 CANDIDATE_ADOPTION phase 的 DependencyClosureSnapshot
创建 superseding CANDIDATE_ADOPTION TaskCommitmentSnapshot
  -> parent 仍是原 current execution snapshot
  -> result / origin / origin Event / Run provenance 与旧 candidate 完全相同
  -> 绑定 current Validation Set、Dependency Set 与新 closure
current_candidate_commitment_id = 新 candidate snapshot
current_completion_commitment_id = null
commitment_revision 单调增加
```

Refresh 不创建 Run、execution epoch、permit 或新 result，也不修改原 execution snapshot。业务守卫失败时，
不提交 refresh、Validation start 或 completion writes；Rust 在一个拒绝事务中持久化 Inbox rejection，并在
dependency 已不再满足时同时追加精确 fence / blocker Event。只有 CAS、`BUSY_SNAPSHOT` 或数据库技术冲突
才整笔 rollback / retry，不伪造业务拒绝。相同外层 `command_id` 重试不得重复创建 refresh snapshots、
rejection Event 或 blocker。

`task_spec_revision` 是 commitment envelope 的硬边界。非终态 Task 修改 spec 时，必须通过受权、CAS 和
Inbox 幂等的 `ReviseTaskSpec` 事务，并要求没有非终态 Run / Validation、活动 Control Intent、UNKNOWN 或
未核对 effect。若 Task 已跨 commitment boundary，同一事务必须：

```text
fence 全部旧 permit
追加 TaskSpecRevised Event
清除 validation_set_snapshot_id 与 dependency_set_snapshot_id
清除 current execution / candidate / completion commitment pointers
supersede 旧 active_dependency_fence_ref，但保留其 source reason / Event 供新 assessment 使用
清除 result_revision，并把旧 candidate 保留为历史
phase_checkpoint = READY
按 current DependencySpec / plan membership 同步重算 precommit assessment，并建立新的 WAITING / BLOCKED context（如适用）
触发 Priority context REVIEW_REQUIRED
要求下一次正式动作重新冻结 Validation / Dependency 并重新采用 candidate
```

旧 spec 的 TaskCommitmentSnapshot 不得启动 Validation、签发 permit、采用 candidate 或完成 Task。DONE Task
不得直接 revision spec；必须先 reopen 或建立 replacement Task。Task spec mutation 与 `create_run`、
candidate adoption、Validation start 和 `complete_task` 使用同一 Task CAS，不能跨 revision 拼接。

Task 进入 `DONE` 时，CompletionCommitmentSnapshot、DONE Event 与 current Task projection 在同一事务
写入。PinnedDoneBinding 只能绑定这份 completion snapshot。Validation Set 只证明要求是什么，不能单独
证明已经通过；completion snapshot 必须引用实际支持完成决定的当前 PASSED attempts、有效 waiver 与其他
required evidence。

本决议中的 `CompletionCommitmentSnapshot` 专指
`TaskCommitmentSnapshot(phase = COMPLETION_ASSESSMENT)` 在 `DONE` 事务中封存的实例，不是另一种
snapshot 类型，也不增加新的 canonical object 或并行 schema。

`DependencySetSnapshot` 只固定本 Task 的直接 edge membership 与 `PinnedDoneBinding`。每次创建 phase-specific
TaskCommitmentSnapshot 时，还要在同一一致读集中创建或复用以下不可变 authority envelope：

```yaml
DependencyClosureSnapshot:
  dependency_closure_snapshot_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  phase: EXECUTION_ADMISSION | CANDIDATE_ADOPTION | COMPLETION_ASSESSMENT
  dependency_set_snapshot_id:
  completion_refs:
    - completion_ref_id:
      assurance_version:
      fence_generation:
  impact_resolution_refs:
    - impact_resolution_id:
      impact_review_completion_ref_id:
      assurance_version:
      fence_generation:
  dependency_closure_fingerprint:
  reducer_contract_version:
  policy_bundle_revision:
  assessed_at_event_sequence:
```

`completion_refs` 必须按 canonical order 覆盖应用当前有效 cut 后实际遍历的直接和传递 assurance ancestry，
包括 cut 所依赖的 impact-review completion refs；被 cut 终止的失效 upstream ref 仍由对应 resolution record
精确保留，但不再被伪装为 `CONFIRMED`。`impact_resolution_refs` 固定遍历中实际采用的 provenance
resolution cuts 及其 review assurance binding；零 edge 使用两个空列表。该 snapshot 是
Task-owned immutable record，不是异步 projection，也不增加正式领域对象。它只证明一次 gate 读到了什么，
自身不授予权限；Rust 和 host 仍必须核对其中每个 version / fence 当前匹配。两份 snapshot 的名称不得混用：

```text
dependency_set_snapshot_id
  -> 直接 edge 和 binding membership

dependency_closure_snapshot_id
  -> 某 phase 对完整传递 assurance closure 的版本化 authority envelope
```

dispatch claim、host effect check 和 Goal closure 等不会创建 Task commitment 的 gate，必须在一致读集中按同一
规范化算法重算 closure，并与已绑定 snapshot、current assurance / fence 比较；它们不得为了让旧 permit
继续有效而另建一个 snapshot。

#### 10.14.7 同步 gate、事务与 permit

以下动作必须在同一 Rust / SQLite 写事务的一致读集中同步重算 canonical dependency facts：

```text
create_run
permit issuance
dispatch claim
effectful Validation start
candidate adoption
complete_task
CLOSED + ACHIEVED Goal closure
```

尚未建立 binding 的 commitment 使用 `PRECOMMIT_NEW_BINDING`，并在同一事务创建 bindings 后再以
`POSTCOMMIT_EXISTING_BINDING` 核对新 snapshot；已有 current bindings 的所有后续 gate 只使用
`POSTCOMMIT_EXISTING_BINDING`。调用方不得自行选择 mode。

正式 gate 只接受：

```text
assessment freshness == CURRENT
assessment outcome == SATISFIED
全部直接与传递 completion assurance == CONFIRMED
全部采用的 impact resolution cut 仍 current，且其 review completion assurance == CONFIRMED
全部相关 fence generation 与读入版本仍匹配
```

v0.1 禁止在事务外完成正式 assurance 决定。事务外结果只能作为规划或 UI 预览；最终写事务必须重新
读取全部 source bindings、重算 immutable provenance closure、检查 Task CAS 和相关 source
`assurance_version`。SQLite transaction 升级冲突或 `BUSY_SNAPSHOT` 必须 rollback 后重试，不能使用旧读集
提交。

SchedulePlanProjection、TimeCriticalPathProjection、Eligibility、Effective ordering 和
TaskPrioritySelectionSnapshot 都不满足本节的正式 dependency gate。它们观察到的 dependency evidence 只可
用于规划、选择和诊断；`create_run` admission 仍必须在本节规定的一致读集中完成完整同步重算。

每个 effectful permit 至少绑定：

```yaml
dependency_authority_binding:
  dependency_closure_snapshot_id:
  completion_refs:
    - completion_ref_id:
      assurance_version:
      fence_generation:
  dependency_closure_fingerprint:
```

任一 completion ref 不再 `CONFIRMED`，或 assurance / fence version 不匹配，旧 permit 永久失效。即使
`UNCERTAIN -> PRESERVED`，旧 permit、dispatch 或 lease 也不恢复；恢复只能使用新 execution epoch、
新 gate 和新 permit。

Outbox `ACKED` 只表示 host 接收。Host 必须在副作用发生前校验当前 permit 与 fence；不支持 fence、
revoke 或 terminal receipt 的 host 进入 `UNKNOWN / BLOCKED`，不得伪造已经停止。已经发生或可能发生的
外部动作继续服从 Control Intent 与 reconciliation。

Fact / Receipt 接纳、UNKNOWN reconciliation、Deadline stop、Control Intent finalizer 和 ledger recovery
不得被 dependency gate 拒绝。

#### 10.14.8 Reopen disposition 与 consumer impact

Section 10.8 的 `prior_completion_disposition` 与 reopen 在同一事务中追加 Event 并更新准确 completion ref
assurance / fence。Source authority 只描述自己的历史完成，不取得 consumer 的 Task、plan、result 或
Goal 决定权。

`UNCERTAIN` 使用追加式命令解决：

```yaml
ResolvePriorCompletionDisposition:
  completion_ref_id:
  base_assurance_version:
  from: UNCERTAIN
  to: PRESERVED | INVALIDATED
  actor:
  basis_refs: []
  reason:
```

该命令不修改旧 Event。`PRESERVED` 不能清除其他 active reason；`INVALIDATED` 不可逆。

DONE consumer 的 impact 由 consumer authority 独立接受：

```yaml
AcceptConsumerImpactAssessment:
  consumer_completion_ref_id:
  challenged_binding_id:
  challenged_upstream_completion_ref_id:
  base_assurance_version:
  expected_challenge_set_fingerprint:
  outcome: UNAFFECTED | INVALIDATED | REMEDIATION_REQUIRED
  impact_review_task_id: required_for_UNAFFECTED
  impact_review_completion_ref_id: required_for_UNAFFECTED
  remediation_task_id: required_for_REMEDIATION_REQUIRED
  remediation_task_lifecycle_generation: required_for_REMEDIATION_REQUIRED
  remediation_task_spec_revision: required_for_REMEDIATION_REQUIRED
  validation_refs: []
  actor:
  basis_refs: []
```

```text
UNAFFECTED
  -> 只解决该 consumer completion 的准确 challenge
  -> 必须具有正式 impact Validation 和 authority
  -> 创建精确范围的 provenance resolution cut
  -> 不复活旧 binding、permit 或执行权

INVALIDATED
  -> consumer completion ref 进入吸收态
  -> 从该 ref 开始逐层挑战下一跳

REMEDIATION_REQUIRED
  -> 保持 challenge
  -> 必须绑定 remediation Task
```

`REMEDIATION_REQUIRED` 的 Task 不接受裸 task ID。它必须存在且不为 `FAILED / CANCELLED`，其 current
lifecycle generation 与 spec revision 必须精确绑定 consumer completion ref、challenged binding、upstream
completion ref、challenge-set fingerprint、remediation success contract、owner、next review 与 resolution
condition。它不得以被挑战 completion 建立循环 Task dependency。Resolution Task revision 变化后，旧
RISK currentness 立即失效并重新评估。

Impact Validation 只提供证据，不能自行决定 consumer outcome。普通已确认 Goal 内的 Task 由 Nobao 管理；
Jenn-only、HUMAN_ACCEPTANCE、顶层 Goal closure 或成功标准变化由 Jenn 决定；Domain Agent 只能 proposal，
Worker、Validator 和 host 只能报告各自事实。

因为 consumer 已经是 `DONE`，不得在它自身终态上偷偷启动新 Validation。`UNAFFECTED` 的
`validation_refs` 必须来自一个独立、linked `DependencyImpactReview` Task 的当前、非豁免、required
`PASSED` Validation；该 review Task 必须已经 `DONE`，其 completion ref assurance 必须为 `CONFIRMED`，
其 Task spec 和 Requirement 精确绑定 consumer
completion ref、challenged binding、upstream completion ref 与 challenge-set fingerprint。它不得以被挑战
completion 建立 Task dependency 来循环证明自己。若需要 Jenn 主观判断，review Task 使用真正的
`HUMAN_ACCEPTANCE` Requirement。Review Task 的成功只提供 evidence，仍不能代替有权限 actor 提交本命令。

每次接受都在同一事务中追加不可修改的 `ConsumerImpactResolution` Event-backed record：

```yaml
ConsumerImpactResolution:
  impact_resolution_id:
  consumer_completion_ref_id:
  challenged_binding_id:
  challenged_upstream_completion_ref_id:
  challenge_set_fingerprint:
  outcome: UNAFFECTED | INVALIDATED | REMEDIATION_REQUIRED
  impact_review_task_id: optional
  impact_review_completion_ref_id: optional
  remediation_task_id: optional
  remediation_task_lifecycle_generation: optional
  remediation_task_spec_revision: optional
  validation_refs: []
  decided_by:
  basis_refs: []
  created_event_sequence:
```

`UNAFFECTED` resolution 是一个窄范围 provenance cut，不是删除历史：assurance traversal 到达准确
`challenged_binding_id + challenged_upstream_completion_ref_id + challenge_set_fingerprint` 时，把当前有效
impact resolution 作为该分支的终止证据，不再让同一个已裁决上游 challenge 穿透到 consumer 之后；原
binding、upstream invalidation 和全部 Event 仍永久保留。这样 consumer completion ref 可以在没有其他
active reason 时重新成为 `CONFIRMED`，后续 closure snapshot 必须同时固定这个 resolution ref。

Cut 不适用于其他 binding、其他 upstream completion ref、后来的新 challenge 或未被 Validation 覆盖的
事实。Impact review completion assurance 不再 `CONFIRMED`、Validation 失效、证据过期、challenge set
改变、resolution ref 损坏或 authority 被证伪时，
cut 立即失去当前效力，consumer assurance 重新进入 `CHALLENGED / INDETERMINATE` 并提升 fence。旧 permit
永不复活。`INVALIDATED` 和 `REMEDIATION_REQUIRED` 不创建 cut。

#### 10.14.9 状态影响、迟到事实与逐层传播

Source completion 的 `assurance_version` 发生任何变化时，绑定旧 version 的 permit 立即永久失效。
若 assessment 进入 `CHALLENGED / INVALIDATED / INDETERMINATE`，还必须先原子提升准确 completion ref
的 fence，而不是等待异步 projection。反向索引只用于影响枚举和状态收口加速，不是安全前提。

若新 assessment 仍为 `CONFIRMED`，历史 completion support 不被挑战，但活动 Run 仍须按旧 permit
失效路径停止新增副作用并安全收口；收口后只能创建新 execution epoch、Run、DependencyClosureSnapshot、
EXECUTION_ADMISSION snapshot 和 permit。它不得给旧 Run 重签 permit，也不得仅因 projection 看起来仍为
`CONFIRMED` 而跳过版本核对。

`CONFIRMED` version 变化且没有活动 Run 时不改变 Task state；下一次 permit 或 dispatch 必须绑定新
version。以下状态影响只适用于 assessment 已不是 `CONFIRMED` 的 consumer：

```text
未 commitment consumer
  -> 重新计算 assessment
  -> WAITING / BLOCKED

非终态 consumer 且无活动 Run
  -> 建立 dependency fence
  -> 按 reducer 进入 BLOCKED

ACTIVE consumer 且存在非终态 Run
  -> Task 保持 ACTIVE
  -> fence permit 与新 effect
  -> 创建或复用 PAUSE intent
  -> 已有 CANCEL 时 CANCEL 优先
  -> Run 和副作用收口后才进入 BLOCKED

VERIFYING consumer
  -> 禁止 complete_task
  -> fence effectful Validation
  -> 允许受控、无副作用的 impact review

DONE consumer
  -> 仍保持 DONE
  -> plan_progress 不变
  -> completion assurance 进入 CHALLENGED
  -> Goal member support 进入 REVIEW_REQUIRED
  -> 不自动 reopen、重跑或补偿
```

当 `ResolvePriorCompletionDisposition -> PRESERVED`、current `UNAFFECTED` provenance cut、新证据或 policy
恢复使 effective closure 重新全部 `CONFIRMED` 时，Rust 必须运行可重入
`DependencyResolutionFinalizer`，不能只更新 assurance projection：

```text
确认 Task generation / completion epoch / dependency revision / set snapshot 仍 current
同步确认 assessment = CURRENT + SATISFIED
同步确认全部 effective closure assurance 与 impact resolution cuts 为 CONFIRMED
确认目标 active_dependency_fence_ref、challenge refs 与待解决 blocker 精确匹配
确认没有非终态 Run / Validation、活动 Control Intent、UNKNOWN 或未核对 effect
追加 DependencyFenceResolved Event（task + fence + assurance version 唯一）
只清除这些已解决 refs 产生的 dependency blocker
仅在 pointer 仍指向同一 fence 时清 active_dependency_fence_ref
按其他 blocker、pause、wake condition 与 phase_checkpoint 重新归约 Task state
```

任一守卫不满足时保持 fence，等待后续 Fact 或 recovery 重试。Finalizer 不复活旧 permit、lease、dispatch、
Run、candidate 或 Validation；下一次执行必须使用新 gate / epoch / commitment / permit，旧 candidate 在正式
Validation 或完成前仍须 candidate commitment refresh。Source resolution 的 fan-out 使用有界、可恢复、
幂等的 consumer finalizer；每一层 consumer assurance 改变后再逐层重算，不以一次全图写入跨越 authority。
DONE consumer 只更新 assurance / Goal support，Task state 和 `plan_progress` 不变。

迟到 `SUCCEEDED / PASSED` 继续作为历史事实入账，但不得形成当前 candidate 或完成资格。迟到事实若揭示
UNKNOWN、矛盾终态或未核对副作用，即使属于旧 epoch，也必须建立 reconciliation blocker；旧事实可以
阻止当前工作，不能推进当前工作。

Assurance challenge 可以沿 immutable closure 传播；consumer completion 只有在自己的 impact 被明确判定
`INVALIDATED` 后，才成为下一层不可逆 invalidation source。系统不得用全图自动 reopen 或自动补偿代替
逐层判断。

#### 10.14.10 RecommitTaskDependencies

旧 binding 失效后，非终态 Task 使用受控 recommit，避免形成永久死路：

```yaml
RecommitTaskDependencies:
  command_id:
  actor:
  task_id:
  expected_task_aggregate_version:
  base_completion_epoch:
  base_commitment_snapshot_id:
  unchanged_edge_set_fingerprint:
  replacement_source_completion_refs:
    - edge_id:
      prerequisite_task_id:
      completion_ref_id:
  prior_effect_disposition: NO_EXTERNAL_EFFECTS | COMPENSATED | RETAINED_WITH_AUTHORIZED_EVIDENCE
  effect_evidence_refs: []
  reason:
```

前置守卫：

```text
Task 非终态
无非终态 Run 或 Validation
无活动 Control Intent
所有旧 permit 已 fenced
所有 effect 已核对
无 UNKNOWN
edge membership 完全不变
每条 edge 恰好一个 replacement ref，不得缺失、重复或多出
replacement prerequisite_task_id 与 edge prerequisite 完全匹配
每个 source 当前仍为 DONE，且 replacement ref 就是它的 current completion ref
每个 ref 的 Task、generation、completion epoch、completion snapshot、result、Validation decisions 与 DONE Event 一致
每个 source DONE Event 早于本次 recommit commitment
每个 replacement ref 的直接和传递 assurance 全部为 CONFIRMED
同 Goal、非 shared endpoint 与 plan membership 仍 current
```

`RETAINED_WITH_AUTHORIZED_EVIDENCE` 只适用于已知副作用；不能接受 UNKNOWN。补偿本身是新的受治理
Run，仍要求 idempotency、permit、host gate 和 reconciliation。

同一事务中：

```text
追加 DependencyRecommitStarted
存在 candidate 时追加 CandidateRejectedByDependencyRecommit
result_revision = null
current_candidate_commitment_id = null
current_completion_commitment_id = null
phase_checkpoint = READY
completion_epoch 增加一次
commitment_revision 增加一次
旧 Validation 失去当前裁决权，但历史不删除
创建相同 edge membership 的新 DependencySetSnapshot
逐 edge 创建指向上述 current source completion refs 的新 PinnedDoneBindings
创建当前 epoch 的 Validation Set snapshot
创建当前 assurance versions / fences 的新 DependencyClosureSnapshot
创建绑定三个 snapshot 的新 EXECUTION_ADMISSION snapshot
dependency_set_snapshot_id = 新 DependencySetSnapshot
validation_set_snapshot_id = 新 Validation Set snapshot
current_execution_commitment_id = 新 EXECUTION_ADMISSION snapshot
追加 DependencyFenceSupersededByRecommit，精确引用旧 active_dependency_fence_ref 与旧 bindings
只解决由这些旧 bindings 产生的 dependency blocker，并将匹配的 active_dependency_fence_ref 置 null
追加 DependencyRecommitCompleted
```

Recommit 不得清除其他 dependency reason、UNKNOWN、Deadline、Budget、permit、policy、Control Intent 或任意
非本次旧 bindings 产生的 blocker。若新 closure 在提交前不再 `CONFIRMED`，整个事务 rollback，不得先清 fence。

相同 `command_id` 最多增加一次 epoch。DONE Task 不允许 recommit，必须先 reopen。Reopen 后尚未形成
当前 generation commitment 时使用普通首次 commitment，不再次增加 epoch。新的 candidate 必须绑定
recommit 后的新 execution snapshot 和 origin-specific source。`RUN_RESULT` 还必须绑定新的 execution epoch、
Run 与 permit；`DIRECT_RESULT_ADOPTION` 按 Section 10.14.6 的无 Run 规则处理。Recommit 本身不自动采用
candidate。

如果 Task 仍有有效 PAUSE 或其他 blocker，`phase_checkpoint = READY` 不直接覆盖 reducer 优先级；最终
Task state 仍按 Section 10.4 计算。

#### 10.14.11 Mutation、plan、authority 与恢复

```text
commitment 前
  -> 可以使用新 dependency revision 增删 edge

commitment 后
  -> 当前 lifecycle generation 禁止增删 edge
```

Recommit 只能把完全相同的 edge membership 绑定到新的 DONE Event。真正需要增删 edge 时，非终态 Task
必须安全取消并由新 plan revision 建立 replacement Task；DONE Task 使用 reopen、remediation 或
replacement。Dependency spec mutation 与 `complete_task` 使用同一 Task CAS：修改先提交时旧 snapshot
不得完成；完成先提交时修改不得追溯改写 DONE。

Edge 保存 goal、plan 和 stable membership refs。无关 plan member 变化不影响 dependency currentness；
影响本 Task 或 edge membership 的 plan revision 必须显式 carry forward、replace 或使后续 gate fail-closed，
不得静默把历史 snapshot 当作新计划事实。Plan revision 永远不能删除旧 Event、binding、fence 或 challenge。

权限：

```text
Jenn
  -> 最高 dependency、prior completion 和 consumer impact 决定权
  -> Jenn-only / HUMAN_ACCEPTANCE / 顶层 Goal 事项

Nobao
  -> 在已确认 Goal 和既定成功标准内管理普通 dependency spec、disposition、impact 与 recommit

Domain Agent
  -> 只能在授权领域提出 proposal

Worker / executor / Validator / host / UI
  -> 只能提交各自事实或转发真实 actor Command

Rust core
  -> 唯一 spec、snapshot、assurance、fence、CAS、state 和 projection 写入者
```

Jenn 也不能通过 disposition 或 effect retention 绕过 UNKNOWN、未收口副作用、P3 或其他现有硬边界。
Edge 创建权不授予 source 或 dependent 对对方生命周期、结果、权限或 Goal 的额外控制权。

启动恢复必须先验证 Event、immutable snapshot、current pointer 与 `last_event_id` 对齐，恢复 completion-ref
fence，重建 reverse index，扫描 assurance / observed revision / reducer version mismatch，重算 assurance，
恢复 Control Intent、Outbox、finalizer 和 effect reconciliation，最后才开放新 permit。Snapshot 缺失、
fingerprint mismatch 或 policy 不可用时不得从历史 digest 猜测为 `CONFIRMED`。

#### 10.14.12 最终不变量

```text
Dependency 不增加正式领域对象数量
Dependency 不直接 set Task state
PINNED_DONE_EVENT 只证明历史完成前置，不证明结果内容等价
新的 consumer 只绑定 source 当前 CONFIRMED DONE
历史 closure 只沿 immutable commitment provenance 计算
异步 projection 永不授权
正式 gate 只接受 CURRENT + SATISFIED + 全闭包 CONFIRMED
Fence 后旧 permit 永不复活
UNKNOWN 不得被 disposition、impact、recommit 或 Jenn 判断绕过
活动 Run 存在时 dependency fence 不覆盖 Task ACTIVE 强不变量
迟到事实继续入账，但旧 epoch 不推进当前 Task
DONE consumer 不自动 reopen，plan_progress 不自动变化
Challenge 可以传递，invalidation 与生命周期动作逐层决定
UNAFFECTED 只能通过 current impact Validation 支撑的精确 provenance cut 终止对应 challenge 分支
Post-commit edge mutation 不追溯生效
Dependency 不传播 Priority、Deadline、Budget、权限或 Goal ancestry
Cross-Goal、FOLLOW_CURRENT 和 result dependency 不进入 v0.1
```

### 10.15 Task Scheduling Architecture Boundary v0.1

> **Pending R1 synchronization:** The already accepted three-layer boundary below remains authoritative. Every tighter
> R1 clause in this Section that is named by Section 2.1 is a non-authoritative replacement mirror with no effect before
> Jenn freezes the complete atomic bundle. No implementation or activation is authorized.

Jenn 正式选择：

```text
滚动时间规划
+ 基于当前事实的事件驱动 Task 选择
+ 原子执行准入
```

这里的“事件驱动”表示相关 canonical fact 改变后重新评估，不承诺 hard real-time、固定毫秒级 latency
或确定的派发时限。该合同只冻结层次、权威和安全边界；Duration、Calendar、Capacity、effective-order
和传统时间关键路径的精确字段与算法仍按本节末尾的顺序逐项讨论。

#### 10.15.1 三层控制链

```text
Rolling planning
  -> 读取带版本的当前事实
  -> 生成有界、可重算的 SchedulePlanProjection / TimeCriticalPathProjection
  -> 只预测，不授予执行权

Current-fact selection
  -> Eligibility
  -> Effective ordering
  -> 现有 TaskPrioritySelectionSnapshot
  -> 只留下选择证据，不授予执行权

Atomic execution admission
  -> create_run 同步重新读取当前 canonical facts
  -> 只有准入事务成功，才创建当前 execution commitment、Run、permit 与 Outbox intent
  -> execution host 在副作用前继续执行本地 gate
```

三层共享同一个 GlobalTaskLedger 和 Rust 单写入顺序，不建立第二个 scheduler ledger、第二套 Task 状态或
第二个 selection authority。Planner、Dashboard、Workbench、VCPChat、VCPMobile、Domain Agent、Worker 和
external solver 都不能直接写 Task 状态、创建 Run 或签发 permit。

#### 10.15.2 Rolling planning 的边界

Rolling planning 在一个有界未来区间内生成建议排程，并在相关事实或 policy revision 改变后允许重算。
精确 horizon、步长、刷新频率、稳定区间和重排阈值尚未冻结。
滚动窗口只决定本轮预测看多远，不增加、删除或替换 Goal plan member，不创建 Dependency binding，也不让
窗口外的 canonical plan work 消失；窗口覆盖不足时只能降低 forecast 自身的完整度。

当前已经可以作为规划输入的 canonical fact class 是：

```text
Task lifecycle / plan membership
Task Dependency v0.1
Task Priority v0.1
Goal and Task Deadline v0.1
Goal and Task Budget v0.1
已冻结的 permit、P3、Control Intent、UNKNOWN 和 host fact 边界
```

以下输入只有在各自专项合同被 Jenn 接受后才可成为 canonical scheduling input：

```text
Duration Estimate
Calendar
Capacity
```

缺少这些未来合同或当前值时，planner 必须明确表现为不能形成相应时间或资源预测，不得猜零、使用隐藏默认值、
阻止原本合法的非时间型执行，或改变 Task / Goal canonical state。

SchedulePlanProjection 是计划建议，不是：

```text
Task lifecycle state
plan_revision mutation
not_before gate
DeadlineConstraint
Budget reservation
capacity claim
permit
Run
执行承诺
```

预计开始时间不是执行资格，预计结束时间不是完成事实。Projection 可以过期、删除和无副作用重建；任何持久化
projection 都必须带足够 input revision / event sequence provenance 供 Rust 判断 currentness。精确 schema 留给
后续专项合同。

内置或外部 planner 只能提出候选 projection。外部 optimizer / solver 的输出必须作为无权 proposal 进入 Rust
边界；不得直接修改 canonical plan、Task、Priority、Dependency、Deadline、Budget、Run、permit 或 Outbox。

#### 10.15.3 Eligibility、Effective ordering 与 selection

Eligibility 与 Effective ordering 必须分开：

```text
Eligibility
  -> 判断 Task 是否可以进入本轮普通候选集
  -> 不合格 Task 不能靠分数、Priority 或 forecast 变合格

Effective ordering
  -> 只在本轮合格候选之间形成确定性顺序
  -> 不回写 base_priority_class
```

当前 Task state、Dependency、Deadline、Budget、permit eligibility / revocation / fence facts、P3、host 能力、
Control Intent、UNKNOWN 和一个 Task 最多一个非终态执行 Run 等硬条件都必须被 selection 观察；但
selection 的观察结果仍不是正式
admission。Eligibility reason、aging、公平性、backoff、Jenn focus、temporary expedite、BACKGROUND 最低服务、
连续高优先上限和 stable tie-break 的精确 policy 尚未冻结。

现有 `TaskPrioritySelectionSnapshot` 是唯一 canonical selection record。它是 Event 的不可变内嵌值，不是
正式领域对象、reservation、lease、permit 或长期令牌。selection 本身：

```text
不领取 capacity
不预留 Budget
不创建 Run
不写 Outbox
不修改 Task state
不保证稍后仍能准入
```

Task 未被选择、暂时没有可用顺序或 projection 无法形成，不等于 Task `FAILED / BLOCKED / WAITING`，也不产生
Run failure。相关事实变化后可以事件驱动地重新评估；不得盲从旧 projection 或旧 selection。

#### 10.15.4 原子执行准入与 host gate

`create_run` 是普通 execution Run 的 canonical admission boundary。它必须在 Section 10.5、10.11、10.12、
10.14 和 P3 / TaskPermit 既有合同下，同步重新检查至少：

```text
Task 当前 state、aggregate version、lifecycle generation 和 execution epoch
当前 candidate disposition 与一个非终态执行 Run 上限
活动 Validation / Control Intent、UNKNOWN 和未核对 effect
当前 Validation Set / Dependency Set commitment 条件
CURRENT + SATISFIED dependency assessment 与全闭包 CONFIRMED assurance
全部适用 Hard Deadline
全部适用 HARD_CAP Budget
当前 authorization / policy / P3 / host capability facts
```

Selection 后任何事实改变都可以令 `create_run` 拒绝。业务守卫失败只持久化既有合同允许的 rejection、fence
或 blocker，不得留下半个 execution commitment、Run、permit、BudgetReservation 或 Outbox；SQLite / CAS
技术冲突整体 rollback / retry。

准入成功时，继续沿用既有原子边界：current execution commitment、适用的 BudgetReservation、Run、Event、
permit 和 Outbox intent 在同一 Rust / SQLite 写事务中形成一致结果。Planning 和 selection 都不得提前执行
其中任何一步。

会占用普通 executor、调用 provider / external host 或产生副作用的 Validation 不能成为旁路。在独立的
`Validation Execution Admission` 合同被 Jenn 接受前，每个 effectful Validation 必须绑定一个通过
`create_run` admission 创建的 Run，并继续通过既有 `effectful Validation start` 同步 gate。纯 ledger、
无副作用复核、HUMAN_ACCEPTANCE 和不产生外部副作用的正式 Validation attempt 可以沿既有独立 attempt 路径
启动，不因此占用普通执行容量。

未来若采用独立 Validation admission command，只有 Jenn 冻结的等价合同才能启用；它必须提供与本节等价的
current-fact 重检、原子持久化、permit、fencing、host gate 和恢复保证。普通 `NON_PREEMPTIVE` 约束适用于
全部已经 admission 的普通工作，包括 execution Run 和 effectful Validation Run。

Capacity v0.1 尚未冻结，因此本合同不声称当前已经存在 CapacityReservation、pool、unit、lease 或 allocation。
本合同只冻结两个约束：

```text
selection 不取得 capacity ownership

若未来 Capacity 合同令 canonical allocation 具有排他资源占用意义或构成 admission prerequisite
  -> 不得在 admission 失败后留下孤立 allocation
  -> 必须纳入 create_run 原子事务，或由新的 ADR 证明等价且可恢复的 fenced protocol
  -> allocation 自身永不授予执行权
```

SQLite 事务不能冒充与外部 host 的分布式事务。对应 execution host 拥有真实执行进程、会话和本机可用事实；
它必须在副作用发生前重验当前 permit、fence、capability 和本地 availability。Host 拒绝或无法确认时只提交
Fact / Receipt，由 Rust 按既有 Run、UNKNOWN 和 reconciliation 合同处理；host 不能直接写 Task 状态。

#### 10.15.5 NON_PREEMPTIVE 与 control / recovery lane

普通 scheduling v0.1 冻结为：

```text
NON_PREEMPTIVE
```

新的 Priority、selection、schedule revision 或预测变化不自动暂停、取消、替换或终止活动 Run。未来
preemptive scheduling 必须另立 v0.2+ 合同，并证明 Control Intent、host capability、fencing、UNKNOWN 和
恢复窗口全部闭合。

以下工作不进入普通 effective-order 竞争：

```text
Fact / Receipt 接纳
UNKNOWN reconciliation
Deadline stop
活动 Control Intent finalizer
lease / crash recovery
ledger integrity recovery
```

它们走独立 control / recovery lane，但这不是角色可填写的“超级 Priority”，也不能把普通业务执行伪装成
control work。Fact 接纳、UNKNOWN reconciliation、stop/fence、finalizer 和 ledger recovery 自身服从各自的
authority 与 safety 合同，不得被不适用的普通 Dependency、Budget、Validation 或 permit admission gate 阻断；
一旦 control work 需要新增付费 provider call、外部副作用或扩大 effect scope，适用的 Jenn authority、P3、
Budget、permit 和 host safety gate 仍然有效。独立 worker slot、预留容量、处理时限和饥饿保护的精确实现留给
Capacity 与 scheduling policy 专项合同。

普通 admission 不得占用或阻断完成本地 Rust reducer、Fact / Receipt 接纳、fence 持久化、stop dispatch、
Control Intent finalizer 和 recovery read barrier 所需的最小控制路径。这个架构保证不等于已经冻结具体 slot、
pool 数量、容量单位或 latency SLO；这些数值与实现仍留给 Capacity v0.1。

Deadline hard stop、dependency fence、Jenn / Nobao 的既有 Control Intent、P3 与 host safety stop 是各自合同的
安全控制，不属于 scheduling preemption。

#### 10.15.6 Timer、恢复与投影边界

Timer 只负责请求重新评估：

```text
setTimeout / node-schedule / VCP scheduler / process uptime
  -> wake-up optimization only

GlobalTaskLedger current facts + Event
  -> due fact、missed wake-up 和恢复权威
```

Timer 到期、重复、延迟或丢失都不能直接创建 Run、签发 permit、修改 Task 或执行副作用。进程重启必须从总账
重建待唤醒事实；重复 wake 只触发幂等重算。`projected_start_at` 不是 durable wake authority，Calendar window
打开也只能请求重新选择。Calendar recurrence、catch-up 和 overlap policy 尚未冻结。

四种投影必须保持分离：

```text
Critical Work Frontier
  -> Goal 成功路线的逻辑必要工作；参与 Goal Health

SchedulePlanProjection
  -> 有界未来排程建议

TimeCriticalPathProjection
  -> 传统 precedence / duration / calendar 时间分析；精确合同未冻结

ResourceScheduleProjection
  -> 加入 capacity 竞争后的资源受限预测；继续延后
```

后三者都不增加正式领域对象，不授予执行权。任何 schedule / critical-path projection 都不得改变
`plan_progress`、Goal success criteria、Goal closure、Task completion、Task state、base Priority、Dependency、
Validation requirement、Deadline、Budget、permit 或 P3。缺失或 stale 的时间投影只影响自身可用性，不能自动
把 Goal 标成 `BLOCKED / INSUFFICIENT_EVIDENCE`，也不能让逻辑上完整的 Critical Work Frontier 变不完整。

#### 10.15.7 组件责任

```text
Rust core
  -> 当前事实的 Eligibility / Effective ordering 确定性归约
  -> TaskPrioritySelectionSnapshot 唯一写入
  -> create_run 同步 admission 与既有原子事务
  -> 持久化 projection 的版本/currentness 接纳和无副作用重建边界

JavaScript shell
  -> 请求 planning / selection
  -> timer wake-up
  -> Outbox dispatch 与 host Fact / Receipt 接入

execution host
  -> 报告真实 capability / availability / execution-session facts
  -> 副作用前本地 gate

UI / Agent / external planner
  -> 提交命令或 proposal，读取 projection
  -> 不直接写 ledger 或取得执行权
```

本节不把尚未冻结的 Duration、Calendar 或 Capacity policy 宣布为 Rust 已拥有的事实合同。

#### 10.15.8 最终不变量与下一顺序

```text
Planning 只预测
Selection 只留下选择证据
普通 execution Run 的执行权只在成功的 create_run admission 中产生
独立 Validation Execution Admission 冻结前，effectful Validation 必须绑定 create_run 创建的 Run
未来 effectful Validation 不能绕过 Jenn 已冻结的等价原子 admission
旧 projection / selection 永不恢复执行权
Scheduler 不直接 set Task state
普通 scheduling v0.1 不抢占活动 Run
Control / recovery lane 与普通排序分离，但不扩大权限
Timer 不是事实权威
Time critical path 不等于 Critical Work Frontier
Resource-constrained scheduling 不冒充传统 CPM
Scheduling 不增加第六个正式领域对象
Scheduling 不建立第二个 ledger 或第二个 selection authority
Schedule revision 不等于 plan / task_spec / result / validation revision
Schedule estimate 不等于 WALL_CLOCK_MS Budget、Deadline 或完成事实
Resource ordering 不创建 Task Dependency edge
```

后续讨论顺序冻结为：

```text
1. Duration Estimate v0.1
2. Calendar v0.1
3. Capacity v0.1
4. Eligibility and Effective Ordering v0.1
5. Atomic Admission and Recovery v0.1 的未决细节
6. Time Critical Path v0.1
7. Resource-constrained Scheduling v0.2+
```

## 11. Run 状态

> **Pending R1 synchronization:** `LEASED` is proposed to mean “bounded start authority committed; actual start not
> yet confirmed.” `RUNNING` still requires canonical `STARTED` or stronger reconciled execution evidence. See Section
> 2.1; this note is not effective before Jenn freezes R1. Section 2.1 also proposes replacing the accepted
> `EXECUTION_ADMISSION`-only provenance bullet below: `TASK_EXECUTION` binds the exact `EXECUTION_ADMISSION` snapshot,
> while `EFFECTFUL_VALIDATION` binds the exact current `CANDIDATE_ADOPTION` snapshot. That replacement likewise has no
> effect before the complete bundle freeze.

已冻结：

```text
QUEUED
LEASED
RUNNING
WAITING
SUCCEEDED
FAILED
TIMED_OUT
CANCELLED
REJECTED
UNKNOWN
```

强制语义：

```text
每个 Run 是一次具体执行尝试
每个 Run 绑定一个 TaskPermit、EXECUTION_ADMISSION TaskCommitmentSnapshot、executor、host、attempt number、lease 和 idempotency key
每个 Run 固定 dependency closure snapshot、completion assurance versions 和 fence generations
Run FAILED 只说明这次尝试失败
REJECTED 表示执行前被许可、能力、前置条件或 host gate 拒绝
取消请求不立即等于 CANCELLED，必须等 host 确认没有继续执行
旧 epoch 或 fence 前的 Run Fact 可以触发 reconciliation 或 blocker，但不得形成当前 candidate 或完成资格
```

### 11.1 UNKNOWN

`UNKNOWN` 是关键安全状态，不是普通错误状态。

进入条件包括：

```text
进程或连接在可能产生副作用后中断
无法证明外部动作是否已经发生
无法证明 host 是否已经接受或执行请求
回执丢失且没有可靠幂等查询
```

强制规则：

```text
UNKNOWN 不得自动重试
UNKNOWN 不得伪装成 FAILED
UNKNOWN 不得伪装成 SUCCEEDED
必须先 reconciliation，再决定后续动作
```

## 12. Validation 类型和状态

已冻结的 Validation 类型：

```text
DETERMINISTIC
RUNTIME_OBSERVATION
INDEPENDENT_REVIEW
HUMAN_ACCEPTANCE
```

已冻结的 Validation 状态：

```text
PENDING
RUNNING
PASSED
FAILED
INCONCLUSIVE
ERROR
CANCELLED
```

强制规则：

```text
Task 在创建或激活时声明 draft required validations
所有当前未豁免的 REQUIRED Requirement 都有有效 PASSED attempt，且至少存在一个当前、非豁免、REQUIRED 的真实 PASSED Validation 后，Task 才有资格进入 DONE
Worker 自己声明成功不能代替 Validation
Run SUCCEEDED 不能代替 Validation
Validation ERROR 表示验证器自身失败，不表示被验证对象失败
Validation INCONCLUSIVE 表示证据不足，不能当作 PASSED
HUMAN_ACCEPTANCE 只用于确实需要 Jenn 主观判断或 Jenn-only 接受权的对象
```

### 12.1 Required Validation set 的组成与权限

正式采用分层合并模型：

```text
required Validation set
  = Nobao 根据 Task 内容声明的验证
  + Rust policy 根据风险强制加入的验证
  + Goal / Domain 合同继承的验证
  + Jenn 明确要求的验证
```

各层权限：

```text
Nobao
  -> 理解 Task 目标并提出任务特定验证

Rust policy
  -> 自动加入安全、权限、副作用和恢复相关的强制验证
  -> 调用方不得删除或降低

Goal / Domain contract
  -> 为下属 Task 提供领域必需验证

Jenn
  -> 可以追加验证
  -> 保留 Jenn-only 的特殊豁免决定权

Domain Agent
  -> 可以在授权范围内提出候选验证
  -> 不能自行删除 required Validation

Worker / executor
  -> 不得修改 required Validation set

Rust core
  -> 合并、去重、保存权威快照并冻结版本
```

分层合并的原则是：诺宝负责理解任务，Rust policy 守住系统底线，Goal / Domain 提供专业要求，
Jenn 保留最终例外权。任何执行者都不能通过减少验收项来让自己更容易完成 Task。

required Validation set 必须明确存在；空集合不具备 `DONE` 资格。

### 12.2 ValidationRequirement 与 Validation attempt 的关系

`ValidationRequirement` 不是第六个正式领域对象。它是 Task Validation Set 内的不可变验收条款；
实现上可以使用关系表存储，但逻辑所有权仍属于 Task 的验收合同。

关系已冻结：

```text
一个 Task
  -> 一个当前 Validation Set snapshot
    -> 多个 ValidationRequirement

一个 ValidationRequirement
  -> 零到多个历史 Validation attempt

一个 Validation attempt
  -> 只对应一个 ValidationRequirement 的一个 revision
```

每个 `ValidationRequirement` 至少具有：

```text
requirement_id
requirement_revision
source / provenance
validation type
acceptance contract 或 validator contract version
被验证的结果范围
requiredness
waivability classification
waiver duration policy
evidence reuse mode
carry-forward equivalence contract version（仅 CONDITIONAL_CARRY_FORWARD）
evidence freshness / expiry rule
enforcement phase
```

每个正式 `Validation` 都是一次 attempt，至少绑定：

```text
validation_id
task_id
requirement_id
requirement_revision
lifecycle_generation
completion_epoch
task_spec_revision
result_revision
task_commitment_snapshot_id
dependency_authority_binding:
  dependency_closure_snapshot_id:
  completion_refs:
    - completion_ref_id:
      assurance_version:
      fence_generation:
  dependency_closure_fingerprint:
validator_contract_version
attempt_number
state
ArtifactRef / evidence digest
actor 或 host
validation method: FRESH_VALIDATION | EVIDENCE_CARRY_FORWARD_REVIEW
source_validation_id / root_source_validation_id（仅证据复用时）
evidence equivalence fingerprint（仅证据复用时）
carry-forward equivalence contract version（仅证据复用时）
```

强制语义：

```text
一个 Requirement 可以有多次历史 attempt
同一 Requirement 同时最多一个非终态 attempt
一个 attempt 只满足一个 Requirement
同一个 Run 可以产生多个 attempt，但 Run SUCCEEDED 不自动让任何 Requirement 通过
正式 attempt 必须引用权威 Validation Set snapshot 内的 Requirement
正式 attempt 必须引用其阶段适用的 current TaskCommitmentSnapshot；effectful attempt 还必须通过当前 dependency gate
冻结前的探索性检查不能自动作为正式验收；后续只能通过明确 carry-forward 决定复用
```

当前 Requirement 是否满足，不由“是否存在任何 PASSED”决定，而由下述条件共同决定：

```text
存在一个 PASSED attempt
  -> 对应当前 requirement_id 和 requirement_revision
  -> 对应当前 lifecycle_generation、completion_epoch、task_spec_revision 和 result_revision
  -> 使用当前 validator contract version，或符合 Section 12.6 的有效复用规则
  -> 其证据仍有效
```

`validation_set_revision` 只表示当前验收清单包含哪些 Requirement reference；它不作为所有
Validation evidence 的统一失效键。新增 Requirement 时，未改变的既有 Requirement evidence
仍可保持有效，只需补验新增项。

完全相同的 Requirement 可以共享 canonical requirement identity 并保留多个 provenance；验收
标准、范围或 validator contract 存在语义冲突时不得静默去重，必须在 snapshot 冻结前由受权规则
解决或令 Task 保持不可推进。

### 12.3 Required Validation set 的承诺边界冻结

正式采用承诺边界冻结，而不是在 Task 创建或仅进入 `ACTIVE` 时冻结。

冻结点是下列事件中最早发生的一个：

```text
创建第一个 Run
启动第一个正式 Validation attempt
Task 第一次进入 VERIFYING
```

在该事件的同一 SQLite 事务中，必须先：

```text
合并四层 Requirement
检查每个 Requirement 的定义和来源完整性
解决重复和语义冲突
记录 Task / Goal / Domain / Policy 的适用版本
生成不可修改的 Validation Set snapshot
读取当前 DependencySpecRevision，验证同 Goal、非 shared endpoint、无重复和无 cycle
同步重算全部 source completion assurance
生成不可修改的 DependencySetSnapshot；零 edge 也必须生成明确空 snapshot
生成不可修改的 DependencyClosureSnapshot；零 edge 也必须固定空 closure
生成该动作所需的 current TaskCommitmentSnapshot，并绑定 Validation Set、Dependency Set 与 closure
若动作是正式 Validation 或进入 VERIFYING，先确认 current result，并创建或复用 CANDIDATE_ADOPTION snapshot
追加 ValidationSetFrozen Event
```

只有随后才允许创建 Run、签发 permit、启动正式 Validation 或进入 `VERIFYING`。Requirement 或
dependency 任一侧未准备好时，Task 只能保持 `READY`、`WAITING` 或 `BLOCKED`，不得跨越承诺边界；
整个冻结与动作事务不得部分提交。没有 current candidate 的 Task 可以创建 Run，但不得启动结果验收
Validation 或进入 `VERIFYING`；运行前 safety gate 仍属于 permit / host policy，不伪装成结果 Validation。

Validation Set snapshot 的生命周期：

```text
DRAFT
  -> FROZEN v1
  -> FROZEN v2（后续合法变化产生新的不可修改快照）
  -> FROZEN v3
```

旧快照始终保留，不得原地修改。暂停、等待和阻塞不会解冻当前快照。

`reopen_task` 后，旧快照作为新一代的起点，但在新的 Run、正式 Validation 或 `VERIFYING` 之前，
必须重新组合并冻结新的 snapshot。已 `DONE` Task 保留其历史快照；新 policy 不得直接追溯改写
历史完成。发现历史风险时应创建 remediation Task；只有原完成证据被证伪时才可 reopen 原 Task。

探索性检查不自动计入正式 Validation；需要先探索任务需求时，应在规划阶段完成，或建立独立的
Discovery Task。

### 12.4 冻结后新增 Requirement 合同

本节只适用于已经 `FROZEN` 的 Validation Set snapshot。冻结前的规划编辑与冻结后的正式扩展
必须分开：

```text
DRAFT
  -> DraftRequirementAdded / Edited / Removed
  -> 可以整理，不构成正式验收承诺

FROZEN
  -> AddRequirement / ReplaceRequirementRevision / AttachRequirementProvenance
  -> 只能从旧快照生成新的不可修改快照
```

冻结后的操作类型：

```text
AddRequirement
  -> 新增一条以前不存在、且验证既有 Task 成功标准的验收条款

ReplaceRequirementRevision
  -> 用新 revision 替换当前 snapshot 对已有 Requirement 的引用

AttachRequirementProvenance
  -> 为完全相同的 Requirement 追加来源；不改变验收语义或验证工作
```

`AttachRequirementProvenance` 不得改变：

```text
requiredness
waivability classification
waiver duration policy
evidence reuse mode
carry-forward equivalence contract
evidence freshness / expiry rule
结果范围
验收标准
validator contract
enforcement phase
effective scope
```

这些字段任一变化都不是 provenance attach，必须使用 `ReplaceRequirementRevision`、
`AddRequirement`，或走 Task / Goal 规格变更。

#### 12.4.1 范围与权限

每个 `AddRequirement` 或 `ReplaceRequirementRevision` 必须带有：

```yaml
scope_basis:
  task_spec_revision:
  existing_success_criterion_ref:
  goal_success_criterion_ref: optional
change_basis:
  - VALIDATOR_IMPLEMENTATION
  - POLICY_CONTRACT
  - GOAL_DOMAIN_CONTRACT
  - TASK_SPEC
impact_class:
  - VALIDATES_EXISTING_OUTCOME
  - CHANGES_TASK_SPEC
  - CHANGES_GOAL_CRITERIA
  - PRE_EXECUTION_SAFETY
```

只有 `VALIDATES_EXISTING_OUTCOME` 可以作为普通 `AddRequirement` 扩展当前 Task。

```text
CHANGES_TASK_SPEC
  -> 必须产生 task_spec_revision；必要时产生 plan revision

CHANGES_GOAL_CRITERIA
  -> 必须由 Jenn 决定，并产生相应 Goal / plan 变更

PRE_EXECUTION_SAFETY
  -> 不得伪装成 Validation Requirement
  -> 必须进入 TaskPermit / host gate
```

权限：

```text
Nobao
  -> 可以增加验证既有成功标准的任务特定 Requirement
  -> 可以提出 Replace，但不能自行改变已冻结验收语义

Rust policy
  -> 可以按明确 policy bundle revision 增加或替换其强制 Requirement

Goal / Domain contract
  -> 可以按明确合同版本产生继承 Requirement

Jenn
  -> 可以增加 Requirement
  -> 决定涉及 Task spec 或 Goal criteria 的变更

Worker / executor / Validation attempt
  -> 不得新增、替换或降低 Requirement
```

Rust core 只检查 authority、版本和引用完整性；它不声称能够自行理解自然语言来判定范围是否真的
未变。

#### 12.4.2 继承与来源版本

Goal / Domain / policy 来源必须声明：

```yaml
effective_scope: FUTURE_ONLY | OPEN_TASKS
source_contract_revision:
source_bundle_hash: optional_for_policy
```

`FUTURE_ONLY` 只作用于后续 Task。`OPEN_TASKS` 也不得直接修改任意 Task；必须为每个目标
非终态 Task 追加明确的 `ValidationInheritanceApplied` Event，并通过本节的 snapshot extension
事务。`DONE` Task 永远不因新来源合同被直接改写；历史风险通过 linked remediation Task 处理。

#### 12.4.3 扩展事务与并发

扩展 Command 至少绑定：

```yaml
command_id:
expected_task_aggregate_version:
base_snapshot_id:
task_spec_revision:
goal_domain_contract_revision: optional
policy_bundle_hash: optional
operation:
reason:
```

Rust core 在同一 SQLite 事务中：

```text
Inbox 幂等检查
-> 检查 Task 非终态、没有活动或未收口 Control Intent
-> 检查没有非终态 Validation；存在 current candidate 时也不得存在非终态 Run
-> 检查 base snapshot、Task spec 和所有来源版本仍匹配
-> 检查 authority、scope_basis、impact_class 和 requirement readiness
-> 创建新的 Requirement / revision / provenance record
-> 从 base snapshot 生成新的 immutable snapshot
-> 追加 Requirement 变化 Event 和 ValidationSetExtended Event
-> validation_set_snapshot_id = 新 immutable snapshot
-> current_completion_commitment_id = null
-> 若存在 current candidate，同步重算 dependency closure
-> closure 通过时，创建或复用新的 CANDIDATE_ADOPTION DependencyClosureSnapshot
-> 创建 superseding CANDIDATE_ADOPTION snapshot：保持同一 result / origin，绑定新 Validation Set、current Dependency Set / closure，parent 仍为 current execution snapshot
-> 更新 current_candidate_commitment_id，并增加 commitment_revision
-> closure 不通过时，追加 CandidateRejectedByValidationSetExtensionDependencyGate，清除 result_revision 与 current_candidate_commitment_id，phase_checkpoint = READY，保留全部历史
-> 提交
```

任一版本过期时，Rust core 不得拿旧来源拼出新快照；必须重新合并或拒绝该 Command。`complete_task`
使用同一 Task CAS：扩展先提交则阻止完成；完成先提交则后续扩展被拒绝。

#### 12.4.4 Requirement readiness 与去重

正式扩展前必须满足 `requirement_ready_for_commitment=true`。最低字段：

```text
canonical_requirement_key
semantic digest
结果范围
validation type
acceptance / validator contract 和版本
责任 actor 或 host
enforcement phase
effect class / permit 需求
requiredness、waivability、waiver duration policy 与 evidence reuse mode
carry-forward equivalence contract 与 evidence freshness / expiry rule（条件复用时）
失败处置方式
source / provenance
```

`canonical_requirement_key` 至少由被验证对象、验收谓词、结果范围、acceptance contract version 和
enforcement phase 组成。只有 key 与 semantic digest 都相同的条款可以 attach provenance。存在差异时必须保留为独立
Requirement，或在生成快照前显式解决冲突；不得按自然语言“看起来差不多”自动合并。

不完整的 Nobao 候选扩展被拒绝，不改变 Task。来源为强制 policy 的不完整 Requirement 则令 Task
进入 `BLOCKED`，直到该强制合同可以被完整表达和执行。

#### 12.4.5 Run、状态与证据影响

每个 Run 创建时必须记录：

```text
execution_commitment_snapshot_id
dependency_closure_snapshot_id
dependency_assurance_versions_and_fence_generations
execution_epoch
permit_id
```

冻结后新增的 Requirement 必须声明为 `POST_RESULT_VALIDATION`。运行中的 Run 继续按创建时的
permit 与 execution commitment snapshot 执行；新 Validation Set snapshot 不修改该 Run 的 snapshot，
也不复活或重签其许可。新 snapshot 约束后续 Run 和最终完成：dependency gate 仍通过时，current result
通过同 result / origin 的 superseding CANDIDATE_ADOPTION snapshot 保留；旧 candidate 和
COMPLETION_ASSESSMENT pointer 立即失去 current 资格。下一次正式 attempt 绑定新 candidate，下一次完成
gate 再创建 completion snapshot，并精确引用扩展后的 Requirement decision。Dependency gate 已不通过时，
current candidate 被拒绝而不是跨 envelope 拼接。新增 effectful Validation 必须等待当前 Run 已知终结且没有
`UNKNOWN` 后才可启动。

状态语义：

```text
READY / WAITING / PAUSED / BLOCKED
  -> 扩展后通常保持原状态；能力缺失时保持或进入 BLOCKED

ACTIVE
  -> 可以扩展；有运行中 Run 时不影响该 Run

VERIFYING
  -> 只有 candidate commitment refresh 成功才保持 VERIFYING
  -> refresh 失败时按 dependency blocker 与 phase_checkpoint = READY 归约，不得留下无 candidate VERIFYING

DONE
  -> 直接扩展被拒绝；新政策使用 remediation Task
  -> 只有完成证据被证伪时才先 reopen

FAILED / CANCELLED
  -> 直接扩展被拒绝；先 reopen 或创建替代 Task
```

证据影响：

```text
AddRequirement
  -> 只新增待满足项，不废掉无关既有 PASSED evidence

ReplaceRequirementRevision
  -> 只使被替换 Requirement 的旧 evidence 失去当前裁决权

AttachRequirementProvenance
  -> 不改变任何 evidence 的当前有效性
```

v0.1 明确不允许：

```text
修改旧 frozen snapshot
通过 attach provenance 暗中改变 Requirement 语义
新增 Requirement 自动 reopen DONE Task
用 Validation extension 补做运行前 host / permit gate
在活动 CANCEL 或未收口 Control Intent 期间扩展 snapshot
```

### 12.5 Requirement 豁免合同

Requirement waiver 是 Jenn 对缺失或无法取得的验收证据作出的明确风险决定。它不是 Validation
状态，不是 `PASSED`，也不删除 Requirement。它是 Event-backed operational record，并在新
Validation Set snapshot 中引用。

#### 12.5.1 可豁免分类

每个 Requirement 必须显式声明：

```yaml
waivability: NON_WAIVABLE | JENN_WAIVABLE
waiver_duration_policy: NOT_APPLICABLE | COMPLETION_SCOPED_ONLY | EXPIRY_REQUIRED
```

未声明时默认 `NON_WAIVABLE + NOT_APPLICABLE`。`NON_WAIVABLE` 必须使用
`NOT_APPLICABLE`；`JENN_WAIVABLE` 必须选择后两种 duration policy 之一。一个 Requirement 有多个
provenance 时，只要任一有效来源为 `NON_WAIVABLE`，最终有效分类就是 `NON_WAIVABLE + NOT_APPLICABLE`。

`NON_WAIVABLE` 包括但不限于：

```text
权限与授权边界
秘密、隐私和数据泄露防护
UNKNOWN reconciliation
外部副作用的已知结果
数据完整性、恢复和关键安全 policy
TaskPermit 与 host gate
```

这些底线不能通过 waiver 伪装为完成。Jenn 可以取消 Task、改变 Goal 或通过新的架构决议改变
未来规则，但当前运行合同下不得把它们标为已满足。

#### 12.5.2 普通 waiver 的资格

普通 `GrantRequirementWaiver` 仅适用于已有具体当前结果的 `VERIFYING` 或安全可解释的
`BLOCKED` Task，并且 target Requirement 当前处于：

```text
PENDING
INCONCLUSIVE
ERROR
CANCELLED
尚未能启动 Validation attempt
```

下列情形不得授予普通 waiver：

```text
Requirement 是 NON_WAIVABLE
存在对应当前结果的有效 FAILED attempt
存在 UNKNOWN、未核对外部副作用或未收口 Control Intent
活动 CANCEL
Task 没有当前 result_revision
```

已知 `FAILED` 不是“缺少证据”。若 Jenn 接受已知缺陷，必须通过 Task spec / Goal 标准的正式
变更产生新的 Requirement revision，或取消 / 替代该 Task；不得用 waiver 把旧标准的失败改写成
完成。

Requirement 必须足够原子，不支持“豁免一半”。需要部分豁免说明 Requirement 定义过粗，应先
拆分为多个独立 Requirement。

#### 12.5.3 授予、范围与快照

Nobao 或 Domain Agent 可以提出 waiver proposal；只有 Jenn 可以提交当前、明确的
`GrantRequirementWaiver`。Rust core 验证权威、资格、版本和机械安全后，在同一事务中：

```text
记录 RequirementWaived Event
创建 waiver record
从旧 snapshot 生成新的 immutable snapshot
将 waiver reference 附加到 target Requirement membership
重新计算 Task 完成资格
```

waiver 至少绑定：

```text
waiver_id
task_id
requirement_id
requirement_revision
lifecycle_generation
completion_epoch
task_spec_revision
result_revision
base_snapshot_id
approved_by: Jenn
reason
risk_acknowledgement
review_at
waiver_duration_policy
expires_at（EXPIRY_REQUIRED 时）
follow_up_task_id（需要未来补验时）
```

每个 `Task + Requirement revision + lifecycle_generation + completion_epoch + result_revision` 最多一个
活动 waiver。`base_snapshot_id` 只记录起源；如果后续 snapshot 仍引用相同 Requirement binding，
且 waiver 未撤销、未到期，则 waiver reference 必须明确 carry forward。Requirement 被替换、
Task reopen、Task spec 或 result revision 改变时，旧 waiver 自动失去当前效力。

`GrantRequirementWaiver`、`RequirementWaiverRevoked`、`WaiverExpired`、
`WaiverInvalidatedByPolicy` 与 `complete_task` 使用同一个 Task CAS / SQLite 事务边界。谁先
提交，谁决定当前 snapshot；活动或未收口 Control Intent、UNKNOWN 和未核对副作用不得被 waiver
绕过。

#### 12.5.4 到期、撤销与 policy 失效

```text
COMPLETION_SCOPED_ONLY
  -> 仅对当前开放 Task 有效
  -> 必须具有 review_at
  -> Task DONE 后成为历史记录，不自动 reopen

EXPIRY_REQUIRED
  -> 必须具有 expires_at
  -> 开放 Task 到期时，WaiverExpired 生成新 snapshot，Requirement 恢复 REQUIRED
  -> 若允许 Task 在此 waiver 下 DONE，批准时必须已有 linked、非终态的 follow-up / remediation Task
  -> complete_task 必须再次验证该 durable link；缺失、失效或已终态时一律拒绝完成
```

Jenn 可在 Task 仍开放时撤销 waiver。撤销产生 `RequirementWaiverRevoked` Event 和新 snapshot，
Requirement 恢复 `REQUIRED`。

新的有效 policy、Goal 或 Domain 来源将开放 Task 中的 Requirement 升为 `NON_WAIVABLE` 时，Rust core
追加 `WaiverInvalidatedByPolicy` Event 与新 snapshot，Requirement 恢复 `REQUIRED`。`DONE` Task 不被
直接改写；必要时创建 remediation Task。

#### 12.5.5 完成规则

使用 waiver 的 Task 仍必须满足：

```text
所有当前未豁免 REQUIRED Requirement 都有有效 PASSED attempt
至少存在一个当前、非豁免、REQUIRED 的真实 PASSED Validation
```

全部 Requirement 被豁免时不得 `DONE`。Jenn 想亲自结束 Task 时，应增加有明确验收问题和结果
范围的 `HUMAN_ACCEPTANCE` Requirement，并由 Jenn 实际形成 `PASSED` attempt；不得添加空壳
Requirement 仅为凑完成条件。

Task 生命周期绑定规则已经冻结：

```text
Validation 默认只在 Task VERIFYING 时启动
Validation 必须绑定当前 Requirement revision、lifecycle_generation、completion_epoch、task_spec_revision 和 result_revision
有副作用的 Validation 必须通过 Run、permit 和 host gate 执行
有副作用的 Validation 与 Task 的执行 Run 互斥
旧 epoch 的 Validation 默认不具有当前裁决权
进入终态前，当前 epoch 的非终态 Validation 必须结束、取消或显式 detach
```

有副作用的 Validation 无法确定执行结果时，不新增 Validation `UNKNOWN` 状态：

```text
Run -> UNKNOWN
Validation -> INCONCLUSIVE
Task -> BLOCKED
```

### 12.6 Required Validation 的重验与证据复用合同

本节只决定既有 Requirement 的证据在新的当前上下文中是否仍具有裁决权；它不增加、删除或替换
Validation Set membership。历史 Validation 永远保留，但旧 `PASSED` 不因 `reopen_task`、新
`lifecycle_generation` 或新 `completion_epoch` 自动成为当前通过。

#### 12.6.1 三种证据处理模式

每个 Requirement 必须具有有效的 `evidence_reuse_mode`：

```text
NEVER_REUSE
  -> 必须产生新的 FRESH_VALIDATION；历史证据只能参考

REVALIDATE_WITH_OLD_EVIDENCE
  -> 默认值；旧证据可以作为新验证的输入，但不能直接满足 Requirement

CONDITIONAL_CARRY_FORWARD
  -> 仅在本节所有等价守卫均通过时，允许旧证据支持一次新的当前 Validation
```

未声明时一律采用 `REVALIDATE_WITH_OLD_EVIDENCE`。只有明确为确定性、无副作用、被验证对象可由
不可变 digest 精确标识，并具有版本化 `carry_forward_equivalence_contract` 的 Requirement，才可选择
`CONDITIONAL_CARRY_FORWARD`。

下列 Requirement 必须是 `NEVER_REUSE`：

```text
HUMAN_ACCEPTANCE
权限、授权、秘密、隐私和数据泄露防护
TaskPermit、host gate 和外部副作用 / reconciliation
UNKNOWN reconciliation 或任何曾经无法确定的执行结果
运行时真实状态、时效性检查和需要现场观察的安全检查
```

这不是对历史证据的不信任，而是承认这些事实只能在当前时点重新确认。

#### 12.6.2 何时必须重验

无论原 Requirement 的模式为何，发生下列任一事实时，旧证据都不能直接进入当前完成判断；需要新的
`FRESH_VALIDATION`：

```text
Requirement id 或 requirement_revision 改变
task_spec_revision 或 result_revision 改变
acceptance / validator contract version 改变
输入 artifact digest、环境 fingerprint 或 policy fingerprint 改变
evidence freshness / expiry rule 已到期或无法证明仍有效
源 Validation 不是权威 PASSED、证据不可读取或完整性校验失败
源 Validation 关联 UNKNOWN Run、未核对副作用或非权威来源
Requirement 的 evidence_reuse_mode 不是 CONDITIONAL_CARRY_FORWARD
```

同一当前 `lifecycle_generation`、`completion_epoch`、Task spec、结果和 Requirement revision 内，未改变的
既有 `PASSED` evidence 仍按 Section 12.2 有效；单纯新增无关 Requirement 不要求重验它。跨 epoch 时
则永远不自动继承。

#### 12.6.3 条件复用的形式

条件复用不是“把旧 PASSED 搬回来”，而是执行一个新的当前 `Validation` attempt：

```text
validation_method: EVIDENCE_CARRY_FORWARD_REVIEW
state: PASSED（仅在等价合同完整通过后）
```

该 attempt 必须绑定当前：

```text
task_id
requirement_id + requirement_revision
lifecycle_generation + completion_epoch
task_spec_revision + result_revision
validator / acceptance contract version
```

同时必须引用：

```text
source_validation_id
root_source_validation_id
source evidence digest
current input / environment / policy equivalence fingerprint
carry_forward_equivalence_contract version
```

`source_validation_id` 必须属于当前 `task_id`、同一 `requirement_id + requirement_revision`，且是原始、
权威、`FRESH_VALIDATION` 的 `PASSED` attempt；一个 `EVIDENCE_CARRY_FORWARD_REVIEW` 不得成为下一次
复用的 source。这样每次复用都能回到同一条原始证据，不会形成无限或不可审计的证据链。

符合本节的 `EVIDENCE_CARRY_FORWARD_REVIEW` 是真实的、当前的 Validation attempt，不是 waiver；它可以
作为当前、非豁免 `REQUIRED` Requirement 的 `PASSED` 证据，但只能证明其等价合同所覆盖的范围。

#### 12.6.4 权限、事务与完成

Nobao 或被授权的 Domain Agent 可以提交 `carry_forward_validation_evidence`；Worker、executor 和历史
Validation 本身不得自行声明复用。Rust core 只做版本、digest、fingerprint、时效和权限的确定性检查，不对
自然语言语义作推断。

该 Command 仅可在 Task `VERIFYING`、没有 `UNKNOWN`、没有未核对副作用、没有活动 CANCEL 或未收口
Control Intent 时处理。Rust core 在同一 SQLite 事务中：

```text
Inbox 幂等检查
-> 检查当前 snapshot membership 和所有等价守卫
-> 创建新的当前 Validation attempt
-> 追加 ValidationEvidenceCarriedForward Event
-> 更新 Task 的 Validation projection
-> 重新计算完成资格
-> 提交
```

它不修改历史 attempt，不修改 Validation Set snapshot，不签发 permit，也不产生外部副作用。
`carry_forward_validation_evidence` 与 `complete_task` 使用相同的 Task CAS；完成先提交则复用命令被拒绝，
复用先提交则完成只读取新产生的当前 attempt。任何守卫失败时，旧证据可以保留为参考，但 Task 必须回到或
保持正常重验路径。

#### 12.6.5 新鲜度、失效与审计

`CONDITIONAL_CARRY_FORWARD` Requirement 必须在其 equivalence contract 中明确 evidence freshness：

```text
IMMUTABLE_WHEN_FINGERPRINT_MATCHES
  -> 仅当所有规定 fingerprint 完全相同才可复用

EXPIRES_AT
  -> 除 fingerprint 相同外，当前时间还必须早于明确 expires_at
```

没有明确新鲜度合同的 Requirement 不得条件复用。过期、完整性失败或任一 fingerprint 不同，不删除历史
证据，只令其失去当前裁决权并要求重验。每一次复用、拒绝、失效和重新验证都必须留下关联
Requirement、源 Validation、当前 epoch 和合同版本的 Inbox / Event / Validation 审计链。

## 13. Current State 与 Event

采用 Event-Sourcing-Ready Hybrid，而不是现在直接采用纯 Event Sourcing。

```yaml
current_state:
  operational_authority: true

event_log:
  history_authority: true
  append_only: true
  domain_events_complete: true
  typed: true
  versioned: true
  globally_sequenced: true

transaction:
  state_and_event_atomic_write: required

replay:
  required_for_normal_startup: false
  side_effect_free: true
  shadow_replay_supported: true

future:
  pure_event_sourcing: optional
  migration_requires_evidence: true
  migration_requires_new_ADR: true
```

Event 必须记录重要领域事实变化，但不能保存：

```text
真实 secret / token / cookie / credential
provider raw response
原始私人记忆
完整 prompt 或原始日志
大型二进制内容
```

这些内容只能通过低披露的 `ArtifactRef` 关联，并服从 Section 9.1。

Task Dependency 的 canonical history 必须完整覆盖：spec revision、edge revision、dependency / commitment
snapshot 创建、binding、assurance fact 与 resolution、fence generation、current pointer 变更、reopen
disposition、consumer impact 和 recommit。不可变 row 与对应 Event 同事务写入；current assurance、reverse
index、Goal member support 和 Dashboard 视图是可重建 projection。删除这些 projection 后必须能从 Event 与
不可变 row 无副作用重建，且重建不能签发 permit、派发 Outbox 或推进 Task。

## 14. Inbox 与 Outbox

仅有 Current State + Event 同事务，不能解决数据库与外部副作用之间的断点问题。

因此采用：

```text
Transactional Inbox
+ Current State
+ Append-Only Event
+ Transactional Outbox
```

一次领域命令事务至少完成：

```text
1. 按 (source, command_id) 检查 Inbox 和 canonical request hash
2. 验证当前状态、权限、版本和不变量
3. 更新 Current State
4. 追加 Event
5. 写入待派发的 Outbox Intent
6. 在同一 SQLite transaction 中 COMMIT
```

Node Dispatcher 只负责领取和执行 Outbox Intent，不拥有领域状态的自由修改权。

Scheduling planning / selection 与 Outbox dispatch 是不同边界：

> **Pending R1 synchronization:** On complete-bundle freeze, Section 2.1 replaces the successful `create_run` line
> below with phase-correct allocate-or-reuse semantics: only a newly allocated commitment joins the write transaction;
> a reused immutable commitment remains byte-identical. This mirror has no effect before Jenn freezes R1.

```text
SchedulePlanProjection / TimeCriticalPathProjection
  -> 不写 Outbox、不创建 permit

TaskPrioritySelectionSnapshot
  -> 不写 Outbox、不创建 permit、不领取 reservation

成功的 create_run admission
  -> 按既有合同原子写 current commitment、BudgetReservation、Run、Event、permit 和 Outbox intent
```

旧 planning projection 或 selection 不能让旧 Outbox 重新有效。Outbox claim / dispatch 仍须读取当前 permit、
Deadline、Dependency 和 host fence；未来是否加入 Capacity gate，等待 Capacity v0.1 冻结。

Command 幂等最低合同：

```text
相同 (source, command_id) 和相同 payload
  -> 返回首次持久化结果，不重复产生 Event 或 Outbox

相同 (source, command_id) 但不同 payload
  -> 协议冲突

已拒绝 Command
  -> 持久化拒绝结果；条件改变后重试必须使用新的 command_id
```

异步 Fact / Receipt 不使用 Task 当前 aggregate version 作为身份：

```text
按稳定 source_id / receipt_id 去重
绑定 run_id / validation_id / effect_id / intent_id
绑定 lifecycle_generation / completion_epoch / execution_epoch / host_fence_epoch
绑定 task_commitment_snapshot_id / dependency authority binding / completion-ref fence generations
真实迟到事实仍然入账
旧 generation 的事实不得推进当前 Task
```

Outbox 使用稳定 `effect_id` 作为 host idempotency key。Task 完成所依赖的最低 effect 语义是：

```text
PENDING -> CLAIMED -> DISPATCHED -> ACKED
        -> SUCCEEDED | FAILED | UNKNOWN
        -> RECONCILED
```

`ACKED` 只表示 host 已接收，不表示副作用完成。completion-blocking 属性由 Rust policy 根据
effect class 决定，调用方不得自行降级。Outbox 的 claim、lease、retry 和 dead-letter 精确 schema
仍留给后续专项合同。

`claim_outbox`、dispatch 与 lease renewal 必须同步读取当前 permit、host fence 和 Task Dependency fence。
若 commitment snapshot、assurance version 或 fence generation 已过期，则拒绝新的副作用，并把 intent
送入受控收口；不得因队列中已有旧记录就恢复旧执行权。Fact 接纳、UNKNOWN reconciliation、Control
Intent finalizer 和 recovery 操作不受该 admission gate 阻挡。

恢复语义：

```text
提交后、派发前崩溃
  -> Outbox 仍存在，重启后可以继续领取

派发后、确认前崩溃
  -> 使用同一 idempotency key 对账

无法确认副作用是否发生
  -> Run 进入 UNKNOWN，不自动重试

同一回执重复返回
  -> source_id / receipt_id 去重并返回首次处理结果
```

Inbox 和 Outbox 是基础设施记录，不增加正式领域对象数量。

## 15. 最优 Rust 技术落点

经源码反证后，采用：

```text
VCPToolBox 内唯一 JavaScript hybridservice Resident
+ Rust N-API 确定性内核
```

不默认采用 Rust child sidecar。

### 15.1 JavaScript shell 负责

```text
VCPToolBox 插件生命周期适配
API 和 route 适配
模型、工具、Agent 和 executor 调用
Outbox dispatch
定时唤醒
host 返回结果的接入
VCPToolBox 日志与可观察性适配
```

### 15.2 Rust core 负责

```text
Goal / Task / Run / Validation / Event 类型和状态机
领域命令验证
完成规则和非法转移拒绝
Task dependency DAG、不可变 binding、phase-specific commitment snapshot 和同步 gate
completion-reference transitive assurance、fence、resolution finalizer、recommit 与 Goal closure ancestry
Eligibility / Effective ordering 的确定性归约和 TaskPrioritySelectionSnapshot 唯一写入
create_run 的 current-fact admission orchestration
SchedulePlanProjection / TimeCriticalPathProjection 的无副作用派生、版本与 currentness 接纳边界
普通 scheduling 与 control / recovery lane 的分离
许可结果、lease、幂等和恢复约束
Current State / Event / Inbox / Outbox 原子事务
SQLite schema、migration 和唯一写入
只读 query contract
```

Rust core 不直接：

```text
调用模型
调用 provider
执行插件
执行 Shell / Python / Codex
启动 HTTP server
连接 VCPChat 或 VCPMobile
保存原始秘密、prompt、记忆或 provider response
```

### 15.3 初始技术基线

```yaml
rust:
  role: deterministic_in_process_kernel
  edition: "2024"
  toolchain: exact_pinned_modern_stable
  panic: unwind
  unsafe_code_in_our_crates: forbidden

node_bridge:
  framework: napi-rs
  public_surface:
    - execute_command
    - execute_query
    - claim_outbox
    - acknowledge_outbox
    - reconcile

persistence:
  engine: SQLite
  driver: rusqlite
  authoritative_connections: 1
  writer: Rust_core_only
  write_transaction: BEGIN_IMMEDIATE
  initial_journal_mode: DELETE
  initial_synchronous: EXTRA

serialization:
  command_and_event_contract: serde_plus_versioned_JSON

errors:
  typed_errors: thiserror
```

初版不引入：

```text
Tokio
Axum
SQLx
HTTP / gRPC
stdio IPC
独立 Rust daemon
第二个常驻 supervisor
```

这些部件只有在真实需求和 benchmark 证明后才能加入。

本机现有 `rustc 1.75.0` 不是新内核的正式基线。建设时必须使用项目内
`rust-toolchain.toml` 和 `Cargo.lock` 锁定经过验证的现代稳定工具链，不要求现有 VCP
Rust 子项目同时升级 edition。

## 16. SQLite 运行原则

初始原则：

```text
一个数据库
一个 Rust 权威连接和写入者
所有 Dashboard / Workbench / VCPChat / VCPMobile 查询通过受控 query API
任何 JavaScript、UI、adapter 或外部工具不得直接打开总账数据库
数据库放在 Linux 本地文件系统和 Git 之外
数据库目录和文件使用本地私有权限
在线备份使用 SQLite Backup API 或 VACUUM INTO
```

Dependency 持久化至少必须用数据库约束和 Rust 事务共同保证：spec / edge / commitment identity 唯一、
同 Goal 非 shared endpoint、无 self-edge / duplicate / cycle、binding 指向准确 immutable DONE Event、
assurance version 与 fence generation 单调、current pointer 只指向同一 Task envelope。Reverse index 和
assessment projection 允许删除重建；Event、immutable spec / snapshot / binding / fact row 不允许靠 projection
反向猜测恢复。

初始采用 `DELETE + synchronous=EXTRA`，原因是全局任务总账写入量低，当前优先级是耐久、
简单和容易恢复，而不是并发吞吐。

只有 benchmark 证明并发只读投影形成真实瓶颈后，才考虑：

```text
WAL + synchronous=FULL + controlled checkpoint
```

这个切换必须验证备份、掉电、重启、checkpoint、长读事务和 SQLite 版本，不得只因 WAL
看起来更现代就切换。

## 17. 启动、关闭和恢复

### 启动

```text
1. VCPToolBox 加载 AGENTSOSResident direct hybridservice
2. JS shell 加载 Rust N-API core
3. Rust core 打开数据库并验证 schema / migration
4. 执行 quick integrity
5. 校验 Event、immutable dependency / commitment snapshot、current pointer 与 last_event_id 对齐
6. 提升 host fence epoch，阻止崩溃前执行世代重新取得推进权
7. 从 canonical facts 恢复 completion-reference fence generations
8. 从 canonical bindings 重建 dependency reverse index，但暂不发布 assessment / Goal support
9. 扫描活动 Control Intent、recommit、过期 Run / Validation lease 和未完成 Outbox
10. 可能产生副作用但无最终回执的执行进入 UNKNOWN；非终态 Task 进入 BLOCKED，终态 Task 保持终态并追加 reconciliation / assurance challenge
11. 运行可重入 pause / cancellation / terminal / dependency-resolution finalizer 与 effect reconciliation
12. 扫描 assurance / observed revision / reducer version mismatch，并按上述恢复事实和 immutable provenance closure 重算
13. 基于最终 assurance versions 重建 dependency assessment 和 Goal member support projection，并确认无 stale input
14. 将历史 scheduling selection 只保留为历史证据，并把持久化 SchedulePlan / TimeCriticalPath projection 标记为 stale
15. 从总账 current facts 重建 durable due / wake 索引；missed 或重复 wake 只请求幂等重新评估
16. 执行 recovery read barrier；若 Event sequence 或 assurance version 在步骤 12 后改变，则重复 9-15
17. 逐项重验 permit、dependency gate、幂等和 fencing 后，才恢复可安全领取的 Outbox
18. 完成全部 recovery gate，并确认 control / recovery lane 可工作后，才允许新 permit 和普通 selection
19. SchedulePlan / TimeCriticalPath projection 可以按当前已接受输入无副作用重建；缺输入时保持不可用，不猜测数值
20. Resident 报告 readiness
```

任一 snapshot 缺失、fingerprint mismatch、非法 cycle、source Event 不一致、assurance 无法重算或 policy
版本不可用时，dependency / completion assurance 必须是 `INDETERMINATE`。非终态 Task 由 reducer 进入
`BLOCKED`；`DONE / FAILED / CANCELLED` 保持原终态，只有显式 reopen Command 才能改变生命周期。DONE 的
completion assurance 和 Goal member support 可以进入 review，FAILED / CANCELLED 只追加恢复与风险事实。
不得用缓存 projection、旧 digest 或最后一次成功结果猜测为 `CONFIRMED`。Recovery 可重复执行，崩溃后
重入不得重复增加 epoch、Event 或 fence。

Scheduling projection 不可用本身不阻止 Resident readiness，也不阻止原本通过同步 gate 的非时间型执行；
真正的 Deadline、UNKNOWN、dependency、permit、host fence 或 ledger integrity 问题继续 fail-closed。恢复过程
不得复活旧 selection、Run、permit、Outbox authority 或尚未冻结的 capacity claim。

### 关闭

```text
1. 停止接收新的领域命令
2. 停止领取新的 Outbox Intent
3. 等待有界的当前事务完成
4. 保存必要的 lease / shutdown Event
5. 关闭 SQLite connection
6. 向 VCPToolBox 返回 shutdown 完成
```

### 时间调度

定时器不是任务真相。到期时间和待唤醒状态保存在总账中：

```text
node-schedule / setTimeout / VCP scheduler
  -> 只是唤醒优化

GlobalTaskLedger
  -> 到期事实和 missed wake-up 恢复权威
```

## 18. Rust N-API 的真实边界

Rust N-API 是：

```text
正确性边界
类型和状态机边界
数据库唯一写入边界
VCPToolBox 内的模块边界
```

它不是：

```text
抵御已完全控制 VCPToolBox 进程的恶意代码的安全沙箱
独立 OS 权限边界
阻止同一 OS 用户直接破坏文件的绝对防线
```

如果未来威胁模型要求：

> 即使 VCPToolBox 进程或第三方插件被完全控制，也不能伪造 permit、读取签名私钥或改写
> canonical ledger。

那么必须通过新的 ADR 评估：

```text
独立 Rust authority daemon
独立 OS user / credential boundary
本地 socket peer identity
VCPToolBox fail-closed adapter
独立 supervisor 和升级恢复
```

同一 OS 用户下的普通 child sidecar 只增加故障隔离，不构成上述安全隔离。

## 19. 每类事实的权威写入者

| 事实类别 | 权威写入者 |
|---|---|
| Jenn 顶层 Goal 最终变更和结束 | Jenn，通过 AGENTSOSResident 记录 |
| Subgoal 生命周期 | Nobao，通过 AGENTSOSResident 记录 |
| AGENTS OS 全局 Task 生命周期 | `AGENTSOSResident.GlobalTaskLedger` |
| Run / Validation / Event | `AGENTSOSResident` Rust core |
| Task dependency spec / snapshot / commitment / assurance / fence | `AGENTSOSResident` Rust core |
| Eligibility / Effective ordering / TaskPrioritySelectionSnapshot | `AGENTSOSResident` Rust core |
| 持久化 SchedulePlanProjection / TimeCriticalPathProjection | `AGENTSOSResident` Rust core 派生，只读且可重建 |
| Permit / lease / idempotency canonical record | `AGENTSOSResident` Rust core |
| 真实执行进程和本机执行会话 | 对应 execution host |
| execution host capability / availability 真实事实 | 对应 execution host 报告，`AGENTSOSResident` Rust core 接纳和绑定版本 |
| VCPToolBox 插件运行状态 | VCPToolBox |
| VCPChat 窗口和桌面状态 | VCPChat |
| VCPMobile 设备和传感器状态 | VCPMobile |
| ColaMeta plan version 和本地工作流状态 | ColaMeta |
| VCP 原生记忆内容和生命周期 | VCP native memory runtime |
| 记忆访问许可和低披露证据 | governed memory bridge |
| Artifact bytes、访问、保留和删除 | 对应 storage_authority |
| ArtifactRef 的领域语义关联 | `AGENTSOSResident` Rust core |
| Dashboard / Workbench 视图 | derived read-only projection |

execution host 报告自己的事实，但不能直接修改 Task / Goal canonical state。
Duration、Calendar 与 Capacity 的语义决定者和精确写入权威等待各自专项合同，不能从上述 planning / selection
权威反向推定。

## 20. 与高权限架构的关系

本决议继承：

```text
最大能力
+ 最小常驻授权
+ 最大安全自治
+ 任务级临时许可
```

因此：

```text
Nobao 可以在已确认 Goal、Green/Yellow scope 和有效 permit 内高度自主推进
Worker 不常驻持有 Root、万能 token 或全部设备身份
每次外部副作用绑定具体 Run、host、permit 和 idempotency key
每个 effectful permit 绑定当前 TaskCommitmentSnapshot、dependency closure、assurance versions 和 fence generations
dependency fence 后的旧 permit 永久失效，后续 PRESERVED 或恢复投影都不得令其复活
host 必须在副作用发生前执行本地 gate
AGENTSOSResident 不把秘密值写进 Event、Outbox、Receipt 或模型上下文
```

需要修改 VCPToolBox core 的首选且可能唯一理由，是增加无法从模块完成的统一 host gate。
即使如此，也只增加通用 hook，不把 AGENTS OS 业务规则写进 core。

## 21. 已明确取代的旧建议

以下建议不再作为当前架构：

```text
Workbench 升格为执行或状态内核
codex-router 自动成为 kernel + state + runtime 的唯一所有者
把 codex-router `task-graph.v2` 或其他现有 task graph 直接当成 canonical Task Dependency schema
把所有事实塞进一个统一数据库
GlobalTaskLedger 必须放在 VCPToolBox 之外
默认用 Rust sidecar 承载 AGENTSOSResident
默认采用 Tokio + Axum + SQLx + stdio IPC
默认采用 WAL
```

取代这些建议，不表示否定相关项目已有能力。它们仍可作为 adapter、library、host 或
benchmark 对象使用。

## 22. 仍未决定

以下内容共同组成一个 `R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`，已经完成 R1 收口修订。它必须绑定可复核哈希
与独立终审 artifact 才能提交 Jenn；无论终审结果如何，只有 Jenn 能决定是否正式冻结，当前不属于已冻结架构：

```text
Main document Sections 3-9:
  Scheduling Work Request and Enforcement Profile v0.1
  SchedulePlanProjection v0.1
  Duration Estimate v0.1
  Calendar v0.1
  Capacity v0.1
  Eligibility and Effective Ordering v0.1
  Atomic Admission and Recovery v0.1
  Time Critical Path v0.1

Parent document:
  Section 2.1 Pending R1 amendment overlay
```

本版本不允许选择性冻结。任一成员需要修订时，整包继续保持 pending；冻结任一单独 Section、只冻结父
overlay 或只冻结部分 overlay 都没有合同效果，也不改变既有已接受父架构。

终稿位置：

```text
control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
```

`Resource-constrained Scheduling v0.2` 已拆到独立草案：

```text
control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
```

它明确为 `PRESERVED_DESIGN_DRAFT_NOT_PROPOSED_FOR_ACCEPTANCE`，带有待未来单独解决的已知缺口，不包含在
`R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE` 中，也不授权实现或激活。

以下其他内容仍需后续单独讨论：

```text
preemptive scheduling v0.2+
Task Dependency v0.2+：cross-Goal owner / consumer、shared endpoint、PINNED_VALIDATED_RESULT 与冻结后 extension
Nobao / Domain Agent / Worker 身份记录的精确 schema
Agent session、working context 与长期 memory 的边界
TaskPermit 的最终签名算法、密钥保管和撤销协议
VCPChat / VCPMobile 的 projection、offline 和 sync 合同
Outbox 的 claim / lease / retry / dead-letter 精确合同
Rust crate 的源码目录、发布产物和 upstream 跟踪方式
SQLite migration、backup、restore 和 disaster recovery runbook
Dashboard 的正式读模型
```

这些内容可以讨论、建模和实验，但在 Jenn 确认前不能写成 accepted contract。
`Task Scheduling Architecture Boundary v0.1` 已在 Section 10.15 冻结，不再属于未决定项。R1 的下一动作由
hash-bound review artifact 决定：终审通过后提交 Jenn 冻结裁决；若未通过则只修订并重新审查。任何分支都
不得开始实现。

## 23. 实施前验证要求

未来建设至少需要：

```text
Pending R1 acceptance tests, effective only if Jenn freezes the complete atomic bundle:
- Before Jenn freezes `R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`, every member remains pending and the parent overlay has no
  runtime, database, reducer, migration, or activation effect; reject every attempted partial freeze.
- HostWorkAcceptanceFact(ACCEPTED) grants bounded start authority but keeps every bound RUN_ATTEMPTS reservation RESERVED.
- `create_run` atomically commits exactly one immutable `RunAttemptsBudgetAuthorityBinding` with the complete canonical
  Task/Goal member set, references the exact reusable immutable commitment snapshot, and cross-binds its ID/fingerprints
  to the Run, every member reservation, permit, admission Event, and Outbox; any mismatch or missing member rolls back
  the admission. The commitment snapshot receives no Run-specific reverse binding and is not refreshed for admission.
- `TASK_EXECUTION` with a current candidate must use authorized `REJECT_FOR_NEW_EXECUTION` and clear only through that
  atomic branch; `EFFECTFUL_VALIDATION` must instead use `PRESERVE_FOR_EFFECTFUL_VALIDATION`, bind the exact candidate,
  result, frozen Validation Set, Requirement, and validator contract, and must not clear or supersede candidate support.
- Effectful Validation reuses the exact current candidate commitment without writing it; ordinary Task execution
  allocates a new EXECUTION_ADMISSION commitment only when absent or when commitment inputs changed, otherwise reusing
  the current immutable phase-correct snapshot unchanged.
- HostWorkStartDispositionFact(STARTED) or stronger positive execution evidence settles the complete bound RUN_ATTEMPTS
  reservation set exactly once.
- Authoritative no-launch proof releases the complete bound RUN_ATTEMPTS reservation set even if Capacity is still RELEASING.
- Possible execution moves every unsettled bound RUN_ATTEMPTS reservation to UNKNOWN and forbids automatic retry.
- A late authenticated same-epoch positive execution fact corrects the complete bound RUN_ATTEMPTS reservation set from RELEASED to SETTLED exactly once,
  preserves the prior release and real execution history, contradicts the prior no-execution assurance, and keeps the
  old Run terminal REJECTED rather than reopening it as UNKNOWN or another nonterminal state.
- Late-positive correction must discover the complete canonical sorted set of every Task- and Goal-scoped
  RUN_ATTEMPTS reservation only from the original immutable authority binding and compensate the entire set atomically;
  a missing/corrupt binding or missing, duplicated,
  conflicting, or partially writable member produces BUDGET_CORRECTION_SET_INDETERMINATE and no partial compensation.
- Missing authority binding or reservation rows must never let a surviving-row or current-envelope scan self-certify
  completeness; the Task stays fenced and the immutable expected plus observed-conflict scopes, or every scope
  independently reconstructable from authenticated cross-references, remain fail closed through recovery replay.
- The same correction transaction raises the no-new-Run fence and scans every later execution epoch plus current
  candidate, result, evidence, and Validation completion bindings before any completion decision can proceed.
- Late STARTED with no successor and possibly active physical execution keeps a nonterminal Task ACTIVE only through
  existing `activity_kind=COORDINATING` with `coordination_subtype=LATE_EFFECT_RECONCILIATION`, reconciliation ID,
  owner, next action, and activity deadline while addressable stop/query remains unfinished; it becomes unresolved-effect
  BLOCKED only after physical activity has stopped and effect influence remains unresolved. This narrow exception does
  not override current Run UNKNOWN -> Task BLOCKED.
- A later QUEUED successor is fenced before dispatch and becomes REJECTED only with proof it never left the ledger;
  uncertain dispatch follows UNKNOWN query/reconciliation without reopening the old Run.
- A later LEASED, RUNNING, or WAITING successor remains the sole nonterminal execution Run and receives immediate
  fence/PAUSE/stop/query/reconciliation; a terminal successor stays terminal while its candidate, result, evidence, and
  Validation completion eligibility remain quarantined.
- With no successor, late terminal execution evidence still opens effect reconciliation; with an already terminal Task,
  the Task state stays unchanged, no automatic reopen occurs, and affected completion/Goal/dependency support is
  challenged until reconciliation.
- Crash replay of any late-positive branch is idempotent, preserves at most one nonterminal execution Run, creates no
  new Run, and authorizes neither automatic retry nor duplicate Budget settlement, fence, stop intent, or quarantine.
- A later stronger positive Fact for the same execution epoch enriches the existing late-effect reconciliation and does
  not create a second contradiction Event or Budget compensation for the same released reservation.
- Calendar / HARD_NEW_START_AUTHORITY_CUTOFF gates authority commit, not remote physical start.
- The canonical effective field, value field, reached Event, blocker reason, TaskPermit field, host capability field, and
  Deadline snapshot use only the Section 2.1 start-authority names; historical names remain read-only aliases.
- HostWorkAcceptanceFact committed by Rust before the effective cutoff proves start-authority compliance but not
  physical STARTED; HostWorkStartDispositionFact STARTED or stronger bound evidence proves physical start.
- Dependency assurance-only changes stale SchedulePlan and TimeCriticalPath.
- Task DONE without effective CONFIRMED completion assurance cannot contribute a zero time boundary.
- TaskForecastBoundary must partition the complete current constraint ref set exactly once across dependency geometry,
  active Duration geometry, active-work release, and completion release; duplicate, missing, kind-incompatible, or
  basis-mismatched ownership produces INDETERMINATE and no aggregate TASK_DONE forecast.
- Dependency-owned active holds use DELEGATED_TO_DEPENDENCY_GEOMETRY; ZERO_ACTIVE_WORK_PROVEN requires an empty active
  Duration owner set and exact zero-basis alignment with the completion-release owner set. SchedulePlan and
  TimeCriticalPath must bind the same owner-partition fingerprint.
- Rebuilding identical forecast semantics under a different snapshot/projection ID, aggregate CAS version, read
  watermark, computed time, or unrelated Event must preserve byte-identical owner-partition and analytical input
  fingerprints; a relevant Task state/phase, source pointer, constraint, Dependency/Duration basis, release, zero-basis,
  evidence, or policy change must change the fingerprint and stale dependents.
- New/reactivated fairness accounts inherit the current virtual-service floor and cannot burst from zero.
- Fairness assignment transition flags must derive from the exact before/after input set; compound transitions use the
  checked maximum of every applicable existing/source/target floor, and same-account work-request revision preserves
  continuous lineage service debt.
- Lineage head transition identity must bind canonical change_flags and trigger_flags, including comparator-only and
  mixed fact/time changes; materialization context cannot replace semantic trigger flags.
- A same-instant boundary batch must reduce backlog episodes and system state only from complete pre-batch and final
  post-batch semantic sets. Swap, cycle, and many-to-one lineage moves cannot create an intermediate EMPTY episode.
- Focus, expedite, and Deadline urgency reduction must bind their complete current ref sets and set fingerprints;
  Focus/expedite use complete-set OR and Deadline urgency records its canonical driver.
- Backoff identity must use the fixed-order complete rejection reason set and reason-set fingerprint; input order or a
  caller-selected scalar reason cannot change replay, delay, or same-reason identity.
- Successful local admission atomically commits one service charge; rollback commits none.
- Evidence-backed zero Duration is legal; missing or unknown work encoded as zero is rejected.
- Compatible cumulative PARTIAL timing updates DurationRemainingProjection without staling the base estimate.
```

```text
状态转移表测试
非法转移负路径测试
Goal health direct set 写入拒绝测试
非 ACTIVE Goal 只产生 NOT_ACTIVE、不得计算 assessment 测试
Critical Work Frontier UNAVAILABLE / PARTIAL / COMPLETE 判定测试
ANY_OF route groups 与 ALL_OF frontier members 组合测试
单一路线阻断但存在替代路线时只进入 ATTENTION_REQUIRED 测试
任一必要 criterion 的全部路线阻断时进入 BLOCKED 测试
前沿不完整且存在硬阻塞时产生 ATTENTION_REQUIRED + CONFIRMED_CRITICAL_BLOCKER + FRONTIER_INCOMPLETE 测试
前沿不完整且没有硬阻塞时产生 INSUFFICIENT_EVIDENCE 测试
HEALTHY / BLOCKED 仅允许在 COMPLETE frontier 上产生测试
HARD_BLOCKER 非白名单 code 拒绝测试
Agent 自行声明 blocker_class=HARD 拒绝测试
同一 frontier member 的具体 blocker 与通用 Task blocker 去重测试
授权 PENDING、普通 WAITING 和单次 Validation FAILED 不得产生 HARD_BLOCKER 测试
裸 ArtifactRef 不得证明 HARD_BLOCKER 测试
reason Goal spec / plan / affected Task lifecycle / completion / result 版本过期后失去当前裁决权测试
TIME_BOUND blocker 到期后转 EVIDENCE_GAP、不得直接 HEALTHY 测试
Task reopen、plan revision、policy revision 和 reconciliation 清除对应 blocker 测试
RISK 无论数量多少都不得自动产生 HARD_BLOCKER 或 BLOCKED 测试
ALTERNATIVE_ROUTE_REDUCED 仅在仍有可行替代 route group 时产生测试
必要 Validation FAILED 时产生 REQUIRED_VALIDATION_FAILURE_REMEDIATION_REQUIRED 测试
remediation_status MISSING / PLANNED / ACTIVE 转换测试
当前有效 PASSED、合法 Requirement replacement 或 Task 合法终态结束 Validation remediation RISK 测试
Validation ERROR / INCONCLUSIVE 不得产生 REQUIRED_VALIDATION_FAILURE_REMEDIATION_REQUIRED 测试
plan_progress 100% 但 Goal criteria 未满足时产生 GOAL_CRITERIA_UNMET_AT_PLAN_100 测试
关键前沿 PAUSED 或活动 Control Intent 产生 CRITICAL_FRONTIER_PROGRESS_SUSPENDED 测试
普通 WAITING、一次 Run FAILED、Agent idle 和无合同的 deadline / budget 判断不得产生 RISK 测试
Domain Agent 风险 scope policy / Nobao acceptance gate 测试
Worker 直接声明 Goal risk 拒绝测试
RISK 达到 review_at / expires_at 未复查时转 EVIDENCE_GAP、不得直接 HEALTHY 测试
RISK 路线真正被截断时以 canonical fact 结束并产生白名单 HARD_BLOCKER 测试
RISK 被证伪或 mitigation 完成时追加解决 Event、保留历史测试
SOFT_TARGET consumed + reserved 超限产生 SOFT_BUDGET_TARGET_EXCEEDED、但不阻止 Run 测试
EVIDENCE_GAP 非白名单 root code 拒绝测试
FRONTIER_INCOMPLETE 不得脱离具体 root gap 单独存在测试
GOAL_SUCCESS_CRITERIA_INCOMPLETE 抑制依赖 criteria 的 route mapping gap 测试
CURRENT_PLAN_UNAVAILABLE 抑制 plan 下 route mapping 和 member fact gap 测试
CRITERION_ROUTE_MAPPING_INCOMPLETE 的 ANY_OF / ALL_OF 缺失测试
CURRENT_REQUIRED_FACT_MISSING 仅在跨过 fact_required_at_event 后产生测试
合法 PENDING / WAITING 与尚未到期未来事实不得产生 CURRENT_REQUIRED_FACT_MISSING 测试
CANONICAL_FACT_RECONCILIATION_REQUIRED 必须绑定 conflicting_fact_refs 测试
required Validation ERROR / INCONCLUSIVE 产生 REQUIRED_VALIDATION_RESULT_INCONCLUSIVE 测试
Validation 关联 UNKNOWN Run 时由 HARD_BLOCKER 取代 gap 测试
正式 Validation 已表达 evidence unavailable 时抑制重复 evidence gap 测试
TIME_BOUND health fact 过期产生 TIME_BOUND_HEALTH_FACT_STALE 测试
BUDGET_ACCOUNTING_UNRECONCILED 与外部 effect UNKNOWN 抑制优先级测试
HEALTH_POLICY_VERSION_UNAVAILABLE 使用 Rust 内置 fallback、不依赖外部 registry 测试
Rust core 以外角色直接声明、清除或 dismiss EVIDENCE_GAP 拒绝测试
gap 持续时间或数量不得自动升级为 RISK / BLOCKED 测试
新 canonical fact 修复 gap 后重新计算 projection、保留历史测试
裸 ArtifactRef 不得直接解决 EVIDENCE_GAP 测试
BudgetEnvelope 四维度、整数 limit、currency 和 price_schedule_ref schema 测试
负数、浮点 monetary limit 和缺 currency 的 MONEY_MICRO_UNITS 拒绝测试
SOFT_TARGET 超限允许 reservation、HARD_CAP 超限拒绝 reservation 测试
SETTLED consumption 与 outstanding reservation 不双计、UNKNOWN 按完整 reserved_amount 占用测试
create_run 与所有适用 Goal / Task HARD_CAP reservations 同事务测试
任一适用 envelope 额度不足时不创建 Run、不签发 permit 测试
重复 reservation command / receipt 幂等测试
Run 创建后执行前崩溃保留 reservation、确认未派发后释放测试
执行后 receipt 前崩溃令 reservation UNKNOWN、禁止自动释放和付费重试测试
晚到 usage receipt 幂等 SETTLED 并释放未使用额度测试
实际消耗超过 reservation 仍完整入账并进入 OVER_CAP 测试
降低 limit 到 consumed + reserved 以下保留历史并阻止新 reservation 测试
Task cap 总和高于 Goal cap 时仍由 Goal pool 原子约束测试
Jenn-only monetary HARD_CAP increase 测试
Nobao 不得增加父级总预算、Domain Agent 只能提议或收紧、Worker 不得修改预算测试
预算存在不得绕过 P3、provider、permit、host、secret 或 external-effect gate 测试
可信 host / metering receipt 只保存低披露 usage、不得包含 raw provider response 测试
DeadlineConstraint kind、UTC integer、revision 和每 scope/kind 单一 current revision schema 测试
display_timezone、客户端时间和 host 时间不得参与 Deadline 裁决测试
Task DONE 与 Goal CLOSED + ACHIEVED 的 Soft completion 精确边界测试
now < deadline 允许、now >= deadline 到期的半开边界测试
同一 deadline revision 的 crossing Event 幂等测试
JavaScript timer 丢失、重复或延迟不得绕过 Rust deadline gate 测试
Resident 停机跨过 Deadline 后在 readiness 前恢复 fence 测试
wall-clock 超容差倒退产生 DEADLINE_TIME_AUTHORITY_UNCERTAIN、不得伪造 crossing 测试
wall-clock 向前跳过 Hard Deadline 建立 sticky fence、回拨不自动释放测试
Soft miss 产生 SOFT_DEADLINE_TARGET_MISSED 但不阻止 Run 测试
非关键 Task Soft miss 不改变 Goal Health 测试
Goal / Task Hard Deadline ancestor 继承与两个 effective cutoff 公式测试
父级 projection 尚未传播时 create_run 仍读取 canonical ancestor Deadline 测试
Hard new cutoff 时已由 host 接受的 Run 保持 ACTIVE 并可在原 scope 内续 lease 测试
host acceptance Fact 必须在边界前由 Rust 入账，迟到 accepted_at 不得反向取得开始资格测试
Hard new cutoff 时 QUEUED / LEASED 但未接受的 Run 不得派发测试
可能已被 host 接受但无法确认时 Run 进入 UNKNOWN、不得自动重试测试
Deadline fence 不直接生成 Task blocker 或覆盖活动 Run 的 Task ACTIVE 测试
只有结构化新执行 commitment 且无 closure 路线时产生 DEADLINE_NEW_EXECUTION_PROHIBITED 测试
试探性 create_run 拒绝和 Agent 主观判断不得独立产生 HARD blocker 测试
Hard stop scope fence 先于后代有界停止批次生效测试
Hard stop 与既有 PAUSE / CANCEL Control Intent 去重及优先级测试
AbortSignal、signal send 或 Outbox ACKED 不得独立证明停止测试
Deadline stop confirmed -> CANCELLED、独立 Run timeout -> TIMED_OUT、无法确认 -> UNKNOWN 测试
迟到 SUCCEEDED / FAILED Receipt 保留真实结果与原 epoch 测试
permit 失效后执行产生 DeadlineAuthorityViolation 与 completion-blocking effect 测试
Hard Deadline 后 closure-only Validation / HUMAN_ACCEPTANCE 可继续、effectful Validation 拒绝测试
Deadline revision 不增加 task_spec / result / validation_set revision、不废掉无关 PASSED 测试
Task 终态 / Goal CLOSED 后独立 Deadline CREATE / REVISE / RETIRE 拒绝测试
reopen / reactivate 不清除旧 Deadline 或 fence 测试
到期后延长或 retirement 不自动删除 Event 或 release fence 测试
ReleaseDeadlineFence authority、CAS、UNKNOWN、Control Intent、其他到期 constraint 守卫测试
未确认 host capability 使用 CURRENT_REQUIRED_FACT_MISSING、不得产生 HARD blocker 测试
所有允许路线被证明不支持 Hard Stop 时产生 DEADLINE_HARD_STOP_ENFORCEMENT_UNAVAILABLE 测试
Deadline 不得越过 dependency、budget、permit、host、priority 或 P3 测试
Task 创建未声明 Priority 时同事务持久化 NORMAL / NOBAO_MANAGED 测试
HIGH / NORMAL / LOW / BACKGROUND 固定枚举与顺序测试
数字、浮点、P0/P1、自由文本 Priority 和调用方 comparator 拒绝测试
Priority revision 保留稳定 priority_id、旧 revision 不可修改测试
standalone Task 空 goal_bindings 与 shared Task 多 goal_bindings 测试
goal / criterion / plan membership binding 稳定排序、去重与重复拒绝测试
无关 Task / plan member 变化不改变 priority context fingerprint 测试
Task spec、Goal binding、criterion revision 或本 Task membership 变化产生 REVIEW_REQUIRED 测试
REVIEW_REQUIRED 保留 declared_class、scheduling_class 回落 NORMAL 测试
REVIEW_REQUIRED 不改变 Task state、不阻塞 Task、不产生 Goal Health reason 测试
context confirmation 即使 class 不变也创建 REPRIORITIZATION revision 测试
priority-context.v0.1 canonical JSON 与 SHA-256 deterministic fingerprint 测试
调用方伪造 context binding / fingerprint 被 Rust 忽略或拒绝测试
SYSTEM_DEFAULT 只能由 Rust 初始 NORMAL 产生测试
Nobao 伪造 JENN_EXPLICIT 或 Jenn Command Event 拒绝测试
GOAL_PLAN basis 缺 Goal / criterion / membership refs 拒绝测试
DECOMPOSITION 非子 Task 初始 revision 或缺 parent/decomposition Event 拒绝测试
REPRIORITIZATION 缺上一 revision 或新 basis refs 拒绝测试
Domain Agent proposal 可引用但不得成为 decided_by 测试
JENN_LOCKED 只能由 Jenn 创建、修改、确认和解除测试
Unlock 创建 NOBAO_MANAGED 新 revision、默认保持 class 测试
Priority revision 不改变 task_spec / result / validation_set revision 或 PASSED evidence 测试
Priority revision 不改变 Task state、不取消或抢占活动 Run 测试
Task 终态 Priority revision / Lock / Unlock 拒绝测试
reopen context 未变保留 CURRENT、context 改变进入 REVIEW_REQUIRED 测试
Priority selection snapshot 绑定 aggregate version、lifecycle generation、revision 与 fingerprint 测试
首次 pre-commit Priority selection 的 dependency_set_snapshot_id 为 null、不得提前冻结测试
Priority revision 与 selection 单写入顺序竞态测试
reopen 后旧 lifecycle generation selection 不得创建 Run 测试
selection 后 Task 事实变化仍由 create_run 全量重检测试
普通 Priority 不延迟 Receipt、UNKNOWN reconciliation、Deadline stop 或 Control Intent finalizer 测试
父 Task / Goal / Frontier / Deadline / failure / wait 不自动改写 base priority 测试
子 Task 默认 NORMAL、显式复制必须使用 DECOMPOSITION basis 测试
不支持 Priority policy 使用 Rust 内置 REVIEW_REQUIRED + NORMAL fallback 测试
Priority policy 无兼容映射产生 PRIORITY_POLICY_CHANGED 测试
Priority policy 故障不阻止安全收口与 ledger recovery 测试
Priority 不得绕过 dependency、Deadline、Budget、permit、host 或 P3 测试
NOW / NEXT 不得写入 canonical Priority 测试
Task Dependency 同 Goal、ALL_OF、PINNED_DONE_EVENT 正路径测试
self-edge、duplicate、direct / indirect cycle、ANY_OF、FOLLOW_CURRENT 和 result dependency 拒绝测试
cross-Goal edge 与任一 endpoint 为多 Goal shared Task 的拒绝测试
commitment 后 endpoint 增加第二个当前 Goal membership 的拒绝与 legacy fail-closed 测试
零 edge Task 仍生成 immutable empty DependencySetSnapshot 测试
DependencySetSnapshot 与 DependencyClosureSnapshot identity、范围和零 edge 空 closure 测试
每个 commitment snapshot 单调 revision、同事务 phase 连续分配与幂等重放不增加测试
source 非当前 CONFIRMED DONE、DONE Event 晚于 commitment 或 completion ref identity mismatch 拒绝 binding 测试
Dependency spec / edge identity 唯一、revision 不可修改与 fingerprint deterministic 测试
dependency fingerprint 不得读取或泄露 raw artifact、prompt、secret、private memory 或 provider response 测试
DependencyAssessment revision 与 input fingerprint currentness、无关 Task 变化不致 stale 测试
PRECOMMIT_NEW_BINDING 要求 source current DONE，POSTCOMMIT_EXISTING_BINDING 只核 immutable bound ref 测试
CONFIRMED / CHALLENGED / INVALIDATED / INDETERMINATE × 两 assessment mode 完整 reducer table 与多 edge 合并优先级测试
A -> B -> C immutable commitment ancestry assurance 正向闭包测试
closure 缺失、非法 cycle、未知 schema、policy unavailable 或 Event 顺序错误产生 INDETERMINATE 测试
source reopen 的 PRESERVED / INVALIDATED / UNCERTAIN 与追加式 resolution 测试
UNCERTAIN -> PRESERVED 后 resolution finalizer 精确清 fence/blocker、但旧 permit 永不复活测试
source reopen + PRESERVED 后 postcommit assessment 恢复 SATISFIED，但新 consumer / recommit 仍拒绝历史 ref 测试
reopen 原子清理 Validation / Dependency Set 与 execution / candidate / completion pointers，并按 REOPENED_PRIOR_RESULT 重建所需 current pointers 测试
PRESERVED 只维持既有 binding、不得为 source 当前非 DONE 的新 consumer 建立 binding 测试
DONE consumer impact 的 UNAFFECTED / INVALIDATED / REMEDIATION_REQUIRED authority 与逐层传播测试
UNAFFECTED provenance cut 精确 scope、closure 固定、证据失效后重新 challenge 测试
UNAFFECTED 令非终态 consumer closure 恢复后幂等 finalizer 正向恢复与其他 blocker 保留测试
UNAFFECTED 只能引用独立 DONE impact-review Task 的当前 PASSED Validation、不得在 DONE consumer 上启动 Validation 测试
dependency challenge 下活动 Run 的 Task 保持 ACTIVE、fence 新副作用并先收口测试
dependency PAUSE intent 不得覆盖既有 CANCEL 测试
DONE consumer 保持 DONE、plan_progress 不变、Goal member support 进入 REVIEW_REQUIRED 测试
Goal `CLOSED + ACHIEVED` 同步核对 selected route 与全部 pinned dependency ancestry 测试
INVALIDATED member 使用 HARD_BLOCKER 白名单、替代路线仍在时使用 ALTERNATIVE_ROUTE_REDUCED 测试
INVALIDATED 是 COMPLETE frontier 的完整负面事实、全部路线截断时 Goal BLOCKED 测试
CHALLENGED 且 current impact-review / remediation path 使用 COMPLETION_ASSURANCE_RESOLUTION_ACTIVE / ATTENTION_REQUIRED 测试
REMEDIATION_REQUIRED 绑定 current remediation Task，不得落入无原因的 health 状态测试
remediation Task lifecycle/spec/success contract/owner/currentness 与循环 dependency 负路径测试
CHALLENGED 无 current review path或 INDETERMINATE 只按准确 EVIDENCE_GAP 根因映射、不得生成未登记 reason code 测试
顶层 CLOSED Goal 出现历史 challenge 时不得自动 reopen 或改 outcome、必须交 Jenn review 测试
Priority selection snapshot 绑定 dependency revision / assessment / fingerprint，但 create_run 仍全量重检测试
create_run、permit、dispatch claim、effectful Validation、candidate adoption、complete_task 的同步 dependency gate 测试
VERIFYING rerun 原子 REJECT_FOR_NEW_EXECUTION、清 candidate/result/completion 与旧 PASSED currentness 测试
create_run 与 complete_task CAS 竞态、无 current candidate 的 NONE_EXPECTED 负路径测试
Run / Validation / TaskPermit 使用同构 dependency authority binding 和 completion-ref version/fence vector 测试
assurance 或 fence generation 改变后旧 permit / lease / dispatch 永久失效测试
assurance version 改变但仍 CONFIRMED 时活动 Run 安全收口、只以新 execution epoch 恢复测试
assurance / fence / policy 变化后仍 CONFIRMED 时 formal Validation / complete 先原子 refresh candidate commitment 测试
candidate refresh 业务拒绝持久化 Inbox/fence、CAS或BUSY技术冲突整笔 rollback/retry 测试
Fact 接纳、UNKNOWN reconciliation、Deadline stop、Control Intent finalizer 和 recovery 不被 dependency gate 拒绝测试
Validation Set 与 Dependency Set 在 commitment boundary 同事务冻结、部分失败全 rollback 测试
无 Run 的 DIRECT_RESULT_ADOPTION 与 REOPENED_PRIOR_RESULT candidate / VERIFYING 可达性测试
三个 candidate origin 的 Event kind、actor、run / epoch / result identity mismatch 拒绝测试
Task spec revision fence 旧 permit、清 set/commitment/candidate pointers、强制 refreeze 与 Priority REVIEW_REQUIRED 测试
旧 task_spec_revision commitment 不得启动 Validation / candidate / complete，且 spec mutation 与这些动作 CAS 竞态测试
Validation extension 不改写活动 Run execution commitment、生成同结果 superseding candidate、使旧 completion assessment 失去 current 资格测试
Validation extension 时 dependency gate 失效则原子拒绝 current candidate、不得跨 envelope 启动 attempt 测试
RecommitTaskDependencies 静止条件、相同 edge membership、replacement ref 与 effect disposition 守卫测试
recommit 逐 edge prerequisite identity、source current DONE/current completion provenance 与 Event 顺序测试
reopened source 的历史 PRESERVED ref 不得成为 recommit 新 binding 测试
Recommit 清 result、candidate/completion pointers、单次增加 completion epoch、重建三个 snapshot、更新 set/execution pointers 的原子性与幂等测试
Recommit 只 supersede 精确旧 dependency fence/blocker、不得清除其他 blocker 测试
recommit 后 RUN_RESULT 与 DIRECT_RESULT_ADOPTION 的 origin-specific candidate 绑定测试
UNKNOWN、未收口 effect、活动 Run / Validation / Control Intent 的 recommit 拒绝测试
迟到 SUCCEEDED / PASSED 只可阻止或触发 reconciliation、不得推进 current candidate 测试
projection 删除后从 Event 与 immutable rows 重建 assurance / reverse index / Goal support 且无副作用测试
SQLite selection/create、dependency mutation/complete 和 assurance/fence 并发竞态与 BUSY_SNAPSHOT rollback 测试
启动恢复在开放 permit 前校验 pointer、snapshot、fingerprint、fence、assurance 和 reverse index 测试
recovery 先产生 UNKNOWN / reconciliation facts，再重算 assurance，最后重建 projection 与执行 read barrier 测试
assurance 重算改变 version 后旧 assessment / Goal support 不得进入 readiness 测试
dependency recovery 在每个事务崩溃窗口可重入且不重复 epoch、Event、fence、permit 或 Outbox 测试
recovery mismatch 保持 DONE / FAILED / CANCELLED 终态，只更新 assurance / support / reconciliation 测试
Red TaskPermit 缺 Jenn authorization Event、policy revision、scope currentness 或撤销核验时拒绝测试
Dependency 不传播 Priority、Deadline、Budget、权限、P3 或 Goal ancestry 测试
Rolling planning 改变 horizon 不增加、删除或替换 canonical Goal plan member 测试
SchedulePlanProjection / TimeCriticalPathProjection / selection 不得创建 Run、permit、BudgetReservation、Outbox 或修改 Task state 测试
Planner / UI / Agent / external solver proposal 直接写 canonical scheduling state 拒绝测试
持久化 planning projection 删除后从当前输入无副作用重建、不产生 Event、permit 或 dispatch 测试
Duration / Calendar / Capacity 合同或当前输入缺失时只令相应时间预测不可用、不自动阻塞 Task / Goal 测试
时间投影不可用不得令逻辑上 COMPLETE 的 Critical Work Frontier 变成 PARTIAL / UNAVAILABLE 测试
预测迟到不得伪造 SoftCompletionTargetMissed、HARD_BLOCKER 或 Deadline 到期测试
TimeCriticalPathProjection 不改变 Critical Work Frontier、plan_progress、Goal closure、Task completion 或 base Priority 测试
Schedule revision 不增加 plan / task_spec / result / validation revision 测试
TaskPrioritySelectionSnapshot 保持唯一 canonical selection record、平行 DispatchSelectionSnapshot 拒绝测试
selection 不领取 capacity、不预留 Budget、不创建 permit 测试
selection 后 Task / dependency / Deadline / Budget / permit / host / P3 事实变化时 create_run 全量重检并拒绝旧依据测试
Pending R1：create_run 新分配 phase-correct commitment 时，该新 revision 与本次 BudgetReservation、Run、Event、permit、Outbox 原子全有或全无测试
Pending R1：create_run 复用 commitment 时，成功或 rollback 后既有 snapshot 均 byte-identical 且无写入，只有本次新记录原子全有或全无测试
Pending R1：create_run 业务拒绝或 SQLite / CAS 失败时不得留下本次新 commitment、Run、permit、reservation 或 Outbox，复用 snapshot 保持不变测试
host acceptance 与外部副作用不属于 SQLite 原子事务、失联时按 UNKNOWN / reconciliation 收口测试
effectful Validation 不得绕过 current-fact admission、permit、fence、host gate 和恢复测试
独立 Validation Execution Admission 合同冻结前，effectful Validation 未绑定 create_run Run 的启动拒绝测试
普通 NON_PREEMPTIVE scheduling 不因 Priority、selection 或预测变化暂停、取消或替换活动 Run 测试
Deadline stop、dependency fence、Jenn / Nobao Control Intent、P3 和 host safety stop 不被 NON_PREEMPTIVE 禁止测试
control / recovery lane 不参与普通 Priority / fairness 竞争，且不适用的普通 gate 不阻塞安全收口测试
普通业务伪装成 control work 拒绝、付费 provider call / 外部副作用仍服从适用 Budget / permit / P3 测试
普通 admission 不得占用或阻断本地 reducer、Receipt、fence、stop dispatch、finalizer 与 recovery read barrier 最小路径测试
projected_start_at 不成为 durable wake authority 测试
timer 丢失、重复或延迟只触发基于 ledger due fact 的幂等重新评估测试
启动恢复保留旧 selection 历史但不恢复 admission authority 测试
Run FAILED 不结束 Task 测试
UNKNOWN 不自动重试测试
BLOCKED 不被 PAUSED 遮盖测试
暂停和取消异步收口测试
迟到 receipt 入账但不推进旧 generation 测试
reopen 后旧 Validation 不自动复用测试
control intent supersede 和迟到回执测试
completion-blocking effect 未核对时不得终结测试
启动 fencing 和 recovery gate 测试
Jenn-only unresolved risk cancellation 测试
required Validation 完成资格测试
ArtifactRef schema、低披露 handle 和 digest 格式校验测试
无 digest 的 ArtifactRef 不得支持 PASSED 或 DONE 测试
原始路径、URL credential、secret、raw memory 和 raw provider response 不得进入 ArtifactRef 测试
storage_authority 不得通过 ArtifactRef 直接改写 Task / Goal 测试
完成所需 ArtifactRef 缺失或 digest 不匹配时不得产生 PASSED 测试
ArtifactRef 不形成第六领域对象或独立状态机测试
同一 epoch 新增无关 Requirement 不废掉既有 PASSED evidence 测试
reopen 后旧 PASSED 不自动继承测试
未声明 evidence_reuse_mode 时默认重验测试
NEVER_REUSE Requirement 的证据复用拒绝测试
REVALIDATE_WITH_OLD_EVIDENCE 只能参考旧证据、不能直接完成测试
CONDITIONAL_CARRY_FORWARD 仅在等价合同全部匹配时创建当前 PASSED 测试
跨 Task 或跨 Requirement revision 的 source Validation 复用拒绝测试
Requirement / Task spec / result / validator / input / environment / policy 变化后复用拒绝测试
过期或完整性失败 evidence 的复用拒绝测试
carry-forward Validation 不得成为下一次 source 的证据链拒绝测试
证据复用与 complete_task 的 CAS 竞争测试
证据复用不修改历史 attempt 或 Validation Set snapshot 测试
NON_WAIVABLE Requirement waiver 拒绝测试
已有当前 FAILED attempt 的普通 waiver 拒绝测试
UNKNOWN、未核对副作用或未收口 Control Intent 的 waiver 拒绝测试
waiver 与 complete_task 的 CAS 竞争测试
无关 snapshot extension 后有效 waiver carry-forward 测试
Requirement replace、reopen、Task spec / result revision 变化后 waiver 失效测试
waiver 到期或 Jenn 撤销后 Requirement 恢复 REQUIRED 测试
EXPIRY_REQUIRED waiver 的 follow-up / remediation Task 前置测试
全部 Requirement 被豁免时不得 DONE 测试
新 policy 使开放 Task waiver 失效、DONE Task 仅产生 remediation 测试
Validation Set commitment-boundary atomic freeze 测试
冻结后 Add / Replace / Attach 语义隔离测试
新增 Requirement 与 complete_task CAS 竞争测试
新增 Requirement 不废掉无关 PASSED evidence 测试
Replace 只使被替换 Requirement evidence 失效测试
运行中 Run 的 commitment snapshot / permit 绑定测试
OPEN_TASKS inheritance application event 测试
新 policy 不直接 reopen DONE、remediation Task 链接测试
Inbox 重复 command 测试
相同 command_id 不同 payload 协议冲突测试
Outbox 崩溃窗口和重复派发测试
SQLite 原子事务测试
migration forward / backup / restore 测试
进程崩溃后 reopen / reconciliation 测试
Node N-API integration 测试
VCPToolBox core unavailable 时 fail-closed 测试
无 provider、无 secret、无真实外部副作用的三任务 benchmark
```

## 24. 本决议不授权什么

本文件只记录架构，不授权：

```text
修改 VCPToolBox / VCPChat / VCPMobile runtime 源码
启用或恢复任何插件
启动任何服务
安装或升级 Rust toolchain
创建或修改活动 runtime 配置
读取 .env / config.env / secret / token / cookie / credential
调用真实 provider、Shell、Python、Codex CLI 或 executor
创建真实数据库或迁移真实状态
读取或迁移原始私人记忆
扩大公共 API / MCP schema / device capability
发布、部署、push、merge、tag 或 release
```

所有后续建设继续服从根 `AGENTS.md`、P3 和 Jenn 当时的明确任务范围。

## 25. 当前架构快照

```yaml
topology:
  backend_and_resident_home: VCPToolBox
  desktop_frontend: VCPChat
  mobile_frontend: VCPMobile

resident:
  name: AGENTSOSResident
  lifecycle_owner: VCPToolBox
  global_coordinator: Nobao
  resident_process_count: 1

agent_model:
  unique_resident_coordinator: Nobao
  long_lived_domain_agents: allowed
  temporary_workers: task_scoped
  deterministic_identity_continuity: required

ledger:
  canonical_global_task_ledger: AGENTSOSResident.GlobalTaskLedger
  one_authority_per_fact_class: required
  dashboard: read_only_projection

pending_r1_scheduling_amendment:
  status: pending_Jenn_freeze_decision
  effect_before_acceptance: none
  source: control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
  calendar_gate: NEW_START_AUTHORITY_ALLOWED
  deadline_kind: HARD_NEW_START_AUTHORITY_CUTOFF
  effective_deadline_field: effective_new_start_authority_cutoff
  effective_deadline_value_field: effective_new_start_authority_cutoff_utc_ms
  deadline_snapshot_field: effective_new_start_authority_cutoff_utc_ms
  deadline_reached_event: HardNewStartAuthorityCutoffReached
  deadline_task_blocker_reason: DEADLINE_NEW_START_AUTHORITY_PROHIBITED
  task_permit_field: start_authority_commit_before_utc_ms
  host_capability_field: checks_start_authority_commit_before
  start_authority_compliance_evidence: HostWorkAcceptanceFact_ACCEPTED_committed_by_Rust_before_cutoff
  physical_start_evidence: HostWorkStartDispositionFact_STARTED_or_stronger_authenticated_execution_fact
  host_acceptance_proves_physical_start: false
  run_attempts_settlement: positive_execution_evidence
  run_attempts_late_positive_after_RELEASED: RELEASED_to_SETTLED_exactly_once
  late_positive_old_run_state: REJECTED_terminal_unchanged
  late_positive_no_execution_assurance: CONTRADICTED
  late_effect_reconciliation: independent_existing_control_recovery_and_unresolved_effect_paths
  late_effect_budget_accounting_identity: complete_bound_reservation_and_release_event_set_fingerprint
  late_effect_later_positive_fact: enrich_existing_reconciliation_without_second_compensation
  late_effect_successor_scan: all_later_execution_epochs_and_current_completion_bindings
  late_effect_no_new_run_fence: required_atomic
  late_effect_active_task_projection:
    activity_kind: COORDINATING
    coordination_subtype: LATE_EFFECT_RECONCILIATION
    scope: physical_execution_possibly_active_while_stop_query_unfinished_and_no_current_UNKNOWN_or_nonterminal_successor_determines_state
    overrides_current_Run_UNKNOWN: false
  late_effect_blocked_task_projection: physical_execution_stopped_but_effect_influence_unresolved
  late_effect_terminal_task_auto_reopen: false
  late_effect_automatic_retry: false
  schedule_plan: pure_resource_unconstrained_time_forecast
  dependency_assurance_bound_to_time_projections: true
  fairness: checked_u128_virtual_service_with_system_floor
  zero_duration_requires_positive_evidence: true
  implementation_authorized: false

objects:
  - Goal
  - Task
  - Run
  - Validation
  - Event

artifact_refs:
  formal_core_object: false
  representation: typed_immutable_embedded_value
  content_in_ledger: forbidden
  storage_authority: external_governed_owner
  low_disclosure_handle: required
  independent_lifecycle_in_ledger: false
  promotion_requires_new_ADR: true

goal:
  lifecycle:
    - CLARIFYING
    - READY
    - ACTIVE
    - PAUSED
    - COMPLETION_REVIEW
    - CLOSED
  outcome:
    - ACHIEVED
    - ABANDONED
    - UNACHIEVABLE
    - SUPERSEDED
  top_level_close_authority: Jenn_only
  subgoal_close_authority: Nobao
  blocked: derived_health_not_lifecycle
  health_projection:
    direct_write: forbidden
    applicability:
      - NOT_ACTIVE
      - ACTIVE
    assessment_when_active:
      - HEALTHY
      - ATTENTION_REQUIRED
      - BLOCKED
      - INSUFFICIENT_EVIDENCE
    critical_frontier_status:
      - UNAVAILABLE
      - PARTIAL
      - COMPLETE
    route_expression:
      criterion_routes: ANY_OF
      route_group_members: ALL_OF
    hard_blocker_registry: v0.1
    hard_blocker_codes:
      - UNRECONCILED_UNKNOWN_EFFECT_ON_CURRENT_FRONTIER
      - CURRENT_FRONTIER_HARD_TASK_BLOCKER
      - CURRENT_FRONTIER_REQUIRED_TASK_TERMINAL
      - CURRENT_FRONTIER_REQUIRED_COMPLETION_ASSURANCE_INVALIDATED
      - REQUIRED_AUTHORIZATION_ROUTE_DENIED_OR_REVOKED
      - REQUIRED_POLICY_ROUTE_DENIED
      - REQUIRED_EXTERNAL_DEPENDENCY_CURRENTLY_UNAVAILABLE
    risk_registry: v0.1
    risk_never_auto_escalates_to_blocked: true
    risk_codes:
      - ALTERNATIVE_ROUTE_REDUCED
      - COMPLETION_ASSURANCE_RESOLUTION_ACTIVE
      - REQUIRED_VALIDATION_FAILURE_REMEDIATION_REQUIRED
      - GOAL_CRITERIA_UNMET_AT_PLAN_100
      - CRITICAL_FRONTIER_PROGRESS_SUSPENDED
      - SOFT_BUDGET_TARGET_EXCEEDED
      - SOFT_DEADLINE_TARGET_MISSED
      - EVIDENCE_BACKED_DOMAIN_RISK_ACTIVE
    validation_remediation_status:
      - MISSING
      - PLANNED
      - ACTIVE
    evidence_gap_registry: v0.1
    evidence_gap_direct_write: forbidden
    evidence_gap_summary_code: FRONTIER_INCOMPLETE
    evidence_gap_root_codes:
      - GOAL_SUCCESS_CRITERIA_INCOMPLETE
      - CURRENT_PLAN_UNAVAILABLE
      - CRITERION_ROUTE_MAPPING_INCOMPLETE
      - CURRENT_REQUIRED_FACT_MISSING
      - CANONICAL_FACT_RECONCILIATION_REQUIRED
      - REQUIRED_VALIDATION_RESULT_INCONCLUSIVE
      - REQUIRED_EVIDENCE_UNAVAILABLE_OR_UNVERIFIABLE
      - TIME_BOUND_HEALTH_FACT_STALE
      - DEADLINE_TIME_AUTHORITY_UNCERTAIN
      - BUDGET_ACCOUNTING_UNRECONCILED
      - HEALTH_POLICY_VERSION_UNAVAILABLE
    health_policy_unavailable_fallback: Rust_builtin_fail_closed
    time_critical_path_changes_goal_health: false
  plan_progress:
    basis: equal_weight_current_plan_leaf_tasks
    only_DONE_counts: true
    plan_revision_required: true
    reaches_100_does_not_close_goal: true
    dependency_challenge_changes_percent: false
  closure_assurance:
    synchronous_gate: required
    selected_route_must_be_complete: true
    all_required_members_done: true
    pinned_dependency_ancestry_must_be_confirmed: true
    unresolved_goal_closure_challenge_forbidden: true
    top_level_closed_goal_challenge_authority: Jenn_only

task:
  states:
    - READY
    - ACTIVE
    - WAITING
    - PAUSED
    - BLOCKED
    - VERIFYING
    - DONE
    - FAILED
    - CANCELLED
  direct_set_state: forbidden
  state_writer: Rust_reducer_only
  one_nonterminal_execution_run: true
  parallel_execution_requires_child_tasks: true
  unknown_forces_blocked: true
  blocked_precedes_paused: true
  reopen_isolates_old_evidence: true
  reopen_requires_prior_completion_disposition_when_done: true
  completion_epoch_increments_once_on_every_reopen_or_successful_dependency_recommit: true
  commitment_snapshots:
    - EXECUTION_ADMISSION
    - CANDIDATE_ADOPTION
    - COMPLETION_ASSESSMENT
  commitment_snapshot_binds_task_spec_revision: true
  commitment_revision_allocation: monotonic_per_snapshot_and_idempotent
  candidate_origins:
    - RUN_RESULT
    - DIRECT_RESULT_ADOPTION
    - REOPENED_PRIOR_RESULT
  unresolved_risk_acceptance: Jenn_only_CANCELLED
  required_validation_set:
    composition: layered_union
    layers:
      - NOBAO_TASK_SPECIFIC
      - RUST_POLICY_MANDATORY
      - GOAL_DOMAIN_INHERITED
      - JENN_EXPLICIT
    worker_can_remove: false
    empty_set_done_eligible: false
    freeze_boundary:
      earliest_of:
        - first_run_creation
        - first_formal_validation_attempt
        - first_entering_verifying
      snapshot_immutable: true
      reopen_requires_refreeze: true
    frozen_extension:
      operations:
        - ADD_REQUIREMENT
        - REPLACE_REQUIREMENT_REVISION
        - ATTACH_REQUIREMENT_PROVENANCE
      append_only_snapshot: true
      done_direct_extension: forbidden
      new_policy_reopens_done: forbidden
      active_run_snapshot_binding: required
      pre_execution_safety_via_validation_extension: forbidden
    waiver:
      default_waivability: NON_WAIVABLE
      grant_authority: Jenn_only
      failed_attempt_waivable: false
      unknown_or_unreconciled_effect_waivable: false
      waiver_is_validation_pass: false
      all_waived_done_eligible: false
      duration_policies:
        - NOT_APPLICABLE
        - COMPLETION_SCOPED_ONLY
        - EXPIRY_REQUIRED
      reopen_carries_waiver: false
    evidence_reuse:
      default_mode: REVALIDATE_WITH_OLD_EVIDENCE
      old_pass_auto_inherits_after_reopen: false
      conditional_carry_forward:
        deterministic_effect_free_immutable_only: true
        creates_new_current_validation_attempt: true
        source_must_be_authoritative_fresh_pass: true
        carry_forward_chain: forbidden
        exact_equivalence_fingerprint: required
        freshness_contract: required
        changes_snapshot_membership: false
        produces_external_side_effect: false
    requirement_attempt_relationship:
      requirement_is: immutable_task_owned_contract_item
      validation_is: attempt_against_one_requirement_revision
      one_requirement_many_attempts: true
      one_attempt_one_requirement: true
      set_revision_invalidates_unrelated_evidence: false
  progress_credit:
    DONE: 1
    FAILED: 0
    CANCELLED: 0

budget:
  contract_version: v0.1
  formal_core_object: false
  dimensions:
    - RUN_ATTEMPTS
    - MODEL_TOKENS
    - WALL_CLOCK_MS
    - MONEY_MICRO_UNITS
  modes:
    - SOFT_TARGET
    - HARD_CAP
  reservation_status:
    - RESERVED
    - SETTLED
    - RELEASED
    - UNKNOWN
  create_run_atomic_reservation: required
  run_attempts_authority_binding:
    cardinality: exactly_one_immutable_complete_member_set_per_Run_execution_epoch
    transaction: same_as_create_run_and_all_reservations
    expected_set_source_after_commit: binding_only
    commitment_reference: one_way_from_binding_to_exact_reusable_immutable_snapshot
    cross_binding: Run_reservations_permit_admission_Event_Outbox
    missing_or_corrupt: fail_closed_INDETERMINATE_no_partial_compensation
  all_applicable_envelopes_must_allow_hard_cap: true
  actual_usage_is_never_discarded: true
  over_cap_blocks_new_reservation: true
  monetary_hard_cap_increase_authority: Jenn_only
  budget_grants_provider_or_external_authority: false

deadline:
  contract_version: v0.1
  formal_core_object: false
  canonical_time: Rust_UTC_wall_clock
  boundary: now_greater_than_or_equal_is_reached
  kinds:
    - SOFT_COMPLETION_TARGET
    - HARD_NEW_EXECUTION_CUTOFF
    - HARD_ACTIVE_EXECUTION_STOP_CUTOFF
  client_or_js_time_authoritative: false
  timer_authoritative: false
  time_authority_states:
    - TRUSTED
    - UNCERTAIN
  hard_deadline_on_uncertain_time: fail_closed
  soft_deadline_inherits_to_descendants: false
  hard_deadline_inherits_to_descendants: true
  run_start_evidence: host_acceptance_fact_committed_by_Rust_before_cutoff
  late_host_timestamp_grants_retroactive_start: false
  active_run_continues_after_new_execution_cutoff: true
  same_run_scope_preserving_lease_renewal_after_start_cutoff: allowed
  hard_stop_control_intent: PAUSE
  deadline_cancel_task_automatically: false
  fence_is_task_blocker_automatically: false
  sticky_fence_release_requires_command: true
  closure_only_validation_after_cutoff: allowed
  effectful_validation_after_cutoff: forbidden
  task_blocker_subtypes:
    - DEADLINE_NEW_EXECUTION_PROHIBITED
    - DEADLINE_HARD_STOP_ENFORCEMENT_UNAVAILABLE
  deadline_revision_invalidates_validation_evidence: false
  independent_revision_after_task_or_goal_terminal: forbidden
  priority_overrides_hard_deadline: false

priority:
  contract_version: task-priority.v0.1
  formal_core_object: false
  classes_in_order:
    - HIGH
    - NORMAL
    - LOW
    - BACKGROUND
  default_class: NORMAL
  numeric_or_freeform_priority: forbidden
  authority_modes:
    - JENN_LOCKED
    - NOBAO_MANAGED
  basis_types:
    - SYSTEM_DEFAULT
    - JENN_EXPLICIT
    - GOAL_PLAN
    - DECOMPOSITION
    - REPRIORITIZATION
  multiple_goal_bindings: supported
  one_global_class_per_task: true
  context_fingerprint_contract: priority-context.v0.1
  context_representation: structured_task_specific_bindings
  context_digest: canonical_JSON_SHA256_lowercase_hex
  context_status:
    - CURRENT
    - REVIEW_REQUIRED
  review_required_scheduling_class: NORMAL
  context_reason_codes:
    - TASK_SCOPE_CHANGED
    - GOAL_BINDING_CHANGED
    - CRITERION_BINDING_CHANGED
    - PLAN_MEMBERSHIP_CHANGED
    - PRIORITY_POLICY_CHANGED
    - PRIORITY_POLICY_UNAVAILABLE
  selection_snapshot_binds_priority_revision: true
  selection_snapshot_binds_lifecycle_generation: true
  priority_change_preempts_selected_or_active_work: false
  parent_or_goal_auto_inheritance: false
  terminal_task_priority_mutation: forbidden
  reopen_preserves_priority_when_context_matches: true
  Jenn_lock_and_unlock_authority: Jenn_only
  unsupported_policy_fallback: REVIEW_REQUIRED_NORMAL
  priority_grants_execution_authority: false
  ordinary_priority_orders_safety_closure: false
  deferred_to_scheduling:
    - JENN_FOCUS
    - TEMPORARY_EXPEDITE
    - ELIGIBLE_WAIT_AGING
    - CROSS_GOAL_FAIRNESS
    - BACKGROUND_MINIMUM_SERVICE
    - STABLE_TIE_BREAK
    - CONCURRENCY_CAPACITY
    - FUTURE_PREEMPTIVE_SCHEDULING_POLICY

scheduling_architecture:
  contract_version: task-scheduling-architecture-boundary.v0.1
  formal_core_object: false
  model:
    - ROLLING_TIME_PLANNING
    - CURRENT_FACT_EVENT_DRIVEN_TASK_SELECTION
    - ATOMIC_EXECUTION_ADMISSION
  hard_realtime_latency_promised: false
  planning_projections:
    - SchedulePlanProjection
    - TimeCriticalPathProjection
  projections_are_read_only_rebuildable: true
  resource_schedule_projection: deferred
  selection_record: existing_TaskPrioritySelectionSnapshot
  parallel_selection_authority: forbidden
  selection_writer: Rust_core_only
  selection_grants_execution_authority: false
  selection_claims_capacity_or_budget: false
  scheduler_direct_set_task_state: forbidden
  execution_run_admission_boundary: create_run
  effectful_validation_bypass: forbidden
  effectful_validation_requires_create_run_until_separate_contract: true
  admission_rechecks_current_canonical_facts: true
  admission_atomicity_scope: local_Rust_SQLite_write_transaction
  host_acceptance_inside_ledger_transaction: false
  normal_scheduling_preemption: NON_PREEMPTIVE
  safety_control_stop_is_scheduling_preemption: false
  control_and_recovery_lane: separate_from_ordinary_effective_order
  control_lane_expands_authority: false
  inapplicable_normal_admission_gate_blocks_safety_closure: false
  new_paid_or_effectful_control_work_still_gated: true
  ordinary_admission_may_block_minimum_local_control_path: false
  timer_role: wakeup_only
  projected_start_is_durable_wake_authority: false
  ledger_due_facts_authoritative: true
  critical_work_frontier_is_time_critical_path: false
  schedule_changes_plan_progress_or_goal_closure: false
  future_input_contracts:
    DurationEstimate: proposed_final_draft_pending_Jenn_review
    Calendar: proposed_final_draft_pending_Jenn_review
    Capacity: proposed_final_draft_pending_Jenn_review
  future_exclusive_capacity_allocation:
    selection_owns_allocation: false
    atomic_or_equivalent_fenced_admission_required: true
    exact_contract: deferred_to_capacity_v0.1
  next_contract: scheduling-time-capacity-v0.1-final-review

task_dependency:
  contract_version: task-dependency.v0.1
  formal_core_object: false
  composition: ALL_OF
  edge_kind: PINNED_DONE_EVENT
  scope: same_goal_non_shared_endpoints
  alternative_routes_owner: Goal_ANY_OF_route_groups
  dependency_revision: immutable_append_only
  dependency_set_snapshot: immutable_direct_membership_and_bindings
  dependency_closure_snapshot: immutable_transitive_authority_envelope
  commitment_snapshot: immutable_phase_specific_and_binds_both_dependency_snapshots
  zero_edge_snapshot: required
  new_binding_requires_source_current_confirmed_done: true
  provenance_closure: pinned_completion_commitment_ancestry
  assessment:
    mode:
      - PRECOMMIT_NEW_BINDING
      - POSTCOMMIT_EXISTING_BINDING
    freshness:
      - CURRENT
      - STALE
      - EVALUATING
    outcome:
      - SATISFIED
      - WAITING
      - INTERVENTION_REQUIRED
      - INDETERMINATE
  completion_reference_assurance:
    - CONFIRMED
    - CHALLENGED
    - INVALIDATED
    - INDETERMINATE
  invalidated_is_absorbing: true
  fence_generation_monotonic: true
  synchronous_gate_phases:
    - create_run
    - permit_issuance
    - dispatch_claim
    - effectful_validation_start
    - candidate_adoption
    - complete_task
    - goal_closed_achieved
  asynchronous_projection_grants_authority: false
  active_run_fence_keeps_task_active_until_reconciled: true
  done_consumer_auto_reopen: false
  done_consumer_challenge_changes_plan_progress: false
  old_permit_revives_after_preserved_resolution: false
  confirmed_resolution_uses_precise_idempotent_fence_finalizer: true
  unaffected_impact_requires_evidence_backed_provenance_cut: true
  unaffected_impact_validation_owner: linked_DONE_DependencyImpactReview_Task
  recommit_requires_same_edge_membership_and_quiescence: true
  post_commit_edge_mutation: forbidden
  propagates_priority_deadline_budget_authority_or_goal_ancestry: false
  deferred:
    - CROSS_GOAL
    - SHARED_ENDPOINT
    - FOLLOW_CURRENT
    - PINNED_VALIDATED_RESULT
    - POST_COMMIT_EXTENSION

storage:
  current_state: operational_authority
  event_log: append_only_history_authority
  inbox: command_deduplication
  outbox: durable_effect_intents
  atomic_transaction: required
  database: SQLite
  writer: Rust_core_only

implementation:
  shell: VCPToolBox_JavaScript_hybridservice
  deterministic_core: Rust_NAPI
  default_sidecar: false
  initial_async_runtime: none
  initial_network_server: none

completion:
  run_success_completes_task: false
  required_validations_gate_task_done: true
  dependency_assurance_gates_task_done: true
  tasks_done_complete_goal: false
  goal_success_criteria_gate_goal_completion: true
  pinned_dependency_ancestry_gates_goal_closure: true

safety:
  unknown_run_auto_retry: false
  host_gate_before_side_effect: required
  dependency_fence_invalidates_old_permit_permanently: true
  red_permit_requires_current_Jenn_authorization_event: true
  raw_secrets_in_events_or_outbox: forbidden
```

## 26. 当前结论

```text
ACCEPTED ARCHITECTURE
IMPLEMENTATION NOT STARTED
NEXT REVIEW: SCHEDULING TIME CAPACITY V0.1 PROPOSED FINAL PACKAGE FROM SECTION 22
```
