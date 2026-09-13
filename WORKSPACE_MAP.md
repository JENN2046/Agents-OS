# 工作区、机器与仓库映射

版本：`2026-09-13.1`。这是可复核的观测清单，不是权限、自动迁移或部署配置。
项目职责见 [WORKSPACE_MANIFEST.md](WORKSPACE_MANIFEST.md)，操作规则从 [AGENTS.md](AGENTS.md) 进入。
机器和仓库数据以 [机器清单](ops/inventory/machines-and-repositories.v1.json) 为准；本页提供解释与阅读入口。

## 机器与工作区

以下 ID 是文档内的逻辑标签。`linux-observed` 已确认是腾讯云 CVM；Codex 将 `/home/jenn/AGENTS_OS_Workspace` 登记在 `local` 主机。应用登记不能替代本机文件或部署检查，WSL 平台本身仍未重新核实。

| 工作区 ID | 根路径 | 证据等级 | 根仓库状态 |
|---|---|---|---|
| `linux-observed` | `/mnt/datadisk0/apps/AGENTS_OS_Workspace` | 2026-09-13 直接检查文件路径和 Git 元数据；确认腾讯云 CVM | `.git` 为空；Jenn 指定对应 `JENN2046/Agents-OS`，关联尚未恢复 |
| `wsl-documented` | `/home/jenn/AGENTS_OS_Workspace` | Codex 已登记本机项目；文件／Git 状态未实读 | 分支、提交和运行状态均未重新核实 |
| `windows-reference` | `A:\AGENTS_OS_Workspace` | 旧迁移文档记载，本次未访问 | 历史参考／资产路径；不是已确认运行目录 |
| `docs-review` | `/home/ubuntu/Agents-OS-docs-20260913` | 本任务新建的独立稀疏检出 | `docs/workspace-orientation-20260913`；基于远端 `6e2f8fcf4a19`，仅供文档审阅 |

`docs-review` 位于当前腾讯云环境，不在用户本地主机上。它的基线提交是编辑前的来源，不是本次改动提交，也不是部署版本。
该检出故意只展开指定的安全文档与验证文件；未展开的路径不等于远端不存在。

## 项目结构与机器上的目录别名

| 项目职责 | Agents-OS 仓库中的逻辑位置 | `linux-observed` 上的观测 |
|---|---|---|
| 控制平面 | `control-plane/` | 使用旧布局 `AGENTS_OS/`；内容未做全量等价验证 |
| 运行时核心 | `runtime/` | 有两个 VCPToolBox 工作树；传统 `runtime/VCPToolBox` 路径不存在 |
| 治理 | `governance/` | 有 `codex-router`；未发现预期路径下的 `Bounded-High-Autonomy` |
| 执行 | `execution/` | 有 Harness、colameta；另一个 colameta 工作树位于 `runtime/worktrees/` |
| 扩展 | `extensions/` | 有 `Jenn-VCP-Extensions`，无远端配置 |
| 领域与实验 | `domains/`、`labs/` | Photo Studio 为三个仓库；`agent-image-lab` 当前位于 `domains/` |
| 界面 | 由项目组件职责确定，不自动新增顶层目录 | 本机存在 `interfaces/`；未发现预期 `interfaces/VCPChat` 路径 |
| 私有状态 | `state-private/` | 不读取内容、不纳入本清单的组件或部署扫描 |

这些差异是映射事实，不是移动、删除、覆盖或重新注册组件的指令。

## 仓库与工作树

完整提交、跟踪分支、改动数量和观测时间见机器清单的 `checkouts`。
VCPToolBox 与 Jenn 扩展有未提交改动；其余列出的工作树干净。colameta 的 `main` 跟踪 `upstream/main`。

| 本机目录（相对 `linux-observed` 根） | 分支／源码 HEAD | 实际远端 |
|---|---|---|
| `runtime/VCPToolBox-upstream-core` | `codex/phase1-clean-core-plugin-contract` / `6f6cf84d0ecf` | origin = lioensky/VCPToolBox |
| `runtime/VCPToolBox-upstream-next` | `update/merge-20260905-r1` / `1dbbd29edf05` | origin = lioensky/VCPToolBox |
| `extensions/Jenn-VCP-Extensions` | `codex/r0a-authority-baseline` / `7fcc5d93e2f8` | 未配置 |
| `execution/runners/colameta` | `main` / `b516c0ae6f5b` | origin = JENN2046/colameta；upstream = riccilnl/colameta |
| `runtime/worktrees/colameta-self-e0` | `evolution/e0-baseline` / `9c92f05d90c9` | origin = JENN2046/colameta；upstream = riccilnl/colameta |
| `execution/Codex_Autonomous_Work_Harness` | `master` / `1c496afb2e04` | origin = JENN2046/Codex_Autonomous_Work_Harness |
| `governance/codex-router` | `fix/p1-controlled-output-safety` / `ddde28ca5238` | origin = JENN2046/codex-router |
| `domains/Photo_Studio_OS_Backend` | `main` / `1a86dca49108` | origin = JENN2046/Photo_Studio_OS_Backend |
| `domains/Photo_Studio_OS_Control` | `main` / `2391a4a4282b` | origin = JENN2046/Photo_Studio_OS_Control |
| `domains/Photo_Studio_OS_Frontend` | `main` / `3c3d7b4a03ca` | origin = JENN2046/Photo_Studio_OS_Frontend |
| `domains/agent-image-lab` | `master` / `6d8bba680349` | origin = JENN2046/agent-image-lab |

共 9 个有效独立子仓库、11 个工作树；不包括无有效 Git 元数据的原工作区根和本任务文档检出。

## 运行与部署版本

2026-09-13 Jenn 明确确认：腾讯云 VCP 的正式运行目录为 `/mnt/datadisk0/apps/AGENTS_OS_Workspace/runtime/VCPToolBox-upstream-next`。清单将此记录为用户确认的运行路径；部署版本、健康状态和 `verified_at` 仍未知，不把用户确认的目录等同于完整服务验证。

补充只读进程元数据检查发现：next 下有 Node、Codex 和 DailyNoteSearcher 等进程；core 下有 PM2 管理进程，以及位于 `vcp-chatgpt-app-r0a` 子目录的 Node 进程。进程 cwd 不能单独证明某目录是正式 VCP 实例。

**next 的共享 Git 元数据位于 core/.git。** core 的全部用途及其他运行依赖仍待核对，不能因 next 是正式运行目录就直接搬走或归档 core。未读取进程参数、环境变量、原始日志或运行配置。

其他组件的 `deployment.runtime_path`、全部组件的 `deployment.version` 和 `deployment.verified_at` 仍为 `null`。未知不表示未部署、已停机或已通过验证。

以后确认部署时，单独填写运行路径、实际工件版本或摘要、验证时间和脱敏证据引用。
有未提交改动时，Git HEAD 尤其不能作为整个工作目录的版本；工作区干净也不证明运行工件与 HEAD 一致。

## 更新与替代关系

- 本页和机器清单接替 `_ROOT_POLICY.md`、`_MIGRATION_MAP.md` 及旧注册表绝对路径字段的跨机器定位用途。
- 旧规则中的安全约束保持有效；路径映射不继承另一台机器的权限、批准或运行资格。
- 修改机器清单时同时更新本页和 [CURRENT_STATE.md](CURRENT_STATE.md)，每次重新观测使用新的时间。
- 历史记录只追加或归档；没有新的证据时保留 `unverified`，不沿用历史 PASS 作为当前结果。
