# Life Core Policy Router

Router ID: `life-core.policy-router.v0.1`
Status: `local_read_only_router`
Scope: `control-plane/policies/life-core/`

## Purpose

Classify a proposed action against the local life-core policy modules before
execution.

The router is deliberately small. It reads `policy-router.rules.json` and
`policy-index.json`, matches action text against transparent rules, and returns
a routing decision. It does not execute the action and does not authorize the
action by itself.

Rules may use:

- `terms_any`: at least one listed term must appear.
- `terms_all`: every listed term must appear.
- `terms_all_any`: every group must have at least one matching term.
- `terms_none`: if any listed term appears, the rule does not match.

ASCII terms use word-boundary matching. CJK or mixed-language terms use
substring matching.

When a strict decision such as `needs_activation`, `blocked`, or
`proposal_only` wins, required modules, evidence, denied boundaries, and next
steps are built only from strict matched rules. Lower-priority `allowed` matches
remain visible in `matched_rules` for audit, but do not dilute the stricter
output.

`needs_classification` is also more cautious than `allowed`. If a yellow-zone
draft/planning rule matches, it wins over plain read-only `allowed` output and
keeps its own evidence requirements.

## Usage

```text
python3 control-plane/policies/life-core/policy-router.py --action "split local life-core policy docs"
```

JSON output:

```text
python3 control-plane/policies/life-core/policy-router.py --action "VCPToolBox real probe" --json
```

## Decisions

- `allowed`: the action appears allowed at the routed permission level, with
  required evidence.
- `blocked`: current life-core policy does not authorize execution.
- `needs_activation`: stop before execution and prepare a higher gate,
  explicit authorization, or Activation package.
- `proposal_only`: A4/P3b-style path. Do not execute; produce only a boundary
  report or proposal.
- `needs_classification`: no rule matched strongly enough. Use manual Review.

## Output Fields

- `decision`
- `permission_level`
- `confidence`
- `reason`
- `required_modules`
- `required_evidence`
- `denied_boundaries`
- `matched_rules`
- `next_steps`
- `warnings`

## Known Limits

- Keyword routing is conservative but not semantic proof.
- The router cannot override Jenn, root `AGENTS.md`, local security boundaries,
  or higher-priority instructions.
- The router cannot grant runtime, provider, external-write, secret, private
  memory, or formal Memory authority.
- If output and a human/Jenn instruction conflict, re-check the applicable
  authority chain before execution.

## Local Examples

Expected A2:

```text
python3 control-plane/policies/life-core/policy-router.py --action "organize local life-core policy modules and receipt"
```

Expected A0:

```text
python3 control-plane/policies/life-core/policy-router.py --action "explain AGENTS OS permission levels from local life-core modules"
```

Expected block:

```text
python3 control-plane/policies/life-core/policy-router.py --action "run VCPToolBox real probe and provider call"
```

Expected proposal-only:

```text
python3 control-plane/policies/life-core/policy-router.py --action "read state-private secrets"
```

## Fixtures

Run the local fixture tests from the workspace root:

```text
python3 control-plane/policies/life-core/test-policy-router.py
```

Fixtures can assert:

- expected decision and permission level
- required or forbidden matched rules
- required or forbidden evidence
- required or forbidden denied boundaries
