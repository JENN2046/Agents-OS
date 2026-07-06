# Confirmation Package: Promote Governance Drafts Toward Active Local Use

Package ID: `governance-drafts-active-confirmation-package-2026-06-30`
Status: `draft_confirmation_package`
Date: 2026-06-30
Scope: `control-plane/registry/`
Prepared by: Nobao
Decision owner: Jenn

## 一句话

这是给 Jenn看的确认包：哪些 AGENTS OS 治理草案可以升成“本地默认用法”，哪些还继续留在草案区。

这份确认包本身不生效。只有 Jenn 明确确认后，才进入实际改文件步骤。

## 当前已经跑通什么

当前本地治理小闭环已经跑通：

```text
life-core
-> policy-router
-> task-envelope / validator / loop-runner
-> Governance Registry draft
-> Scorecard draft
-> Scorecard Validator
-> Decision Record draft
-> Golden Path real example
-> receipt + review + tests
```

最近验证结果：

```text
Governance Registry scorecard: objects=9 pass=9 warn=0 fail=0
Scorecard validator tests: cases=3 failures=0
Task-envelope loop tests: cases=3 failures=0
Policy-router tests: cases=17 failures=0
```

## 这次请 Jenn 确认什么

建议 Jenn 确认的是：

```text
允许把部分治理草案升级为 AGENTS OS 本地默认工作流。
```

不是确认：

```text
不是外部写入许可。
不是 runtime/provider/plugin 调用许可。
不是正式 Memory 注册。
不是部署、发布、Git 推送。
不是放开 P3。
不是让 registry 或 scorecard 替 Jenn 做最终决定。
```

## 推荐方案

推荐采用“分层激活”，不要一次把所有草案都变 active。

## 建议升 active 的部分

### 1. Golden Paths v0.1

建议状态：

```text
promote_to_active_local_guidance
```

建议原因：

```text
它已经跑过一条真实样例。
它能让常见治理动作不用每次重想。
它有停止条件。
它明确不能绕过 Jenn、P3、外部写入、runtime/provider/plugin、正式 Memory。
```

建议 active 后的效力：

```text
作为 AGENTS OS 本地建设的默认路线参考。
适用于新增治理部件、改规则、草案升 active、新增检查器、红线事件处理、本地小闭环。
不自动授权任何红线动作。
```

批准后建议改动：

```text
1. 新增 active 文件：control-plane/registry/GOLDEN_PATHS.md
2. 保留 draft 文件作为历史来源。
3. 在 README 里标注 active guidance。
4. 留 active-promotion receipt/review。
```

### 2. Decision Record Template v0.1

建议状态：

```text
promote_to_active_template
```

建议原因：

```text
已经用它写出第一条真实 decision record 草案。
它解决“为什么这样定”的留痕问题。
它明确小改动不必写 decision record，避免治理过重。
```

建议 active 后的效力：

```text
凡是草案升 active、权限边界变化、registry schema 变化、重要治理方向变化，默认使用这个模板写 decision record。
普通小修不强制使用。
```

批准后建议改动：

```text
1. 新增 active template：control-plane/registry/templates/decision-record-template-v0.1.md
2. 或新增 active guidance：control-plane/registry/DECISION_RECORDS.md
3. 保留 draft 文件作为历史来源。
4. 留 active-promotion receipt/review。
```

### 3. Governance Scorecard v0.1 + Scorecard Validator

建议状态：

```text
promote_to_active_local_check
```

建议原因：

```text
Scorecard Validator 已经是本地可运行检查器。
它能检查 registry 对象是否有 id、type、status、owner、authority、red_zone、validation、evidence、receipt、review。
它已经通过正常样例、坏样例、secret-like 样例测试。
```

建议 active 后的效力：

```text
凡是新增或修改 Governance Registry 对象，默认跑 scorecard validator。
Scorecard 只给 PASS/WARN/FAIL，不授权执行。
```

批准后建议改动：

```text
1. 新增 active guidance：control-plane/registry/SCORECARD.md
2. 保留 validate-governance-registry.py 作为 active local checker。
3. README 标注本地默认检查命令。
4. 留 active-promotion receipt/review。
```

### 4. First Decision Record

建议状态：

```text
accept_with_limited_scope
```

建议对象：

```text
control-plane/registry/drafts/2026-06-30-decision-governance-control-plane-layer.draft.md
```

建议原因：

```text
它记录了为什么先采用“草案 + 检查器 + receipt + review”的中间路线。
它没有请求放开红线。
它把回看条件写清楚了。
```

批准后建议改动：

