import os

# 1. PracticeWorkspace.jsx
filepath = 'frontend/src/features/practice/PracticeWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if "import { useTheme } from" not in content:
    content = content.replace('import { useEditorSettings } from "../../hooks/useEditorSettings";', 'import { useEditorSettings } from "../../hooks/useEditorSettings";\nimport { useTheme } from "../theme/ThemeContext";')

# Add hook call
if "const { resolvedTheme } = useTheme();" not in content:
    content = content.replace('const { settings } = useEditorSettings();', 'const { settings } = useEditorSettings();\n  const { resolvedTheme } = useTheme();')

# Modify Monaco
old_monaco = 'theme={settings.theme === "vs-dark" ? "vs-dark" : "light"}'
new_monaco = 'theme={resolvedTheme === "dark" ? "vs-dark" : "light"}'
content = content.replace(old_monaco, new_monaco)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Workspace.jsx
filepath = 'frontend/src/features/workspace/Workspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if "import { useTheme } from" not in content:
    content = content.replace('import { useEditorSettings } from "../../hooks/useEditorSettings";', 'import { useEditorSettings } from "../../hooks/useEditorSettings";\nimport { useTheme } from "../theme/ThemeContext";')

# Add hook call
if "const { resolvedTheme } = useTheme();" not in content:
    content = content.replace('const { settings } = useEditorSettings();', 'const { settings } = useEditorSettings();\n  const { resolvedTheme } = useTheme();')

# Modify Monaco
content = content.replace(old_monaco, new_monaco)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
