import { describe, it, expect } from 'vitest';
import { APIClient } from '../api-client';

describe('APIClient', () => {
  it('connects to default base URL', () => {
    const client = new APIClient();
    expect(client).toBeDefined();
  });

  it('creates WebSocket stream', () => {
    const client = new APIClient();
    const ws = client.connectStream();
    expect(ws).toBeDefined();
    ws.close();
  });
});
