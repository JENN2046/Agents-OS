# 持久停止围栏

Runtime围栏属于原dispatcher持久Store中的限制状态，不是新的授权来源。
需要固定实例、SourceRelease/version、epoch及准确停止阶段；任何Human批准关联
只能来自既有真实批准的验证结果，不能把普通OS signal/随机epoch称为Human同意。

候选启动、所有WorkspaceCall/Control、queue、refresh、reconnect和Owner状态更新
均须保持此限制。进程换代/重开Store的隔离测试用于验证runtime持久性，不假称整机
reboot或真实systemd安装已发生。若提前创建business DB/engine后才读围栏，仍不合格。

未来OS层需要/etc内持久保护或等价受审机制，在实际unit服务启动之前生效；已有
/run维护drop-in不满足跨reboot条件。本次不安装保护、不启动systemd服务来制造证据。

本轮不实现未经整体合同验收的解围栏入口。未来解除必须复用既有准确授权，重新核
Release/Grant/目标selector/停止事务/无未知效果/原窗口；同一批准已覆盖时不重复弹窗。
Heartbeat、服务启动、旧lease续期、普通Owner更新均无隐式解除权。

Runtime候选限制可独立验，OS层持久保护与真实授权解除仍NOT_IMPLEMENTED/NOT_RUN，
不能合并成G3全PASS。维护安装还须先解决旧Native退出决策。
