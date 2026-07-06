# AGENTS OS 做事单

Status: local first version
Date: 2026-06-30

这个目录放 AGENTS OS 的“做事单”。

做事单的作用很简单：

```text
做事前先写清楚。
能自动做就做。
该留痕就留痕。
该停就停。
```

它不是为了拖慢建设，而是为了让 AGENTS OS 在加速的时候不乱跑。

## 当前文件

- `agents-os-task-envelope-v0.1.md`
  第一版做事单模板。
- `examples/`
  已填好的真实样例做事单。
- `drafts/`
  本目录的草案和治理试点材料。
- `validation-rules.json`
  做事单本地检查规则。
- `validate-task-envelope.py`
  做事单本地检查器。
- `run-task-envelope-loop.py`
  一键小闭环：读取做事单，运行 policy-router，运行本地检查器，并生成本地回执。
- `test-task-envelope-loop.py`
  一键小闭环的本地样例测试。
- `receipts/`
  本目录动作收据。
- `reviews/`
  本目录本地复核。

## 文档状态边界

本目录现在按三种文档边界看：

```text
active：README、做事单模板、validation-rules、validator、loop runner、测试脚本。
draft：drafts/ 里的文档治理试点材料，还不是 active authority。
example：examples/ 里的样例，只能当范本，不能当新规则。
```

`drafts/document-registry.v0.1.example.yaml` 是 Documentation Governance
Pilot 2 的 Document Registry 样例。它用来测试文档治理规则能不能扩展到
`control-plane/task-envelope/`，不替代 `WORKSPACE_REGISTRY.yaml`，也不授权
外部写入、runtime/provider 调用或正式 Memory 注册。

## 使用方式

每次遇到不是一句话就能完成的事情，先按模板填一张做事单。

如果不知道怎么填，先看：

```text
examples/2026-06-30-example-local-task-envelope-loop.md
```

最小判断：

- 这件事是什么？
- 现在是解释、草案、本地改动、外部执行，还是红线？
- 属于绿色区、黄色区，还是红色区？
- 能不能自动做？
- 做完要留下什么记录？
- 是否需要复核？
- 是否需要 Jenn 确认？

## 本地检查器

检查一张做事单有没有漏掉关键栏目：

```text
python3 control-plane/task-envelope/validate-task-envelope.py control-plane/task-envelope/examples/2026-06-30-example-local-task-envelope-loop.md
```

检查器只读 Markdown 文件，不执行里面的任务。

## 一键小闭环

把一张做事单跑完整预检：

```text
python3 control-plane/task-envelope/run-task-envelope-loop.py control-plane/task-envelope/examples/2026-06-30-example-local-task-envelope-loop.md
```

它会做四件事：

- 从做事单里读取 `行动描述`。
- 调用 `control-plane/policies/life-core/policy-router.py` 判断权限和边界。
- 调用 `validate-task-envelope.py` 检查做事单结构。
- 在 `receipts/` 生成一份轻量本地回执。

可能输出：

- `ALLOW`：绿色区，允许在做事单写明的本地安全范围内推进。
- `DRAFT_ONLY`：黄色区，只能做本地草案、收据和必要复核。
- `NEEDS_REVIEW`：黄色区，需要先复核。
- `NEEDS_JENN_CONFIRMATION`：红色区，需要 Jenn 明确确认。
- `FORBIDDEN`：红色区，不能执行，只能写边界说明或安全预案。
- `NEEDS_ENVELOPE_FIX`：做事单本身没填完整，先补齐再重跑。

本地测试：

```text
python3 control-plane/task-envelope/test-task-envelope-loop.py
```

这个闭环仍然不会执行做事单里的任务。它只做本地预检和本地留痕。

## 边界

这个目录只放本地流程、模板、收据、复核。

这里不能放：

- 密钥
- 私密记忆原文
- provider 原始响应
- 外部系统写入结果
- 运行时日志
- 正式记忆注册内容

## 关联规则

主要参考：

- `control-plane/policies/life-core/progressive-workflow.md`
- `control-plane/policies/life-core/policy-router.py`
- `control-plane/policies/life-core/permission-levels.md`
- `control-plane/policies/life-core/evidence-levels.md`
