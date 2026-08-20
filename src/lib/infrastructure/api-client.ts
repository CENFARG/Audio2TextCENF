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
  private base = "http://127.0.0.1:8765";

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
    try { const r = await fetch(`${this.base}/settings`); return r.ok ? await r.json() : {}; } catch { return {}; }
  }

  async saveSettings(patch: Record<string, unknown>): Promise<void> {
    try { await fetch(`${this.base}/settings`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) }); } catch { /* no-op */ }
  }

  async checkUpdate(): Promise<Record<string, unknown>> {
    try { const r = await fetch(`${this.base}/update/check`); return r.ok ? await r.json() : {}; } catch { return {}; }
  }
}
