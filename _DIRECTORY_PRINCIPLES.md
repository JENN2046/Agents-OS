# Directory Principles V1.1

入口修订 `2026-09-13.1`：[AGENTS.md](AGENTS.md) 是唯一根操作规则入口；
[WORKSPACE_MANIFEST.md](WORKSPACE_MANIFEST.md) 维护项目职责；
[WORKSPACE_MAP.md](WORKSPACE_MAP.md) 接替本文件的跨机器路径定位用途。
以下 WSL／Windows 路径及迁移约定保留其原环境语境，本次未重新核实；
分层、安全和私有状态约束保持有效，不因路径映射而扩权。

目录不是为了收纳文件。  
目录是为了表达边界。

本文件用于定义 AGENTS OS 在 WSL / Linux canonical dev root 下的目录原则。它不是普通文件夹命名建议，而是 Agent 权限、运行边界、私有状态、upstream 同步、审计证据和业务系统隔离的基础约束。

Canonical dev root:

```text
/home/jenn/AGENTS_OS_Workspace
```

Windows reference / archive root:

```text
A:\AGENTS_OS_Workspace
```

原则：Windows 根目录可以保留素材、附件、历史证据和旧仓库快照；AGENTS OS 的核心代码、执行器、验证、Docker、数据库、Agent runner 与 Codex workspace 默认以 WSL Linux 路径为准。

---

## 1. 先分层，再放文件

不要先问：

```text
这个文件放哪里？
```

先问：

```text
它属于哪一层？
它是否会执行？
它是否会改变 Agent 行为？
它是否包含私有状态？
它是否需要追 upstream？
它是否属于业务系统？
```

固定层级：

```text
control-plane/   控制平面规则与协议
governance/      治理、安全、授权、路由与 hard gate
execution/       执行器、worker、provider adapter、harness
runtime/         可追 upstream 的运行时核心
extensions/      Jenn 外置扩展
domains/         领域应用与业务系统
labs/            实验项目与尚未定型的探索系统
memory/          记忆系统代码、协议与测试 fixture
state-private/   私有状态、secret、运行痕迹与本地数据
ops/             验证、运维、报告、receipt、dry-run
archive/         历史归档、废弃版本、迁移快照
```

目录判断优先级：

```text
先判断边界，再判断项目名。
先判断是否可执行，再判断是否方便。
先判断是否私有，再判断是否应该进入 Git。
```

---

## 2. 推荐顶层结构

```text
/home/jenn/AGENTS_OS_Workspace
├── _ROOT_POLICY.md
├── _DIRECTORY_PRINCIPLES.md
├── _MIGRATION_MAP.md
│
├── control-plane
│   ├── contracts
│   ├── schemas
│   ├── task-envelope
│   └── policies
│
├── governance
│   ├── codex-router
│   ├── Bounded-High-Autonomy
│   └── Codex_Autonomous_Work_Harness
│
├── execution
│   ├── harness
│   ├── workers
│   ├── providers
│   └── bridges
│
├── runtime
│   ├── VCPToolBox
│   └── ColaMeta
│
├── extensions
│   └── vcp-toolbox-jenn
│
├── domains
│   └── Photo_Studio_OS
│
├── labs
│   └── agent-image-lab
│
├── memory
│   └── codex-memory
│
├── state-private
│   ├── AGENTS.override.md
│   ├── MEMORY.md
│   ├── .agent_board
│   ├── audit-ledger
│   ├── runtime-cache
│   ├── data
│   ├── secrets
│   └── scratch
│
├── ops
│   ├── validation
│   ├── reports
│   ├── receipts
│   ├── dry-runs
│   └── maintenance
│
└── archive
    ├── superseded
    ├── deprecated
    └── windows-migration
```

每个一级目录必须有 `README.md`，说明：

```text
purpose        这个目录的用途
allowed        可以放什么
denied         不可以放什么
read policy    Agent 是否默认可读
write policy   Agent 是否默认可写
sensitive      是否可能包含敏感数据
```

---

## 3. `control-plane/`：控制平面

`control-plane/` 用于定义 AGENTS OS 的规则、协议、schema、任务信封和全局 contract。

它回答的问题是：

```text
任务如何被描述？
权限如何被声明？
边界如何被验证？
receipt 如何形成？
哪些字段是稳定协议？
```

允许：

```text
contracts/
schemas/
task-envelope/
policies/
protocol notes
validation contracts
```

禁止：

```text
真实运行缓存
secret
provider token
业务数据
临时输出
node_modules
.venv
```

说明：原先的 `AGENTS_OS/` 容易和整个 workspace 名称混淆，因此控制平面统一命名为 `control-plane/`。

---

## 4. `governance/`：治理与安全