```text
1. 复制或移动为：control-plane/registry/decisions/2026-06-30-governance-control-plane-layer.md
2. 将 Status 从 draft 改为 accepted。
3. 保留原 draft 或在原 draft 里标注 superseded_by active decision。
4. 留 active-promotion receipt/review。
```

## 建议暂缓升 active 的部分

### Governance Registry YAML example

当前文件：

```text
control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml
```

建议状态：

```text
keep_as_draft_example_for_now
```

暂缓原因：

```text
它现在还是 example YAML。
它登记了 9 个对象，但还没有变成正式 authority data。
直接升 active 会比其他草案更重。
目前已有 WORKSPACE_REGISTRY.yaml 是 active workspace registry；不要混淆两个 registry。
```

建议下一阶段：

```text
如果 Jenn 确认需要 active Governance Registry，再单独创建：
control-plane/registry/GOVERNANCE_REGISTRY.yaml

并且只登记治理对象，不替代 WORKSPACE_REGISTRY.yaml。
```

### Governance Registry Markdown draft

当前文件：

```text
control-plane/registry/drafts/agents-os-governance-registry-v0.1-draft.md
```

建议状态：

```text
keep_as_design_draft
```

暂缓原因：

```text
它是设计说明，不一定要直接 active。
其中成熟部分可以被拆进 active GOLDEN_PATHS.md、SCORECARD.md、DECISION_RECORDS.md。
```

## Jenn 可以选择的确认项

Jenn 可以只确认其中一部分。

```text
[ ] A. 批准 Golden Paths v0.1 成为本地默认路线参考。
[ ] B. 批准 Decision Record Template v0.1 成为本地默认决策记录模板。
[ ] C. 批准 Governance Scorecard v0.1 + Validator 成为本地默认 registry 体检流程。
[ ] D. 接受第一条 Decision Record，限定范围为本地 governance control-plane。
[ ] E. 暂不批准 Governance Registry YAML example 升 active，继续作为 draft example。
[ ] F. 授权 Nobao 在本地执行上述被勾选项的 active-promotion 文件改动，并留下 receipt/review。
```

推荐勾选：

```text
A, B, C, D, E, F
```

不推荐现在做：

```text
不推荐把 Governance Registry YAML example 直接升为 active authority data。
不推荐把任何外部写入、runtime/provider/plugin、正式 Memory 纳入这次确认。
```

## 如果 Jenn 批准，Nobao 将做什么

只在本地做这些：

```text
1. 新增 active guidance/template 文件。
2. 把 accepted Decision Record 放到 decisions/。
3. 更新 README，区分 active / draft / example。
4. 更新 Governance Registry draft/example 中相关对象状态。
5. 跑 scorecard validator。
6. 跑 scorecard tests。
7. 跑 task-envelope loop tests。
8. 跑 policy-router tests。
9. 留 active-promotion receipt 和 review。
```

不会做这些：

```text
不会改 WORKSPACE_REGISTRY.yaml，除非 Jenn 明确要求。
不会外部写入。
不会 git push。
不会部署、发布、打 tag。
不会调用 provider/runtime/plugin。
不会读取或记录密钥、私密记忆、provider 原始响应。
不会注册正式 Memory。
```

## 风险

```text
1. active 文件增多，可能让 control-plane 看起来更重。
2. 如果 active / draft 标注不清，未来 agent 可能误用。
3. Scorecard Validator 仍然是结构检查，不是语义真理。
4. Decision Record 不能被滥用到每个小改动，否则会拖慢建设。
```

## 缓解方式

```text
1. 只激活最小必要文件。
2. 每个 active 文件开头写清楚它不授权什么。
3. README 明确 active、draft、example 的区别。
4. Scorecard 继续只作为检查器，不作为授权器。
5. 小改动继续用 receipt，不强制 decision record。
```

## 验证依据

已有验证：

```text
Governance Registry scorecard: objects=9 pass=9 warn=0 fail=0
Scorecard validator tests: cases=3 failures=0
Task-envelope loop tests: cases=3 failures=0
Policy-router tests: cases=17 failures=0
Golden Path example completed
```

## 最终确认句

如果 Jenn 要批准，可以直接说：

```text
确认 A B C D E F，按这个确认包执行本地 active-promotion，不碰外部写入、runtime、provider、正式 Memory、WORKSPACE_REGISTRY.yaml。
```

如果 Jenn 只想部分批准，也可以说：

```text
只确认 A C E F。
```

## 当前状态

```text
draft_confirmation_package
未执行升 active
等待 Jenn 明确确认
```
