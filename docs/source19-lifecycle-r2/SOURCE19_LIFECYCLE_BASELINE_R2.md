# Source19 生命周期基线 R2

任务 SOURCE19_FIRST_STOP_LIFECYCLE_DECOUPLING_R2，范围 SOURCE / ISOLATED ONLY。
开始 HEAD fa5fd0ee4e183ccb5dce1f844cf4dcc3343bfad7；PR51 Draft、准确 HEAD CI SUCCESS、干净且上下游同步。

本轮重新验证 `/run/r16-owner/public-config.json` 的 Release/Grant 签名和公配置 digest
56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec。
SourceRelease 为 r16-daily-20261015-r15-app-recovery-r6；已签公开角色清单的
App4018、Bridge3960、Native8613条文件绑定在已安装修复基底逐字 reread，0缺失/0差异。
本机 Owner、Native 当前 unit/PID/InvocationId 已读取。云机进程、双机 accepted
store 和完整受保护业务账本本轮未重新认证；历史 R12 accepted19 不冒充 fresh。

旧 Source19 dispatcher/headless/runner 与当前候选分开。历史 fixture 17份文件
（15份原源码+固定pin+README）保持不可变，八项负例仍应通过。
旧 participant.stop 要求 operations 全 KNOWN，Native.close 无条件调用并检查
unresolved=0；失败后 socket/store/writer 路径不达。新代码不能修改这些历史事实。

原2 UNKNOWN 为 p2vox/c434da49-055a-43dc-a3e3-695cce137909/gen30 和
pmog2/d0364f8b-3a68-4ca2-a396-7953b29cee4c/gen38。原operationHash与签名绑定见
migration/r17-one-time-recovery-admission.mjs。Operation摘要已经绑定其leaseHash；
仍需原签名operation、Issuer签名lease与project/gen/source版本逐项对应，不仅是ID匹配。

当前 Source19 的原signed19 control 为 connectRequested=true，无旧v2三方STOP接口。
配置20仅历史保留，21/22是未分配规划；本轮不分配任何版本或续旧期限。
源码中 runner/headless/upstream 由正式基底继承；修改时应新增tracked候选覆盖，不能改/opt。
必要 VCP 低披露记忆工具不可用；未调用不同项目的记忆工具。
