import os

filepath = "backend/app/main.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace(
        'allow_origin_regex=r"https://pamsu-python-ide.*\.vercel\.app",',
        'allow_origin_regex=r"https://.*\.vercel\.app",'
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed CORS regex in main.py")
