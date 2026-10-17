import { buildMemorySearchArgs } from "./search-parameters.mjs";

const RESERVED_MARKERS = [
  "<<<[TOOL_REQUEST]>>>",
  "<<<[END_TOOL_REQUEST]>>>",
  "「始」",
  "「末」",
];

// The native parser can enable fuzzy markers without restarting the wrapper.
// Reject its complete marker families even while native fuzzy mode is off.
const NATIVE_MARKER_PATTERNS = [
  /<{2,4}\[(?:END_)?TOOL_REQUEST\]>{2,4}/i,
  /[「{][始末](?!ESCAPE)[^\r\n「{]*?[」}]/,
  /[「{][始末]ESCAPE[」}]/i,
];
const RESERVED_PARAMETER_NAMES = new Set([
  "tool_name", "archery", "ink", "river", "vref", "__proto__",
]);

function stringifyToolValue(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function assertSafeValue(value, label) {
  const text = stringifyToolValue(value);
  if (typeof text !== "string") {
    throw new Error(`${label} cannot be encoded`);
  }
  for (const marker of RESERVED_MARKERS) {
    if (text.includes(marker)) {
      throw new Error(`${label} contains reserved VCP framing marker: ${marker}`);
    }
  }
  if (NATIVE_MARKER_PATTERNS.some((pattern) => pattern.test(text))) {
    throw new Error(`${label} contains a reserved VCP framing marker variant`);
  }
  return text;
}

export function encodeVcpToolRequest(toolName, args = {}) {
  if (typeof toolName !== "string") throw new Error("tool_name must be a string");
  if (!args || typeof args !== "object" || Array.isArray(args)) {
    throw new Error("VCP arguments must be an object");
  }
  const safeToolName = assertSafeValue(toolName, "tool_name").trim();
  if (!safeToolName) throw new Error("tool_name cannot be empty");

  const lines = [`tool_name:「始」${safeToolName}「末」`];

  for (const [key, value] of Object.entries(args)) {
    if (value === undefined) continue;
    // Native _scanFields accepts only word characters. Dotted/hyphenated
    // names are parsed as suffix fields and can become a second tool_name.
    if (!/^[A-Za-z0-9_]+$/.test(key)) {
      throw new Error(`Invalid VCP parameter name: ${key}`);
    }
    if (RESERVED_PARAMETER_NAMES.has(key)) {
      throw new Error(`Reserved VCP parameter name: ${key}`);
    }
    lines.push(`${key}:「始」${assertSafeValue(value, key)}「末」`);
  }

  return [
    "<<<[TOOL_REQUEST]>>>",
    lines.join(",\n"),
    "<<<[END_TOOL_REQUEST]>>>",
  ].join("\n");
}

export class VcpHttpError extends Error {
  constructor(message, { status, body, path } = {}) {
    super(message);
    this.name = "VcpHttpError";
    this.status = status;
    this.body = body;
    this.path = path;
  }
}

// HTTP success is not proof that a native action succeeded. Inspect only the
// native envelope and its immediate result, never arbitrary content strings.
export function describeNativeToolOutcome(data) {
  const result = data?.result ?? data;
  if (data === null || data === undefined || data === "") {
    return { ok: false, result: null, code: "VCP_NATIVE_OUTCOME_UNKNOWN",
      message: "VCP returned no tool outcome. Completion is unknown; verify state before retrying." };
  }
  const failed = [data, result].some((value) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const status = typeof value.status === "string" ? value.status.toLowerCase() : "";
    return ["error", "failed", "failure", "rejected"].includes(status) ||
      value.isError === true || value.success === false || value.ok === false ||
      value.error_type === "approval_rejected" || !!value.plugin_error || !!value.plugin_execution_error ||
      (status !== "success" && value.success !== true && value.ok !== true && !!value.error);
  });
  return failed
    ? { ok: false, result: data, code: "VCP_NATIVE_TOOL_FAILED", message: "VCP reported a failed or rejected tool action. See the native result; do not automatically retry." }
    : { ok: true, result };
}

export class VcpClient {
  constructor({
    baseUrl = "http://127.0.0.1:6005",
    apiKey,
    timeoutMs = 120000,
    chatPath = "/v1/chat/completions",
    defaultModel = "",
    systemPrompt = "",
  } = {}) {
    this.baseUrl = String(baseUrl).replace(/\/+$/, "");
    this.apiKey = String(apiKey || "");
    this.timeoutMs = Number(timeoutMs) || 120000;
    this.defaultModel = String(defaultModel || "");
    this.systemPrompt = String(systemPrompt || "");

    const allowedChatPaths = new Set([
      "/v1/chat/completions",
      "/v1/chatvcp/completions",
    ]);
    if (!allowedChatPaths.has(chatPath)) {
      throw new Error(`Unsupported VCP_CHAT_PATH: ${chatPath}`);
    }
    this.chatPath = chatPath;
  }

  requireKey() {
    if (!this.apiKey) {
      throw new Error("VCP_API_KEY is required");
    }
  }

  async request(path, {
    method = "GET",
    contentType,
    body,
    accept = "application/json",
  } = {}) {
    this.requireKey();

    const headers = {
      Authorization: `Bearer ${this.apiKey}`,
      Accept: accept,
    };
    if (contentType) headers["Content-Type"] = contentType;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers,
        body,
        signal: controller.signal,
      });

      const raw = await response.text();
      let parsed = raw;
      if (raw) {
        try {
          parsed = JSON.parse(raw);
        } catch {
          // Keep text response.
        }
      } else {
        parsed = null;
      }

      if (!response.ok) {
        throw new VcpHttpError(`VCP HTTP ${response.status} on ${path}`, {
          status: response.status,
          body: parsed,
          path,
        });
      }
      return parsed;
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new VcpHttpError(`VCP request timed out after ${this.timeoutMs}ms`, {
          path,
        });
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  async listModels() {
    return this.request("/v1/models");
  }

  async callTool(toolName, args = {}) {
    const requestText = encodeVcpToolRequest(toolName, args);
    return this.request("/v1/human/tool", {
      method: "POST",
      contentType: "text/plain; charset=utf-8",
      body: requestText,
    });
  }

  async memorySearch(input) {
    return this.callTool("LightMemo", buildMemorySearchArgs(input));
  }

  async memoryCreate({
    date,
    content,
    maid,
    folder,
    fileName,
    tag,
  }) {
    const args = {
      command: "create",
      maid,
      Date: date,
      Content: content,
    };
    if (folder) args.folder = folder;
    if (fileName) args.fileName = fileName;
    if (tag) args.Tag = tag;
    return this.callTool("DailyNote", args);
  }

  async memoryUpdate({ maid, folder, target, replace }) {
    return this.callTool("DailyNote", {
      command: "update",
      maid,
      folder,
      target,
      replace,
    });
  }

  async chat({
    prompt,
    model,
    system = "",
    temperature,
  }) {
    const selectedModel = String(model || this.defaultModel || "").trim();
    if (!selectedModel) {
      throw new Error("No VCP model supplied. Pass model or set VCP_DEFAULT_MODEL.");
    }

    const messages = [];
    const combinedSystem = [this.systemPrompt, system]
      .map((item) => String(item || "").trim())
      .filter(Boolean)
      .join("\n\n");

    if (combinedSystem) {
      messages.push({ role: "system", content: combinedSystem });
    }
    messages.push({ role: "user", content: prompt });

    const body = {
      model: selectedModel,
      messages,
      stream: false,
    };
    if (temperature !== undefined) body.temperature = temperature;

    return this.request(this.chatPath, {
      method: "POST",
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  }
}
