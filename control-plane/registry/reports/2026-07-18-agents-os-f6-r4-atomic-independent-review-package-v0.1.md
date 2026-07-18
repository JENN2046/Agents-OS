# AGENTS OS F6 R4 Fresh Full Atomic Independent Review Package v0.1

Review unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R4_ATOMIC_BUNDLE`

Manifest SHA-256:

```text
22396132777538619620c6e1e5ceb4b03338d08b9792c60c266a6d744721bb93
```

This is one indivisible 16-subject unit: R1 four subjects, R2 four subjects,
R3 four subjects and R4 four subjects. Partial review is forbidden. Precedence
is R4 explicit replacements, then R3, R2 and R1 for all remaining clauses.

The reviewer must independently verify all 49 declared input hashes, read all
16 subjects, all 32 authority inputs and the one non-independent author review,
then execute all eight fixed commands from the Manifest.

R4 is limited to five findings:

1. exact Task identity across F1 assessment, Requirement, Validation Set,
   attempt and completion;
2. every consumer revision equals its resolved assessment revision;
3. waiver currentness is derived from TrustedTime;
4. evidence binds exact Requirement revision, attempt context and F3 evidence
   assessment;
5. strict attempt-predecessor and carry-source Event ordering.

The reviewer must not rely only on the fixed validator. It must independently
construct fully re-signed, cross-object synthetic consistency cases and confirm
that rejection is caused by the intended R4 semantic rule rather than an old
fingerprint, an unpropagated reference or an exception.

Allowed results are only `PASS_NO_BLOCKER` or `BLOCK`.

Author validation currently claims:

```yaml
fixed_negative_total: 62/62_REJECTED
R2_coordinated_cases: 17/17_REJECTED
R3_independent_cases: 7/7_REJECTED
case_exceptions: 0
builder_byte_reproduction: PASS
real_occurrences: 0
```

This author claim does not accept or freeze F6. No F7, implementation, runtime,
database, provider, production authentication, Git delivery or real effect is
authorized.

