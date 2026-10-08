import os

filepaths = ["frontend/src/features/dashboard/InstructorDashboard.jsx", "frontend/src/features/dashboard/Analytics.jsx", "frontend/src/features/dashboard/StudentAnalytics.jsx"]
for filepath in filepaths:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace('var(--color-psu-red, #ce0000)', 'var(--color-text-brand)')
        content = content.replace('text-psu-red transition-colors hover:text-[#60a5fa]', 'text-text-brand transition-colors hover:text-text-brand/80')
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {filepath}")
