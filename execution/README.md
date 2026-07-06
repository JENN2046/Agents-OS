# execution

Purpose:
- execution harnesses, workers, provider adapters, and bridges.

Allowed:
- harness code
- worker code
- provider adapters
- bridge implementations

Denied:
- top-level governance rules
- secrets
- persistent private state

Agent policy:
- read allowed by default
- write only with explicit task scope
