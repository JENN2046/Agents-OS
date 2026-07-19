# AGENTS OS F8 R1 Independent Review

**Result: `BLOCK`**  
**Requires R2: `true`**

## Counts

- Blockers: 4
- Major findings: 2
- Minor findings: 0
- Independent attacks: 23
- Favorable invalid paths: 3

## Blockers

1. **F8-R1-B01 — Internal contradiction**  
   The contract orders the F3 intake results as `COMMITTED, REJECTED, INDETERMINATE`, while the builder, fixture, and validator enforce `COMMITTED, INDETERMINATE, REJECTED`.

2. **F8-R1-B02 — Same-revision assessment rewrite bypass**  
   Consumers bind only assessment ID and revision. Re-signing the stale F7 assessment at the same revision as current/accepted made H10 return `CANDIDATE_FORMED`.

3. **F8-R1-B03 — Acknowledgement currentness bypass**  
   An F3 outcome assessment with `subject_revision=999` and an old watermark still produced `ACKNOWLEDGED_COMMITTED`.

4. **F8-R1-B04 — Schema totality not enforced**  
   A fully re-signed candidate containing integer `created_event_ref=17` passed the semantic validator when fixture anchors were disabled.

## Required R2 changes

- Canonicalize the prospective F3 result ordering across all four subjects.
- Add exact assessment fingerprint/event commitment binding to consumers and candidate assessment sets.
- Close acknowledgement subject revision, context, and watermark validation.
- Implement complete field-level schema validation independent of fixed fixture anchors.
- Include or explicitly supersede the two missing direction inputs.
- Replace the Git-dependent whitespace command with a reproducible package-local check.

The review does not accept or freeze F8 and does not authorize Phase 5A, implementation, runtime, authentication, private-memory access, sensing, provider calls, effects, or Git delivery.
