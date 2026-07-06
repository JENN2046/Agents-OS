# AGENTS OS Workspace Root Policy

Canonical development root:

/home/jenn/AGENTS_OS_Workspace

Rules:
- Core repositories live inside the WSL Linux filesystem.
- Windows A:\AGENTS_OS_Workspace is archive / asset / evidence storage, not canonical execution root.
- Agent runners, Codex tasks, tests, Docker, databases, and validation scripts run from Linux paths.
- state-private is denied by default.
- archive is historical read-only reference by default.
- Do not blindly copy node_modules, .venv, dist, build, cache, logs, secrets, or tokens from Windows.