`governance/` 决定“能不能做、以什么边界做”。

典型项目：

```text
codex-router
Bounded-High-Autonomy
Codex_Autonomous_Work_Harness
```

允许：

```text
policy engine
permission model
provider selection policy
hard gate
permit / authorization logic
read-only preflight
validation matrix
```

禁止：

```text
绕过 gate 的执行脚本
业务系统代码
runtime cache
secret
直接生产写入入口
```

治理层必须先于执行层生效。任何真实 side effect 发生之前，必须已经完成 policy preflight、BHA boundary check 与 approval / permit 校验。

---

## 5. `execution/`：执行器与 harness

`execution/` 负责“在允许边界内怎么做”。

允许：

```text
execution harness
workers
provider adapters
bridge runners
sandbox launcher
process capture wrapper
```

禁止：

```text
最高治理规则
长期私有状态
业务数据
secret
未授权真实生产入口
```

推荐执行链路：

```text
TaskEnvelope
↓
Policy Preflight
↓
codex-router Plan / Provider Selection
↓
Bounded-High-Autonomy Boundary Check
↓
Approval Gate / Permit
↓
Execution Harness
↓
Runtime / Extension / Domain Bridge
↓
Audit Event + Receipt
```

关键规则：

```text
Plan 可以早于 Permit。
真实执行必须晚于 Permit。
Audit Event 必须覆盖每一次真实 side effect。
Receipt 必须能回溯 TaskEnvelope、Permit、执行范围和结果。
```

---

## 6. `runtime/`：可追 upstream 的运行时核心

`runtime/` 只放可追 upstream、可与外部项目保持同步的运行时核心。

典型项目：

```text
VCPToolBox
ColaMeta
```

判断标准：

```text
能追 upstream 的，放 runtime/。
属于 Jenn 自定义能力的，不放 runtime/，放 extensions/。
属于私有状态的，不放 runtime/，放 state-private/。
```

`VCPToolBox` 是 core。Jenn 自定义能力是 extension。

Core 越干净，追 upstream 越轻。

禁止把下面内容放进 core runtime：

```text
Jenn 私有 prompt
Jenn 私有状态
provider token
本地数据库
业务数据
运行缓存
长期审计账本
不可 upstream 的私有 patch
```

---

## 7. `extensions/`：Jenn 外置扩展

`extensions/` 放 Jenn 自定义能力、外置插件、业务增强和不应污染 upstream core 的能力。

典型项目：

```text
vcp-toolbox-jenn
```

每个扩展必须有身份证：

```text
jenn-extension.manifest.json
README.AGENTS_OS.md
SECURITY.md
CONTRACT.md
```

没有 manifest，不自动加载。

manifest 至少声明：

```text
id
name
owner
version
entrypoints
compatible_core_versions
read_roots
write_roots
network_policy
side_effects
audit_events
default_enabled
```

默认策略：

```text
Extension default_enabled = false。
Extension 必须被显式 allowlist 后才能加载。
Extension 不得直接读取 state-private/，除非 task permit 明确授权。
Extension 不得直接 import core 内部不稳定路径，必须通过 bridge / contract 连接。
```

---

## 8. `domains/`：领域应用

`domains/` 放真实业务系统。

典型项目：

```text
Photo_Studio_OS
```

领域系统回答的问题是：

```text
AGENTS OS 正在服务哪个现实业务？
这个业务的对象、流程、交付、验收是什么？
```

规则：

```text
业务系统不要被 VCPToolBox 吞掉。
VCPToolBox 通过 Bridge 连接业务系统，不复制业务系统。
Domain systems connect to runtime through bridge contracts, not direct internal imports.
```

`Photo_Studio_OS` 与成熟后的视觉系统属于领域系统。  
如果项目仍处于实验状态，先放 `labs/`，成熟后再提升到 `domains/`。

---

## 9. `labs/`：实验项目

`labs/` 放尚未定型、仍在探索的系统。

典型项目：

```text
agent-image-lab
experiments
```

规则：

```text
可以试错。
可以快速重构。
不默认进入生产路径。
不默认被 runtime 自动加载。
成熟后通过 review 升级到 domains/、runtime/ 或 extensions/。
```

`labs/` 的价值是隔离探索风险。它不能反向污染 governance、runtime 或 domains。

---

## 10. `memory/`：记忆系统代码

`memory/` 放记忆系统的代码、协议、fixture 与测试工具。

典型项目：

```text
codex-memory
agent-memory-fixtures
```

注意：

```text
memory/ 放记忆系统代码。
state-private/ 放真实私有记忆和本地状态。
```

不要把真实个人记忆、secret、长期私有上下文提交到 `memory/` 里的 Git 仓库。

---

## 11. `state-private/`：私有状态

