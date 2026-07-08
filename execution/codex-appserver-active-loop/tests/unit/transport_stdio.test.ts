import { describe, expect, it } from "vitest";
import { sanitizeStderr } from "../../src/appserver/transport_stdio.js";

describe("stdio transport helpers", () => {
  it("redacts secret-like stderr fragments", () => {
    const sanitized = sanitizeStderr(
      "home=C:\\Users\\617\\.codex token=Bearer abc.def key=sk-proj-secret",
    );

    expect(sanitized).toContain("<REDACTED_CODEX_HOME>");
    expect(sanitized).toContain("Bearer <REDACTED>");
    expect(sanitized).toContain("sk-<REDACTED>");
  });
});
