import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Lenient
    content = content.replace(
        "border-psu-maroon dark:border-psu-gold bg-emerald-500/5 shadow-sm",
        "border-border-focus bg-bg-panel shadow-sm shadow-border-focus/20 ring-1 ring-border-focus"
    )
    content = content.replace(
        """{settings.default_ast_strictness === 'lenient' && <div className="w-2 h-2 rounded-full bg-emerald-500"></div>}""",
        """{settings.default_ast_strictness === 'lenient' && <div className="w-2 h-2 rounded-full bg-psu-maroon dark:bg-psu-gold"></div>}"""
    )
    
    # Moderate
    content = content.replace(
        "border-psu-maroon dark:border-psu-gold bg-psu-maroon/5 dark:bg-psu-gold/5 shadow-sm",
        "border-border-focus bg-bg-panel shadow-sm shadow-border-focus/20 ring-1 ring-border-focus"
    )
    content = content.replace(
        """{settings.default_ast_strictness === 'moderate' && <div className="w-2 h-2 rounded-full bg-psu-maroon"></div>}""",
        """{settings.default_ast_strictness === 'moderate' && <div className="w-2 h-2 rounded-full bg-psu-maroon dark:bg-psu-gold"></div>}"""
    )
    content = content.replace(
        """<div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon' : 'border-border-strong'}`}>""",
        """<div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon dark:border-psu-gold' : 'border-border-strong'}`}>"""
    )

    # Strict
    content = content.replace(
        "border-red-500 bg-red-500/5 shadow-sm",
        "border-border-focus bg-bg-panel shadow-sm shadow-border-focus/20 ring-1 ring-border-focus"
    )
    content = content.replace(
        """<div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'strict' ? 'border-red-500' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'strict' && <div className="w-2 h-2 rounded-full bg-red-500"></div>}""",
        """<div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${settings.default_ast_strictness === 'strict' ? 'border-psu-maroon dark:border-psu-gold' : 'border-border-strong'}`}>
                              {settings.default_ast_strictness === 'strict' && <div className="w-2 h-2 rounded-full bg-psu-maroon dark:bg-psu-gold"></div>}"""
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed AST strictness toggles")
