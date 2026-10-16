import { useEditorSettings } from "../../hooks/useEditorSettings";
import { SettingsSection } from "./AccountSections";

function Toggle({ id, label, description, checked, onChange }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <label htmlFor={id} className="text-sm font-medium text-text-main">
          {label}
        </label>
        <p id={`${id}-description`} className="text-xs text-text-muted">
          {description}
        </p>
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-describedby={`${id}-description`}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
          checked ? "bg-psu-maroon" : "bg-border-strong"
        }`}
      >
        <span
          className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-[22px]" : "translate-x-0.5"
          }`}
          aria-hidden="true"
        />
      </button>
    </div>
  );
}

/** Editor preferences are stored in this browser and applied by the workspace. */
export default function EditorSettings() {
  const { settings, updateSetting } = useEditorSettings();

  return (
    <SettingsSection
      id="editor-heading"
      title="Code editor preferences"
      description="Saved in this browser and applied the next time you open a workspace."
    >
      <div className="space-y-6">
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="editor-font-size" className="text-sm font-medium text-text-main">
              Font size
            </label>
            <span className="text-sm font-semibold text-text-brand">{settings.fontSize}px</span>
          </div>
          <input
            id="editor-font-size"
            type="range"
            min="10"
            max="24"
            value={settings.fontSize}
            onChange={(e) => updateSetting("fontSize", parseInt(e.target.value, 10))}
            className="w-full accent-psu-maroon"
          />
        </div>

        <div>
          <label htmlFor="editor-tab-size" className="field-label">
            Tab size
          </label>
          <select
            id="editor-tab-size"
            value={settings.tabSize}
            onChange={(e) => updateSetting("tabSize", parseInt(e.target.value, 10))}
            className="input-field sm:w-48"
          >
            <option value={2}>2 spaces</option>
            <option value={4}>4 spaces</option>
          </select>
        </div>

        <Toggle
          id="editor-word-wrap"
          label="Word wrap"
          description="Wrap lines that are wider than the editor."
          checked={settings.wordWrap === "on"}
          onChange={(on) => updateSetting("wordWrap", on ? "on" : "off")}
        />
        <Toggle
          id="editor-minimap"
          label="Minimap"
          description="Show a zoomed-out overview of the code on the right."
          checked={Boolean(settings.minimap)}
          onChange={(on) => updateSetting("minimap", on)}
        />
      </div>
    </SettingsSection>
  );
}
