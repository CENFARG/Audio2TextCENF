export type WSEventHandler = (event: MessageEvent) => void;

export function createReconnectingWS(
  url: string,
  onMessage: WSEventHandler,
  maxRetries = 3,
): { ws: WebSocket; close: () => void } {
  let retries = 0;
  let ws: WebSocket;

  function connect() {
    ws = new WebSocket(url);
    ws.onmessage = onMessage;
    ws.onclose = () => {
      if (retries < maxRetries) {
        retries++;
        const delay = Math.pow(2, retries) * 1000;
        setTimeout(connect, delay);
      }
    };
  }

  connect();

  return {
    get ws() { return ws; },
    close: () => ws.close(),
  };
}