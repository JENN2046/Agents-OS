# AGENTS OS 项目结构清单

版本：`2026-09-13.1` · Owner：Jenn · 状态：项目职责索引。
规则唯一入口：[AGENTS.md](AGENTS.md)。当前状态：[CURRENT_STATE.md](CURRENT_STATE.md)。
机器路径、仓库分支和部署信息独立维护在 [WORKSPACE_MAP.md](WORKSPACE_MAP.md)；本清单不把某一台机器的绝对路径定义成全项目根目录。

## 逻辑结构

| 项目相对路径 | 职责 | 边界 |
|---|---|---|
| `control-plane/` | 协议、合约、模式、验证器、策略、注册表、任务信封 | 定义与治理；登记不等于授权执行 |
| `governance/` | 安全、授权和自动化规则 | 从根 AGENTS 进入，再遵守具体边界 |
| `execution/` | Harness、worker、adapter、bridge、受控工作台 | 组件能力与运行资格分别验证 |
| `runtime/` | 可跟踪上游的运行时核心 | 不混入 Jenn 业务或私有状态 |
| `extensions/` | Jenn 外置能力 | 清单、加载与权限必须分别明确 |
| `domains/` | 业务领域系统 | 独立仓库和业务边界 |
| `labs/` | 草案、实验和工作综合材料 | 不自动成为有效规则或运行组件 |
| `memory/` | 记忆系统代码、协议与测试 | 不存放真实私有记忆 |
| `ops/` | 验证、观测清单、报告、回执和维护 | 证据不构成能力授权 |
| `archive/` | 已替代材料与历史参考 | 默认只读，不作为执行根 |
| `state-private/` | 私有记忆、配置、数据和状态 | 默认禁止读取，不纳入本次整理 |

外部运行时和领域源码可在独立仓库中维护。根仓库只有目录说明时，不推断组件缺失或已安装。
当前机器上的 `AGENTS_OS/`、`interfaces/` 等旧布局保留原状；别名与差异见机器映射，未自动迁移。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)：现行操作规则和适用范围。
2. [CURRENT_STATE.md](CURRENT_STATE.md)：当前可确认事实和未完成事项。
3. 本清单及 [WORKSPACE_MAP.md](WORKSPACE_MAP.md)：项目职责与机器事实。
4. 目标目录的本地规则、组件 README 和具体任务边界。

## Runtime Note

`runtime/VCPToolBox` is a private local runtime body under separate boundary
review. Do not treat it as ready for provider/plugin/autonomous use without the
current VCPToolBox first-use posture checks.

## 历史与外发边界

此版本替代[旧清单](https://github.com/JENN2046/Agents-OS/blob/6e2f8fcf4a19c70a72a4c91a69e870746e35cae7/WORKSPACE_MANIFEST.md)的通用路径定位说明；旧 WSL 和 Windows 路径在机器映射中保留为文档证据。
根仓库仍按既有 private-local 历史边界处理：对外推送、镜像、发布或 PR 需要满足根规则和 Jenn 当前授权；本次整理没有完成私有历史审查，也没有对外发布。
