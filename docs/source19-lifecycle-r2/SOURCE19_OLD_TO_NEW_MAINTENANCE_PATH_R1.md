# Source19 旧运行实例到新维护版本的可达性

任务：`SOURCE19_FIRST_STOP_LIFECYCLE_DECOUPLING_R2`。本文件仅为 G4 源码与既有公开证据分析，不是安装入口或生产许可。

## 判定

`SOURCE19_STOP_DEPLOYMENT_DECISION_REQUIRED`。

旧 Native 已加载原 UNKNOWN 时，其支持的关闭路径存在真实、可复现的拒绝；新 Native 的生命周期修复不能倒过来作为旧实例首次退出的能力。强首次 STOP 仍为 `SOURCE19_FIRST_STOP_OR_SNAPSHOT_CONTRACT_BLOCKED`，直到旧实例退出与当前执行风险分别取得准确证据。

这里不声称本轮现场 PID 一定不能自然退出：本子任务没有读取其当前内存执行集合、双机受保护账本或进程句柄。结论是现有代码不能保证本合同所需的过渡，不能凭历史安装成功推导本次可达。

## 已核基底与证据层级

本轮读取时仓库 HEAD 为 `fa5fd0ee4e183ccb5dce1f844cf4dcc3343bfad7`。任务书要求的历史负例与 fixture 未改。

| 项目 | 固定身份 |
|---|---|
| 当前控制 Release | `r16-daily-20261015-r15-app-recovery-r6` |
| 公共配置 digest | `56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec` |
| accepted19 envelope digest | `b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9` |
| App manifest/version | `34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500` |
| Native manifest/version | `2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4` |
| Bridge manifest/version | `9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352` |

上述完整固定校验位于 `execution/minimal-human-trust/authority/source-baseline.mjs:11–48`。实际公开安装源码与便携 fixture 已在上一轮逐字核对；本轮重新执行原八项负例，8/8 PASS、0 skip。该 PASS 表示反例成立，不表示首次 STOP 成功。

公开历史读回来源包括 Documents 下 `2026-10-17/SOURCE19_PROTECTED_DELIVERY21_22_EXECUTION_R2/SOURCE19_V_EXECUTION_BASELINE_R1.json`，以及 `G1D-R15-REPAIR-INSTALL-R12-R2/post-install-readback-r1/` 的安装/签配置/保留审计读回。它们属于历史观察。本轮没有重新认证云现场、accepted store、原执行者或数据库；没有使用私钥、root、SSH、服务操作。

## 第一段：旧实例如何结束

实际 Source19 公开根：`/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6`。下列源码亦由 `test/fixtures/source19-first-stop/PUBLIC_SOURCE_PINS.json` 固定，测试不依赖机器存在 `/opt`。

1. `host/workspace-dispatcher.mjs:417–426` 设置 `closing=true`，等待 control queue 和 `active`，然后对每个已加载 participant 调 `participant.stop({lease})`。旧 `src/lease-core.mjs:288–300` 保持严格业务闭合条件，遇 UNKNOWN 拒绝。即使该项目已经没有租约，dispatcher 的 `status().unresolved.length===0` 检查仍拒绝。
2. 引擎关闭、`native.cleanup()` 和 Store 关闭位于上述检查之后，拒绝时不可达。这不是将 UNKNOWN 与 LIVE 工作独立分类的 Physical Shutdown。
3. `host/headless-host.mjs:139–155` 先等待 `port.close()`，才等待 transport pending、关闭 socket、释放 Store 和运行 writer lease。port 拒绝使后续释放不执行。
4. `host/native-runner.mjs:90–98` 的 SIGTERM 路径捕获失败后只设置 `process.exitCode=1`，没有保证关闭尚存 socket/句柄；没有当前受支持的外部 RPC 可以安全跳到 `releaseStores()`。连接偶然断开或进程后来退出也不等于已排空。

复跑命令：

```sh
node --test execution/minimal-human-trust/test/source19-first-stop-contract.test.mjs
```

该测试使用真实固定 Source19 dispatcher/headless/core 和隔离持久 Store，覆盖有租约、无租约两种 UNKNOWN 拒绝，验证 UNKNOWN 保留、socket/Store/writer 释放未发生。它没有启动真实 Native 或以 fixture 生成生产 STOP。

## 现有维护机制能复用什么

`maintenance/release-r6/quiescence.py:427–447,472–531` 已有固定角色、准确 code pins、PID/start/cgroup、manager job、restart fence、单次 stop intent、graceful wait 和无盲重发检查。实际停止限定 `SendSIGKILL=no`、`KillSignal=15`；超时返回 `GRACEFUL_STOP_INCOMPLETE`，没有合法强杀后门。

`maintenance/release-r6/transaction-driver.mjs:74–79` 的顺序是 baseline → quiesce/observe → payload → signed → cloud/local commit → activate。它要求旧进程先停止，不能先运行新 shutdown 再停止旧代码。其 ABORT/ROLLBACK 为已准入同一事务的恢复，不是任意新停机权力；未知效果不重发、期限不延长。

该 generic recipe 仍固定旧 R15 → 修复 R15 的 source/target 版本；`recovery-r12/constants.py:26–28` 的历史链为 18→19/20。原 R12 已消费，不能重复 APPLY，也不能只把旧 plan 的 sourceRevision 改成 19 后继续。

