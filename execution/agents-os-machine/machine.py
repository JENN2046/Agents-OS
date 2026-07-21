#!/usr/bin/env python3
"""Preview-only AGENTS OS machine skeleton.

The machine reads the Active Work Queue, normalizes queue items, emits a NOW
preview, and validates that all dangerous capabilities remain disabled. It does
not execute tasks, start services, call providers, write Memory, or modify the
queue.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


MACHINE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = MACHINE_DIR.parents[1]
REGISTRY_DIR = WORKSPACE_ROOT / "control-plane" / "registry"
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import preflight_target

MANIFEST_PATH = MACHINE_DIR / "machine-manifest.json"
SCHEMA_PATH = MACHINE_DIR / "queue-item.schema.json"
DEFAULT_QUEUE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-21-agents-os-active-work-queue-v10.9.md"
ROUTE_SELECTION_PACKAGE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-07-agents-os-next-route-selection-package-v0.1.md"
ROUTE_ADOPTION_BUNDLE_PREVIEW = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-07-agents-os-control-chain-route-choice-adoption-bundle-preview-v0.1.md"
TASK_ENVELOPE_VALIDATOR = WORKSPACE_ROOT / "control-plane" / "task-envelope" / "validate-task-envelope.py"
DOCCTL = WORKSPACE_ROOT / "control-plane" / "registry" / "docctl.py"

LANES = ("NOW", "NEXT", "LATER", "BLOCKED", "CLOSED")
DANGEROUS_FLAGS = (
    "provider_call_authorized",
    "service_start_authorized",
    "executor_run_authorized",
    "external_write_authorized",
    "memory_write_authorized",
    "runtime_plugin_activation_authorized",
)

DENIED_SIGNAL_PATTERNS = {
    "provider_call": re.compile(r"\b(call|invoke|use|run)\s+(a\s+)?provider\b|\bprovider_call_authorized\s*=\s*true\b", re.I),
    "service_start": re.compile(r"\b(start|launch|run)\s+(a\s+)?service\b|\bservice_start_authorized\s*=\s*true\b", re.I),
    "executor_run": re.compile(r"\b(run|start|launch)\s+(the\s+)?executor\b|\bexecutor_run_authorized\s*=\s*true\b", re.I),
    "external_write": re.compile(
        r"\b(perform|do|make|authorize|execute)\s+(an\s+)?external\s+write\b"
        r"|\b(write|post|send|upload|create|update|publish)\s+(to\s+)?(notion|github|email|mail|slack|discord|external)\b"
        r"|\b(create|update|close|delete)\s+(a\s+)?github\s+(issue|pr|pull request|release)\b"
        r"|\b(send|write)\s+(an\s+)?email\b"
        r"|\bexternal_write_authorized\s*=\s*true\b",
        re.I,
    ),
    "database_write": re.compile(r"\b(database|db)\s+write\b|\b(write|update|delete|insert|migrate)\s+(database|db)\b", re.I),
    "memory_write": re.compile(r"\b(write|update|register)\s+(formal\s+)?memory\b|\bmemory_write_authorized\s*=\s*true\b", re.I),
    "runtime_plugin_activation": re.compile(r"\bactivate\s+(plugin|runtime|vcptoolbox|colameta)\b|\bruntime_plugin_activation_authorized\s*=\s*true\b", re.I),
    "state_private": re.compile(r"\bstate-private/", re.I),
    "auth_or_secret_config": re.compile(r"\b(auth|token|cookie|session|credential|secret|provider config|runtime config)\b", re.I),
    "git_release_boundary": re.compile(r"\b(git push|git tag|force push|release|deploy|publish|history rewrite|npm publish|package publish)\b", re.I),
}

ROUTE_SELECTION_REQUIRED = re.compile(
    r"\bNo Active Automatic Construction Item\b"
    r"|\brequires_jenn_route_choice\s*=\s*true\b"
    r"|\bno_active_route_selected\s*=\s*true\b"
    r"|\bdo not infer a new construction route without Jenn direction\b",
    re.I,
)

JENN_DECISION_REQUIRED = re.compile(
    r"\brequires_jenn_decision\s*=\s*true\b"
    r"|\bdecision_owner\s*=\s*Jenn\b",
    re.I,
)

NEGATED_SIGNAL_CONTEXT = re.compile(
    r"\b(no|do not|does not|cannot|can't|must not|must remain false|blocked actions?|blocked until|keep .*blocked|forbidden|denied)\b",
    re.I,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_queue_path(queue_path: Path) -> tuple[Path | None, list[dict[str, str]]]:
    candidate = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    findings = preflight_target(candidate, WORKSPACE_ROOT, "MACHINE-QUEUE-PATH")
    if findings:
        return None, findings
    return candidate.resolve(), []


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def dangerous_authorization_defaults() -> dict[str, bool]:
    return {flag: False for flag in DANGEROUS_FLAGS}


def review_gate(requires_jenn_decision: bool = False, review_reason: str | None = None) -> dict[str, Any]:
    return {
        "machine_generated": True,
        "status": "preview_or_draft",
        "requires_nobao_review": True,
        "requires_jenn_decision": requires_jenn_decision,
        "review_status": "pending",
        "execution_authorized": False,
        "review_reason": review_reason or "machine preview must be reviewed before execution",
    }


def has_false_dangerous_flags(value: dict[str, Any]) -> tuple[bool, list[str]]:
    failures = [flag for flag in DANGEROUS_FLAGS if value.get(flag) is not False]
    return not failures, failures


def find_denied_signals(text: str) -> list[str]:
    scan_text = "\n".join(
        line for line in text.splitlines() if not NEGATED_SIGNAL_CONTEXT.search(line)
    )
    hits: list[str] = []
    for signal_id, pattern in DENIED_SIGNAL_PATTERNS.items():
        if pattern.search(scan_text):
            hits.append(signal_id)
    return sorted(set(hits))


def parse_route_option_ids(path: Path = ROUTE_SELECTION_PACKAGE) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return re.findall(r"(?m)^### Option ([A-Z]):\s+", text)


def next_user_action_for_item(item: dict[str, Any]) -> dict[str, Any]:
    route_choice_required = "route_selection_required" in item.get("denied_signals", [])
    governance_decision_required = "jenn_decision_required" in item.get("denied_signals", [])
    route_ids = parse_route_option_ids() if route_choice_required else []
    status = "none"
    instruction = None
    if route_choice_required:
        status = "route_choice_required"
        instruction = "choose_one_route_id"
    elif governance_decision_required:
        status = "governance_decision_required"
        instruction = "follow_current_queue_decision_gate"
    requires_jenn_decision = route_choice_required or governance_decision_required
    return {
        "schema_version": "agents-os.machine.next-user-action.v0.1",
        "status": status,
        "decision_owner": "Jenn" if requires_jenn_decision else None,
        "requires_jenn_decision": requires_jenn_decision,
        "instruction": instruction,
        "accepted_route_ids": route_ids,
        "template_source_path": rel(ROUTE_SELECTION_PACKAGE),
        "exact_confirmation_templates_available": ROUTE_SELECTION_PACKAGE.exists() and bool(route_ids),
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
    }


def route_choice_adoption_bundle_readiness_for_item(item: dict[str, Any]) -> dict[str, Any]:
    route_choice_required = "route_selection_required" in item.get("denied_signals", [])
    bundle_exists = ROUTE_ADOPTION_BUNDLE_PREVIEW.exists()
    return {
        "schema_version": "agents-os.machine.route-choice-adoption-bundle-readiness.v0.1",
        "status": "waiting_for_jenn_route_choice" if route_choice_required else "not_active",
        "decision_owner": "Jenn" if route_choice_required else None,
        "requires_jenn_decision": route_choice_required,
        "bundle_preview_path": rel(ROUTE_ADOPTION_BUNDLE_PREVIEW),
        "bundle_preview_exists": bundle_exists,
        "bundle_preview_available": bundle_exists,
        "can_apply_now": False,
        "preview_only": True,
        "read_only": True,
        "route_auto_selection_authorized": False,
        "route_adoption_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "raw_content_output": False,
    }


def parse_item_heading(line: str) -> tuple[str, str] | None:
    match = re.match(r"^###\s+([A-Z]+-\d{3}):\s+(.+?)\s*$", line)
    if not match:
        return None
    return match.group(1), match.group(2)


def normalize_item(lane: str, item_id: str, title: str, body_lines: list[str]) -> dict[str, Any]:
    body = "\n".join(body_lines).strip()
    item_text = "\n".join([title, body])
    denied_signals = find_denied_signals(item_text)
    route_selection_required = bool(ROUTE_SELECTION_REQUIRED.search(item_text))
    if route_selection_required:
        denied_signals.append("route_selection_required")
    jenn_decision_required = bool(JENN_DECISION_REQUIRED.search(item_text))
    if jenn_decision_required and not route_selection_required:
        denied_signals.append("jenn_decision_required")
    denied_signals = sorted(set(denied_signals))
    requires_jenn = bool(denied_signals)
    review_reason = "machine preview must be reviewed before execution"
    if route_selection_required:
        review_reason = "route selection required by queue stop-state"
    elif jenn_decision_required:
        review_reason = "Jenn governance decision required by queue stop-state"
    elif requires_jenn:
        review_reason = "denied signal detected"
    return {
        "id": item_id,
        "lane": lane,
        "title": title,
        "body": body,
        "denied_signals": denied_signals,
        "blocked": requires_jenn,
        "authorization": dangerous_authorization_defaults(),
        "review_gate": review_gate(
            requires_jenn_decision=requires_jenn,
            review_reason=review_reason,
        ),
    }


def parse_code_entries(lane: str, lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    in_fence = False
    index = 1
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and stripped:
            entries.append(
                {
                    "id": f"{lane}-{index:03d}",
                    "lane": lane,
                    "text": stripped,
                }
            )
            index += 1
    return entries


def parse_queue_markdown(text: str, source_path: Path) -> dict[str, Any]:
    lanes: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    lane_lines: dict[str, list[str]] = {lane: [] for lane in LANES}
    errors: list[str] = []
    current_lane: str | None = None
    current_item: tuple[str, str, list[str]] | None = None

    def finish_item() -> None:
        nonlocal current_item
        if current_lane and current_item:
            item_id, title, body_lines = current_item
            lanes[current_lane].append(normalize_item(current_lane, item_id, title, body_lines))
        current_item = None

    for line in text.splitlines():
        lane_match = re.match(r"^##\s+(.+?)\s*$", line)
        if lane_match:
            heading = lane_match.group(1).strip()
            if heading in LANES:
                finish_item()
                current_lane = heading
                continue
            if current_lane:
                finish_item()
                current_lane = None
            continue

        if current_lane is None:
            continue

        lane_lines[current_lane].append(line)
        if line.startswith("### "):
            parsed = parse_item_heading(line)
            if parsed is None:
                errors.append(f"invalid item heading under {current_lane}: {line}")
                finish_item()
                current_item = None
                continue
            finish_item()
            item_id, title = parsed
            if not item_id.startswith(f"{current_lane}-"):
                errors.append(f"item id does not match lane {current_lane}: {item_id}")
            current_item = (item_id, title, [])
            continue

        if current_item:
            current_item[2].append(line)

    finish_item()

    blocked_entries = parse_code_entries("BLOCKED", lane_lines["BLOCKED"])
    closed_entries = parse_code_entries("CLOSED", lane_lines["CLOSED"])
    now_count = len(lanes["NOW"])

    if now_count != 1:
        errors.append(f"expected exactly one NOW item, got {now_count}")

    all_items = [item for lane in LANES for item in lanes[lane]]
    schema = load_json(SCHEMA_PATH)
    for item in all_items:
        item_errors = validate_queue_item(item, schema)
        errors.extend(f"{item['id']}: {error}" for error in item_errors)

    return {
        "schema_version": "agents-os.machine.normalized-queue.v0.1",
        "source_path": rel(source_path),
        "parse_errors": errors,
        "passed": not errors,
        "lanes": lanes,
        "blocked_entries": blocked_entries,
        "closed_entries": closed_entries,
        "summary": {
            "now_count": len(lanes["NOW"]),
            "next_count": len(lanes["NEXT"]),
            "later_count": len(lanes["LATER"]),
            "blocked_count": len(blocked_entries),
            "closed_count": len(closed_entries),
            "item_count": sum(len(lanes[lane]) for lane in LANES),
        },
    }


def validate_queue_item(item: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in schema.get("required", []):
        if field not in item:
            errors.append(f"missing required field: {field}")
    if not re.match(r"^[A-Z]+-\d{3}$", str(item.get("id", ""))):
        errors.append("id must match ^[A-Z]+-[0-9]{3}$")
    if item.get("lane") not in LANES:
        errors.append(f"invalid lane: {item.get('lane')}")
    if not str(item.get("title", "")).strip():
        errors.append("title must not be empty")
    authorization = item.get("authorization", {})
    required_false = (
        schema.get("properties", {})
        .get("authorization", {})
        .get("required_false", DANGEROUS_FLAGS)
    )
    ok, failures = has_false_flags(authorization, required_false)
    if not ok:
        errors.append(f"dangerous authorization flags not false: {','.join(failures)}")
    review = item.get("review_gate", {})
    if review.get("machine_generated") is not True:
        errors.append("review_gate.machine_generated must be true")
    if review.get("requires_nobao_review") is not True:
        errors.append("review_gate.requires_nobao_review must be true")
    if review.get("review_status") != "pending":
        errors.append("review_gate.review_status must be pending")
    if review.get("execution_authorized") is not False:
        errors.append("review_gate.execution_authorized must be false")
    return errors


def has_false_flags(value: dict[str, Any], flags: Any) -> tuple[bool, list[str]]:
    if not isinstance(flags, list):
        flags = list(DANGEROUS_FLAGS)
    failures = [str(flag) for flag in flags if value.get(str(flag)) is not False]
    return not failures, failures


def load_queue(queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    resolved, findings = resolve_queue_path(queue_path)
    if findings or resolved is None:
        return {
            "schema_version": "agents-os.machine.normalized-queue.v0.1",
            "source_path": str(queue_path),
            "parse_errors": [item["message"] for item in findings],
            "path_findings": findings,
            "passed": False,
            "lanes": {lane: [] for lane in LANES},
            "blocked_entries": [],
            "closed_entries": [],
            "summary": {
                "now_count": 0,
                "next_count": 0,
                "later_count": 0,
                "blocked_count": 0,
                "closed_count": 0,
                "item_count": 0,
            },
        }
    return parse_queue_markdown(read_text(resolved), resolved)


def now_item(normalized_queue: dict[str, Any]) -> dict[str, Any]:
    now_items = normalized_queue.get("lanes", {}).get("NOW", [])
    if len(now_items) != 1:
        raise ValueError(f"expected exactly one NOW item, got {len(now_items)}")
    return now_items[0]


def task_envelope_markdown(item: dict[str, Any]) -> str:
    blocked = ", ".join(item.get("denied_signals", [])) or "none"
    return f"""# Machine Preview Task Envelope: {item['title']}

