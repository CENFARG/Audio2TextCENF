import { z } from 'zod';

const HealthSchema = z.object({ status: z.string(), version: z.string() });
const SettingsSchema = z.object({}).passthrough();
const TranscriptionsSchema = z.array(z.object({
  id: z.string(), filename: z.string(), title: z.string().optional(),
  emoji: z.string().optional(), language: z.string().optional(),
  provider: z.string().optional(), duration_s: z.number().optional(),
  created_at: z.string().optional(),
}));
const ModelsSchema = z.array(z.object({ id: z.string(), name: z.string() }));
const StartResponseSchema = z.object({ session_id: z.string(), status: z.string() });
const StopResponseSchema = z.object({ final_text: z.string() });

export class APIClient {
  private baseUrl: string;

  constructor(baseUrl = 'http://127.0.0.1:8765') {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(path: string, schema: z.ZodType<T>, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, options);
    if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
    const data = await res.json();
    return schema.parse(data);
  }

  async getHealth() {
    return this.fetch('/health', HealthSchema);
  }

  async getSettings() {
    return this.fetch('/api/v1/settings', SettingsSchema);
  }

  async updateSettings(data: Record<string, unknown>) {
    return this.fetch('/api/v1/settings', SettingsSchema, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
  }

  async getHistory(limit = 50, offset = 0) {
    return this.fetch(`/api/v1/transcriptions?limit=${limit}&offset=${offset}`, TranscriptionsSchema);
  }

  async deleteTranscription(id: string) {
    return this.fetch(`/api/v1/transcriptions/${id}`, z.any(), { method: 'DELETE' });
  }

  async updateTranscription(id: string, data: Record<string, unknown>) {
    return this.fetch(`/api/v1/transcriptions/${id}`, TranscriptionsSchema, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
  }

  async getModels() {
    return this.fetch('/api/v1/models', ModelsSchema);
  }

  async startRecording(): Promise<{ session_id: string; status: string }> {
    return this.fetch('/api/v1/transcribe/start', StartResponseSchema, { method: 'POST' });
  }

  async stopRecording(): Promise<{ final_text: string }> {
    return this.fetch('/api/v1/transcribe/stop', StopResponseSchema, { method: 'POST' });
  }

  async getContextBlocks() {
    return this.fetch('/api/v1/context-blocks', z.array(z.object({ id: z.string(), name: z.string(), enabled: z.boolean() })));
  }

  enhanceText(text: string, profile = 'medium') {
    return this.fetch('/api/v1/enhance', z.object({ enhanced_text: z.string() }), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, profile }),
    });
  }

  getVocabulary() {
    return this.fetch('/api/v1/vocabulary', z.array(z.object({ original: z.string(), correction: z.string(), enabled: z.boolean() })));
  }

  updateVocabulary(data: unknown[]) {
    return this.fetch('/api/v1/vocabulary', z.any(), {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
  }

  checkUpdate() {
    return this.fetch('/api/v1/update/check', z.object({ available: z.boolean(), version: z.string().optional() }));
  }

  connectStream(): WebSocket {
    return new WebSocket(`ws://127.0.0.1:8765/api/v1/transcribe/stream`);
  }
}