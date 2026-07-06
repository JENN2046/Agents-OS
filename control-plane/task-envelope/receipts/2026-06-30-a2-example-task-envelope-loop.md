# A2 Control-Plane Receipt: Example Task Envelope Loop

Receipt ID: `a2-example-task-envelope-loop-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/task-envelope/`

## Action

Filled the first real AGENTS OS task envelope example and ran a small local
loop around it.

## Why This Is A2

- The action is local to `control-plane/task-envelope/`.
- It creates one example, updates the local README, and leaves evidence.
- It does not write to external systems.
- It does not execute runtime/provider/plugin calls.
- It does not read secrets, private memory, or provider raw responses.
- It does not register formal Memory.

## Files Added

- `examples/2026-06-30-example-local-task-envelope-loop.md`
- `receipts/2026-06-30-a2-example-task-envelope-loop.md`
- `reviews/2026-06-30-a2-example-task-envelope-loop.review.md`

## Files Updated

- `README.md`

## Validation Plan

- Confirm the example file exists.
- Confirm README points to `examples/`.
- Confirm receipt and review files exist.
- Confirm the example includes stage, color-zone, router precheck, automation,
  evidence, validation, final status, and plain-language recap.
- Run the life-core policy-router fixture tests.

## Result

Validated locally after creation:

- Example file exists.
- Receipt file exists.
- Review file exists.
- README points to `examples/2026-06-30-example-local-task-envelope-loop.md`.
- The example contains task description, stage, color-zone, policy-router
  precheck, automation decision, steps, evidence, validation, final status, and
  plain-language recap.
- The example records `decision: allowed` and `permission: A2`.
- The example final status is `已完成`.
- `test-policy-router.py` passed: 17 cases, 0 failures.

## Continuation

`COMPLETED`
