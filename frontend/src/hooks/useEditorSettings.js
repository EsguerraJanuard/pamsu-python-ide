import { useState, useEffect } from 'react';

const STORAGE_KEY = 'editor-settings';
const DEFAULTS = {
  fontSize: 14,
  tabSize: 4,
  wordWrap: 'on',
  minimap: false,
};

function readSettings() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? { ...DEFAULTS, ...JSON.parse(saved) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

export function useEditorSettings() {
  const [settings, setSettings] = useState(readSettings);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // Preferences fall back to defaults when storage is unavailable.
    }
  }, [settings]);

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return { settings, updateSetting };
}