Template ID: `agents-os.task-envelope.v0.1`
Status: `machine_preview`
Date: 2026-07-07

## 1. 事情本身

事情名称：

```text
{item['title']}
```

一句话说明：

```text
Machine preview for {item['id']} from the Active Work Queue.
```

为什么现在要做：

```text
Active Work Queue marks this as the single NOW item.
```

谁来做：

```text
Nobao after Machine preview review.
```

## 2. 现在处在哪个阶段

在下面选一个最接近的：

```text
[ ] 只是看一眼 / 解释
[ ] 写本地草案
[x] 整理本地文档或结构
[ ] 改本地规则或流程
[ ] 跑已有本地测试
[ ] 新增本地测试样例
[ ] 准备外部工具或运行时方案
[ ] 改外部工具或运行时配置
[ ] 真实调用外部工具 / provider / plugin
[ ] 写入外部平台，比如 Notion、GitHub、邮件
[ ] 影响正式记忆、身份、关系、家规、生命内核
[ ] 碰到密钥、私密记忆、provider 原始响应
```

阶段说明：

```text
This is a preview-only local control-plane task envelope. It does not execute the task.
```

## 3. 颜色区判断

绿色区：

```text
可以默认自动做。通常是本地、低风险、可回看、不会碰外部系统或红线。
```

