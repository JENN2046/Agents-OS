# Validator Boundary Review Checklist v0.1

Status: active
Scope: local AGENTS OS validators and checkers

这个清单专门约束本地 validator。以后做新的 validator，或者改已有
validator，至少要按这张表过一遍；能变成测试的项目，要尽量进 fixture。

## 必查边界

1. 读文件前先挡
   - CLI target 必须先 preflight，再 open/read。
   - preflight 失败时要返回结构化 FAIL，不要抛 traceback。

2. 原始路径和真实路径都要查
   - raw path 要检查 protected path。
   - resolved path 也要检查 protected path。
   - resolved path 必须仍在 workspace 内。

3. symlink 要按真实落点判断
   - symlink 指向 workspace 外：FAIL。
   - symlink 指向 protected path：FAIL。
   - symlink loop：结构化 FAIL，不崩溃。

4. protected 区不能被读取
   - `state-private/`
   - `.env` / `.env.*`
   - `secrets/`
   - `credentials/`
   - `tokens/`
   - `cookies/`
   - private memory raw text
   - provider raw response

5. 输入错误不能打断治理链
   - 数字字段类型错误要 FAIL，不崩溃。
   - YAML root 类型错误要 FAIL 或清晰报错。
   - 子 validator 异常要被包成当前 validator 的 finding。

6. CLI 入口和函数入口都要测
   - 不能只测 helper。
   - 至少有一个 subprocess fixture 覆盖 CLI target。

7. 证据要跟当前行为同步
   - test case 数量要和 receipt/review 一致。
   - registry 里的 `review_by` 要指向当前 review。
   - 新增文档要进 document registry，计数要同步。

## 最小测试组

每个读取本地路径的 validator，至少要覆盖：

```text
valid example passes
missing required path fails
raw protected path fails
outside workspace path fails
symlink to outside workspace fails
symlink to protected path fails
symlink loop fails without traceback
CLI outside target fails before read
malformed typed metadata fails without traceback
secret-like metadata fails when relevant
```

## 不是授权

这个 checklist 不授权读取 private state，不授权外部写入，不授权 provider
call，不授权 runtime execution，不授权正式 Memory registration。
