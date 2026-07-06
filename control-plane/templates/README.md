# control-plane/templates

Purpose:
- Store reusable AGENTS OS templates for ordinary documentation and
  schema-adjacent example assets.
- Keep templates placeholder-only so they can be reused without carrying local
  secrets, runtime state, or project-specific authority.

Template library files:
- `common/README.template.md`
- `env/config.env.example.template`
- `extensions/jenn-extension.manifest.example.json`
- `security/SECURITY.template.md`
- `validation/validation-execution-authorization.template.md`

Deferred template families:
- registry templates
- runbook templates

Rules:
- Templates must contain placeholders or examples only.
- Templates must not contain real secret values, credentials, private memory,
  runtime logs, or active local configuration.
- Templates do not authorize permissions, deployments, releases, pushes, or
  registry changes.
- Validation authorization templates are request/approval forms, not script
  execution instructions.
- Templates do not authorize validation-script execution by themselves.

Validation:
- Review template content before reuse.
- Parse machine-readable examples before adopting them.
- Do not treat validation placeholders as current runnable commands unless the
  referenced scripts are separately migrated and reviewed.
- Do not run validation scripts from a template unless the exact run receives
  separate explicit approval.

Owner:
- Human owner: Jenn
- Agent owner: Review Agent
- Review required: yes for templates that affect permissions, security, env
  handling, validation execution, or extension manifests
