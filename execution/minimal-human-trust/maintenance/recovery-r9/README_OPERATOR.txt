R9 新事务入口与固定 APT 索引清理（工程源，尚未封存/批准/执行）

operator.py 供普通 UID1000 桌面终端使用。CAPSULE/ENTRY_SHA/LOADER_SHA/ROOT_LOADER
先为 None，必须由最终独立审查过的builder写入精确摘要及root-loader.py逐字节内容，
再交付 RUN_IN_DESKTOP_TERMINAL.py。未封存不能 --verify 或 --install；--describe
仅说明。root-loader.py 是审查材料，root仅执行外层携带的已绑定内存字节，
随后读取固定Ops/云candidate，不执行Documents路径源码。

完整路径：本机 .../r15-backport/maintenance-recovered-r9；
云 /home/ubuntu/r16-maintenance-recovered-r9-candidate。
新生产ROOT/STATE/helper/unit属于recovery-r9；不覆盖R8旧记录、不续旧计划，
新围栏固定为94-r16-maintenance-recovery-r9.conf，已有该94及pending/next即拒绝fresh安装。
不adopt旧92/93。旧补偿仅历史证据；prior-verifier只读验证真实闭合关系及当前源状态。

普通 --verify 不联网/提权，验证19源+12600物理包文件bytes/modes。
root MODE=preflight 为只读工程核查，不mint原生批准，不建journal，不清理、不安装；
此模式先拒绝存在的R9 ROOT/STATE/unit/helper/sudoers/freeze/dropin/pending，
再读完整候选/历史provenance/当前源状态，云端只读取APT索引完整清单与空间预算。

本人 Enter 后才云端SSH -tt/sudo -k，真实foreground TTY、原21eb native_guard
确认前后身份校验，输入 APPLY CLOUD <完整pending摘要hash>。
摘要绑定最终CAP、entry、目标版本、真实factsHash、sourceRecoveryEvidence、
精确APT inventoryHash/文件数/逻辑与已分配字节、空间预算和失败回滚。
接受后起5分钟，重新完整验源码+包+真实facts，才允许此批精确缓存清理和新bootstrap。
云bootstrap仅准备维护源码/完整包/helper/sudoers，不签发/安装目标发行。
云成功后本机pkexec及独立 APPLY LOCAL <完整pendinghash>，会先优雅停止仍运行的
Native、Bridge、Owner；完成既有Release/Issuer同Grant签发和双机安装后，
按Owner、Bridge、Native、目标App顺序启动应运行角色。原Owner/Grant/两笔UNKNOWN/历史保留。
签发窗口5分钟，恢复最多30分钟且受云准入上限；从实际本人接受时点计，不延旧时间。

cache-cleanup.py只操作/var/lib/apt/lists顶层普通root文件，逐字节hash+元数据完整清单，
仅允许已复核腾讯Ubuntu noble四pocket/四component/五种APT索引命名结构，
保留lock/partial/auxfiles，不递归读取这些子目录。不读业务/日志，不备份/上传原索引。
APT索引是可重建公共数据，恢复方法为未来另行执行apt-get update；本程序不执行它。
清理前在现有lists/lock获取POSIX排他锁、不创建lock，完整CAS后写独立durable INTENT：
/var/lib/r16-maintenance/recovery-r9-cache-prep/<CAP>/（目录0700/文件0600）。
逐文件DELETE_INTENT后，紧贴unlink再次检查身份与授权5分钟；fsync目录后存REMOVED。
任何中断/结果不明禁止自动重发；已有attempt在preflight即拒绝，需要只读核查和新的
准确人工处理，不提供continue或通用清理接口。删除后不声称能原inode恢复索引。

空间只用bavail，按同filesystem已分配可释放bytes抵扣新root完整副本+target增长，
要求余256MiB。清理后还须实测bavail、以零清理信用再验同预算，防仍打开文件未释放块；不足不进bootstrap。
root预算含两份SOURCE_FREEZE（ROOT和STATE capsule）及16MiB有界余量；
target另保留1MiB。所有旧R8及R3/R4归档、包和账本不删除、不压缩。

退出：认证stdio完全继承，不录密码/批准。云失败不进本机。0只代表准确已核终态，
75待恢复、78拒绝/不明，均不是业务验收；窗口保留退出码，等本人阅读后Enter关闭。
失败恢复App保持 SOURCE STOPPED；不承诺旧App运行。未知签发/安装/清理不自动重试。
可以代开仅说明并等待本人Enter的窗口，不代按Enter、不输入密码或原生批准。

隔离验证：python3 -I -B test_operator.py；python3 -I -B test_cache_cleanup.py。
均不连接生产、root、SSH或服务；缓存测试仅可丢弃普通用户fixture与明确metadata适配器。
最终还需父线程针对封存候选跑真实只读preflight；本工程测试不冒充生产安装。
