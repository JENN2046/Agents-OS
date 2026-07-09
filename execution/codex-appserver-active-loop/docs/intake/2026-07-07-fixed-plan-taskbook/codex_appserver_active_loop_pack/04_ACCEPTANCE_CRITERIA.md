# 04｜Acceptance Criteria

## Overall Acceptance

```yaml
overall_acceptance:
  result_required: PASS
  workspace_agents_api: NOT_USED
  responses_api: NOT_USED
  browser_automation: NOT_USED
  websocket_transport: NOT_USED
  stdio_transport: USED
  synthetic_workspace_only_for_mvp: true
  real_appserver_smoke: true
  real_repo_access_for_mvp: false
```

## Phase Acceptance

### Phase 0

```yaml
phase0:
  codex_found: PASS
  codex_version_checked: PASS
  appserver_started: PASS
  initialize_success: PASS
  initialized_sent: PASS
  ts_schema_generated: PASS
  json_schema_generated: PASS
```

### Phase 1

```yaml
phase1:
  jsonrpc_client: PASS
  stdio_transport: PASS
  request_response_correlation: PASS
  notifications_handled: PASS
  server_requests_handled: PASS
  clean_shutdown: PASS
```

### Phase 2

```yaml
phase2:
  synthetic_workspace_created: PASS
  no_secret_files: PASS
  restricted_read_root_set: PASS
```

### Phase 3

```yaml
phase3:
  worker_thread_started: PASS
  worker_turn_started: PASS
  worker_output_schema_used: PASS
  need_reviewer_detected: PASS
```

### Phase 4

```yaml
phase4:
  reviewer_thread_started: PASS
  reviewer_turn_started: PASS
  reviewer_output_schema_used: PASS
  reviewer_decision_valid: PASS
```

### Phase 5

```yaml
phase5:
  reviewer_decision_returned_to_worker: PASS
  worker_resumed: PASS
  done_detected: PASS
```

### Phase 6

```yaml
phase6:
  unknown_server_request_decline_or_block: PASS
  file_change_request_declined_in_mvp: PASS
  denied_paths_blocked: PASS
  forbidden_methods_not_called: PASS
```

### Phase 7

```yaml
phase7:
  job_json_written: PASS
  events_jsonl_written: PASS
  receipt_written: PASS
  final_report_written: PASS
```

## Hard Fail Conditions

Any of the following is automatic BLOCK:

```text
Workspace Agents API used
Responses API used
browser automation used
WebSocket used in MVP
non-loopback WebSocket opened
experimentalApi enabled
thread/shellCommand called
command/exec called
process/* called
full_access or dangerFullAccess used
real repo accessed during MVP smoke
secret-like file read
target project boundary exceeded
app-server smoke silently skipped
```

## Evidence Required

Final delivery must include:

```text
data/reports/phase0_reality_calibration.json
data/jobs/<job_id>.json
data/events/<job_id>.events.jsonl
data/receipts/<job_id>.receipt.md
data/reports/final_report.json
```

## Manual Review Checklist

Before accepting:

- [ ] Did smoke use real `codex app-server`?
- [ ] Did smoke use synthetic workspace only?
- [ ] Were schemas generated from installed Codex?
- [ ] Were Worker / Reviewer readOnly restricted?
- [ ] Were all forbidden APIs unused?
- [ ] Is event log complete?
- [ ] Is receipt human-readable?
- [ ] Did final state equal `DONE`?
