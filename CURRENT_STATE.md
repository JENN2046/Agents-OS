# AGENTS OS 当前状态

候选说明：保留原云端草稿的观测来源与时间；本批次没有重新核实机器运行状态。

版本：`2026-09-13.1` · 状态：源码／文档概览；Jenn 已确认腾讯云 VCP 运行目录为 next，部署版本和健康状态未核实。
项目基线：`JENN2046/Agents-OS@6e2f8fcf4a19`（2026-09-05）；本机 Git 检查：2026-09-13 03:32 UTC。
规则入口：[AGENTS.md](AGENTS.md) · 项目职责：[WORKSPACE_MANIFEST.md](WORKSPACE_MANIFEST.md) · 机器／仓库：[WORKSPACE_MAP.md](WORKSPACE_MAP.md)。

## 当前组件与位置

“有效”表示当前规则入口、仓库中存在的实现或本机已观测源码；不表示服务已运行。
`L` = `/mnt/datadisk0/apps/AGENTS_OS_Workspace`；`R` = Agents-OS 远端基线的仓库相对路径。

| 组件 | 已确认的源码／文档位置 | 当前证据与待办 |
|---|---|---|
| 根控制平面 | R:`control-plane/`；L:`AGENTS_OS/` | 布局不同；L 根 `.git` 为空，尚未关联目标远端 |
| 控制链、工作台、仪表盘 | R:`execution/agents-os-*` | 仓库存在实现；机器上的实际运行位置未核实 |
| App Server active loop | R:`execution/codex-appserver-active-loop/` | 仓库存在实现；本次未运行或启动 |
| resident 扩展 | R:`extensions/agents-os-resident/` | 有 2026-08-24 历史修复报告；本次未重新验证部署 |
| VCPToolBox | L:`runtime/VCPToolBox-upstream-core`、`runtime/VCPToolBox-upstream-next` | Jenn 确认 next 为正式运行目录；两者均有改动，next 依赖 core/.git，origin 为 lioensky 上游 |
| Jenn 扩展 | L:`extensions/Jenn-VCP-Extensions` | 有未提交改动、未配置远端；不等于已注册／已加载 |
| 治理与执行 | L:`governance/codex-router`、`execution/runners/colameta`、`execution/Codex_Autonomous_Work_Harness` | 源码存在；边界链是否实际接通未验证 |
| Photo Studio／image lab | L:`domains/Photo_Studio_OS_{Backend,Control,Frontend}`、`domains/agent-image-lab` | 四个独立仓库，工作区干净；前序实时查询显示与远端提交不同 |

VCP 正式运行路径由 Jenn 确认为 L:`runtime/VCPToolBox-upstream-next`（2026-09-13）；部署版本、健康状态及其他组件运行路径仍未核实。完整源码版本与机器证据见[机器清单](ops/inventory/machines-and-repositories.v1.json)。
已确认 L 位于腾讯云 CVM；Codex 登记了本机 `/home/jenn/AGENTS_OS_Workspace` 项目，但其文件／Git 状态未实读；Windows 参考路径也未核实。

## 验证时间与范围

- 2026-09-13：核对远端基线、根 Git 元数据、11 个子工作树的路径／分支／提交／改动和远端名称。
- 原 D 的历史文档验证见[旧整理回执](ops/reports/workspace-orientation-20260913/README.md)；本候选限定检查见 [README 验收摘要](README.md#candidate-verification-scope)，完整报告私有保留。全系统、服务和部署验证未执行。
- 2026-08-24：[resident 修复报告](ops/reports/mmr0-git-source-integration-remediation-2026-08-24/README.md)记录当时的验证结果，只作历史证据。

## 未完成事项

1. 先比较 L 根目录与远端的文件来源和有效性，再恢复根 Git 关联；不覆盖本地工作区。
2. 保护正在运行的 VCP next；核实 core 的辅助用途和共享 Git 依赖，逐项保全两者改动后再安排集成。
3. 对工作区干净但远端提交不同的仓库补齐历史，判断落后、分叉或修复已被合入。
4. 核实 Jenn 扩展的目标远端与提交范围；重新核实旧 WSL 机器上的组件位置。
5. 在相应任务授权下核实运行工件、部署版本和健康状态；源码观测不能替代这些证据。

## 历史与维护

历史全文仍保留在原 D（`/home/ubuntu/Agents-OS-docs-20260913`）；本轮未准入，未读、未复制到本候选。候选不包含完整历史副本。
历史授权、关闭状态和 PASS 不自动成为本轮授权或验证。本页只保留当前摘要，目标不超过 60 行；后续过程记录链接到对应回执。
