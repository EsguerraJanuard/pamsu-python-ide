import os

filepath = 'frontend/src/features/theme/ThemeContext.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add resolvedTheme state
new_state = """  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("pamsu_theme");
    return saved || "system";
  });
  const [resolvedTheme, setResolvedTheme] = useState("light");"""

content = content.replace("""  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("pamsu_theme");
    return saved || "system";
  });""", new_state)

# Update resolved theme in useEffect 1
new_effect_1 = """    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      root.classList.add(systemTheme);
      setResolvedTheme(systemTheme);
    } else {
      root.classList.add(theme);
      setResolvedTheme(theme);
    }"""

content = content.replace("""    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }""", new_effect_1)


# Update resolved theme in useEffect 2
new_effect_2 = """    const handleChange = () => {
      const root = window.document.documentElement;
      const systemTheme = mediaQuery.matches ? "dark" : "light";
      root.classList.remove("light", "dark");
      root.classList.add(systemTheme);
      setResolvedTheme(systemTheme);
    };"""

content = content.replace("""    const handleChange = () => {
      const root = window.document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(mediaQuery.matches ? "dark" : "light");
    };""", new_effect_2)


# Update provider
content = content.replace('<ThemeContext.Provider value={{ theme, setTheme }}>', '<ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