黄色区：

```text
可以小步推进。先做草案、留痕、回看，不直接变正式。
```

红色区：

```text
不能自动做。只能停下、说明边界、给 Jenn 预案。
```

本次判断：

```text
[ ] 绿色区
[x] 黄色区
[ ] 红色区
```

为什么这样判断：

```text
Machine output requires Nobao review before execution. External write, 密钥, 私密记忆, provider, runtime, plugin, and Memory actions remain blocked.
```

## 4. policy-router 预检

行动描述：

```text
preview local AGENTS OS machine queue item
```

预检结果：

```text
decision: needs_review
permission: yellow_zone_preview
需要的证据: receipt, review, validation_summary
不能碰的边界: provider_call, service_start, executor_run, external_write, formal_memory_write, state-private, 密钥, 私密记忆
```

如果没有跑 policy-router，说明原因：

```text
Machine v0.1 does not execute policy-router. It emits a preview that Nobao must review.
```

## 5. 能不能自动做

自动推进判断：

```text
[ ] 可以自动做
[ ] 只能做本地草案
[x] 需要复核后再继续
[ ] 需要 Jenn 明确确认
[ ] 不能做，只能写预案
```

允许做的范围：

```text
Preview-only local planning, task-envelope validation, and docctl validation.
```

不能做的范围：

