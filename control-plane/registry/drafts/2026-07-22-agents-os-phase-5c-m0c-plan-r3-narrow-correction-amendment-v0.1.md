# Phase 5C M0-C Plan R3 Narrow Correction Amendment v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW

## Authority and immutability

R3 is authorized by
`JENN_EXPLICIT_PHASE_5C_M0C_PLAN_R3_START_DECISION` and may close only
`PHASE5C_M0C_PLAN_R2_IR_B01`, `B02`, and `B03`. R1 and R2 subjects,
manifests, author evidence, independent reviews, dispositions, and fixed
commits remain immutable historical bytes.

## Exact correction surface

1. The normative profile, builder, fixture, and validator use one eleven-field
   `member_manifest` projection. It covers member identity and every normalized
   ustar metadata field that affects emitted archive bytes.
2. The synthetic witness now executes success, failure, cleanup-residue, and
   wrong-return probes in a newly created owned temporary root. It records only
   normalized inventories and byte-bound outputs, then removes the root before
   return. It never emits the volatile host path.
3. The R3 ZIP is built from the manifest's complete input list. It includes the
   R1 validator and R1 fixture required by inherited fixed command 5, so every
   declared command runs from an extracted no-Git archive.

## Non-expansion boundary

The temporary-root exercise is an offline synthetic proof only. R3 does not
build, install, enable, load, or run a plugin; modify extension source;
access VCPToolBox; create a database; access private Memory; call a provider;
perform production authentication; sense, record, or cause a real effect.

R3 creates no new permission, identity, Task, Command, plugin-loader, service,
or effect authority. It ends at a fresh full atomic independent review and does
not authorize plan freeze, implementation, Git delivery, or a later phase.
