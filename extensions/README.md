# extensions

Purpose:
- Jenn-owned external extensions.

Allowed:
- Jenn extension packages
- extension manifests
- extension contracts
- extension security docs

Required per extension:
- jenn-extension.manifest.json
- README.AGENTS_OS.md
- SECURITY.md
- CONTRACT.md

Denied:
- core upstream code copies unless explicitly justified
- secrets
- private state

Agent policy:
- read allowed by default
- write only with explicit task scope