现有维护 drop-in 在 `quiescence.py:117–124` 的 `/run/systemd/system/...`，blocked-start 路径也在 `/run`。它能阻挡本次 OS 自动/手工启动，却不满足 R2 的跨系统重启持久围栏。必须在新的受审维护设计中补持久保护及相应 runtime 再入检查；不能只给当前 `/run` 文件改一个“persistent”名称。

R8 `first-stop-r8/stop_driver.py:13–16`、`linux_backend.py:22–25` 和 `native_entry.py:149–161` 固定云 App、其 cgroup、代码及 `ONE_TIME_CONTROLLED_CRASH_STOP_SOURCE_APP`。旧审批和实现没有覆盖本机 Native、SQLite writer、Native 子进程或新的停止实例。不能复用旧 App 批准，也不能把已发生的 App crash-stop 当 Native 排空事实。

## 执行者与历史 UNKNOWN：能证明和不能证明的内容

原两笔身份必须继续严格固定：

| Project | Operation | Generation | Operation hash |
|---|---|---|---|
| p2vox | `c434da49-055a-43dc-a3e3-695cce137909` | 30 | `fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f` |
| pmog2 | `d0364f8b-3a68-4ca2-a396-7953b29cee4c` | 38 | `38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1` |

`migration/r17-one-time-recovery-admission.mjs:101–148` 验原 App operation、Crown proof、Native/三 participant、Owner 原 lease/activation 和原 `find_symbol`。该身份仍来自历史旧 R15，不能改成当前 Source19。该验证保留 UNKNOWN/无结果/禁重放；没有声称无活执行者。

当前公开 ProjectForge 源码把 `find_symbol` 路由到本地 `findSymbolCmd`（`native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js:2670–2686`），随后可能通过 pipe 调本地 indexer（`:790–823`，`indexerClient.js:128–135,198–209,246–248`）。不是已证明会派给远端服务的动作；不能虚构这两笔必有远程 executor。当前 runner 明确 `AST_INDEX_ENABLED:false`（`:76`），但当前配置不能倒推当年操作的执行环境。

历史安装终态、当前不同 PID、旧账 3555 文件 checkpoint `36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c` 与签名身份保全，可支持“旧记录未改”或特定已观察实例退出。现有公开材料没有将两个 requestId 的原 executor 实例、全部子进程/队列/可能外部派发与完整结束证据绑定。因此本 G4 不能宣布这两笔当前执行者已全部结束，也不要求恢复其结果。补齐绑定后才可把它们分类成不阻断物理关闭的历史 UNKNOWN。

泛用 App 的上游工具/聊天与这两笔本地 FindSymbol 应分开：`app/upstream/src/server.mjs` 和 `vcp-client.mjs` 的 fetch abort/超时不是远端完成回执。新合同必须明确观察范围，不能用 Native 当前 active 集为空替代整个 App 的上游排空。

## 第二段：新代码如何取得真实身份

新 Native 代码改变任一已签文件后必须产生新的 Native manifest digest、新 Release 及准确签名配置；若 App/Bridge 同改也须分别更新其 digest。签名与 selector 必须仍由现有受保护机制消费，保持同 Owner/Grant，不是原目录原位覆盖或旧身份热补丁。

必须先解决第一段。可离线构建新包，但其安装器 PASS 不证明正在运行的旧 Native 可交接 writer。OS 观察者不能以新进程加载旧 role key 冒充原实例 Quiescence；Quiescence 在原角色退出前签发、OS 证明在其后组合，30 秒验证窗不被延长。

当前19是实际源，历史20不可复用，21/22仅为未分配的旧 R17规划。新增维护 Release/config 或预先签 disconnect 控制都会改变后续 source 与 revision 链。实际旧 Owner `authority-worker.mjs:47–52,85–86` 的连接控制改变会产生下一 delivery；从19直接操作不能假设“无新版本”，更不能隐式占20。新计划需显式拒用20、核 accepted/全部已签/历史保留最大值，重新分配维护前进/恢复及其后 R17所需版本。当前21/22不能同时保留原含义又用于维护。

新 source 的公配置/envelope/Release/manifest digest、版本、冻结清单、物理包、G1/G5摘要都必须重算；当前 `SOURCE19_BASELINE` 的固定19验收不能通过 caller override 接受新的维护 source。

## 最小决策与停止点

| 路线 | 本次结论 |
|---|---|
| 原支持的正常 stop → 原子维护安装 | 有固定 UNKNOWN 的真实反例；当前实例安全可达性未证，不可宣布完整 PASS |
| 先安装新 shutdown 再让旧进程退出 | 循环依赖，不合法 |
| 新准确授权的有界受控中止 → 新签维护版本 | 仅可形成待审决策；不是本任务授权效果，更不是零在途或角色 STOP |
| 不接受受控中止风险 | 保持旧Source19，继续离线修复/证据研究，不安装、不扩Handoff/21/22 |

建议保留新生命周期源码工程和原八项反例，但把 G4 决策单独显式提交。若不能排除当前/远端继续执行，受控中止方案只能如实 `CONTROLLED_CRASH_STOPPED_NOT_DRAINED`，不能满足当前强首次 STOP；需要 Jenn 先决定是否接受独立维护过渡风险，不能由工程测试替她接受。

故障恢复需分三个边界：未发停止效果前只撤自己且授权覆盖的保护；stop效果不明先观察不重发；已签/已提交后只按新准确事务的有界恢复与新版本回退，绝不回写旧账、重复旧APPLY或延长旧deadline。详细未来批准边界见同目录 `NEXT_SOURCE19_STOP_NATIVE_AUTHORIZATION_BOUNDARY_R2.md`。
