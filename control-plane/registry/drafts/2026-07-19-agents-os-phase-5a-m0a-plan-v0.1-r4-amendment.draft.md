# AGENTS OS Phase 5A M0-A Plan v0.1 R4 Narrow Closure Amendment

Date: 2026-07-19
Status: fixed for fresh full atomic independent review
Owner: Jenn
Agent steward: Nobao

## 1. Atomic precedence

R4 is accepted or rejected only with the full R1–R4 bundle. Partial review is
forbidden. R4 replaces only the clauses explicitly named by its three
correction profiles. Precedence is:

```text
R4 explicit replacements
R3 all other clauses
R2 all other clauses
R1 all other clauses
```

R1–R3 subjects and manifests remain immutable.

## 2. Closed scope

R4 closes exactly the three R3 independent-review blockers:

1. F3 incarnation and authority epoch persistence plus transaction ownership;
2. F5 receipt/guard, arm/request, lease-fact and stored-first exact bindings;
3. the real VCP manager-to-module two-value invocation and nonauthority
   `directContext` boundary.

R4 adds no table, state, permission, provider, runtime capability or Phase 5B
semantic. The effective database inventory remains exactly 18 tables.

## 3. F3 persistence rule

One startup transaction must persist the new incarnation, exact next authority
epoch, `RECOVERING` lifecycle fact, current pointer and ownership Event
all-or-zero. The epoch row binds the exact prior epoch fingerprint and its
incarnation. A second transaction may project `READY` only after the frozen F3
witness COMMIT has been durably observed.

Epoch genesis is exactly `1`. Every successor is exactly `N + 1`; gaps, forks,
wrong prior incarnation, missing Event and reused incarnation are rejected by
the effective DDL or the closed transaction precondition.

## 4. F5 exact tuple rule

The following are exact, non-separable tuples:

```text
claim = intent + claim + lease fact kind/logical/ref/revision/fingerprint
attempt = attempt + intent + claim + request ID/fingerprint/canonical bytes
guard = intent + winning attempt + winning claim + guard fingerprint
receipt = source/receipt + exact attempt tuple + exact guard tuple
arm = exact attempt/request tuple + stored-first Event/call authorization
```

The first stored Event count and call-authorization count are each exactly
`1`. Exact replay returns those stored counts and adds zero; zero stored-first
counts are invalid.

## 5. Actual VCP direct-call rule

At fixed VCP commit `555b3b538f6eb736e530c2912de678c5941f9985`, the manager
calls:

```text
serviceModule.processToolCall(pluginSpecificArgs, directContext)
```

The future module may retain one formal business parameter `args`, but it must
explicitly tolerate and ignore the manager's second value. A static dataflow
probe must prove the native request frame depends only on a closed whitelist
projection of `args` and frozen constants. The module body may not read
`arguments`, rest parameters, the second parameter, `requestIp`, `sourceNode`,
`signal`, `decryptedAuthCode` or other context aliases. The blocked plugin
manifest fixes `requiresAdmin=false`.

`directContext` is nonauthority transport context. It cannot enter N-API,
reducers, fingerprints, logs, receipts, errors or output.

## 6. Stop boundary

R4 remains planning evidence only. It does not authorize Rust, JavaScript,
N-API, SQLite implementation, database creation, dependency installation,
VCPToolBox modification/start, plugin enablement, runtime activation,
production authentication, private Memory, sensing, provider calls or effects.

A fresh full atomic independent review must return `PASS_NO_BLOCKER` before a
Jenn plan-freeze decision surface may be prepared. Plan freeze would still not
authorize implementation; implementation requires a second explicit Jenn
decision.
