import { z } from "zod";

export const OperationEnvelope = z.object({
  operation_id: z.string(),
  state: z.enum(["idle", "recording", "processing", "displayed", "failed"]),
  text: z.string(),
  text_sha256: z.string().optional(),
  duration_s: z.number().optional(),
  provider: z.string().optional(),
  error: z.object({ code: z.string(), message: z.string(), recoverable: z.boolean() }).optional(),
});

export type OperationEnvelope = z.infer<typeof OperationEnvelope>;

/** Minimal APIClient — Single Owner contract: Rust is source of truth, HTTP fallback */
export class APIClient {
  private base = "http://127.0.0.1:8765/api/v1";

  async getHistory(): Promise<Array<Record<string, unknown>>> {
    try {
      const res = await fetch(`${this.base}/transcriptions`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : data.items ?? [];
    } catch { return []; }
  }

  async updateTranscription(id: string, patch: Record<string, unknown>): Promise<void> {
    try { await fetch(`${this.base}/transcriptions/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) }); } catch { /* no-op */ }
  }

  async deleteTranscription(id: string): Promise<void> {
    try { await fetch(`${this.base}/transcriptions/${id}`, { method: "DELETE" }); } catch { /* no-op */ }
  }

  async getSettings(): Promise<Record<string, unknown>> {
    try {
      const r = await fetch(`${this.base}/settings`);
      if (!r.ok) return {};
      const data = await r.json().catch(() => ({}));
      // Support both {config:{...}} and raw {...}
      if (data && typeof data === 'object' && 'config' in data) {
        return (data as Record<string, unknown>).config as Record<string, unknown> ?? data;
      }
      return data ?? {};
    } catch (e) {
      console.warn("[api-client] getSettings failed", e);
      return {};
    }
  }

  async saveSettings(patch: Record<string, unknown>): Promise<Record<string, unknown> | void> {
    try {
      const body = { config: (patch as Record<string, unknown>).config ?? patch };
      const r = await fetch(`${this.base}/settings`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!r.ok) {
        const text = await r.text().catch(() => "");
        console.warn("[api-client] saveSettings failed", r.status, text);
        return;
      }
      const data = await r.json().catch(() => ({}));
      if (data && typeof data === 'object' && 'config' in data) {
        return (data as Record<string, unknown>).config as Record<string, unknown> ?? data;
      }
      return data;
    } catch (e) {
      console.warn("[api-client] saveSettings failed", e);
    }
  }

  // Legacy alias for backwards compat (SettingsView previously used updateSettings)
  async updateSettings(patch: Record<string, unknown>): Promise<Record<string, unknown> | void> {
    return this.saveSettings(patch);
  }

  async checkUpdate(): Promise<Record<string, unknown>> {
    try { const r = await fetch(`${this.base}/update/check`); return r.ok ? await r.json() : {}; } catch { return {}; }
  }
}
