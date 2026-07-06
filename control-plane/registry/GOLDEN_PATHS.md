# AGENTS OS Golden Paths v0.1

Status: `active_local_guidance`
Date: 2026-06-30
Scope: local AGENTS OS control-plane work
Accepted by: Jenn confirmation in current Codex thread

## 一句话

Golden Paths 是 AGENTS OS 的本地默认做事路线。

它让常见治理动作不用每次重想：

```text
遇到常见事情
走固定路线
做完留下证据
碰到红线就停
```

## 不授权什么

Golden Paths 不授权：

- 外部写入。
- runtime / provider / plugin 调用。
- 正式 Memory 注册。
- 部署、发布、打 tag、git push。
- 读取密钥、私密记忆原文、provider 原始响应。
- 绕过 Jenn、P3、review、task-envelope 或 policy-router。

## 默认三档

AGENTS OS 的默认执行方式收敛为三档：

```text
Green Fast Lane
Yellow Work Batch
Red Hard Stop
```

### Green Fast Lane

适用：

```text
本地
可逆
边界清楚
不碰 secrets / token / cookie / private raw memory / provider raw response
不改 auth/provider/runtime 配置
不启动服务
不做 provider call
不做外部不可逆写入
不做 destructive / bulk 操作
不写正式 Memory
```

默认行为：

```text
直接做
少解释
跑最近的有用验证
最终回复里说明结果、验证、风险
不要准备 confirmation package
不要为了习惯额外造 receipt/review
```

只有当 Green 工作会影响未来回放时，才留一份很短的 receipt。

### Yellow Work Batch

适用：

```text
本地 source checkout
本地 dependency/toolchain setup
本地 build artifact
多文件治理更新
runtime-local cache 或 report 写入
边界清楚但副作用真实
```

默认行为：

```text
把相关动作合成一个 batch
一次说清 scope / allowed writes / forbidden actions
按 batch 推进
失败或出现新风险就停
只留一份 batch report 或 receipt
只有边界变化或风险不低时才加 review
```

Yellow 不应该拆成很多小门。能一批完成的，就一批完成。

### Red Hard Stop

适用：P3。

```text
secrets / token / cookie / credential
private raw memory
provider raw response
auth/provider/runtime 配置修改
provider call
服务联网首启或对外暴露
force push / tag / deploy / release / publish
database write
destructive / bulk delete / move / overwrite
外部不可逆写入
正式 Memory / Activation
```

默认行为：

```text
停
写最小 preflight
等 Jenn 当前明确授权
如果 package 写了 Exact Confirmation Text，必须收到该 text 或 Jenn 明确说确认执行该 exact text
不得从模糊短语推断授权
```

## 通用前置判断

每次先问：

```text
1. 这是本地事，还是外部事？
2. 会不会碰密钥、私密记忆、provider 原始响应？
3. 会不会改正式记忆、身份、关系、家规、生命内核？
4. 做错了能不能回看、修正？
5. 做完需要什么证据？
```

判断结果：

```text
全是本地、可逆、无 P3 -> Green Fast Lane
本地写入真实但边界清楚 -> Yellow Work Batch
碰 P3 或授权不清 -> Red Hard Stop
```

碰红线就停，只写边界说明或安全预案。

## 路线 1：新增治理部件

适用：新增 policy module、validator、registry 草案、runbook、task-envelope 类型。

步骤：

```text
1. 写一句话说明这个部件解决什么问题。
2. 判断它是绿色、黄色还是红色。
3. 如果是黄色，先放 drafts/，不要直接 active。
4. 写清楚它不是什么，避免误用。
5. 写清楚 owner、scope、authority、green/yellow/red zone。
6. 如果它会被机器使用，准备最小 example 或 fixture。
7. 按三档证据规则收口：Green 少证据，Yellow 一份 batch evidence，Red 等确认。
8. 只有边界变化或风险不低时才留 review。
9. 跑最近的本地验证。
10. 如果留了 evidence，把结果写回 evidence。
```

停止条件：

- 需要读取密钥、私密记忆、provider 原始响应。
- 需要写外部平台。
- 需要 runtime/provider/plugin 调用。
- 需要把草案直接升成正式规则。
- 需要改 Jenn 身份、关系、家规、生命内核。

## 路线 2：修改已有规则或流程

适用：改 workflow、router rules、validator rules、task-envelope 模板、registry schema。

步骤：

```text
1. 先说清楚为什么要改。
2. 标出影响范围。
3. 判断是不是只影响本地 control-plane。
4. Green 小改动可以直接 patch，不默认造 confirmation package。
5. Yellow 变化用一个 batch evidence 收口。
6. 如果会改变权限、红线、正式状态，先写 decision record。
7. 跑相关测试或检查。
8. 如果测试失败，用失败结果修正；不能修就停。
```

