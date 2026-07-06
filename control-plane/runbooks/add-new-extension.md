# Runbook: Add New Jenn Extension

Status: ordinary runbook guidance. This document is not authorization to
install, activate, release, deploy, or register an extension.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Purpose

Use this runbook to draft and review a new Jenn extension before any activation
or registry change.

## Required Draft Materials

```text
README.AGENTS_OS.md or README.md
SECURITY.md
jenn-extension.manifest.json
config.env.example or another approved example/template config file
```

Config material must remain example-only. Do not create or modify active
`.env`, `.env.*`, `config.env`, token, credential, or private local config
files through this runbook.

## Procedure

1. Choose the intended extension layer and record whether it is verified or
   still a candidate.
2. Draft or update the extension manifest using the current contract schema.
3. Declare requested permissions explicitly.
4. Add installation and usage notes as documentation, not activation.
5. Record validation needs. Validator use requires separate scoped execution
   authorization before any script is run.
6. Complete a no-secret review before any later activation or publication.
7. Prepare registry-entry notes separately. Adding or updating registry entries
   requires separate explicit authorization and a receipt.

## Registry Registration

The authority registry data file exists at:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
```

Adding, changing, or activating extension registry entries remains a separate
controlled patch. This runbook does not authorize registry writes.

Do not write to historical source path:

```text
AGENTS_OS/registry/extensions.yaml
```

Do not treat this example-only file as active registry state:

```text
control-plane/registry/examples/extensions.example.yaml
```

## Default Permissions

```text
read-only
no shell
no git push
no release
no deploy
no secret reading
no private-state reading
```

## Approval

Any permission increase requires review, explicit authorization, and a receipt.
