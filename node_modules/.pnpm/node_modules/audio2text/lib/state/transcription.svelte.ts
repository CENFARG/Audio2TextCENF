export const transcriptionState = $state({
  text: '',
  recordingStatus: 'idle' as 'idle' | 'recording' | 'processing',
  elapsedSeconds: 0,
});

export const contextBlocks = $state({
  selected: [] as string[],
  available: [] as { id: string; name: string; enabled: boolean }[],
});
