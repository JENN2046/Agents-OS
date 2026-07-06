# A2 Control-Plane Receipt: Task Envelope Loop Runner v0.1

Receipt ID: `a2-task-envelope-loop-runner-v0.1-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/task-envelope/`

## Action

Created the first local one-command task-envelope loop runner.

The runner reads one task envelope, extracts its policy-router action, runs the
life-core policy router, runs the task-envelope validator, outputs the gate
result, and writes a local receipt.

## Why This Is A2

- The action is local to `control-plane/task-envelope/`.
- The runner only reads local Markdown, JSON, and policy-router files.
- It does not execute the task described in the envelope.
- It does not write to external systems.
- It does not execute runtime/provider/plugin calls.
- It does not read secrets, private memory, or provider raw responses.
- It does not register formal Memory.

## Files Added

- `run-task-envelope-loop.py`
- `test-task-envelope-loop.py`
- `receipts/2026-06-30-a2-task-envelope-loop-runner-v0.1.md`
- `receipts/2026-06-30-task-envelope-loop-2026-06-30-example-local-task-envelope-loop.md`
- `reviews/2026-06-30-a2-task-envelope-loop-runner-v0.1.review.md`

## Files Updated

- `README.md`

## Validation Plan

- Run the loop on the filled example and expect `ALLOW`.
- Run the loop fixture test and expect two passing cases.
- Run the existing task-envelope validator on the filled example and expect
  `PASS`.
- Run the validator on the blank template and expect `FAIL`.
- Run the existing life-core policy-router fixture tests.
- Run Python syntax compilation for the task-envelope scripts.

## Result

The task-envelope system should now have a small local control-plane loop:

```text
task envelope
-> policy-router
-> validator
-> gate result
-> local receipt
```

- Filled example loop result: `ALLOW`.
- Filled example validator result: `PASS`.
- Blank template validator result: `FAIL`, as expected for an unfilled
  template.
- Task-envelope loop fixture tests passed: `cases=3 failures=0`.
- Existing life-core policy-router fixture tests passed: `cases=17 failures=0`.
- Python syntax compilation passed for task-envelope and policy-router scripts.
- Python `__pycache__` files created during syntax compilation were removed
  after validation.

## Continuation

`COMPLETED`
