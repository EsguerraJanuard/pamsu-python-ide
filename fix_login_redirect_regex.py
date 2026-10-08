import os
import re
filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

replacement = """        // Redirect based on role returned by the backend
        if (data.user.role === "instructor") {
          navigate("/instructor/dashboard", { replace: true });
        } else if (data.user.role === "admin") {
          navigate("/admin/dashboard", { replace: true });
        } else {
          navigate("/student/dashboard", { replace: true });
        }"""

pattern = r"\s*// Redirect based on role returned by the backend\s*if \(data\.user\.role === \"instructor\"\) \{\s*navigate\(\"/instructor/dashboard\", \{ replace: true \}\);\s*\} else \{\s*navigate\(\"/student/dashboard\", \{ replace: true \}\);\s*\}"

content = re.sub(pattern, "\n" + replacement, content)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Redirect logic fixed with regex!")
