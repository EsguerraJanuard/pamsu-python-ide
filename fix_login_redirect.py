import os
filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """        // Redirect based on role returned by the backend
        if (data.user.role === "instructor") {
          navigate("/instructor/dashboard", { replace: true });
        } else {
          navigate("/student/dashboard", { replace: true });
        }"""
replacement = """        // Redirect based on role returned by the backend
        if (data.user.role === "instructor") {
          navigate("/instructor/dashboard", { replace: true });
        } else if (data.user.role === "admin") {
          navigate("/admin/dashboard", { replace: true });
        } else {
          navigate("/student/dashboard", { replace: true });
        }"""

content = content.replace(target, replacement)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Redirect logic fixed!")
