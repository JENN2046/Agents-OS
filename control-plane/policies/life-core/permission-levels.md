# Life Core Policy Module: Permission Levels

Policy ID: `life-core.permission-levels.v0.2`
Status: `current_permission_model`
Source anchor: `agents-os-life-core-v0.1.local-mirror.md` section 6
Local scope: action classification and permission routing

## One-Line Model

Jenn defines boundaries. Agent walks inside the boundary. Gates watch
exceptions. Receipts leave footprints.

## Levels

- `A0`: see/read, excluding secrets, private memory, customer data, and
  unauthorized accounts.
- `A1`: light self maintenance, self memory, drafts, suggestions, and
  non-official updates.
- `A2`: home maintenance with log, receipt, and reviewability.
- `A3a`: low-impact real action under valid Standing Authorization, receipt,
  and reversible scope.
- `A3b`: medium-impact real action under item-by-item trial authorization.
- `A3c`: high-impact action with full Activation Package, Project Gate, Memory
  Gate, Review Gate, Jenn final confirmation, and full receipt.
- `A4`: forbidden or quarantine. Proposal path only.

## Executable Rules

- Classify the action before acting.
- If the action crosses external, runtime, provider, money, deploy, release,
  database, browser-login, destructive, secret, private-memory, identity,
  relation, house-rule, or life-core boundary, do not classify it as ordinary
  A2.
- A2 requires local scope, reversibility, no secret/private data, and a receipt.
- A3a requires a currently valid standing authorization and receipt.
- A3b, A3c, and A4 require their stated higher gates.

## Hard Denials

- Do not self-escalate permission.
- Do not treat capability existence as permission.
- Do not treat local file access as authorization to read secrets or private
  memory.

## Receipt Rule

Every A2 or higher action must leave enough evidence for later Review.
