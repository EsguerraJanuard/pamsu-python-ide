/**
 * Monaco themes for the student IDE. Surfaces mirror the CSS tokens in
 * index.css (--bg-panel, --text-main, --border-subtle …) and every syntax
 * color was checked for WCAG AA (≥ 4.5:1) against its background.
 * The editor follows the effective student theme; there is no separate
 * editor-theme preference.
 */
export const EDITOR_THEME_LIGHT = "pamsu-light";
export const EDITOR_THEME_DARK = "pamsu-dark";

export const editorThemeFor = (effectiveTheme) =>
  effectiveTheme === "dark" ? EDITOR_THEME_DARK : EDITOR_THEME_LIGHT;

const rule = (token, foreground, fontStyle) => ({ token, foreground, ...(fontStyle ? { fontStyle } : {}) });

const LIGHT = {
  fg: "1c1917",
  comment: "6b665f",
  keyword: "77250b",
  string: "146c35",
  number: "7a5600",
  builtin: "0b5a8c",
  func: "5b3a9d",
  decorator: "9a3412",
};

const DARK = {
  fg: "f3ede6",
  comment: "9a8f85",
  keyword: "f0b92e",
  string: "86d99b",
  number: "f2a65a",
  builtin: "7cc4f2",
  func: "c9a7ff",
  decorator: "ff9d73",
};

const rulesFor = (c) => [
  rule("", c.fg),
  rule("comment", c.comment, "italic"),
  rule("keyword", c.keyword, "bold"),
  rule("keyword.python", c.keyword, "bold"),
  rule("string", c.string),
  rule("string.escape", c.number),
  rule("number", c.number),
  rule("number.float", c.number),
  rule("type.identifier", c.builtin),
  rule("identifier", c.fg),
  rule("delimiter", c.fg),
  rule("operator", c.fg),
  rule("tag", c.keyword),
  rule("predefined", c.func),
  rule("annotation", c.decorator),
  rule("variable.predefined", c.builtin),
];

/** Registers both themes; call from MonacoEditor's `beforeMount`. */
export function defineEditorThemes(monaco) {
  monaco.editor.defineTheme(EDITOR_THEME_LIGHT, {
    base: "vs",
    inherit: true,
    rules: rulesFor(LIGHT),
    colors: {
      "editor.background": "#ffffff",
      "editor.foreground": "#1c1917",
      "editorLineNumber.foreground": "#6b665f",
      "editorLineNumber.activeForeground": "#1c1917",
      "editor.lineHighlightBackground": "#f7f6f3",
      "editor.lineHighlightBorder": "#00000000",
      "editor.selectionBackground": "#77250b33",
      "editor.inactiveSelectionBackground": "#77250b1f",
      "editor.findMatchBackground": "#eaae1980",
      "editor.findMatchHighlightBackground": "#eaae1950",
      "editorCursor.foreground": "#77250b",
      "editorIndentGuide.background1": "#1c19171a",
      "editorIndentGuide.activeBackground1": "#1c191740",
      "editorWhitespace.foreground": "#1c191730",
      "editorGutter.background": "#ffffff",
      "editorError.foreground": "#b42318",
      "editorWarning.foreground": "#8a6200",
      "editorWidget.background": "#ffffff",
      "editorWidget.border": "#1c191733",
      "scrollbarSlider.background": "#1c19172e",
      "scrollbarSlider.hoverBackground": "#1c19174d",
      "scrollbarSlider.activeBackground": "#1c191766",
      "minimap.background": "#ffffff",
    },
  });

  monaco.editor.defineTheme(EDITOR_THEME_DARK, {
    base: "vs-dark",
    inherit: true,
    rules: rulesFor(DARK),
    colors: {
      "editor.background": "#1c1815",
      "editor.foreground": "#f3ede6",
      "editorLineNumber.foreground": "#9a8f85",
      "editorLineNumber.activeForeground": "#f3ede6",
      "editor.lineHighlightBackground": "#241e19",
      "editor.lineHighlightBorder": "#00000000",
      "editor.selectionBackground": "#eaae194d",
      "editor.inactiveSelectionBackground": "#eaae1930",
      "editor.findMatchBackground": "#eaae1999",
      "editor.findMatchHighlightBackground": "#eaae1966",
      "editorCursor.foreground": "#f0b92e",
      "editorIndentGuide.background1": "#fff0e124",
      "editorIndentGuide.activeBackground1": "#fff0e14d",
      "editorWhitespace.foreground": "#fff0e133",
      "editorGutter.background": "#1c1815",
      "editorError.foreground": "#ff8a80",
      "editorWarning.foreground": "#f2c14b",
      "editorWidget.background": "#26211d",
      "editorWidget.border": "#fff0e166",
      "scrollbarSlider.background": "#fff0e13a",
      "scrollbarSlider.hoverBackground": "#fff0e15c",
      "scrollbarSlider.activeBackground": "#fff0e17a",
      "minimap.background": "#1c1815",
    },
  });
}
