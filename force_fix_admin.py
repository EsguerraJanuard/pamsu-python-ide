import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Generic color replacements
    content = content.replace('text-slate-400', 'text-text-muted')
    content = content.replace('text-slate-500', 'text-text-muted')
    
    # Input field outline should use brand focus ring
    content = content.replace(
        'focus:border-psu-maroon focus:shadow-[0_0_15px_rgba(128,0,0,0.1)]',
        'focus:border-border-focus focus:ring-1 focus:ring-border-focus'
    )
    
    # Also in System Overview cards, let's check for generic colors
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed generic colors in admin")
