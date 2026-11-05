import PropTypes from "prop-types";
import MonacoEditor from "@monaco-editor/react";
import { useTheme } from "../../features/theme/ThemeContext";
import { defineEditorThemes, editorThemeFor } from "../../features/workspace/editorThemes";

// Monaco binds "toggle Tab focus mode" to Ctrl+M, and to Ctrl+Shift+M on macOS.
const IS_MAC = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
const TAB_FOCUS_KEYS = IS_MAC ? "Ctrl+Shift+M" : "Ctrl+M";

const EDITOR_OPTIONS = {
  minimap: { enabled: false },
  lineNumbers: "on",
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
  fontSize: 13,
  fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
  padding: { top: 10, bottom: 10 },
  lineNumbersMinChars: 3,
  renderLineHighlight: "line",
  // Python has no language service here, so word suggestions are only noise,
  // and their popup would be cut off by the field's rounded frame.
  quickSuggestions: false,
  suggestOnTriggerCharacters: false,
  wordBasedSuggestions: "off",
  snippetSuggestions: "none",
  parameterHints: { enabled: false },
  scrollbar: { alwaysConsumeMouseWheel: false },
};

/**
 * Python code input for forms: a small Monaco editor (same themes as the
 * student IDE) bound to a string value. Tab indents instead of moving focus.
 *
 * The editor sits absolutely inside the frame, so the frame's height comes
 * only from its classes (fixed, flex-1, resize-y) and never from the editor:
 * otherwise automaticLayout lets the field grow but never shrink again.
 */
export default function CodeEditorField({ value, onChange, ariaLabel, placeholder, className = "" }) {
  const { effectiveTheme } = useTheme();

  return (
    <div
      className={`relative overflow-hidden rounded-lg border border-border-strong bg-bg-panel transition-colors focus-within:border-border-focus focus-within:ring-2 focus-within:ring-border-focus/20 ${className}`}
    >
      <div className="absolute inset-0">
        <MonacoEditor
          height="100%"
          language="python"
          theme={editorThemeFor(effectiveTheme)}
          beforeMount={defineEditorThemes}
          value={value}
          onChange={(next) => onChange(next ?? "")}
          // Monaco picks the OS line ending (\r\n on Windows); the old textarea
          // always gave \n, so keep saved code in that form.
          onMount={(editor, monaco) => editor.getModel()?.setEOL(monaco.editor.EndOfLineSequence.LF)}
          loading={<span className="text-xs text-text-muted">Starting editor…</span>}
          options={{ ...EDITOR_OPTIONS, ariaLabel, placeholder }}
        />
      </div>
    </div>
  );
}

CodeEditorField.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  ariaLabel: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  /** Sizing for the field, e.g. "h-44 resize-y" or "flex-1 min-h-[280px]". */
  className: PropTypes.string,
};

/** One-line keyboard hint shown under a CodeEditorField. */
export function CodeEditorHint({ className = "" }) {
  return (
    <p className={`text-[11px] text-text-muted ${className}`}>
      Tab indents. Press {TAB_FOCUS_KEYS} to make Tab move to the next field instead.
    </p>
  );
}

CodeEditorHint.propTypes = {
  className: PropTypes.string,
};
