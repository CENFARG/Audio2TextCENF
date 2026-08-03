import { describe, it, expect, vi } from 'vitest';
import { createReconnectingWS } from '../ws-reconnect';

describe('ws-reconnect', () => {
  it('creates a WebSocket connection', () => {
    const handler = vi.fn();
    const { ws } = createReconnectingWS('ws://localhost:9999/test', handler, 1);
    expect(ws).toBeDefined();
    expect(ws.readyState).toBe(WebSocket.CONNECTING);
    ws.close();
  });
});