```text
No provider call, service start, executor run, plugin/runtime activation, external write, formal Memory write, state-private read, auth/token/cookie/session/provider config read/write, Git push/tag/release/deploy/history rewrite.
```

## 6. 做事步骤

计划步骤：

```text
1. Read the Active Work Queue.
2. Confirm exactly one NOW item.
3. Generate a preview task envelope.
4. Validate the preview envelope in a temporary directory.
5. Require Nobao review before any execution.
```

停止条件：

```text
Stop if multiple NOW items, no NOW item, schema failure, dangerous authorization true, protected path, provider/runtime/plugin/external write/Memory/Git signal, or docctl failure appears.
```

## 7. 留痕要求

这件事做完要留下：

```text
[ ] 一句话说明
[x] 收据
[x] 本地复核
[ ] Jenn 确认记录
[ ] 记忆候选
[ ] 正式记忆流程
[ ] 只写边界预案，不执行
```

收据位置：

```text
control-plane/registry/receipts/
```

复核位置：

```text
control-plane/registry/reviews/
```

## 8. 验收

怎么知道这件事做完了：

```text
Machine preview is valid, dangerous authorization remains false, and Nobao review is required.
```

怎么验证：

```text
Run machine.py validate, validate-task-envelope.py, docctl status, and docctl doctor.
```

