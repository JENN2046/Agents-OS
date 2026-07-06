# Review: Federated Document Registry Step 4 v0.1

Date: 2026-07-01
Status: reviewed
Scope: `control-plane/registry` Federated Document Registry Step 4

## Review Result

Step 4 is acceptable as a draft/example federation layer.

```text
Federation target: control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
Registries listed: 3
Result: PASS
```

## What Looks Good

- The federation lists directory-owned registries instead of creating one huge
  central document list.
- The validator only checks explicitly listed registries.
- The existing Document Registry validator is reused for child registries.
- Expected document counts catch drift in child registries.
- The design keeps databases/search/vector indexes as future rebuildable caches,
  not source of truth.

## Remaining Risks

- Federation is still draft/example, not active authority.
- Coverage checking is directory-specific; only life-core currently has an
  extra coverage checker.
- Future expansion needs a policy for when a directory is large enough to own
  its own document registry.

## Recommendation

Next step should be a small `Federation Operating Rules` draft before adding
many more directories:

```text
when to create a directory registry
who owns it
what counts as expected document count
when to update federation
when a cache/index is allowed
```
