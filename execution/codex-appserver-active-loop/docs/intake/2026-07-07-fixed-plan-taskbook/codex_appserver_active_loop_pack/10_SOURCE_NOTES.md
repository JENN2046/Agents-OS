# Source Notes

Checked: 2026-07-07

Official OpenAI references used while preparing this package:

1. Codex App Server
   https://developers.openai.com/codex/app-server

   Key facts used:
   - Codex App Server is for deep product integrations with authentication, conversation history, approvals, and streamed agent events.
   - It uses JSON-RPC 2.0 style bidirectional communication.
   - `stdio` is the default transport.
   - WebSocket transport is experimental/unsupported and must not be exposed remotely without authentication.
   - App Server can generate TypeScript and JSON Schema artifacts for the installed Codex version.
   - `turn/start` supports `cwd`, `sandboxPolicy`, `approvalPolicy`, and `outputSchema`.
   - `review/start` supports `uncommittedChanges`, `baseBranch`, `commit`, and `custom`; detached review can fork a new review thread.
   - `thread/shellCommand` runs outside the sandbox with full access and must not be used in this MVP.
   - `item/fileChange/requestApproval` is an approval request flow the client must answer.

2. Codex SDK
   https://developers.openai.com/codex/sdk

   Key facts used:
   - Codex SDK is the recommended interface for automating jobs or CI-style usage.
   - Sandbox presets include `read_only`, `workspace_write`, and `full_access`.
   - `full_access` removes filesystem access restrictions and is forbidden in this MVP.

3. Codex overview
   https://developers.openai.com/codex

   Key fact used:
   - ChatGPT Plus, Pro, Business, Edu, and Enterprise plans include Codex.
