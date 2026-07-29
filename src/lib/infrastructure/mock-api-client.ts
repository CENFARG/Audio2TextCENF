import type { APIClient } from './api-client';

export class MockAPIClient implements APIClient {
  async getHealth() { return { status: 'ok', version: '0.16.0-mock' }; }
  async getSettings() { return { providers: { primary: 'mock' } }; }
  async updateSettings(_: Record<string, unknown>) { return { providers: { primary: 'mock' } }; }
  async getHistory() { return [{ id: '1', filename: 'test.wav', title: 'Mock', provider: 'mock', created_at: new Date().toISOString() }]; }
  async deleteTranscription(_: string) { return {}; }
  async getModels() { return [{ id: 'mock', name: 'Mock Provider' }]; }
  async startRecording() { return { session_id: 'mock-session', status: 'recording' }; }
  async stopRecording() { return { final_text: 'Mock transcription result' }; }
  async getContextBlocks() { return [{ id: 'cb-1', name: 'Task Extractor', enabled: true }]; }
  async enhanceText(_text: string, _profile?: string) { return { enhanced_text: _text }; }
  async getVocabulary() { return []; }
  async updateVocabulary(_data: unknown[]) { return {}; }
  async checkUpdate() { return { available: false }; }
  connectStream(): WebSocket { return new WebSocket('ws://localhost:9999/mock'); }
}