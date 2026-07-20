# AGENTS OS Phase 5A M0-A Plan v0.1 R3 Narrow Closure Amendment

Status: fixed for fresh full atomic independent review
Runtime usable: no
Implementation authorized: no

## 1. Precedence and scope

R3 closes only the three blockers in the R2 fresh independent review. R1 and
R2 subjects and manifests remain immutable. Effective precedence is:

```text
R3 explicit replacements
→ R2 all other clauses
→ R1 all other clauses
```

R3 replaces affected owner rows, affected SQLite table definitions and
transactions, the installed-tree digest scope, and the direct module ABI. It
does not add a capability, authority, N-API method, runtime or implementation.

## 2. One admitted-command transaction

For an admitted synthetic M0-A Command, exactly one `BEGIN IMMEDIATE`
transaction owns all of:

```text
Inbox state
Command Envelope
canonical facts
Current State pointer CAS
Event
replay result
ledger-only outbox intent, when derived
```

No successful subset may commit. The transaction's internal write order is
fixed by the R3 persistence profile and includes the inherited crash injection
point `after_pointer_CAS_before_Event`. All Event foreign keys used before the
Event insert are `DEFERRABLE INITIALLY DEFERRED`; constraints must be satisfied
at commit or the complete transaction rolls back.

## 3. F3 lifecycle

`resident_incarnation` is immutable identity/provenance only. It no longer
stores a mutable or conflicting state enum. Current lifecycle is an immutable
`canonical_fact` of kind `RESIDENT_LIFECYCLE` plus an exact
`current_fact_pointer` and uses only:

```text
COLD
RECOVERING
READY
DRAINING
STOPPED
INDETERMINATE
```

Every transition inserts a new contiguous fact revision and Event and advances
the pointer in one transaction. `COMPROMISED` is an authority/assessment result,
not a Resident lifecycle value.

## 4. F5 arm, stored-first and first-apply

First-apply eligibility is acquired in the dispatch-arm transaction before any
physical/mock boundary call and before any receipt exists. `first_apply_guard`
therefore does not reference a future receipt. It binds exact intent and
winning attempt identity and is immutable.

`dispatch_arm` persists and replays the complete stored-first tuple:

```text
first Event ref and fingerprint
first call-authorization ref and fingerprint
committed Event count
committed call-authorization count
exact request ID, fingerprint and canonical bytes
```

An exact duplicate returns this stored tuple with zero additional Event and
zero additional call authorization. A different attempt cannot acquire the
same intent's first-apply guard.

Receipt identity is exactly `(source_id, receipt_id)`. Receipt application
binds the already-acquired guard fingerprint; it never creates first-apply
eligibility retroactively. Claim lease expiry remains UTC time and binds an
immutable `OUTBOX_CLAIM_LEASE` canonical fact.

## 5. F6 lineage and pointer binding

`canonical_fact` enforces one row for `(fact_kind, logical_id, fact_revision)`.
Revision 1 has no predecessor. Revision `n > 1` has exactly predecessor
revision `n-1` with the same kind and logical identity and exact predecessor
ref/fingerprint foreign-key binding.

`current_fact_pointer` binds kind, logical identity, revision, fact ref and fact
fingerprint as one foreign-key tuple. Task completion binds
`completion_fact_kind = TASK_COMPLETION` and
`completion_logical_id = task_ref`. Cross-kind, cross-logical-ID,
same-revision rewrite, branch and revision-gap graphs are invalid.

## 6. Installed-tree digest

`installed_tree_sha256` uses exactly the R2 content-tree leaf encoding, file
mode rules, sort order and exclusion set. Its inventory is the installed copy
of `planned_source_inventory` minus `package-manifest.json`, with the
`Plugin/AGENTSOSResident/` prefix stripped before leaf encoding. It therefore
must equal `content_tree_sha256`.

`package-manifest.json` is verified separately by its exact
`package_manifest_sha256`; it is not part of either compared tree digest.

## 7. VCP direct module ABI

The VCP Plugin manager's outer method is:

```text
processToolCall(toolName, toolArgs, requestIp = null)
```

That is not the plugin module export. The exact direct module ABI is:

```text
async initialize(config, dependencies)
async processToolCall(args)
async shutdown()
```

Only the one `args` value crosses from the manager into `index.js`.
`index.js` converts that JSON-safe value into one of the five closed N-API
request frames. It exports no `processMessages`, provider, network, database or
runtime-start surface.

## 8. Stop rule

Fresh independent review must verify the effective R1+R2+R3 unit. A PASS does
not freeze the plan. Jenn retains the atomic plan-freeze decision, followed by
a separate explicit implementation-start decision. No Rust, JavaScript, N-API,
SQLite or plugin source may be created under this amendment.
