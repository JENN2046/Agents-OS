import { describe, expect, it } from "vitest";
import { createStdioTransport, defaultAppServerCommand, sanitizeStderr } from "../../src/appserver/transport_stdio.js";

describe("stdio transport helpers", () => {
  it("defaults to direct codex app-server stdio on Unix platforms", () => {
    expect(defaultAppServerCommand("linux")).toEqual({ command: "codex", args: ["app-server", "--stdio"] });
    expect(defaultAppServerCommand("darwin")).toEqual({ command: "codex", args: ["app-server", "--stdio"] });
  });

  it("keeps the Windows shell wrapper only on Windows", () => {
    expect(defaultAppServerCommand("win32")).toEqual({
      command: "cmd.exe",
      args: ["/d", "/s", "/c", "codex app-server --stdio"],
    });
  });

  it("exposes platform defaults through the created transport options", () => {
    const transport = createStdioTransport({ cwd: "/tmp/synthetic", timeoutMs: 1 });

    expect(transport.options.command).toBe(process.platform === "win32" ? "cmd.exe" : "codex");
  });

  it("redacts secret-like stderr fragments", () => {
    const sanitized = sanitizeStderr(
      "home=C:\\Users\\617\\.codex token=Bearer abc.def key=sk-proj-secret",
    );

    expect(sanitized).toContain("<REDACTED_CODEX_HOME>");
    expect(sanitized).toContain("Bearer <REDACTED>");
    expect(sanitized).toContain("sk-<REDACTED>");
  });
});
