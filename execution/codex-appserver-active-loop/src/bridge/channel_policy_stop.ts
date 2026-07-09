export function assertChannelPolicyOpen(stopReason: string | undefined): void {
  if (stopReason) {
    throw new Error(stopReason);
  }
}
