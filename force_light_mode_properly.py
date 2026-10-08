import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add useTheme import
if "useTheme" not in content:
    content = content.replace('import { useAuth } from "./AuthContext";', 'import { useAuth } from "./AuthContext";\nimport { useTheme } from "../theme/ThemeContext";')

# Replace the manual classList manipulation with useTheme
injection = """  const { setTheme } = useTheme();

  useEffect(() => {
    setTheme("light");
    
    const handleModifier = (e) => {"""
content = content.replace("""  useEffect(() => {
    // Force light mode on login page
    document.documentElement.classList.remove("dark");
    
    const handleModifier = (e) => {""", injection)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated Login.jsx to use setTheme('light') properly")
