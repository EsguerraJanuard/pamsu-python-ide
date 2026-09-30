import re

logo_html = """<img src="/school_logo.png" alt="PSU Logo" className="h-12 w-12 object-contain drop-shadow-md" />
          <div className="flex flex-col">
            <span className="text-[11px] font-bold tracking-widest text-text-muted uppercase">Pampanga State University</span>
            <span className="text-lg font-extrabold tracking-wide text-text-main leading-tight">Python IDE</span>
          </div>"""

def replace_in_file(path, pattern, repl):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(pattern, repl, content, flags=re.DOTALL)
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated", path)
    else:
        print("No match in", path)

pattern_login = r'<div className="flex h-8 w-8 items-center justify-center rounded-md bg-psu-maroon font-mono text-xs font-bold text-white shadow-\[.*?\]">\s*&gt;_\s*</div>\s*<span className="font-semibold tracking-wide text-text-main">PAMSU Python IDE</span>'
replace_in_file("frontend/src/features/auth/Login.jsx", pattern_login, logo_html)

pattern_reg = r'<div className="flex h-8 w-8 items-center justify-center rounded-md bg-psu-maroon font-mono text-xs font-bold text-white shadow-\[.*?\]">\s*&gt;_\s*</div>\s*<span className="text-xl font-bold tracking-wide text-text-main">PAMSU Python IDE</span>'
replace_in_file("frontend/src/features/auth/Register.jsx", pattern_reg, logo_html)

sidebar_html = """<img src="/school_logo.png" alt="PSU Logo" className="h-9 w-9 object-contain drop-shadow-md" />
                {!isCollapsed && (
                  <div className="flex flex-col justify-center">
                    <span className="truncate text-[9px] font-bold tracking-widest text-text-muted uppercase leading-none mb-0.5">Pampanga State</span>
                    <span className="truncate text-sm font-extrabold tracking-wide text-text-main leading-none">University</span>
                  </div>
                )}"""

pattern_sidebar = r'<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-psu-maroon text-white shadow-lg shadow-psu-maroon/20">\s*<span className="font-mono text-sm font-bold">&gt;_</span>\s*</div>\s*\{!isCollapsed && \(\s*<span className="truncate text-sm font-bold tracking-wide text-text-main">\s*PAMSU IDE\s*</span>\s*\)\}'

replace_in_file("frontend/src/components/layout/InstructorSidebar.jsx", pattern_sidebar, sidebar_html)
replace_in_file("frontend/src/components/layout/Sidebar.jsx", pattern_sidebar, sidebar_html)
