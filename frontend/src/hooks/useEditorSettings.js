import { useState, useEffect } from 'react';

export function useEditorSettings() {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('editor-settings');
    return saved ? JSON.parse(saved) : {
      fontSize: 14,
      tabSize: 4,
      wordWrap: 'on',
      minimap: false,
    };
  });

  useEffect(() => {
    localStorage.setItem('editor-settings', JSON.stringify(settings));
  }, [settings]);

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return { settings, updateSetting };
}
