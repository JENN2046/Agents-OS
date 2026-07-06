# 样例做事单：创建第一张本地做事单样例

Template ID: `agents-os.task-envelope.v0.1`
Example ID: `example-local-task-envelope-loop-2026-06-30`
Status: `completed_example`
Date: 2026-06-30

## 这张单子是干嘛的

这是一张真实填过的样例做事单。

它演示 AGENTS OS 怎么从“想做一件小事”走到：

```text
先判断
再执行
再留痕
再复核
最后验收
```

## 1. 事情本身

事情名称：

```text
创建第一张本地做事单样例
```

一句话说明：

```text
把 AGENTS OS 做事单模板填成一张真实样例，让后续任务有可参考的范本。
```

为什么现在要做：

```text
我们已经有了渐进式做事流程和做事单模板，但还缺一张跑过的小样例。
没有样例，模板还是纸面；有了样例，AGENTS OS 才开始真正走第一步。
```

谁来做：

```text
Nobao
```

## 2. 现在处在哪个阶段

在下面选一个最接近的：

```text
[ ] 只是看一眼 / 解释
[ ] 写本地草案
[x] 整理本地文档或结构
[ ] 改本地规则或流程
[ ] 跑已有本地测试
[ ] 新增本地测试样例
[ ] 准备外部工具或运行时方案
[ ] 改外部工具或运行时配置
[ ] 真实调用外部工具 / provider / plugin
[ ] 写入外部平台，比如 Notion、GitHub、邮件
[ ] 影响正式记忆、身份、关系、家规、生命内核
[ ] 碰到密钥、私密记忆、provider 原始响应
```

阶段说明：

```text
这是一个本地文档和结构建设动作。它创建 examples/ 里的第一张样例单，
不对外写入，不调用运行时，不改变正式记忆。
```

## 3. 颜色区判断

绿色区：

```text
可以默认自动做。通常是本地、低风险、可回看、不会碰外部系统或红线。
```

黄色区：

```text
可以小步推进。先做草案、留痕、回看，不直接变正式。
```

红色区：

```text
不能自动做。只能停下、说明边界、给 Jenn 预案。
```

本次判断：

```text
[x] 绿色区
[ ] 黄色区
[ ] 红色区
```

为什么这样判断：

```text
只在 control-plane/task-envelope/ 内新增本地样例、收据和复核。
不碰密钥、私密记忆、provider 原始响应、外部写入、运行时执行、正式记忆。
```

## 4. policy-router 预检

行动描述：

```text
create local task envelope example and receipt
```

预检结果：

```text
decision: allowed
permission: A2
需要的证据: receipt, validation_summary
不能碰的边界: secret_access, external_writes, runtime_execution, formal_memory_registration
```

如果没有跑 policy-router，说明原因：

```text
已运行 policy-router。
```

## 5. 能不能自动做

自动推进判断：

```text
[x] 可以自动做
[ ] 只能做本地草案
[ ] 需要复核后再继续
[ ] 需要 Jenn 明确确认
[ ] 不能做，只能写预案
```

允许做的范围：

```text
创建 examples/ 目录。
新增一张真实样例做事单。
更新 task-envelope README。
留下本次 A2 收据和本地复核。
运行本地验证。
```

不能做的范围：

```text
不能写 Notion、GitHub、邮件或任何外部平台。
不能调用 provider、plugin、runtime。
不能读取密钥、私密记忆、provider 原始响应。
不能声称已经完成正式记忆注册。
```

## 6. 做事步骤

计划步骤：

```text
1. 用 policy-router 判断本次动作。
2. 创建 examples/ 目录。
3. 填写第一张真实样例做事单。
4. 更新 README，让样例可发现。
5. 留下收据和本地复核。
6. 验证样例和收据存在，运行 router 回归测试。
```

停止条件：

```text
如果需要外部写入、读取密钥、读取私密记忆、调用 provider/runtime、
或修改正式记忆，就停止，只写边界说明。
```

## 7. 留痕要求

这件事做完要留下：

```text
[ ] 一句话说明
[x] 收据
[x] 本地复核
[ ] Jenn 确认记录
[ ] 记忆候选
[ ] 正式记忆流程
[ ] 只写边界预案，不执行
```

收据位置：

```text
control-plane/task-envelope/receipts/2026-06-30-a2-example-task-envelope-loop.md
```

复核位置：

```text
control-plane/task-envelope/reviews/2026-06-30-a2-example-task-envelope-loop.review.md
```

## 8. 验收

怎么知道这件事做完了：

```text
examples/ 下有一张真实填完的做事单。
README 指向 examples/。
本次动作有收据和本地复核。
policy-router 回归测试通过。
```

怎么验证：

```text
检查样例文件存在。
检查 README 包含 examples/。
检查收据和复核文件存在。
运行 control-plane/policies/life-core/test-policy-router.py。
```

还剩什么风险：

```text
这是文档级样例，不是机器强制表单。
后续还需要把做事单变成更固定的格式，或接入自动检查。
```

## 9. 最终状态

```text
[ ] 未开始
[ ] 进行中
[x] 已完成
[ ] 已暂停
[ ] 被红线挡住
[ ] 需要 Jenn
```

结果说明：

```text
第一张真实样例做事单已创建，并完成本地收据、复核和验证。
```

## 10. 大白话复述

最后用一句人话复述：

```text
这件事是：给 AGENTS OS 做事单填第一张真实样例。
它属于：绿色区 / A2 本地建设。
我能做：本地创建样例、更新说明、留下收据和复核、跑本地测试。
我不能碰：外部写入、密钥、私密记忆、provider、runtime、正式记忆。
做完会留下：样例做事单、收据、本地复核、验证结果。
```
