# Templates Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record separates ordinary templates, `.env` example templates,
and security templates from the Windows reference root. It does not authorize
copying, moving, deleting, executing, pushing, syncing, or changing source
assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Template target placement and handling |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source area reviewed | `A:\AGENTS_OS_Workspace\templates` |
| Assets included | `README.AGENTS_OS.md`, `README.template.md`, `SECURITY.template.md`, `config.env.example.template`, `jenn-extension.manifest.example.json` |
| Assets excluded | Runtime templates, private state, real `.env` files, scripts, prompts |
| Evidence used | Source file content read, WSL target directory check, `_DIRECTORY_PRINCIPLES.md`, `extensions/README.md`, `governance/README.md`, Phase 0 inventory, security boundary target decision |
| Migration performed | No |

## Grouping Decision

| Group | Planning target | Handling rule |
| --- | --- | --- |
| Ordinary templates | `control-plane/templates/common/` and `control-plane/templates/extensions/` | May become reusable template assets after placeholder and path review. |
| `.env` example template | `control-plane/templates/env/` | Keep isolated as example-only material; never promote to a real env file. |
| Security template | `control-plane/templates/security/` | Keep as a project/repo template that points to governance security boundaries; do not treat it as authority. |

This is a planning split for the current migration, not a permanent category
system. Future templates should be placed by actual role and risk.

## File Decisions

| Source file | Target for planning | Handling decision | Reason |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | Rewrite or adapt as the template library index. | The file says templates are for README, SECURITY, manifest, and registry entries and must contain placeholders only. It should become target-native documentation. |
| `A:\AGENTS_OS_Workspace\templates\README.template.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md` | Phase 2 migration candidate as an ordinary reusable README template after path/layer wording is updated. | The template is generic and contains no real credentials. It still names old `AGENTS_OS` as a layer option, so it needs WSL wording cleanup. |
| `A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json` | Phase 2 migration candidate as an extension manifest example template after JSON validation against the extension manifest schema. | The file is an example manifest with read-only defaults and blocked release/deploy profiles. It is a template for extension metadata, not an actual extension package. |
| `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template` | Defer copy until placeholder-only review is complete; keep example-only if migrated. | The filename intentionally contains `env` and the content contains `EXAMPLE_TOKEN`. It is not a real secret file, but it must stay isolated and must not be renamed to `.env` or `config.env`. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | Phase 2 migration candidate as a security-document template after alignment with `governance/SECURITY_BOUNDARIES.md`. | The file is a template for project security docs. It is not the canonical workspace security boundary, which belongs under governance. |

## Directory Decisions

| Target directory | Decision | Notes |
| --- | --- | --- |
| `control-plane/templates/` | Create only during a later approved Phase 2 migration patch. | Owns reusable workspace templates. |
| `control-plane/templates/common/` | Use for general project/directory templates. | Current candidate: `README.template.md`. |
| `control-plane/templates/extensions/` | Use for extension manifest or extension package templates. | Current candidate: `jenn-extension.manifest.example.json`. |
| `control-plane/templates/env/` | Use for sanitized env examples only. | Must not contain real `.env`, `config.env`, tokens, or private credential values. |
| `control-plane/templates/security/` | Use for security document templates. | Must reference, not replace, `governance/SECURITY_BOUNDARIES.md`. |
| `extensions/templates/` | Not used for this batch. | `extensions/` is for Jenn-owned extension packages, not generic control-plane templates. |
| `governance/templates/` | Not used for this batch. | The safety boundary authority belongs in governance, but these files are reusable templates. |

## Required Review Before Phase 2 Copy

| Asset | Required review |
| --- | --- |
| `README.AGENTS_OS.md` | Convert to `README.md`; state that templates must contain placeholders only and no real secrets. |
| `README.template.md` | Replace old `AGENTS_OS` layer wording with current WSL layout wording; keep permission defaults conservative. |
| `jenn-extension.manifest.example.json` | Validate JSON syntax; validate against `control-plane/contracts/jenn-extension.manifest.schema.json` after schema migration; keep example URL clearly non-authoritative. |
| `config.env.example.template` | Confirm every value is placeholder/example-only; do not rename to `.env`, `.env.example`, or `config.env` during this phase unless separately approved. |
| `SECURITY.template.md` | Align allowed/forbidden config-file wording with the canonical security boundary decision. |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Put all templates under `extensions/templates/` | Rejected | Only the manifest example is extension-shaped; the library itself is a control-plane reusable asset. |
| Put `SECURITY.template.md` under `governance/` | Rejected | The template supports project docs but is not itself a hard-gate or security authority. |
| Put `config.env.example.template` beside active extension packages | Rejected | Env examples should stay isolated until sanitized and intentionally adopted by a specific project. |
| Rename `config.env.example.template` into an active env filename during migration | Rejected | This would blur example-only material with real local configuration. |
| Treat `jenn-extension.manifest.example.json` as a real manifest | Rejected | It is explicitly an example and uses placeholder repository data. |

## Phase 2 Stop Conditions

- Do not copy any real `.env`, `.env.*`, `config.env`, token, key, credential,
  or private auth file.
- Do not convert the env example template into active local configuration.
- Do not treat a template as an authorization, permission grant, or security
  boundary.
- Do not create target directories or copy files until Phase 2.
- Do not migrate a template into a specific repo or extension package without a
  separate scoped decision for that target.

## Related Documents

- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `workspace-registry-security-boundaries-targets-2026-06-27.md`
- `control-plane-assets-targets-2026-06-27.md`
- `runbooks-targets-2026-06-27.md`
