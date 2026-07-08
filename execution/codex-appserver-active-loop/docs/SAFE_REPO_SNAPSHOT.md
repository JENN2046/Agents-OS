# Safe Repo Snapshot

## Purpose

The safe snapshot exporter provides a bridge-owned isolation layer while Codex App Server generated types do not expose restricted readable roots.

Managed Worker and Reviewer sessions must not point directly at real repositories. The Bridge may read an approved source root through an allowlist, copy only safe files into a generated snapshot, and use that snapshot path as the only managed session `cwd`.

## Rules

- Real source roots are read only by the Bridge exporter.
- Snapshot input is allowlist-based.
- Denylist path checks run before file content is opened or copied.
- `.git`, `node_modules`, `dist`, `state-private`, `.ssh`, `secrets`, `data/tmp`, `data/review-packages`, and `data/snapshots` are excluded.
- `.env`, `config.env`, credential, token, cookie, private key, and key-like paths are excluded.
- Files with sensitive content patterns such as bearer-style credentials, provider credential prefixes, environment credential assignments, authorization headers, password assignments, or private credential markers are excluded.
- Snapshot metadata is written under `_snapshot/`.
- Phase 8 direct real repository review remains `BLOCKED`.

## Artifacts

Each snapshot includes:

- `_snapshot/manifest.json`
- `_snapshot/exclusions.json`

The manifest records source root, snapshot root, Worker cwd, allowlist, included file hashes, exclusions, and boundary flags.

## Managed Session Rule

Worker and Reviewer `cwd` must equal the generated snapshot root. A real repository path is not an acceptable managed session `cwd`.
