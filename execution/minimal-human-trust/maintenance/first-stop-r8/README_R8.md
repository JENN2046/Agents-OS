# R8 首次停机入口

Jenn 已批准一次 `ONE_TIME_CONTROLLED_CRASH_STOP_SOURCE_APP` 规则例外，关联提案 SHA-256 为 `98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234`。这不等于现场目标已经确认，也不等于签发、安装、R17 验收或 Owner 切换。

采用既定 TRUSTED_HOST_ADMIN。入口没有新 Owner 服务、Crown 授权、私钥或 Agent 账号迁移。仅实际云机管理员在前台终端核对准确摘要后，才能启动固定旧 App 的一次受控中止。启动器不捕获密码，不替用户输入确认。

## 入口顺序

先运行 `RUN_IN_DESKTOP_TERMINAL.py preflight`：验证候选封存后仅在内存加载只读检查器，核验真实完整基线；不安装 root 源码、不创建 journal 或现场批准、不冻结、不发信号。它通过也不等于已经批准或完成停机，正式 `stop` 仍重新检查现场并要求准确终端确认。

1. 原生 sudo 管理员认证；校验封存源码，安装仅供此次维护使用的 root 源码副本。核对原 PID/start/boot/invocation、原 R15 公共代码、旧 Grant/发行签名和 ACTIVE revision 16。
2. 受保护只读检查现有 root SEALED 账本登记与目录 dev/ino、完整 App 注册图及其全部项目目录、两笔原 UNKNOWN、原租约签名，以及其他写者；不导出私有原文。两笔 UNKNOWN 所属项目不是完整项目清单。
3. 终端显示准确待执行摘要，用户输入现场的 `STOP <摘要前16位>`。窗口五分钟，不续期。
4. 保持原先 SendSIGKILL=no，安装本次 owned 自动/手工重启保护；直接写固定 cgroup.freeze=1，核实内核完成冻结。
5. 冻结后重新核验全树、签名、原两笔 UNKNOWN/租约和所有文件。root 独占 journal 封存文件哈希/模式，持久化 SIGNAL_INTENT，再通过绑定原进程的 pidfd 最多发送一次 SIGKILL。
6. 核实原进程退出、cgroup 空、完整文件字节/模式未变、重启保护仍有效，才写出 `CONTROLLED_CRASH_STOPPED_NOT_DRAINED` 状态回执。信号不明不补发。

请求可能断开，上游已接收的任务可能继续；不能保证零在途，不能自动重试、结清或删除 UNKNOWN。重启保护属于本次 boot；不要把重启云机当作维护恢复办法。

## 恢复与交接

`RUN_IN_DESKTOP_TERMINAL.py status` 只读取已安装 root 胶囊和现场状态，不运行有副作用的 Driver，不依赖用户目录候选仍存在。

`RUN_IN_DESKTOP_TERMINAL.py recover-original` 根据 journal 分流，另由管理员核对准确恢复对象：

- 信号前：包括冻结 request/event 尚不一致的情况，现场 `RESTORE_RUNNING` 只允许取消自己的冻结请求、确认内核恢复、撤自己的重启保护；原 PID 继续运行，不启动新进程。
- 已确认受控停机后、尚未交接维护围栏：现场 `RESTORE_ORIGINAL` 保留所有原锁/账本，原 R15 自己回收死 PID/start 锁，最多尝试启动一次。成功须新 PID/start/invocation、单进程 cgroup、原两笔 UNKNOWN 与租约语义核实；未知 start 不重放。

源身份、登记、账本或围栏所有权不明时拒绝修改，保留状态和回执。不能手删 `.lock`、`.next`、`.reclaim`，不能恢复历史业务快照；上游副作用无法保证撤销。

原冻结 R6 安装器不认识首次停机保护。`build_successor.py` 生成独立的新 recovery-r8 维护胶囊，完整复用 R6 的 12,600 个 package 文件及模式，payload/Release 目标不变。新原生维护 plan 明确绑定本次 first-stop 胶囊；云机接纳 plan 后先建立并核验维护围栏，再撤首次停机围栏，最后把真实 fenced/stopped 观测交给 baseline。中间不能无保护。

停机入口本身不会签发或安装。后续维护签发/安装仍由新胶囊自己的准确原生批准入口执行。围栏一经交给维护 plan，旧停机恢复入口不能删除维护围栏；后续失败由新 plan 的回滚流程处理，其原 SOURCE App baseline 为 stopped，不能宣称自动恢复了原 App 运行。

## 验证边界

R8 初版的隔离账本只有两个项目，未覆盖生产现有的九个注册项目，真实入口在终端确认、冻结和信号之前以 `UNREGISTERED_STORE_DIRECTORY` 拒绝。R8-R2 保留初版源码与回执，完整纳入既有注册图，同时加入只读真实基线预检；不删除或忽略历史目录，不改业务账本，不把未决租约或历史 transition 宣称为已经结清。

所有 `test_*.py` 都是离线故障/签名/文件测试，无生产 root、SSH、业务调用或信号。`manual_real_fixture.py` 仅手动运行一次可丢弃 user-systemd 服务，通过真实 R8 Driver/LinuxBackend、原 R15 ProtectedStore、synthetic 签名账本、真实 kernel freeze/pidfd/锁恢复验证组合。单位名、cgroup 和源码路径有明确测试映射；该演练不是生产管理员准入或生产验收。

`build_delivery.py` 只作普通用户物理组装，校验原 R6 archive SHA、逐文件复用完整 package，生成封存 first-stop 胶囊和固定摘要的终端启动器。原冻结 R6/R7 不修改。root 临时记录只存哈希和低披露回执，私有账本字节只驻内存，所有受保护入口禁 core dump。
