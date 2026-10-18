# 历史 UNKNOWN 与当前执行范围

历史 UNKNOWN 仅表示旧结果未知。它不自动证明还在运行，也不自动证明已经结束。
本轮不把结果改为 KNOWN/NOT_EXECUTED/CLOSED，不合成结果，不重新执行。

允许分类的两行必须全部匹配原Project/OperationId/OperationHash/Generation，
App签名operation、action=find_symbol、Issuer签名lease、leaseHash/project/gen/Grant
与原lease来源版本。历史业务lease的原R15身份与当前Source19 Release必须分开。
缺原完整签名材料时拒绝，不从participant里仅有的hash反造原operation。

当前Native候选的有限观察范围是本进程中所有dispatcher/control/outer调用，以及
其实际ProjectForge后端、握手中/已就绪/正在退出的受控indexer子进程和请求。
spawn尚未握手、RPC超时已删waiter、child仍活或stdio尚未close均不能计为完全结束。
new UNKNOWN、INFLIGHT、未知控制、排队任务或尚可能执行的回调均拒强静默。

强 LIVE_WORK_DRAINED 另需原历史执行实例和完整执行域的结束绑定，及无外部未确认效果。
当前公开材料不足；本轮不把有限LOCAL_EXECUTION_QUIESCENT升为全局STOP。
FindSymbol源码路径是本机ProjectForge/indexer，不虚构必有远端；普通App工具上游的
HTTP abort也不是远端完成回执。任何确实存在的外部执行风险都必须单列并阻断强终态。

隔离正例只证明其真实被测执行范围。synthetic签名/短命子进程不是原2生产操作的
运行结束证据。生产缺证据不阻止写安全源码，但不得由测试替它生成事实。
