# 09｜Codex Handoff Prompt

Use this as the short entry prompt to Codex.

---

You are implementing the project defined in:

```text
03_CODEX_EXECUTION_TASKBOOK.md
```

Target path:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

Scope:

```text
scaffold + schema generation + real app-server smoke
```

Hard boundaries:

```text
- Write only inside target project repo.
- Managed Worker / Reviewer sessions must be readOnly restricted.
- Use synthetic workspace only.
- Use stdio only.
- Do not use WebSocket.
- Do not use Workspace Agents API.
- Do not use Responses API.
- Do not automate ChatGPT browser UI.
- Do not call thread/shellCommand.
- Do not call command/exec.
- Do not call process/*.
- Do not use full_access / dangerFullAccess.
- Do not push, deploy, release, tag, or commit.
- Do not read secrets, env values, credentials, tokens, cookies, SSH keys, or state-private.
```

Execution requirement:

```text
Run:
npm install
npm run build
npm run test
npm run smoke
```

The smoke test must use real `codex app-server` and must not skip if app-server is missing.

Final output format:

```yaml
result: PASS | BLOCK
project_path: ...
validation:
  schema_generation: PASS | FAIL
  build: PASS | FAIL
  unit_tests: PASS | FAIL
  smoke: PASS | FAIL
boundaries:
  workspace_agents_api: NOT_USED
  responses_api: NOT_USED
  browser_automation: NOT_USED
  websocket: NOT_USED
  thread_shell_command: NOT_USED
  command_exec: NOT_USED
  full_access: NOT_USED
  real_repo_access: NOT_USED
artifacts:
  job_json: ...
  events_jsonl: ...
  receipt: ...
findings:
  - ...
next_recommended_step:
  - ...
```
