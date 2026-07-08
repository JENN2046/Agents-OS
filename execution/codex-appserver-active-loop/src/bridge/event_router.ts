export interface RoutedEvent {
  readonly type: string;
  readonly at: string;
  readonly payload?: unknown;
}

export function routeEvent(type: string, payload?: unknown): RoutedEvent {
  return {
    type,
    at: new Date().toISOString(),
    payload,
  };
}
