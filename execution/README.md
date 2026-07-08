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
- preview-first local workbench loops, record previews, and explicit local JSON
  record writes that compose existing preview/control components and emit
  candidate-to-NEXT intake proposals
- reviewed candidate-to-NEXT intake apply gates that append only under accepted
  Nobao review, explicit apply mode, safe queue path checks, and P3 guards,
  without queue promotion, route auto-selection, execution, provider,
  external-write, or Memory authorization
- bounded local-safe workbench advance steps that run authorized local
  validation, write replayable cycle and advance records, emit the next step,
  and stop at Jenn/P3/provider/external/runtime boundaries
- read-only workbench status summaries that inspect local advance and goal
  session records, surface the latest execution, verification, record, effects,
  goal state, and next-step state, including route-choice ids and template
  references plus A-E option readiness when applicable, without raw record, raw
  objective, raw confirmation, or raw template output or writes
- live queue status reconciliation that reads the supplied current queue,
  reports whether the live `NOW` item is blocked or ready for run, and flags
  when the latest stored record boundary may be stale after a reviewed queue
  mutation, without raw queue output or writes
- automatic-until-boundary workbench runs that perform bounded local-safe
  advance steps, write records, and stop at review, route-choice, Jenn decision,
  validation failure, or other protected boundaries
- queue-driven continue runs that read the current live `NOW` item, derive the
  internal task intent without raw queue-body output, perform bounded
  local-safe advance steps when the queue is ready, write records, and otherwise
  stop at the live boundary
- explicit continue completion-promotion gates that, only after the current
  continue run passes local validation and stops at queue-proposal review, can
  apply reviewed close-`NOW`/promote-`NEXT` mutation under an allowed queue root,
  without authorizing execution, provider, external-write, runtime/plugin, or
  Memory actions
- bounded queue-driven continue loops that repeat current-`NOW` continue cycles
  up to a max cycle count, optionally applying reviewed completion promotion
  when `NEXT` is available, and stop at boundaries, missing `NEXT`, failures, or
  the cycle limit
- completion audits that map the requested objective chain to concrete
  workbench evidence, including manifest modes, validation fixtures, live queue
  status, records, boundary handling, and dangerous-authorization defaults
- goal-session workbench entries that accept a long-running objective, call the
  automatic-until-boundary run path, write a local goal session record, and
  surface the next boundary without raw objective output
- route-choice confirmation previews that accept exact Jenn route text, build a
  reviewable route adoption bundle, and stop before any queue write, route
  adoption, queue promotion, execution, raw confirmation, or raw template output
- reviewed route-choice apply gates that can append the selected first safe
  package to a supplied queue's NEXT lane only under explicit apply mode,
  accepted review, allowed queue root, and no-P3 guards, without queue
  promotion, execution, provider, external-write, runtime/plugin, or Memory
  authorization
- reviewed NEXT-to-NOW queue promotion apply gates that can promote the first
  NEXT item only under explicit apply mode, accepted Nobao review, allowed
  queue root, exactly-one-NOW checks, and no-P3 guards, without execution,
  provider, external-write, runtime/plugin, or Memory authorization

Denied:
- top-level governance rules
- secrets
- persistent private state
- provider calls unless explicitly authorized by the active task boundary

Agent policy:
- read allowed by default
- write only with explicit task scope
