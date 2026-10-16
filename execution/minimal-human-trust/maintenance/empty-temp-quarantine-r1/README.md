# 单个空临时文件的受保护隔离

Jenn 已批准 SHA-256 `1ee6217b557dbce981211929201864bfbdde0b278e84b4081937354b09300a9c` 所指规则例外的实现与独立验证。聊天批准不构成原生执行批准。固定源依赖为 R8-R2 胶囊 `cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41`，该源码保持逐字节不变。

入口只处理提案中准确的一个 0 字节 `.next` inode。采用 TRUSTED_HOST_ADMIN；没有新 Owner、Crown 或人类身份登记系统。代码与操作状态分别使用 `/usr/lib/r16-maintenance/empty-temp-quarantine-r1` 与 `/var/lib/r16-maintenance/empty-temp-quarantine-r1`，不复用停机批准或停机 journal。

`preflight` 验封后在内存完整读取登记树和这一空文件，核对原进程、文件身份及所有进程对该 inode 的 FD/mapping；不安装辅助源码、mkdir、取写锁、创建批准、冻结或搬移。输出明确标为完整清单通过，不能声称含临时文件的现场已经通过 R8 完整账本验收。

`execute` 必须从真实前台终端认证管理员并核对准确 `QUARANTINE` 对象。确认后创建独占 root journal 和本次 owned 重启保护，冻结同一原 PID 的 singleton cgroup，重新完整读取文件清单，再持久化一次搬移 intent。仅 `renameat2(RENAME_NOREPLACE)` 同文件系统搬移原 inode 到 root 700 隔离目录；不替换、不复制成新 inode、不删除原物。普通 state、所有归档、锁、`.reclaim`、两笔 UNKNOWN 与租约不改字节或模式。

搬移后调用未修改的 R8 `LedgerCheckpoint.capture`，真实完整验签原登记、原两笔 UNKNOWN 及全部项目，再核普通文件全清单、字节与身份未变，最后撤自己的冻结与重启保护。原 PID 继续运行；可能仍存在内存 ProtectedStore poisoned 状态，因此不宣称业务可用、成功 drain 或完成安装。此入口没有信号、pidfd、进程启动、正式签发、发行安装或 Owner 切换操作。

发生验证失败，只能按准确逆映射还原原物。搬移效果不明或逆向位置冲突时保留自己的保护并返回恢复要求；不能重放消费过的搬移。`status` 只读已安装 root 胶囊和受保护状态。`recover` 要求新原生 `RESTORE_EMPTY` 准确对象：对象绑定当前 journal hash、实际原物位置与 metadata、原批准和目标；只恢复该 inode。成功隔离后也可在同一原进程仍准确时新批准逆向，先冻结并获取当前正常账本的 fresh baseline，保留当前业务状态，不回滚旧业务快照。

只读与正式执行均区分进程运行状态、账本验证、在途状态、业务验收。所有路径禁 core dump，私有账本只驻内存，输出及持久化状态仅存计数、哈希与必要文件身份。任何未知 `.next`、不同 inode/时间/所有者/模式、非零内容、额外写者、目标替换或未知副作用均拒绝。

物理交付只复制约数百 KB 的封存源码，不再复制完整 App/Bridge/Native 大包。进入修复事务前要求普通用户至少保留 32 MiB；这只覆盖小型修复与现场留证，不能代替后续约 194 MB 文件块起步的完整安装预算。磁盘安装预算未解决前不进入 R8 正式停机。