停止条件：

- 改动会削弱 P3。
- 改动会让外部写入自动化。
- 改动会让草案自动 active。
- 改动会绕过 Jenn 确认。

## 路线 3：草案升为 active

适用：`draft_not_active` 要变 active、example YAML 要变正式 data、流程草案要成为默认流程。

步骤：

```text
1. 确认草案已经被实际用过，且有 receipt。
2. 写 decision record。
3. 写清楚为什么现在要升 active。
4. 检查它有没有 owner、scope、authority、red_zone、validation。
5. 跑本地验证。
6. 做本地 review。
7. 如果涉及权限、记忆、身份、关系、外部写入，必须 Jenn 明确确认。
8. 通过后再改 active 文件。
```

停止条件：

- Jenn 没确认但需要 Jenn 确认。
- 草案没有 red_zone。
- 没有验证方式。
- 没有 owner。
- 升级会改变外部行为。

## 路线 4：新增本地检查器

适用：新增 validator、scorecard、fixture test、一键 loop。

步骤：

```text
1. 写清楚检查器只检查什么，不执行什么。
2. 输入必须是本地安全文件。
3. 输出必须能被人看懂。
4. 至少准备一个通过样例和一个失败样例。
5. 不读取 .env、secret、state-private、私密记忆原文。
6. 不调用外部系统。
7. 跑本地测试。
8. 按三档证据规则收口；不要默认成套 receipt/review。
```

停止条件：

- 检查器需要读取秘密或私密状态。
- 检查器会执行被检查对象里的任务。
- 检查器会写外部平台。
- 检查器会把 warning 当成正式授权。

## 路线 5：红线事件处理

适用：碰到密钥、私密记忆、provider 原始响应、外部写入、runtime/provider/plugin、部署发布、强推改历史、正式 Memory、身份关系家规生命内核。

步骤：

```text
1. 立刻停。
2. 不读取、不复制、不总结受保护内容。
3. 只写看得见的边界事实。
4. 写安全预案：要做需要什么确认、范围、回滚、证据。
5. 如果 Jenn 明确授权，再从新的授权范围重新开始。
```

## 路线 6：跑本地小闭环

适用：已有 task envelope，想先看能不能推进。

步骤：

```text
1. 填 task envelope。
2. 跑 task-envelope loop runner。
3. 看结果：
   ALLOW -> 绿色区，可以在本地范围做。
   DRAFT_ONLY -> 黄色区，只做草案。
   NEEDS_REVIEW -> 先复核。
   NEEDS_JENN_CONFIRMATION -> 停，等 Jenn 明确确认。
   FORBIDDEN -> 停，只写预案。
   NEEDS_ENVELOPE_FIX -> 补单子。
4. 如果真的改文件，按三档证据规则收口。
5. 如果边界变化或风险不低，再留 review。
```

推荐命令：

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/task-envelope/run-task-envelope-loop.py <task-envelope-path>
```

## 路线 7：文档治理收尾

适用：新增、修改、归档、登记 AGENTS OS 文档治理对象。

步骤：

```text
1. 先判断新文件属于哪一类：
   当前有效文档 -> 登记进对应 Document Registry。
   草案 / 模板 / 样例 -> 登记，但写清楚不是 active authority。
   已知另管 -> 写进 known_external_scope。
   历史材料 -> 用 archive note 成组覆盖。
2. 不要为了习惯新增 receipt / review；如果新增了 evidence 文件，才同步登记。
3. 如果登记数量变了，同步 expected_document_count。
4. 跑 validate-document-registry。
5. 跑 validate-federated-document-registry。
6. 跑 docctl doctor。
7. 目标是 unregistered=0、warn=0、fail=0。
8. 如果暂时做不到，receipt/review 里必须写清楚偏离原因和下一步。
```

推荐命令：

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

停止条件：

- 要把历史文件批量移动、删除或改写。
- 要把草案自动当 active authority。
- 要碰 secrets、state-private、provider 原始响应或正式 Memory。
- 要把本地文档治理结果写到外部系统。

## 路线选择表

```text
新增东西 -> 路线 1
改规则 -> 路线 2
草案转正式 -> 路线 3
新增检查器 -> 路线 4
碰红线 -> 路线 5
先预检 -> 路线 6
文档治理收尾 -> 路线 7
本地可逆小事 -> Green Fast Lane
本地有副作用但边界清楚 -> Yellow Work Batch
P3 或授权不清 -> Red Hard Stop
```

## 已跑真实样例

```text
control-plane/registry/examples/2026-06-30-golden-path-new-governance-object-scorecard-validator.md
```

## 当前边界

这是 active local guidance，不是外部授权、runtime 授权、provider 授权、正式 Memory 授权，也不是绕过 Jenn 或 P3 的许可。
