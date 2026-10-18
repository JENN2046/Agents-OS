# Source19 下一次真实维护授权边界

这是 `SOURCE19_FIRST_STOP_LIFECYCLE_DECOUPLING_R2` 的决策材料，非可签批准对象、安装入口或现场授权。生产效果为0。

## 当前状态

`SOURCE19_STOP_DEPLOYMENT_DECISION_REQUIRED`。当前运行源为签名配置19及修复 R15 Release，原两笔 UNKNOWN 保持。尚未证明当前旧 Native 能在所需合同下正常退出、也没有完整的原操作执行者终止绑定。旧 Source19 有真实关闭反例；新实现即使隔离测试通过，也不能证明旧进程的第一步退出。

本轮任务仅 SOURCE / ISOLATED；未批准停止、freeze、signal、改围栏、签配置、使用私钥、安装、selector、Owner交接或UNKNOWN处理。没有新的实际 nonce、acceptedAt 或授权窗口。用户无需现在输入任何执行确认。

## 需要 Jenn 决定的最小问题

若无法通过旧代码本身和独立证据建立正常关闭，是否接受一次**另行准确限定的 Native 受控中止维护过渡**？

影响：Native 及其依赖通路会中断；任何尚未完成的执行可能被截断，远端已派发工作不能仅靠本机退出证明停止。风险包括未确认效果、SQLite/WAL恢复、残留运行写锁与重启竞态。原两 UNKNOWN 结果仍未知，不改成 KNOWN/CLOSED，不重放。

建议：先完成可审查的 Native 专用固定目标、完整写者/执行者证据与恢复演练，再由 Jenn 判断准确风险对象。不能直接移用 R8 云 App 旧审批/代码或以“时间久远”免除排空证据。若不接受该风险，保持旧Source19运行，不安装维护版，不推进首次 Handoff 或21/22。

## 未来准确对象必须包含的内容

1. **真实来源与目标。** Fresh accepted19 envelope、公配置、同一Grant/Owner、三manifest与实际加载代码；固定机器、unit、PID/start/boot/invocation/cgroup及全部成员，不以调用者任意路径指定。新Native/App/Bridge字节及新Release/manifest必须另行冻结。
2. **明确效果。** 正常停止与受控中止分别标注。后者若被选择，须明示准确signal及一次性effect、是否允许相关本地indexer子进程结束、当前执行风险仍未证明的范围。不得写“已drained”，也不得用新进程代签旧角色Quiescence。
3. **完整保护范围。** 本机Native、独立`r16-native-link.service` relay及其SSH成员；云端是真正`r16-bridge.service`，不是本机6016 relay。Owner自动reconcile、登录启动器、pending systemd jobs、SQLite/WAL/SHM及`.r16-writer.lock`、注册ProtectedStores、同UID/其他已准写者均须纳入。无foreignwriter不是只有4个主PID为0。
4. **持久围栏。** 目前普通维护drop-in在`/run`，不可宣称重启持久。未来准入需绑定新的、真实跨重启的准确保护位置/字节/epoch及runtime重新准入拒绝；解除只限该新有效权威覆盖的转换。Heartbeat/reconnect/启动不得清除。
5. **完整保全与分类。** 根注册目录/inode和全部文件集合、字节/模式、原2 operation hash/gen/action/lease/签名、无新增UNKNOWN或INFLIGHT；合法生命周期新增只追加准确审计，不回滚业务账。旧checkpoint仅为历史比较输入，不是fresh执行排空。
6. **原执行者结束证据。** 两个requestId与原Native实例/子进程及派发范围绑定；本地FindSymbol源码路径可以缩小调查范围，不能替代真实实例与退出证据。没有证据的外部继续执行风险必须保留，不能由年龄、稳定hash或本机无PID推断已完成。
7. **新签名版本链。** 19是本次源；20历史保留不可用。21/22未分配且旧规划不是授权。若新增维护或disconnect delivery，必须先重规划维护前进/恢复和后续R17版本，重新生成所有包/manifest/G1/G5/hash，不能偷用旧21/22含义或给旧19代码贴新身份。
8. **时限与单次恢复。** 新nonce、准确目标hash、本人实际原生确认后开始的新短窗；原计划、历史期限原样保留，不继承R8/R12/旧21/22权力。意图持久后effect不明只观察、不重复signal/start/install；过期保留准确partial，不能静默续期。

## 失败与恢复要在批准前说清楚

| 边界 | 允许的恢复含义 |
|---|---|
| 原PID仍活、停止effect未消耗 | 在准确授权覆盖下只撤自身保护，证明相同实例/代码仍在；不能伪造完成 |
| freeze/stop/signal结果未知 | 保留owned保护和审计，重新读真实OS身份；不重发未知效果，不擅自解围栏 |
| 旧进程已经退出、未提交新配置 | 原代码/selector/key仍保留，原core按其合法恢复处理死PID锁；不得手工删不明`.next/.reclaim`、恢复旧账或声称原操作成功 |
| 新配置已经签发/部分提交 | 单调转恢复，仅使用新事务准确批准的更高配置修订与真实双机读回；不能回FORWARD或重跑旧APPLY |
| 回退旧Native代码 | 回退代码不会修复其UNKNOWN关闭缺陷；启动必须是另外明确覆盖的恢复效果，并先确认无替代writer和原数据可恢复 |

恢复成功也只描述实际OS、代码、配置和账本身份；业务验收、LEASE_RETIRED与未知结果仍是独立结论。不能保证“回滚自动恢复App运行”：必须按新事务真实原baseline逐角色恢复，若App基线停机则保持停机，若本轮基线运行则另核恢复范围。

## 强首次 STOP 的后续门

若新维护版本实际合法运行后具备新 Physical Shutdown，仍须分别满足：关闭准入且持久防重入 → 当前LIVE工作确已排空 → 原角色在凭据/Store仍可用时签同epoch Quiescence → 关闭资源/退出 → 独立OS组合证明。30秒签名窗口必须覆盖实际退出和验证；超期保留证据并拒绝，不续旧签名。原2历史UNKNOWN只有在执行者终止已证明时，才可不因结果未知阻断物理退出。

当前可继续的是隔离源码、故障注入、版本计划和独立审查。不可产出可执行安装入口，不可将本文件当批准，不可扩大Handoff/生产21/22 backend。
