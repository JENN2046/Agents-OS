# AGENTS OS Phase 5A M0-A Plan v0.1 R5 Narrow Closure Amendment

Date: 2026-07-19
Status: fixed for fresh full atomic independent review
Owner: Jenn
Agent steward: Nobao

## 1. Atomic precedence

R5 is accepted or rejected only with the full R1–R5 bundle. Partial review is
forbidden. R5 replaces only the clauses explicitly named by its three
correction profiles. Precedence is:

```text
R5 explicit replacements
R4 all other clauses
R3 all other clauses
R2 all other clauses
R1 all other clauses
```

R1–R4 subjects and manifests remain immutable.

## 2. Closed scope

R5 closes exactly the three R4 independent-review blockers:

1. exact F3 ownership Event, READY witness COMMIT and historical incarnation binding;
2. exact F5 stored-first Event and call-authorization provenance;
3. an executable fail-closed future `index.js` AST/dataflow validation contract.

R5 adds no table, state, permission, provider, runtime capability or Phase 5B
semantic. The effective database inventory remains exactly 18 tables.

## 3. F3 executable persistence rule

The startup transaction binds one exact ownership Event tuple:

```text
event_sequence + event_id + event_fingerprint
+ event_kind=RESIDENT_OWNERSHIP_STARTED
+ aggregate_ref=resident_id
+ aggregate_revision=authority_epoch
```

That same tuple is referenced by the new incarnation and authority epoch and is
the transaction Event for the `RECOVERING` fact and current pointer. Every
incarnation may appear in at most one authority epoch for one Resident; reuse
of any historical incarnation is rejected, not only reuse of the immediate
predecessor.

The later `READY` transaction must resolve one exact current
`F3_WITNESS_COMMIT` canonical fact whose logical ID is the Resident, whose
subject is the epoch's witness reservation and whose creation Event is at or
after the ownership Event. It must re-read the same resident, epoch,
incarnation, epoch fingerprint and ownership Event tuple before committing the
`READY` fact and pointer. Missing, substituted, stale or indeterminate witness
evidence fails closed.

## 4. F5 exact stored-first rule

The stored first Event tuple is:

```text
event_sequence + event_id + event_fingerprint
+ event_kind=F5_DISPATCH_ARMED
+ aggregate_ref=intent_id
+ aggregate_revision=attempt_revision
```

It must be the same tuple named by `armed_event_sequence`. The stored call
authorization tuple includes and checks:

```text
fact_kind=F5_CALL_AUTHORIZATION
logical_id=intent_id
fact_ref + fact_revision + fact_fingerprint
subject_ref=attempt_id
subject_revision=attempt_revision
```

First apply stores exactly one of each tuple. Exact replay returns those exact
stored identities and counts while adding zero Events and zero call
authorizations. Counts cannot substitute for identity equality.

## 5. Executable JavaScript proof rule

The R5 validator contains a versioned, closed-subset JavaScript lexer/parser
that constructs a fixed AST for the hash-bound synthetic future `index.js`
wrapper. It accepts only the frozen wrapper grammar and exact source SHA-256.
Unsupported syntax, unknown tokens, parse ambiguity or unknown dataflow returns
`BLOCK`.

The only admitted source-to-sink flow is:

```text
args.commandRef -----------+
args.commandFingerprint ---+--> closed object projection --> nativeFrame
args.payload --------------+                                  |
                                                              v
                                                residentNative.process(nativeFrame)
```

No second formal parameter, `arguments`, rest parameter, alias of context,
closure capture, spread, computed property, helper call, `requestIp`,
`sourceNode`, `signal`, `decryptedAuthCode` or returned/logged context flow is
accepted. The validator command consumes the exact future `index.js` file
bytes; string search alone is not an accepted proof.

## 6. Stop boundary

R5 remains planning evidence only. It does not authorize Rust, JavaScript,
N-API or SQLite implementation, database creation, dependency installation,
VCPToolBox modification/start, plugin enablement, runtime activation,
production authentication, private Memory, sensing, provider calls or effects.

A fresh full atomic independent review must return `PASS_NO_BLOCKER` before a
Jenn plan-freeze decision surface may be prepared. Plan freeze would still not
authorize implementation; implementation requires a second explicit Jenn
decision.
