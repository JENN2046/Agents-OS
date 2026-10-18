# Native 物理关闭候选合同

业务 close/participant.stop/closeLease/prepare/activate/complete/reconcile/archiveOperations
保持原严格语义。新局部资源关闭接口不得变成通用UNKNOWN忽略开关。

候选内部顺序：持久封闭准入 → 封住全部入队入口 → 等待所有已接收工作及嵌套执行 →
核原历史签名材料与本实例新未知集合 → 真实后端静默观察 → 资源关闭 → Socket关闭 →
Store关闭 → 运行writer释放。任一失败必须保持围栏、记录准确阶段，不能宣称完整成功。
超时不能让底层执行在后台继续释放writer；相同调用只复用本次结果，不盲重做效果。

局部关闭输出必须限定本进程/受控indexer范围，不能声称整个系统/历史上游已排空。
在完整外部执行域、角色签名与OS组合证据尚未成立时，不能返回强
PHYSICAL_SHUTDOWN_COMPLETE / LIVE_WORK_DRAINED / FIRST_STOP_SOURCE_ACCEPTANCE_PASS。
默认业务close和生产SIGTERM不得仅因新增局部接口而自动跳过旧严格合同。

持久restrictive fence存在同一原dispatcher Store，不创建第二权限账本。重启不得
自动清除；在Native DB/engine初始化前应识别并拒绝重新取得业务执行能力。
OS跨reboot service阻断仍需未来准确维护安装；仅runtime标记不冒充OS层已验收。

任何正式Quiescence签发必须发生在真正排空、凭据和Store尚可用的阶段，且有准确
批准绑定。内部阶段hook不能把caller布尔或普通回调提升为排空/原生授权依据。
本候选不添加真实Human签名、root服务或生产安装入口。
