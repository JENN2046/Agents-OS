# 工作区观测清单

本目录只保存经过限定范围的结构、源码版本与机器映射，不保存运行配置、日志、凭据或私有记忆。

[machines-and-repositories.v1.json](machines-and-repositories.v1.json) 是 [WORKSPACE_MAP.md](../../WORKSPACE_MAP.md) 的机器可读事实来源。
它不是 loader manifest、权限注册表或部署配置，不授权连接其中列出的远端、机器或服务。

约定：

- `observed_at` 表示本次直接观测时间；`documented` 表示只来自既有文档。
- `head` 是源码提交。`tracked_changes`、`untracked_entries` 是 Git 状态条目数，后者可能是目录。
- `repository_id` 相同的行共享仓库；工作树各有自己的分支、工作目录与暂存区。
- `runtime_path`、`version`、`verified_at` 为 `null` 时表示未知，不表示不存在。
- `deployment.status = runtime_path_owner_confirmed` 仅表示 Jenn 确认了运行目录；`evidence` 记录来源，`verified_at` 仍留空直到完成运行验证。
- 历史文档来源、实际远端配置、源码版本和部署版本分别存储；不自动互相替代。
- 更新只依据新的限定观测，不读取私有状态或真实配置补齐未知值。

本清单由本次文档整理单独验证，不冒充既有三个目录 Document Registry pilot 的全工作区覆盖。