私有状态不和代码混住。

以下内容必须放入 `state-private/`：

```text
MEMORY.md
AGENTS.override.md
.agent_board/
data/photo-studio/
audit-ledger/
runtime-cache/
secrets/
local-db/
provider-auth/
scratch/
```

默认规则：

```text
state-private/ is denied by default.
Agents may only read or write it with explicit task authorization.
```

`state-private/` 默认不进入 Git。建议放置 `.gitignore`：

```gitignore
*
!.gitignore
!README.md
```

禁止：

```text
普通任务自动扫描 state-private/
把 secrets 复制进代码仓库
把 provider token 写入 runtime/
把本地 DB 当作 fixture 提交
把 .agent_board 当作普通文档随意修改
```

---

## 12. `ops/`：验证、运维与证据输出

`ops/` 放验证脚本、报告、receipt、dry-run、maintenance 工具和运维记录。

允许：

```text
validation/
reports/
receipts/
dry-runs/
maintenance/
preflight checks
migration reports
```

规则：

```text
ops/ 可以生成证据。
ops/ 不拥有业务代码。
ops/ 不保存 secret。
ops/ 的 report 必须能回溯来源、时间、任务和执行边界。
```

如果是长期审计账本，并且可能含私有状态，应放：

```text
state-private/audit-ledger/
```

如果是可共享的验收报告，可放：

```text
ops/reports/
ops/receipts/
```

---

## 13. `archive/`：归档

归档不删除。

使用：

```text
archive/
archive/superseded/
archive/deprecated/
archive/windows-migration/
```

每个归档目录都要有 README，说明：

```text
为何归档
由谁取代
是否可删除
是否含敏感数据
是否允许 Agent 默认读取
```

默认规则：

```text
archive/, superseded/, deprecated/ are read-only reference roots by default.
They must not be used as execution roots.
```

禁止在归档目录中执行：

```text
npm install
pnpm install
pip install
git commit
git push
docker compose up
production deploy
```

归档是历史证据，不是当前工作区。

---

## 14. 命名稳定

推荐：

```text
kebab-case
clear nouns
stable names
short but explicit names
```

避免：

```text
misc
stuff
temp
new
final-final
backup2
old-new
copy-copy
```

命名规则：

```text
一级目录使用 kebab-case 或稳定英文名。
仓库目录尽量保持 repo 原名，除非迁移映射明确记录。
私有状态目录统一放 state-private/。
历史目录统一放 archive/。
本地根策略文件使用 _ 前缀。
```

---

## 15. 迁移映射必须显式记录

从 Windows 迁移到 WSL 时，必须维护：

```text
_MIGRATION_MAP.md
```

最低字段：

```text
old_windows_path
new_wsl_path
repo_remote
branch
migration_status
last_verified_at
notes
```

示例：

```markdown
| old_windows_path | new_wsl_path | status |
|---|---|---|
| A:\AGENTS_OS_Workspace\runtime\VCPToolBox | /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox | pending |
| A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-Extensions | /home/jenn/AGENTS_OS_Workspace/extensions/vcp-toolbox-jenn | pending |
| A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS_Control | /home/jenn/AGENTS_OS_Workspace/domains/Photo_Studio_OS | pending |
```

迁移规则：

```text
有远端的仓库优先重新 clone。
不要整体复制 node_modules、.venv、dist、build、cache、logs。
不要盲目复制 secrets、tokens、LocalState。
Windows 旧目录在 WSL 验证完成前保留为 read-only reference。
```

---

## 16. 一句话规则

能追 upstream 的，放 `runtime/`。  
属于 Jenn 的外置能力，放 `extensions/`。  
属于治理、安全、授权、路由、hard gate 的，放 `governance/`。  
会真实执行任务的，放 `execution/`。  
属于业务系统的，放 `domains/`。  
还没定型的探索项目，放 `labs/`。  
属于记忆系统代码的，放 `memory/`。  
属于记忆、状态、secret、运行痕迹的，放 `state-private/`。  
用于检查、报告、receipt、dry-run 的，放 `ops/`。  
用于定义规则、协议和 schema 的，放 `control-plane/`。  
过期但不能删除的，放 `archive/`。

---

## 17. 最小 hard rules

```text
1. Core must remain upstream-trackable.
2. Jenn custom capability must live outside core unless explicitly upstreamed.
3. Private state must never live inside source repositories by default.
4. No manifest, no extension auto-load.
5. No permit, no real side effect.
6. No direct domain ingestion by VCPToolBox; use bridge contracts.
7. Archive is read-only reference by default.
8. state-private is denied by default.
9. Every top-level directory must explain its read/write policy.
10. The canonical execution root is the WSL Linux path, not the Windows archive path.
```
