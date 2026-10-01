import os
import re

filepath = "frontend/src/features/practice/PracticeWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'const editorRef = useRef(null);',
    'const editorRef = useRef(null);\n  const monacoRef = useRef(null);'
)

content = content.replace(
    'editorRef.current = editor;',
    'editorRef.current = editor;\n                    monacoRef.current = monaco;'
)

lint_effect = """
  // Intelligent Syntax Linting using LSP simulation via Backend
  useEffect(() => {
    const lintCode = async () => {
      if (!editorRef.current || !monacoRef.current || !code.trim()) return;
      try {
        const response = await api.post('/execution/lint', { code });
        if (response.data && response.data.markers) {
          const monacoMarkers = response.data.markers.map(marker => ({
            startLineNumber: marker.line,
            startColumn: marker.column,
            endLineNumber: marker.line,
            endColumn: marker.column + 1,
            message: marker.message,
            severity: marker.severity === 'error' ? monacoRef.current.MarkerSeverity.Error : monacoRef.current.MarkerSeverity.Warning
          }));
          monacoRef.current.editor.setModelMarkers(editorRef.current.getModel(), 'python', monacoMarkers);
        }
      } catch (err) {
        console.error('Linting failed', err);
      }
    };

    const debounceTimer = setTimeout(() => {
      lintCode();
    }, 1000);

    return () => clearTimeout(debounceTimer);
  }, [code]);
"""

content = content.replace(
    '  const handleRun = async () => {',
    lint_effect + '\n  const handleRun = async () => {'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added linting to PracticeWorkspace.jsx")
