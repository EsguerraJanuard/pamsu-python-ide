import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

button_html = """          {/* TEMP SEED BUTTON FOR DEMO */}
          <button 
            type="button"
            onClick={async () => {
              try {
                const res = await api.get("/admin/seed-production");
                alert(res.data?.message || "Success!");
              } catch (err) {
                alert("Backend still deploying. Please try again in 1 minute. " + (err.message || ""));
              }
            }}
            className="absolute bottom-4 right-4 text-[10px] text-text-muted hover:text-psu-maroon underline"
          >
            Initialize Admin Account (Demo)
          </button>
"""

if "TEMP SEED BUTTON" not in content:
    content = content.replace('<div className="flex flex-1 items-center justify-center bg-bg-base px-6 py-12 lg:px-8 relative z-0">', 
                              '<div className="flex flex-1 items-center justify-center bg-bg-base px-6 py-12 lg:px-8 relative z-0">\n' + button_html)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added seed button to Login.jsx")
