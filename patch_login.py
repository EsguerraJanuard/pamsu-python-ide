import re

with open("frontend/src/features/auth/Login.jsx", "r") as f:
    content = f.read()

old_handler = """  useEffect(() => {
    const handler = (e) => setCapsLock(e.getModifierState("CapsLock"));"""

new_handler = """  useEffect(() => {
    const handler = (e) => {
        if (typeof e.getModifierState === "function") {
            setCapsLock(e.getModifierState("CapsLock"));
        }
    };"""

content = content.replace(old_handler, new_handler)

with open("frontend/src/features/auth/Login.jsx", "w") as f:
    f.write(content)
