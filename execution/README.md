# execution

Purpose:
- execution harnesses, workers, provider adapters, and bridges.
- active code must follow the current task boundary; draft and example code
  remain non-authoritative until reviewed.

Allowed:
- harness code
- worker code
- provider adapters
- bridge implementations
- preview-only local control-machine and task-producer skeletons
- preview-only local dashboard summaries and Memory candidates

Denied:
- top-level governance rules
- secrets
- persistent private state
- provider calls unless explicitly authorized by the active task boundary

Agent policy:
- read allowed by default
- write only with explicit task scope
