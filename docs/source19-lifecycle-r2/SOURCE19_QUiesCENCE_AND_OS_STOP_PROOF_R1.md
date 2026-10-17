# Quiescence 与 OS STOP 组合合同

状态 FIRST_STOP_PROOF_PENDING。本文是精确剩余合同，不是已实现或已发生的三方STOP。

保留 verifySignedBusinessStop 原v2语义、false-connect/Release/version/epoch/30s检查。
原signed19 connectRequested=true 不能塞进旧v2。未来新组合需显式绑定当前signed
Delivery完整digest/revision/control、Grant/SourceRelease和实际运行版本，再以三方
持久封闭准入证明其业务准入关闭，不能删除旧检查或仅信本地boolean。

正确顺序：准确Cutover批准 → 持久围栏 → 全范围真实排空 → 原角色签Quiescence →
关闭资源/进程退出 → 独立OS实际读取 → 同epoch组合验证。Quiescence不声明进程已退出。
绑定role/peer、授权target、Source Release/manifest、原PID/start/boot/cgroup/unit
invocation、fence摘要、签名配置/控制、实际观察范围、原2UNKNOWN/结果摘要和时限。

OS观察在退出前固定原实例，退出后确认正常退出、原cgroup成员/Socket/store-writer
消失、持久restart fence仍有效且没有替代writer；绑定原Quiescence摘要。不得让新进程
加载role key假装原进程，也不得使用caller exit=true/noInflight=true作证。
三方证据最早签发到最终验证仍在合法30秒内；超时或重启返回STOP_PROOF_EXPIRED等
准确失败，不续旧签名、不移动时钟、不在原角色退出后补签。

本轮Native局部资源修复不自动产生App/Bridge的实际角色Quiescence，SSH中继不是Bridge。
当前历史执行域结束未证、旧版本维护第一步未闭合；因此不扩无实际可信调用链的
新签发框架、Handoff或21/22 Backend，也不由隔离fixture凑生产三方proof。
