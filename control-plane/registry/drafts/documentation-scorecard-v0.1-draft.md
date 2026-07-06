# AGENTS OS Documentation Scorecard v0.1 Draft

Status: `draft_not_active`
Date: 2026-07-01
Scope: local document registry health checks

## 一句话

Documentation Scorecard 是 AGENTS OS 的“文档体检表”。

它检查文档登记是不是清楚、安全、可追踪：

```text
有没有 id
有没有类型
有没有状态
有没有 owner
canonical_path 是否存在
source_of_truth 是否存在
draft/example 有没有冒充 active
有没有过期回看字段
有没有 secret-like 内容
```

## 不是什么

Documentation Scorecard 不是：

- 不是全文搜索引擎。
- 不是数据库。
- 不是向量索引。
- 不是发布系统。
- 不是外部写入许可。
- 不是批量改文档工具。
- 不是最终授权系统。

它只是本地只读检查规则草案。

## 规则

```text
DOC-001: 缺 id -> FAIL
DOC-002: 缺 doc_type -> FAIL
DOC-003: doc_type 不在允许列表 -> FAIL
DOC-004: 缺 status -> FAIL
DOC-005: active/accepted 文档缺 owner -> FAIL
DOC-006: active/accepted 文档缺 canonical_path -> FAIL
DOC-007: canonical_path 不存在 -> FAIL
DOC-008: source_of_truth 不存在 -> active/accepted FAIL，其他 WARN
DOC-009: draft/example 被描述成 active authority -> FAIL
DOC-010: superseded 文档缺 superseded_by -> WARN
DOC-011: related 路径不存在 -> WARN；指向敏感路径或工作区外路径 -> FAIL，不读取
DOC-012: active/accepted 文档缺 last_reviewed -> WARN
DOC-013: active/accepted 文档缺 review_by -> WARN
DOC-014: 文档登记或已登记文档内容含 secret-like pattern -> FAIL
DOC-015: security_boundary 为空 -> WARN
DOC-016: README 缺 active/draft/example 边界说明 -> WARN
DOC-017: canonical_path 指向敏感路径 -> FAIL，不读取
DOC-018: source_of_truth 指向敏感路径 -> FAIL，不读取
DOC-TARGET: validator 目标文件指向敏感路径、工作区外路径、目录或不存在文件 -> FAIL，不读取
```

## 默认输入

```text
control-plane/registry/drafts/document-registry.v0.1.example.yaml
```

## 默认 checker

```text
control-plane/registry/validate-document-registry.py
```

## 默认测试

```text
control-plane/registry/test-document-registry-validator.py
```

## 安全边界

Checker 不允许读取：

```text
state-private/
.env
.env.*
secret/
secrets/
credentials/
tokens/
private memory raw text
provider raw response
```

如果 document registry 登记了这些路径，checker 应该报 FAIL，并且不读取内容。

## 当前状态

```text
draft_not_active
用于 control-plane/registry 小试点
```
