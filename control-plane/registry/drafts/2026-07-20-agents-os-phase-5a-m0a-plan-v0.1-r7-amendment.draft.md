# AGENTS OS Phase 5A M0-A Plan v0.1 R7 Narrow Closure Amendment

Date: 2026-07-20
Status: fixed for fresh full atomic independent review
Owner: Jenn
Agent steward: Nobao

## 1. Atomic precedence

R7 is reviewed only with the full R1–R7 bundle. Partial review is forbidden.
R7 replaces only clauses explicitly named below:

```text
R7 explicit replacements
R6 all other clauses
R5 all other clauses
R4 all other clauses
R3 all other clauses
R2 all other clauses
R1 all other clauses
```

R1–R6 subjects and manifests remain immutable.

## 2. Closed scope

R7 closes exactly the two R6 independent-review blockers:

1. every effective plan-only boundary field is discovered from the complete
   effective profile set, type checked and required to retain its frozen value;
2. the fixed F3 positive witness begins with immutable `RECOVERING revision 1`
   and atomically appends `READY revision 2` with the exact predecessor.

R7 adds no table, permission, identity, Task, Command, state, provider protocol,
runtime capability, implementation surface or Phase 5B semantic.

## 3. Derived boundary inventory

The R7 builder recursively walks these exact effective sources:

```text
R7 semantic-owner profile
R7 persistence profile
R6 materialization/ABI profile
R6 structured-input-totality profile
R7 boundary-inventory profile
R7 synthetic witness boundary seed
```

The closed boundary key classes are fixed in both the normative boundary
profile and the offline validator. Every occurrence produces a canonical
`source + JSON Pointer + expected type + expected value` row. The sorted row
set has one fixed inventory digest. Missing, additional, renamed, nonboolean,
noninteger, nonterminal or favorable boundary values block before any positive
case is trusted.

No caller-supplied or graph-local rebuilt fingerprint can replace the fixed
validator inventory digest.

## 4. Actual F3 lifecycle transition

The positive prestate contains:

```text
resident identity
authority epoch 1
immutable RESIDENT_LIFECYCLE RECOVERING revision 1
current lifecycle pointer at revision 1
exact current F3_WITNESS_COMMIT bytes and digest
```

Inside one `BEGIN IMMEDIATE` transaction, the consumer re-reads the exact
witness and current RECOVERING fact, then writes:

```text
RESIDENT_READY Event
RESIDENT_LIFECYCLE READY revision 2
predecessor = exact RECOVERING revision 1 tuple
current lifecycle pointer revision 1 -> revision 2
```

The transaction commits all three writes or rolls them all back. An empty
lifecycle history cannot create READY revision 1. A stale pointer, wrong
predecessor, noncanonical RECOVERING bytes, changed witness tuple or duplicate
revision blocks.

## 5. Stop boundary

R7 is planning evidence only. It does not authorize plan freeze,
implementation, dependency installation, a database file, VCPToolBox change or
startup, plugin enablement, runtime activation, production authentication,
provider use, private Memory, sensing or a real effect. A fresh full atomic
independent review must return `PASS_NO_BLOCKER` before Jenn may make a separate
plan-freeze decision.
