# AGENTS OS Golden Paths v0.1 Draft

Status: `draft_not_active`
Date: 2026-06-30
Scope: local AGENTS OS control-plane work

Promotion note:

```text
Jenn promoted this guidance to active local use on 2026-06-30.
Active file:
control-plane/registry/GOLDEN_PATHS.md

This draft is retained as historical source material.
```

## 一句话

Golden Paths 是 AGENTS OS 的“标准做事路线”。

它的目的不是加审批，而是让正确做法最省事：

```text
遇到常见事情
不用重新想流程
直接走一条清楚路线
做完留下证据
碰到红线就停
```

## 不是什么

Golden Paths 不是：

- 不是授权 Jenn 之外的最终决定。
- 不是跳过 `policy-router`、`task-envelope`、review 或 P3 的捷径。
- 不是外部写入许可。
- 不是 runtime、provider、plugin 调用许可。
- 不是正式 Memory 注册流程。

它只是本地标准路线草案。

## 通用前置判断

走任何路线前，先问五个问题：

```text
1. 这是本地事，还是外部事？
2. 会不会碰密钥、私密记忆、provider 原始响应？
3. 会不会改正式记忆、身份、关系、家规、生命内核？
4. 做错了能不能回看、修正？
5. 做完需要什么证据？
```

如果碰红线：

```text
停。
只写边界说明或安全预案。
不要执行。
```

## 路线 1：新增治理部件

适用场景：

- 新增一个 policy module。
- 新增一个 validator。
- 新增一个 registry 草案。
- 新增一个 runbook。
- 新增一个 task-envelope 类型。

标准步骤：

```text
1. 写一句话说明这个部件解决什么问题。
2. 判断它是绿色、黄色还是红色。
3. 如果是黄色，先放 drafts/，不要直接 active。
4. 写清楚它不是什么，避免误用。
5. 写清楚 owner、scope、authority、green/yellow/red zone。
6. 如果它会被机器使用，准备最小 example 或 fixture。
7. 留 receipt。
8. 如果边界有变化，留 review。
9. 跑最近的本地验证。
10. 把结果写回 receipt。
```

产出：

```text
draft 或 active file
receipt
review if boundary changed
validation summary
```

停止条件：

- 需要读取密钥、私密记忆、provider 原始响应。
- 需要写外部平台。
- 需要 runtime/provider/plugin 调用。
- 需要把草案直接升成正式规则。
- 需要改 Jenn 身份、关系、家规、生命内核。

## 路线 2：修改已有规则或流程

适用场景：

- 改 `progressive-workflow`。
- 改 `policy-router.rules.json`。
- 改 `validation-rules.json`。
- 改 task-envelope 模板。
- 改 registry schema。

标准步骤：

```text
1. 先说清楚为什么要改。
2. 标出影响范围。
3. 判断是不是只影响本地 control-plane。
4. 小改动可以直接 patch，但必须留 receipt。
5. 边界变化必须留 review。
6. 如果会改变权限、红线、正式状态，先写 decision record 草案。
7. 跑相关测试或检查。
8. 如果测试失败，用失败结果修正；不能修就停。
```

产出：

```text
changed file
receipt
review if boundary changed
decision record if authority changed
validation summary
```

停止条件：

- 改动会削弱 P3。
- 改动会让外部写入自动化。
- 改动会让草案自动 active。
- 改动会绕过 Jenn 确认。

## 路线 3：草案升为 active

适用场景：

- `draft_not_active` 要变成 active。
- example YAML 要变成正式 registry data。
- 流程草案要成为默认流程。

标准步骤：

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

产出：

```text
decision record
review
receipt
active file update
validation summary
```

停止条件：

- Jenn 没确认但需要 Jenn 确认。
- 草案没有 red_zone。
- 没有验证方式。
- 没有 owner。
- 升级会改变外部行为。

## 路线 4：新增本地检查器

适用场景：

- 新增 validator。
- 新增 scorecard。
- 新增 fixture test。
- 新增一键 loop。

标准步骤：

```text
1. 写清楚检查器只检查什么，不执行什么。
2. 输入必须是本地安全文件。
3. 输出必须能被人看懂。
4. 至少准备一个通过样例和一个失败样例。
5. 不读取 .env、secret、state-private、私密记忆原文。
6. 不调用外部系统。
7. 跑本地测试。
8. 留 receipt 和 review。
```

产出：

```text
checker script or rules file
fixture/example
receipt
review
validation summary
```

停止条件：

- 检查器需要读取秘密或私密状态。
- 检查器会执行被检查对象里的任务。
- 检查器会写外部平台。
- 检查器会把 warning 当成正式授权。

## 路线 5：红线事件处理

适用场景：

- 任务碰到密钥。
- 任务碰到私密记忆原文。
- 任务想写外部平台。
- 任务想调用 provider/plugin/runtime。
- 任务想部署、发布、打 tag、强推、改历史。
- 任务想直接改正式 Memory、身份、关系、家规、生命内核。

标准步骤：

```text
1. 立刻停。
2. 不读取、不复制、不总结受保护内容。
3. 只写看得见的边界事实。
4. 写安全预案：要做需要什么确认、范围、回滚、证据。
5. 如果 Jenn 明确授权，再从新的授权范围重新开始。
```

产出：

```text
boundary note
safe proposal
no execution
```

停止条件：

```text
已经在红线里。
停止就是正确动作。
```

## 路线 6：跑本地小闭环

适用场景：

- 已经有一张 task envelope。
- 想先看能不能推进。
- 想检查结构和权限判断是否一致。

标准步骤：

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
4. 如果真的改文件，留 receipt。
5. 如果边界变化，留 review。
```

推荐命令：

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/task-envelope/run-task-envelope-loop.py <task-envelope-path>
```

产出：

```text
gate result
local receipt
next step
```

## 最小路线选择表

```text
新增东西 -> 路线 1
改规则 -> 路线 2
草案转正式 -> 路线 3
新增检查器 -> 路线 4
碰红线 -> 路线 5
先预检 -> 路线 6
```

## v0.1 通过标准

这份草案要算可用，至少满足：

- Jenn 能快速知道一件常见事该走哪条路。
- 每条路都有停止条件。
- 每条路都说清楚要留下什么证据。
- 不把草案当正式授权。
- 不绕过 P3。

## 第一条真实样例

```text
control-plane/registry/examples/2026-06-30-golden-path-new-governance-object-scorecard-validator.md
```

这条样例用 `路线 1：新增治理部件` 回放了
`governance-registry-scorecard-validator` 的建设闭环。

它证明 Golden Paths 可以用来检查一个真实新增治理部件有没有：

```text
说明
边界
owner
registry 登记
fixture
receipt
review
validation
```

## 当前状态

This file is a draft. It does not activate any path by itself.
