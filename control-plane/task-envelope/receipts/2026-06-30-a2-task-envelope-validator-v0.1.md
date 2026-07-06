# A2 Control-Plane Receipt: Task Envelope Validator v0.1

Receipt ID: `a2-task-envelope-validator-v0.1-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/task-envelope/`

## Action

Created the first local validator for AGENTS OS task envelopes.

## Why This Is A2

- The action is local to `control-plane/task-envelope/`.
- The validator only reads Markdown and JSON rule files.
- It does not execute task-envelope contents.
- It does not write to external systems.
- It does not execute runtime/provider/plugin calls.
- It does not read secrets, private memory, or provider raw responses.
- It does not register formal Memory.

## Files Added

- `validation-rules.json`
- `validate-task-envelope.py`
- `receipts/2026-06-30-a2-task-envelope-validator-v0.1.md`
- `reviews/2026-06-30-a2-task-envelope-validator-v0.1.review.md`

## Files Updated

- `README.md`

## Validation Plan

- Confirm `validation-rules.json` parses as JSON.
- Run validator on the filled example and expect PASS.
- Run validator on the blank template and expect FAIL.
- Run life-core policy-router fixture tests.

## Result

- `validation-rules.json` parsed successfully.
- Filled example `examples/2026-06-30-example-local-task-envelope-loop.md`
  passed the validator.
- Blank template `agents-os-task-envelope-v0.1.md` failed as expected because
  five required checkbox groups were not selected.
- A false positive around the text fragment `sk-` was corrected by replacing
  the simple marker with a stricter `openai_like_secret_key` pattern.
- Existing life-core policy-router fixture tests passed: `cases=17 failures=0`.

## Continuation

`COMPLETED`
