# Workbench Integration Contract

This component is downstream of AGENTS OS workbench decisions.

Allowed entry:

```text
workbench selector / gate
  -> reviewed task packet
  -> codex-appserver-active-loop
```

Allowed exit:

```text
codex-appserver-active-loop
  -> receipt / review decision / observer summary
  -> ops records
  -> workbench status / selector
```

## Task Packet

A task packet must be explicit and bounded:

- task id
- current goal id or queue item id
- role plan: Worker, Reviewer, Verifier, or a subset
- input snapshot or synthetic workspace path
- permitted files or readable roots
- denied paths and denied actions
- validation command or validation receipt requirement
- stop conditions
- authority flags, all false unless separately authorized

Required false-by-default authority flags:

- `provider_call_authorized`
- `memory_write_authorized`
- `external_write_authorized`
- `queue_mutation_authorized`
- `runtime_plugin_activation_authorized`
- `raw_private_state_authorized`

## Receipt

A receipt returned to AGENTS OS must be evidence-oriented:

- task id
- run id
- source snapshot id or synthetic workspace id
- roles used
- message count
- review decision
- validation result
- stopped boundary, if any
- artifact references
- hashes or character counts instead of raw broad payloads

Minimum schema:

```text
schemas/agents-os/active-loop-receipt.v0.1.schema.json
```

Raw message logs and observer HTML/JSON are local observer artifacts. They must
not become external publication material unless a later exact review approves a
sanitized export.

## Non-Authority

The message bus does not grant authority. A Reviewer or Verifier decision is
evidence for workbench; it is not a gate override.
