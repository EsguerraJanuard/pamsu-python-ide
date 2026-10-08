import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix fetchData
content = content.replace(
    'setSettings(settingsRes.data || settingsRes);',
    'setSettings(settingsRes.data || settingsRes);\n        setInitialSettings(settingsRes.data || settingsRes);'
)

# Fix handleSaveSettings
content = content.replace(
    'showMessage("Global settings successfully saved.");',
    'showMessage("Global settings successfully saved.");\n        setInitialSettings(settings);'
)

# Replace JSON stringify with simple object comparison since keys can be out of order from Python
content = content.replace(
    'const isDirty = JSON.stringify(settings) !== JSON.stringify(initialSettings);',
    'const isDirty = settings.maintenance_mode !== initialSettings.maintenance_mode || settings.default_ast_strictness !== initialSettings.default_ast_strictness || settings.registration_enabled !== initialSettings.registration_enabled;'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed settings dirty logic")
