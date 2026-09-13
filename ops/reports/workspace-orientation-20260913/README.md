# 工作区入口整理回执 · 2026-09-13

> 历史回执：下文记录原 D 的旧整理过程，不是本候选的完整保全或验收声明。本候选已恢复 HEAD 的验证审批措辞；旧全文与 registry draft 未准入、未纳入候选。当前候选的限定验收摘要见 [README](../../../README.md#candidate-verification-scope)；README.candidate.md、manifest.json、review.md 和 validation.json 四份完整附属报告私有保留，不随本 Git 树交付。

任务：Jenn 明确要求整理一页当前状态、唯一规则入口和机器／仓库映射。
范围：基于 `JENN2046/Agents-OS@6e2f8fcf4a19c70a72a4c91a69e870746e35cae7` 的本地文档任务分支。
检出：`/home/ubuntu/Agents-OS-docs-20260913`；分支：`docs/workspace-orientation-20260913`。
风险：有界的文档与导航维护（远端规则的 G6 / Yellow）；原工作区规则下按 A2 记录维护痕迹，两种分类不等价。

## 交付内容

- [当前状态](../../../CURRENT_STATE.md)：43 行的当前概览，区分源码存在、历史验证和运行未知。
- [根规则入口](../../../AGENTS.md)：导航版本 `2026-09-13.1`，说明适用范围和替代关系；第 1–10 节保持基线原文。
- [项目职责](../../../WORKSPACE_MANIFEST.md)、[机器映射](../../../WORKSPACE_MAP.md)、[观测清单](../../inventory/machines-and-repositories.v1.json)：分别记录逻辑结构、机器路径、9 个独立子仓库及 11 个工作树、源码版本和未核实的部署信息。
- 旧根策略、目录原则、迁移表、注册表入口、安全说明与验证入口明确指向根 AGENTS；只修正文档导航、跨机器解释和已被根规则取代的迁移期验证审批说明。

## 历史保留

原 D 的历史记录称 CURRENT_STATE.previous.md 为基线状态全文的逐字副本：407,592 字节、6,976 行。该原件仍在原 D，本轮未准入、未纳入候选；以下哈希只是原记录，不是本候选对全文重新读取或脱敏验证的结果。
SHA-256：`d414dccf05f427b834158a1db5dea23420355895c51fad02ea01dbdaa47cada2`。
来源全文仍保留在原 D（`/home/ubuntu/Agents-OS-docs-20260913`），本轮未准入；此处不提供候选全文入口。
它保留历史上下文，不是当前任务、权限或部署事实；不得删除来替代整理。
旧锚点和以原根目录为基准的相对引用可在原提交版本中解析；历史副本不改写正文。
其他被编辑文档的原文仍保存在同一基线提交中。未删除旧回执、失败记录或私有记忆。

## 证据与授权范围

- Jenn 当前请求授权本次三项文档维护；未授权推送、部署、主分支修改或权限扩张。
- 本任务按根规则 G6 文档维护路径完成限定检查、修改、验证和独立审阅。
- 未调用实际 codex-router／Bounded-High-Autonomy 运行链、Memory provider、服务或领域执行器；不声称这些 gate 已通过或已接通。
- 只读取允许的文档与 Git／文件路径元数据；不读取真实配置、私有状态、原始日志或原始记忆。
- 原 `/mnt/datadisk0/apps/AGENTS_OS_Workspace` 的内容、分支、暂存区和根 Git 状态未被本任务修改。
- 独立文档检出使用远端 origin 作为只读来源；并未给原工作区根添加远端。

## 验证

仅汇总结果进入本回执，不保存扫描器的敏感路径列表或原始输出。

| 检查 | 结果 | 范围与限制 |
|---|---|---|
| 文档内容、相对链接、机器清单、规则不扩权和历史逐字保留 | PASS，119 项检查；见 [validation-summary.json](validation-summary.json) | 本次改动的限定验证，非全工作区验收 |
| `git diff --check` | PASS | 当前已跟踪文档差异无空白错误 |
| 原工作区 `ops/scripts/validate-workspace.sh` | PASS | 必需路径存在 |
| 原工作区 `ops/scripts/validate-no-secrets.sh` | FAIL，退出码 1 | 105 条风险路径匹配，可能重复；不是 105 个已确认秘密。仅路径检查，未读取内容；原环境未改动 |
| 原工作区 `ops/scripts/validate-extension-manifests.sh` | PASS | 按原脚本的目录发现范围，非全扩展运行验证 |
| 文档检出 `ops/validation/validate-workspace.sh` | FAIL，退出码 1 | 缺少 `state-private/README.md`；本任务不展开或伪造私有目录以凑齐验证 |
| 文档检出 `ops/validation/validate-no-secrets.sh` | PASS，范围有限 | 仅已展开的文档检出做路径检查，不构成历史或内容安全审查 |
| 文档检出 `ops/validation/validate-extension-manifests.sh` | 退出码 0，覆盖受限 | 稀疏检出不含扩展实现，不能据此声称扩展全部通过 |
| 文档检出 `docctl doctor`、`docctl status` | FAIL，均退出码 1 | 稀疏检出缺少多数联邦注册表输入；未进行完整联邦健康验证 |
| 服务启动、应用测试、运行／部署版本核验 | NOT RUN | 未改运行代码，本任务未执行这些操作 |

原工作区三项检查完成于 2026-09-13 03:42 UTC；文档检出检查于 03:42–03:44 UTC。
`docctl` 仅展开一个 pilot 的 1,613 条元数据，缺少大部分引用文件，不能把其失败数当成本仓库完整检出的缺陷数。
没有为了获得 PASS 而修改扫描器、放宽规则、制造占位私有文件或展开敏感目录。

## 独立审阅

[导航审阅记录](reviews/navigation-review.md)记录了根规则与入口文档的审阅范围和限制。
机器清单、回执和注册表审阅元数据已完成第二轮独立审阅，未发现可操作问题；未独立重测远端或部署。

## Git 交付

20 个文档／元数据变更已在独立任务分支精确暂存，未提交、未推送、未创建 PR。
完整暂存差异（含历史副本）通过 `git diff --cached --check`。
本地文档整理完成；远端 main 和原工作区尚未采用此版本。

## 待办与回退

- 远端分支、原工作区关联和运行部署均保持未改动状态；本任务不替代后续同步或部署核验。
- 当前源布局与远端结构的等价性未全量检查；旧 WSL／Windows 机器未访问。
- 若需要回退本次文档整理，应在任务分支上创建反向补丁或 revert 本任务提交，保留此回执与历史副本；不用 reset、clean 或覆盖原工作区。
- 根仓库对外发布的私有历史审查尚未进行；该边界不因本次文档完成而解除。

## 机器身份补充观测

2026-09-13T04:09:16.137539+00:00：DMI 显示 `Tencent Cloud / CVM`，Codex 将当前远端项目标为“腾讯云服务器”。
Codex 同时登记了 `local` 主机上的 `/home/jenn/AGENTS_OS_Workspace` 等本地项目；该证据只确认应用登记，不证明已读取其文件、分支、未提交修改或部署状态。
此次补充没有修改原工作区或权限；前述独立审阅早于此补充，不声称已覆盖它。

## 腾讯云 VCP 运行目录纠正

记录时间：2026-09-13T11:48:38.839647+00:00。Jenn 当前明确确认「VCP的真正运行目录是next那个」。
已更新 CURRENT_STATE.md、WORKSPACE_MAP.md、ops/inventory/machines-and-repositories.v1.json 和 ops/inventory/README.md，并在本回执保留纠正来源；原有检查时间和历史全文保持原样。
风险范围：A2 文档维护；依据本任务已授权的状态／映射整理及 Jenn 当前纠正，不改变权限。仅更新独立文档检出，未修改原运行目录、Git 元数据或服务。
补充只读检查：next 与 core 共享 core/.git；core 中可见 PM2 管理进程及 vcp-chatgpt-app-r0a 子目录的 Node 进程，不能据此声称 core 是第二个正式 VCP 实例。
部署版本和健康状态未验证；core 的全部用途仍待核实。未调用实际治理执行链，不声称运行 gate 已通过。既有 119 项检查和独立审阅属于此前版本；本次修订另做 JSON、路径／证据一致性、历史哈希和差异空白检查。
