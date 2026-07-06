# Life Core Policy Module: Cockpit Cards

Policy ID: `life-core.cockpit-cards.v0.1`
Status: `current_interface_policy`
Source anchor: `agents-os-life-core-v0.1.local-mirror.md` section 9
Local scope: Cockpit, data cards, interface-facing AGENTS OS state

## Purpose

Make the home visible without turning Cockpit into a control panel that claims
more truth or permission than the sources allow.

## Minimum Cards

- HouseStatusCard
- CurrentThreadCard
- ActiveAgentCard
- CouncilItemCard
- ActivationRequestCard
- RiskSignalCard
- NextStepCard

## Executable Rules

- Cards must trace back to sources.
- Cards cannot masquerade as truth.
- Memory candidates cannot display as community conclusions.
- Dangerous buttons must bind to Activation.
- Agent states are member states, not resource scheduling.

## Hard Denials

- Do not expose secrets, private memory, or provider raw response through cards.
- Do not turn Cockpit controls into hidden runtime execution.

## Receipt Rule

New or changed cards should state source, status semantics, and any permission
or activation gate they depend on.
