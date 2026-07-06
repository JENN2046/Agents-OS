# control-plane

Purpose:
- AGENTS OS contracts, schemas, task envelopes, and policies.

Allowed:
- protocol documents
- schemas
- policy files
- root rules

Denied:
- runtime cache
- secrets
- private state
- generated build output

Agent policy:
- read allowed by default
- write only with explicit task scope
