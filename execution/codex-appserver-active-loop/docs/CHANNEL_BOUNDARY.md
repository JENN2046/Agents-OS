# Channel Boundary

CEA-027 freezes the Codex-to-Codex channel boundary. CEA-028 freezes the
current channel line as complete for a minimal communication channel.

The Codex-to-Codex Message Bus is a minimal communication channel. It only
transmits, routes, correlates, and records messages. It does not implement
governance, role authority, workspace policy, or AGENTS.md interpretation.

## Message Bus Owns

- envelope validation
- delivery integrity state
- reply correlation
- TTL / timeout
- max-round guard
- append-only message log

## Router / Registry Owns

- registered routing identity lookup
- active target thread check
- delivery routing between registered active thread identities

## Message Bus Does Not Own

- role duties
- role authority
- Commander authority
- workspace permissions
- real repo access
- write permissions
- commit / push / deploy / release policy
- secrets policy
- AGENTS.md content

## Delegation

AGENTS.md owns project role authority and workspace policy.

Codex runtime executes work according to AGENTS.md, current working context, and
active sandbox / approval settings.

Bridge observes, routes, correlates, and records evidence.

Human / project owner owns boundary changes.

Thread roles are routing identities. Labels such as `worker`, `reviewer`,
`verifier`, `planner`, `executor`, `auditor`, and `critic` do not grant
authority by themselves.

The message bus must not decide whether a role can approve, write, read real
repositories, access secrets, commit, push, deploy, or release.

## CEA-028 Channel Freeze And Closeout

- CEA-023 proved single-turn communication.
- CEA-024 hardened delivery integrity.
- CEA-025 proved multi-turn communication.
- CEA-026 proved multi-role routing identities.
- CEA-027 froze channel minimalism and AGENTS.md delegation.
- CEA-028 freezes the communication channel as complete for the current line.

Message Bus transmits information.
It does not interpret authority.
