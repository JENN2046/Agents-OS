# AGENTS OS Phase 5A M0-A Plan v0.1 R8 Narrow Closure Amendment

Date: 2026-07-20
Status: fixed for fresh full atomic independent review
Owner: Jenn
Agent steward: Nobao

## 1. Atomic precedence

R8 is reviewed only with the complete R1–R8 bundle. Partial review is
forbidden. R8 replaces only the clauses explicitly named below:

```text
R8 explicit replacements
R7 all other clauses
R6 all other clauses
R5 all other clauses
R4 all other clauses
R3 all other clauses
R2 all other clauses
R1 all other clauses
```

R1–R7 subjects and manifests remain immutable.

## 2. Closed scope

R8 closes exactly the two R7 independent-review blockers:

1. replace suffix-based boundary-key discovery with a complete recursive
   key-path inventory and exact immutable source commitments;
2. bind the RECOVERING revision 1 fact and current pointer to the exact
   ownership Event sequence before READY revision 2 may commit.

R8 adds no table, permission, identity, Task, Command, lifecycle state,
provider protocol, runtime capability, implementation surface or Phase 5B
semantic.

## 3. Exact closed effective-key contract

Every effective R8 source is covered by one of these closed modes:

```text
content-sealed source
-> exact whole-file SHA-256
+ complete recursive JSON-Pointer key-path inventory

R8 contract profile
-> exact closed object equality in the validator
+ complete recursive JSON-Pointer key-path inventory

synthetic witness boundary
-> exact closed object equality
+ complete recursive JSON-Pointer key-path inventory
```

The inventory covers every mapping key, not only keys whose names match a
suffix. Missing, additional, renamed or reordered source aliases, any changed
source byte, and any changed key path block before a favorable witness can be
trusted. `implementation_frozen: true` is an explicit fixed regression, but the
rule is general and does not depend on `_frozen` or any other spelling.

The R8 builder may derive evidence from the fixed sources. It may not define a
new accepted key, replace a sealed source commitment or turn a rebuilt local
profile into authority.

## 4. Exact inherited ownership-Event binding

The positive F3 prestate reuses the frozen R5 ownership Event tuple:

```text
ownership Event sequence = 1
RECOVERING fact created_event_sequence = 1
RECOVERING current pointer updated_event_sequence = 1
```

Before and inside the `BEGIN IMMEDIATE` transaction, the consumer resolves the
current authority epoch, the exact ownership Event tuple, the RECOVERING fact,
the current pointer and the current witness. Both RECOVERING sequence fields
must equal the ownership Event sequence. Sequence 2 substitution is invalid
even when all local fact and pointer fields are internally consistent.

Only a valid sequence-1 prestate may append:

```text
RESIDENT_READY Event
READY lifecycle revision 2
exact RECOVERING revision 1 predecessor
current pointer revision 1 -> revision 2
```

The Event, fact and pointer commit all-or-zero. Existing predecessor,
canonical-byte, pointer-CAS, duplicate-revision and rollback constraints remain
in force.

## 5. Stop boundary

R8 is planning evidence only. It does not authorize plan freeze,
implementation, dependency installation, a database file, VCPToolBox change or
startup, plugin enablement, runtime activation, production authentication,
provider use, private Memory, sensing or a real effect. A fresh full atomic
independent review must return `PASS_NO_BLOCKER` before Jenn may make a separate
plan-freeze decision.
