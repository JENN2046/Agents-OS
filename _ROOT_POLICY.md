# AGENTS OS Workspace Root Policy

Navigation status (`2026-09-13.1`): [AGENTS.md](AGENTS.md) is the root rule
entry. [WORKSPACE_MAP.md](WORKSPACE_MAP.md) supersedes this file for current
machine lookup. The path statements below describe the documented WSL/Windows
environment, which was not reverified on 2026-09-13. Its private-state and
safe-transfer constraints remain applicable within their existing scope.

Documented WSL development root:

/home/jenn/AGENTS_OS_Workspace

Rules:
- Core repositories live inside the WSL Linux filesystem.
- Windows A:\AGENTS_OS_Workspace is archive / asset / evidence storage, not canonical execution root.
- Agent runners, Codex tasks, tests, Docker, databases, and validation scripts run from Linux paths.
- state-private is denied by default.
- archive is historical read-only reference by default.
- Do not blindly copy node_modules, .venv, dist, build, cache, logs, secrets, or tokens from Windows.
