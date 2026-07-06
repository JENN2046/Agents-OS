# Federated Document Registry v0.1 Draft

Status: `draft_not_active`
Date: 2026-07-01
Scope: AGENTS OS local documentation governance federation

## 一句话

Federated Document Registry 是“文档名册的名册”。

它不把所有文档塞进一个中央大表，而是这样做：

```text
每个大目录维护自己的 document-registry.v0.1.example.yaml
中央 federation 只登记这些目录级名册
validator 逐个检查这些目录级名册
```

## 为什么需要

AGENTS OS 未来文档会非常多。如果一开始就做一个巨大中央 YAML，会很快变得难维护：

```text
所有目录都要改同一个文件。
一点小变化就可能影响全局。
大文件越来越难 review。
目录 owner 没有责任边界。
```

Federated Document Registry 让文档治理保持分区：

```text
control-plane/registry 管自己的文档。
control-plane/task-envelope 管自己的文档。
control-plane/policies/life-core 管自己的文档。
中央只知道这些名册在哪里、怎么验证、边界是什么。
```

## 不是什么

Federated Document Registry 不是：

- 不是 active workspace authority。
- 不是全 workspace document map。
- 不是数据库。
- 不是向量索引。
- 不是搜索引擎。
- 不是发布系统。
- 不是外部写入许可。
- 不是 runtime/provider/formal Memory 入口。

## v0.1 只做什么

第一版只登记三个已经跑过的目录级名册：

```text
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml
control-plane/policies/life-core/drafts/document-registry.v0.1.example.yaml
```

validator 只检查 federation YAML 里列出的 registry，不扫全工作区。

## 通过标准

```text
每个 registry 有 id、owner、directory_root、registry_path。
registry_path 在 workspace 内，不是 protected path。
registry_path 存在。
registry_path 属于对应 directory_root。
每个 registry 自己能通过 validate-document-registry.py。
如果登记 expected_document_count，实际数量必须一致。
如果登记 coverage_checker，路径必须存在且在 workspace 内。
```

## 未来可能扩展

```text
新增 directory owner。
新增 freshness 汇总。
新增 registry dependency graph。
新增 rebuildable search/cache index。
新增 federation coverage checker。
```

但这些都不在 v0.1 自动启用。

## 当前状态

```text
draft_not_active
只作为 Step 4 本地 federation 草案和 example 使用
```
