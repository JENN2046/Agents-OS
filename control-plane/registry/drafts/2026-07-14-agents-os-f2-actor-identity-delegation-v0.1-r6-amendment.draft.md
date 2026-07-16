# AGENTS OS F2 Actor Identity and Delegation v0.1 R6 Final Number Admission Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R6_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r6
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and exact precedence

R6 resolves only `F2-R5-IR-B01`: the contradictory R5 admission rules for a
`context_revision` whose original JSON number token is rounded during binary64
parsing, and for negative zero.

The fixed R1-R5 subjects remain unchanged:

```text
R1 639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
R2 8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
R3 d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
R4 a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
R5 cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
```

R1 through R6 form one indivisible acceptance unit. R6 replaces only R5
Section 4.2 `context_revision`, the corresponding `context_revision` fixtures
in R5 Section 5, the R5 disposition of BindingScope scalar admission, and the
R5 atomic acceptance clause. Every other R1-R5 rule remains unchanged.

## 2. Parsed-number admission domain

`context_revision` validation operates on the already-parsed JSON data-model
value. Its normative numeric domain is ECMAScript `Number`, the IEEE 754
binary64 value model required by RFC 8785 JSON Canonicalization Scheme.

The original JSON number token is not retained, compared, or validated as an
exact decimal. Lexically different valid JSON number tokens that parse to the
same binary64 value are the same input value for this contract. RFC 8785 JCS
serializes that parsed value; it does not reconstruct or preserve its source
token.

This choice is deliberate. F2 does not introduce an exact-decimal data model or
a token-preserving JSON parser solely for `BindingScope`.

## 3. Precedence-complete JCS_SAFE_UINT rule

After standards-compliant JSON parsing to an ECMAScript `Number`, admission is
exactly:

```javascript
Number.isSafeInteger(value) && value >= 0 && !Object.is(value, -0)
```

This predicate is the complete rule. Descriptive terms such as integer,
fractional, negative, exponent, and boundary are interpreted only through the
parsed binary64 result and this predicate.

Consequently:

```text
minimum admitted parsed value = +0
maximum admitted parsed value = 9007199254740991 (2^53 - 1)
-0 is rejected even though Number.isSafeInteger(-0) is true
negative parsed values are rejected
parsed non-integers are rejected
parsed integers outside the safe-integer range are rejected
JSON strings, booleans, objects, arrays, and null are rejected by type
NaN and infinities are outside the RFC 8785 input domain and are never admissible;
  this also rejects a syntactically valid JSON number token such as 1e309 when
  its ECMAScript Number parse result is non-finite
```

A source token containing a decimal point or exponent is not rejected merely
because of its lexical form. It is admitted when its parsed binary64 value
satisfies the exact predicate. A source token that loses information during
binary64 parsing is judged solely by the resulting parsed value.

Examples:

| JSON source token | Parsed ECMAScript Number | Result |
|---|---:|---|
| `0` | `+0` | accept |
| `-0` | `-0` | reject |
| `1e3` | `1000` | accept |
| `1.5` | `1.5` | reject |
| `9007199254740990.5` | `9007199254740990` | accept |
| `9007199254740991` | `9007199254740991` | accept |
| `9007199254740991.5` | `9007199254740992` | reject |
| `9007199254740992` | `9007199254740992` | reject |

The rounded-fraction examples are conformance requirements for an ECMAScript
compatible binary64 parser. A writer must not apply exact-decimal rejection
before or after this parsed-value predicate.

## 4. Canonical insertion and comparison

An admitted `context_revision` is inserted into the R4
`binding_scope_fingerprint` tuple as the RFC 8785 JCS serialization of the
parsed binary64 number. Sorting uses the admitted parsed numeric value.

Thus `1e3`, `1000`, and `1000.0` produce the same JCS number `1000`, compare
equal, and participate in duplicate normalized tuple rejection as the same
revision value. Source spelling is never inserted into a fingerprint.

No legacy value is silently converted during startup recovery. Recovery parses
the persisted JSON number, applies the exact Section 3 predicate including the
negative-zero check, recomputes the owning fingerprint from the admitted parsed
value, and rejects or yields the owning reducer's `INDETERMINATE` on mismatch.

## 5. Mandatory boundary fixtures

A future authorized implementation must test the exact predicate and JCS
insertion with at least these positive fixtures:

```text
0 -> +0 -> JCS 0
1 -> 1 -> JCS 1
1e3 -> 1000 -> JCS 1000
1000.0 -> 1000 -> JCS 1000
9007199254740990.5 -> 9007199254740990 -> JCS 9007199254740990
9007199254740990 -> 9007199254740990
9007199254740991 -> 9007199254740991
```

Negative fixtures must reject:

```text
-0
-1
1.5
9007199254740991.5 after parsing to 9007199254740992
9007199254740992
1e309 or any non-finite parser result
string, boolean, object, array, or null
```

At least two independent implementations must produce the same admission,
sorting, duplicate detection, JCS bytes, and
`binding_scope_fingerprint` for every fixture. Test harnesses may retain source
tokens to prove parser behavior; canonical contract state does not retain them.

## 6. Finding disposition and non-authorization

| Finding | R6 disposition |
|---|---|
| `F2-R5-IR-B01` | resolved by Sections 2-5 |
| `F2-R4-IR-B02` | fully resolved only if an independent R6 review confirms `F2-R5-IR-B01` closure |

R6 changes no digest scalar, fingerprint domain tag, subject projection,
action-ref binding, identity fact, delegation responsibility, prohibited
boundary, or F3 ownership rule.

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R6_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - F2_R3_amendment_sha256_d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
  - F2_R4_amendment_sha256_a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
  - F2_R5_amendment_sha256_cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
  - this_exact_R6_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R6 does not implement a parser, encoder, runtime, database, authenticator,
permit issuer, host integration, service, migration, or provider call. It does
not accept F2 and does not start F3.
