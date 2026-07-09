import { describe, expect, it } from "vitest";
import { assertChannelPolicyOpen } from "../../src/bridge/channel_policy_stop.js";

describe("channel policy stop guard", () => {
  it("allows channel work while policy remains open", () => {
    expect(() => assertChannelPolicyOpen(undefined)).not.toThrow();
  });

  it("fails closed with the recorded policy stop reason", () => {
    expect(() => assertChannelPolicyOpen("decline: command execution blocked")).toThrow("decline: command execution blocked");
  });
});
