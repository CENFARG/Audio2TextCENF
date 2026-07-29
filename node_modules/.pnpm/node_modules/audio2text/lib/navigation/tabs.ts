export interface TabConfig {
  id: string;
  label: string;
  icon: string;
  enabled: boolean;       // feature flag controlled
  children?: TabConfig[];  // sub-tabs within this tab
}

export const defaultTabs: TabConfig[] = [
  { id: 'transcribe', label: 'Transcribir', icon: '🎤', enabled: true },
  { id: 'history',    label: 'Historial',   icon: '📋', enabled: true },
  {
    id: 'settings', label: 'Ajustes', icon: '⚙️', enabled: true,
    children: [
      { id: 'settings/provider',       label: 'Proveedor',            icon: '🔌', enabled: true },
      { id: 'settings/audio',          label: 'Audio',                icon: '🎵', enabled: true },
      { id: 'settings/recording',      label: 'Grabación',            icon: '⏺️', enabled: true },
      { id: 'settings/ui',             label: 'Interfaz',             icon: '🖥️', enabled: true },
      { id: 'settings/post-processing',label: 'Post-Procesamiento',   icon: '🤖', enabled: true },
      { id: 'settings/blocks',         label: 'Bloques',              icon: '🧩', enabled: true },
      { id: 'settings/hotkey',         label: 'Hotkeys',              icon: '⌨️', enabled: true },
      { id: 'settings/vocabulary',     label: 'Vocabulario',          icon: '📝', enabled: true },
    ],
  },
  { id: 'info',       label: 'Info',         icon: 'ℹ️', enabled: true },
  { id: 'update',     label: 'Actualizar',   icon: '📦', enabled: true },
];
