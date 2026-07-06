# control-plane/contracts

Purpose:
- Define exchange formats between AGENTS OS systems.
- Keep task, permission, audit, memory, receipt, agent-card, and extension
  manifest shapes in one control-plane area.

Contains:
- `jenn-extension.manifest.schema.json`
- Future contract schemas after separate review.
- Contract examples only when they contain no private data.

Must not contain:
- implementation-specific secrets
- live runtime logs
- private memory text
- unvalidated experimental payloads without version

Interfaces:
- input: architecture decisions
- output: JSON schemas and examples
- used_by: codex-router, VCP bridges, Jenn extensions, ops validators

Security boundary:
- Schemas may be public.
- Schemas must not contain real tokens, customer data, or private memory
  samples.

Validation:
- JSON syntax for schema files should be checked before use.
- Future validation references: `validate-no-secrets` and
  `validate-extension-manifests`.
- These validator references are not current runnable commands until the ops
  validation script batch migrates and reviews them.

Owner:
- Human owner: Jenn
- Agent owner: Review Agent
- Review required: yes for breaking schema changes
