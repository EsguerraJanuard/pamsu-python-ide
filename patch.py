import re
with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

t1 = "import { DiffEditor } from '@monaco-editor/react';"
r1 = "import { DiffEditor } from '@monaco-editor/react';\nimport { useTheme } from '../../theme/ThemeContext';"

c = c.replace(t1, r1)

t2 = "const SplitPaneGradingWorkspace = () => {"
r2 = "const SplitPaneGradingWorkspace = () => {\n  const { resolvedTheme } = useTheme();"

c = c.replace(t2, r2)

t3 = "theme=\"vs-dark\""
r3 = "theme={resolvedTheme === 'dark' ? 'vs-dark' : 'light'}"

c = c.replace(t3, r3)

with open('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)