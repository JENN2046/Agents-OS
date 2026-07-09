export function assertChannelPolicyOpen(stopReason: string | undefined): void {
  if (stopReason) {
    throw new Error(stopReason);
  }
}

export function classifyChannelFailureResult(stopReason: string | undefined): "BLOCK" | "FAIL" {
  return stopReason ? "BLOCK" : "FAIL";
}
