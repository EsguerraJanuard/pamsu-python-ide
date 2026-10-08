import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add isDarkMode and toggleTheme
injection = """  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.documentElement.classList.contains("dark");
  });

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains("dark");
    if (isDark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setIsDarkMode(true);
    }
  };

  const handleGuestLogin = async () => {"""

if "const toggleTheme" not in content:
    content = content.replace("  const handleGuestLogin = async () => {", injection)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed Login blank screen by defining missing variables")
