# Source19 生命周期修复：本轮工程范围

任务 `SOURCE19_FIRST_STOP_LIFECYCLE_DECOUPLING_R2`，SOURCE / ISOLATED ONLY。

结果门为 `SOURCE19_STOP_DEPLOYMENT_DECISION_REQUIRED`，强首次 STOP 保持
`SOURCE19_FIRST_STOP_OR_SNAPSHOT_CONTRACT_BLOCKED`。本轮不宣称完整工程 PASS，
也不把局部资源关闭升级成 `PHYSICAL_SHUTDOWN_PASS`。

## 实际源码

- dispatcher 新增显式内部 `shutdownLocalResources`，封闭队列及外层异步入口，
  持久写入同一原 Store 的 restrictive marker；严格核原两个历史 read 的完整
  App 签名 operation、原 lease hash、Issuer 签名与旧版本。原 participant 字节、
  业务 stop/closeLease/结算/归档语义保留。
- ProjectForge 实际后端跟踪异步调用及写者，先确认本实例/受控 indexer 关闭，
  再关闭 SQLite，最后释放 DB writer。显式路径与默认严格关闭共享截止条件，
  防止异步等待超时后继续释放 writer。失败保持可观察状态，不静默吞掉 close 错误。
- indexer 在 spawn 时即跟踪子进程，区分启动未握手、RPC waiter、超时后仍未确认的
  执行和真正 close。局部静默不以 kill 当 drained。
- headless 显式局部方法关闭 transport、Store、运行 writer；默认 stop 和 runner
  SIGTERM 继续使用原严格业务路径。runner 在 Native DB/engine 初始化前拒绝
  已有持久 runtime stop marker。没有自动解除入口。
- 封包器与独立验包器均纳入 tracked `native/`，防止新后端修复在封包时被旧基底
  静默替换。新增回归覆盖真实 overlay、role manifest 与 exact HEAD 字节。

## 输出边界

局部资源观察明确为 `LOCAL_ONLY` / `globalExecution: UNPROVEN` /
`firstStopProof: NOT_PROVEN`，没有为历史请求虚构外部执行者完成证据。
测试使用一次性临时 Store、SQLite、实际候选后端和真实本地子进程；测试生成的密钥
只属于临时隔离 fixture，不进入生产包、身份登记或真实签发。

本轮没有构造未经完整合同验证的 Quiescence signer、独立 root OS STOP 服务或
通用授权接口。G2 同 epoch/30 秒组合证明未实现，G3 OS 跨重启保护与准确授权解除
未安装/未验收；本轮 runtime marker 测试不能替代它们。

G4 已保留原八项反例，确认旧版本存在支持路径无法完整关闭的场景。
不能让未安装的新方法结束旧实例；旧角色退出与新签名身份的维护过渡需先解决。
详见 `SOURCE19_OLD_TO_NEW_MAINTENANCE_PATH_R1.md` 及准确边界文档。

## 交付与后续

本轮重建 Source19 基底上的未签名 R17 候选、全部角色版本与 G1 审阅内容目录，
其所有可执行/授权标志均为 false。它不是已批准的 Native 维护发行。
旧20不可复用，21/22仍是未分配规划；若新增维护配置，必须从 fresh accepted/已签/
保留版本重新规划，不同时占用旧含义。旧包保持历史，旧摘要不适用于新字节。

完整回归、独立审查、实际物理包/档案验证和 exact HEAD CI 的准确结果记录于本次
Documents 交付目录的 `SOURCE19_STOP_DELIVERY_RECEIPT_R2.json`。无真实生产效果。