还剩什么风险：

```text
Machine preview is not execution. Nobao must review it before any local work starts. Denied signals detected: {blocked}.
```

## 9. 最终状态

```text
[x] 未开始
[ ] 进行中
[ ] 已完成
[ ] 已暂停
[ ] 被红线挡住
[ ] 需要 Jenn
```

结果说明：

```text
Preview generated; execution_authorized=false.
```

## 10. 大白话复述

最后用一句人话复述：

```text
这件事是：把当前 NOW 转成机器预览。
它属于：黄色区本地 preview。
我能做：生成和验证 task envelope preview。
我不能碰：外部写入、密钥、私密记忆、provider、runtime、plugin、Memory、state-private、Git push/tag/release/deploy/history rewrite。
做完会留下：machine preview, receipt, review, validation summary.
```
"""


def build_preview(item: dict[str, Any]) -> dict[str, Any]:
    authorization = dangerous_authorization_defaults()
    ok, failures = has_false_dangerous_flags(authorization)
    requires_jenn = bool(item.get("review_gate", {}).get("requires_jenn_decision"))
    review_reason = item.get("review_gate", {}).get("review_reason")
    next_user_action = next_user_action_for_item(item)
    route_choice_readiness = route_choice_adoption_bundle_readiness_for_item(item)
    return {
        "schema_version": "agents-os.machine.preview.v0.1",
        "preview_only": True,
        "machine_generated": True,
        "source_item": {
            "id": item["id"],
            "lane": item["lane"],
            "title": item["title"],
        },
        "status": "preview_or_draft",
        "write_performed": False,
        "authorization": authorization,
        "dangerous_authorization_flags_all_false": ok,
        "dangerous_authorization_failures": failures,
        "blocked": bool(item.get("blocked")),
        "denied_signals": item.get("denied_signals", []),
        "actionable": not bool(item.get("blocked")),
        "next_user_action": next_user_action,
        "route_choice_adoption_bundle_readiness": route_choice_readiness,
        "review_gate": review_gate(
            requires_jenn_decision=requires_jenn,
            review_reason=review_reason or "machine preview must be reviewed before execution",
        ),
        "execution_authorized": False,
        "task_envelope_markdown": task_envelope_markdown(item),
        "json_output_authoritative": True,
        "markdown_task_envelope_is_derived": True,
    }


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    defaults = manifest.get("dangerous_authorization_defaults", {})
    ok, failures = has_false_dangerous_flags(defaults)
    if not ok:
        errors.append(f"manifest dangerous authorization flags not false: {','.join(failures)}")
    review = manifest.get("review_gate_defaults", {})
    if review.get("machine_generated") is not True:
        errors.append("manifest review_gate_defaults.machine_generated must be true")
    if review.get("requires_nobao_review") is not True:
        errors.append("manifest review_gate_defaults.requires_nobao_review must be true")
    if review.get("review_status") != "pending":
        errors.append("manifest review_gate_defaults.review_status must be pending")
    if review.get("execution_authorized") is not False:
        errors.append("manifest review_gate_defaults.execution_authorized must be false")
    if manifest.get("default_mode") != "preview_only":
        errors.append("manifest default_mode must be preview_only")
    return errors


def validate_preview(preview: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if preview.get("preview_only") is not True:
        errors.append("preview_only must be true")
    if preview.get("write_performed") is not False:
        errors.append("write_performed must be false")
    if preview.get("execution_authorized") is not False:
        errors.append("execution_authorized must be false")
    if preview.get("blocked") and preview.get("actionable") is not False:
        errors.append("blocked preview must be actionable=false")
    if not preview.get("blocked") and preview.get("actionable") is not True:
        errors.append("unblocked preview must be actionable=true")
    ok, failures = has_false_dangerous_flags(preview.get("authorization", {}))
    if not ok:
        errors.append(f"preview dangerous authorization flags not false: {','.join(failures)}")
    review = preview.get("review_gate", {})
    if review.get("requires_nobao_review") is not True:
        errors.append("preview review_gate.requires_nobao_review must be true")
    if review.get("review_status") != "pending":
        errors.append("preview review_gate.review_status must be pending")
    if review.get("execution_authorized") is not False:
        errors.append("preview review_gate.execution_authorized must be false")
    if preview.get("blocked") and review.get("requires_jenn_decision") is not True:
        errors.append("blocked preview must require Jenn decision")
    next_user_action = preview.get("next_user_action", {})
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
    ):
        if next_user_action.get(flag) is not False:
            errors.append(f"preview next user action must not authorize {flag}")
    route_choice_required = "route_selection_required" in preview.get("denied_signals", [])
    if route_choice_required:
        if next_user_action.get("status") != "route_choice_required":
            errors.append("route selection preview must surface route_choice_required next user action")
        if next_user_action.get("decision_owner") != "Jenn":
            errors.append("route selection preview next user action owner must be Jenn")
        if next_user_action.get("requires_jenn_decision") is not True:
            errors.append("route selection preview next user action must require Jenn decision")
        if not next_user_action.get("accepted_route_ids"):
            errors.append("route selection preview should surface accepted route ids")
        if next_user_action.get("exact_confirmation_templates_available") is not True:
            errors.append("route selection preview should point to available confirmation templates")
    elif "jenn_decision_required" in preview.get("denied_signals", []):
        if next_user_action.get("status") != "governance_decision_required":
            errors.append("Jenn decision preview must surface governance_decision_required next user action")
        if next_user_action.get("decision_owner") != "Jenn":
            errors.append("Jenn decision preview next user action owner must be Jenn")
        if next_user_action.get("requires_jenn_decision") is not True:
            errors.append("Jenn decision preview next user action must require Jenn decision")
        if next_user_action.get("accepted_route_ids"):
            errors.append("generic Jenn decision preview must not surface route ids")
        if next_user_action.get("exact_confirmation_templates_available") is not False:
            errors.append("generic Jenn decision preview must not claim route confirmation templates")
    elif next_user_action.get("status") != "none":
        errors.append("non-decision preview next user action must be none")
    route_choice_readiness = preview.get("route_choice_adoption_bundle_readiness", {})
    for flag in (
        "can_apply_now",
        "route_auto_selection_authorized",
        "route_adoption_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
        "raw_confirmation_text_output",
        "raw_template_output",
        "raw_content_output",
    ):
        if route_choice_readiness.get(flag) is not False:
            errors.append(f"preview route choice adoption bundle readiness must not authorize {flag}")
    if route_choice_readiness.get("preview_only") is not True:
        errors.append("preview route choice adoption bundle readiness must be preview_only")
    if route_choice_readiness.get("read_only") is not True:
        errors.append("preview route choice adoption bundle readiness must be read_only")
    if route_choice_required:
        if route_choice_readiness.get("status") != "waiting_for_jenn_route_choice":
            errors.append("route selection preview must surface waiting_for_jenn_route_choice bundle readiness")
        if route_choice_readiness.get("decision_owner") != "Jenn":
            errors.append("route selection bundle readiness owner must be Jenn")
        if route_choice_readiness.get("requires_jenn_decision") is not True:
            errors.append("route selection bundle readiness must require Jenn decision")
        if route_choice_readiness.get("bundle_preview_available") is not True:
            errors.append("route selection bundle readiness should point to available bundle preview evidence")
    elif route_choice_readiness.get("status") != "not_active":
        errors.append("non-route preview route choice adoption bundle readiness must be not_active")
    return errors


def run_command(command: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def validate_task_envelope_preview(markdown: str) -> dict[str, Any]:
    temp_file_path: str | None = None
    validator_result: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="agents-os-machine-preview-") as temp_dir:
        target = Path(temp_dir) / "machine-preview-task-envelope.md"
        temp_file_path = str(target)
        target.write_text(markdown, encoding="utf-8")
        validator_result = run_command([sys.executable, str(TASK_ENVELOPE_VALIDATOR), str(target), "--json"])
        temp_exists_during_validation = target.exists()
    temp_exists_after_cleanup = Path(temp_file_path).exists() if temp_file_path else False
    parsed: dict[str, Any] | None = None
    if validator_result["stdout"].strip():
        try:
            parsed = json.loads(validator_result["stdout"])
        except json.JSONDecodeError:
            parsed = None
    return {
        "passed": validator_result["passed"] and temp_exists_during_validation and not temp_exists_after_cleanup,
        "validator_returncode": validator_result["returncode"],
        "validator_json_parsed": parsed is not None,
        "validator_passed": bool(parsed.get("passed")) if isinstance(parsed, dict) else False,
        "temporary_file_existed_during_validation": temp_exists_during_validation,
        "temporary_file_exists_after_cleanup": temp_exists_after_cleanup,
        "temporary_preview_cleaned": not temp_exists_after_cleanup,
    }


def docctl_json(command: str) -> dict[str, Any]:
    result = run_command([sys.executable, str(DOCCTL), command, "--json"])
    payload: dict[str, Any] | None = None
    if result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            payload = None
    return {
        "command": command,
        "returncode": result["returncode"],
        "passed": result["passed"] and bool(payload.get("passed")) if isinstance(payload, dict) else False,
        "json_parsed": payload is not None,
    }


def validate_machine(queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    normalized = load_queue(queue_path)
    errors: list[str] = []
    errors.extend(validate_manifest(manifest))
    errors.extend(normalized.get("parse_errors", []))

    preview: dict[str, Any] | None = None
    task_preview_validation: dict[str, Any] | None = None
    if normalized.get("passed"):
        preview = build_preview(now_item(normalized))
        errors.extend(validate_preview(preview))
        task_preview_validation = validate_task_envelope_preview(preview["task_envelope_markdown"])
        if not task_preview_validation["passed"] or not task_preview_validation["validator_passed"]:
            errors.append("task envelope preview validation failed")

    status = docctl_json("status")
    doctor = docctl_json("doctor")
    if not status["passed"]:
        errors.append("docctl status failed")
    if not doctor["passed"]:
        errors.append("docctl doctor failed")

    return {
        "schema_version": "agents-os.machine.validation.v0.1",
        "passed": not errors,
        "errors": errors,
        "manifest_path": rel(MANIFEST_PATH),
        "queue": {
            "source_path": normalized.get("source_path"),
            "summary": normalized.get("summary"),
            "passed": normalized.get("passed"),
        },
        "preview": {
            "present": preview is not None,
            "dangerous_authorization_flags_all_false": preview.get("dangerous_authorization_flags_all_false") if preview else False,
            "requires_nobao_review": preview.get("review_gate", {}).get("requires_nobao_review") if preview else False,
            "execution_authorized": preview.get("execution_authorized") if preview else None,
            "actionable": preview.get("actionable") if preview else None,
            "blocked": preview.get("blocked") if preview else None,
            "next_user_action_status": preview.get("next_user_action", {}).get("status") if preview else None,
            "next_user_action_owner": preview.get("next_user_action", {}).get("decision_owner") if preview else None,
            "route_choice_adoption_bundle_readiness_status": preview.get("route_choice_adoption_bundle_readiness", {}).get("status") if preview else None,
            "route_choice_adoption_bundle_can_apply_now": preview.get("route_choice_adoption_bundle_readiness", {}).get("can_apply_now") if preview else None,
        },
        "task_envelope_preview": task_preview_validation,
        "docctl": {
            "status": status,
            "doctor": doctor,
        },
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def print_validation_text(result: dict[str, Any]) -> None:
    print("AGENTS OS Machine Skeleton validation")
    print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Queue: {result['queue']['summary']}")
    print(f"Task envelope preview cleaned: {result.get('task_envelope_preview', {}).get('temporary_preview_cleaned')}")
    print(f"Docctl status: {'PASS' if result['docctl']['status']['passed'] else 'FAIL'}")
    print(f"Docctl doctor: {'PASS' if result['docctl']['doctor']['passed'] else 'FAIL'}")
    if result["errors"]:
        print("")
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS preview-only machine skeleton.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect-queue", help="Inspect and normalize the active queue.")
    inspect_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    preview_parser = subparsers.add_parser("preview-now", help="Emit preview for the single NOW item.")
    preview_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    validate_parser = subparsers.add_parser("validate", help="Run machine self-validation.")
    validate_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    args = parser.parse_args()
    queue_path = Path(args.queue)
    if not queue_path.is_absolute():
        queue_path = WORKSPACE_ROOT / queue_path

    if args.command == "inspect-queue":
        normalized = load_queue(queue_path)
        if args.json:
            print_json(normalized)
        else:
            print(f"Queue: {normalized['source_path']}")
            print(f"Status: {'PASS' if normalized['passed'] else 'FAIL'}")
            print(f"Summary: {normalized['summary']}")
            if normalized["parse_errors"]:
                print("Errors:")
                for error in normalized["parse_errors"]:
                    print(f"- {error}")
        return 0 if normalized["passed"] else 1

    if args.command == "preview-now":
        normalized = load_queue(queue_path)
        if not normalized["passed"]:
            if args.json:
                print_json({"passed": False, "errors": normalized["parse_errors"]})
            else:
                print("Status: FAIL")
                for error in normalized["parse_errors"]:
                    print(f"- {error}")
            return 1
        preview = build_preview(now_item(normalized))
        errors = validate_preview(preview)
        preview["passed"] = not errors
        preview["errors"] = errors
        if args.json:
            print_json({key: value for key, value in preview.items() if key != "task_envelope_markdown"})
        else:
            print(f"Preview: {preview['source_item']['id']} {preview['source_item']['title']}")
            print(f"Status: {'PASS' if preview['passed'] else 'FAIL'}")
            print(f"Requires Nobao review: {preview['review_gate']['requires_nobao_review']}")
            print(f"Next user action: {preview['next_user_action']['status']}")
            print(f"Route choice adoption bundle readiness: {preview['route_choice_adoption_bundle_readiness']['status']}")
            print(f"Execution authorized: {preview['execution_authorized']}")
        return 0 if preview["passed"] else 1

    if args.command == "validate":
        result = validate_machine(queue_path)
        if args.json:
            print_json(result)
        else:
            print_validation_text(result)
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
