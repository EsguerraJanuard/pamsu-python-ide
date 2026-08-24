import React from 'react';
import { useEditorSettings } from '../../hooks/useEditorSettings';

export default function EditorSettings() {
  const { settings, updateSetting } = useEditorSettings();

  const inputWrap = "mt-2 overflow-hidden rounded-lg border border-border-subtle bg-[#0f1117] transition focus-within:border-[#3b82f6] focus-within:ring-1 focus-within:ring-[#3b82f6]";
  const selectClass = "w-full appearance-none bg-transparent px-3 py-2 text-sm text-text-main placeholder-text-muted focus:outline-none";

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold">Code Editor Preferences</h2>
        <p className="mt-1 text-[11px] text-text-muted">
          Customize your coding environment. Changes apply automatically to the workspace.
        </p>
      </div>

      <div className="space-y-6">
        {/* Font Size */}
        <div>
          <label className="mb-1.5 flex justify-between text-xs font-medium text-text-muted">
            <span>Font Size</span>
            <span className="text-[#3b82f6]">{settings.fontSize}px</span>
          </label>
          <input 
            type="range" min="10" max="24" 
            value={settings.fontSize}
            onChange={(e) => updateSetting('fontSize', parseInt(e.target.value))}
            className="w-full accent-[#3b82f6]"
          />
        </div>

        {/* Tab Size */}
        <div>
          <label className="mb-1.5 block text-xs font-medium text-text-muted">
            Tab Size
          </label>
          <div className={inputWrap}>
            <select 
              value={settings.tabSize}
              onChange={(e) => updateSetting('tabSize', parseInt(e.target.value))}
              className={selectClass}
            >
              <option value={2}>2 spaces</option>
              <option value={4}>4 spaces</option>
            </select>
          </div>
        </div>

        {/* Word Wrap Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-text-main">Word Wrap</p>
            <p className="text-[10px] text-text-muted">Wrap lines that exceed the editor width</p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input 
              type="checkbox" 
              checked={settings.wordWrap === 'on'}
              onChange={(e) => updateSetting('wordWrap', e.target.checked ? 'on' : 'off')}
              className="peer sr-only" 
            />
            <div className="peer h-5 w-9 rounded-full bg-border-subtle after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all peer-checked:bg-[#3b82f6] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
          </label>
        </div>

        {/* Minimap Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-text-main">Minimap Overview</p>
            <p className="text-[10px] text-text-muted">Show a zoomed-out code map on the right side</p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input 
              type="checkbox" 
              checked={settings.minimap}
              onChange={(e) => updateSetting('minimap', e.target.checked)}
              className="peer sr-only" 
            />
            <div className="peer h-5 w-9 rounded-full bg-border-subtle after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all peer-checked:bg-[#3b82f6] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
          </label>
        </div>
      </div>
    </section>
  );
}
