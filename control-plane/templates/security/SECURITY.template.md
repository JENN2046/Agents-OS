# Security Template

This is a reusable project/repo security document template.

It is not the canonical workspace security-boundary authority.

Canonical authority:

```text
governance/SECURITY_BOUNDARIES.md
```

If this template conflicts with the canonical authority, the canonical
authority wins.

## Default Mode

```text
read-only unless explicitly authorized
```

## Forbidden By Default

```text
secret reading
secret printing
git push
release
deploy
arbitrary shell
destructive delete
self-expansion of permissions
```

For the complete hard-stop list, use:

```text
governance/SECURITY_BOUNDARIES.md
```

## Allowed Config Examples

These are example/template patterns only. They do not authorize active local
configuration files or real secret values.

```text
.env.example
config.env.example
*.template
*.example
```

## Forbidden Config And Secret Material

```text
.env
.env.*
config.env
tokens
API keys
private credentials
```

For the full protected file list, use:

```text
governance/SECURITY_BOUNDARIES.md
```

## Private State

Private state is governed by:

```text
governance/SECURITY_BOUNDARIES.md
```

Do not copy private state, private memory, local audit traces, or project data
into a public template.

## High-Risk Areas

Do not duplicate the full high-risk path list in this template.

Use the canonical authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Approval

High-risk actions require explicit approval and receipt.
