import google.generativeai as genai
import os

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # If the backend env doesn't have it, I can't test it directly unless I read the .env
    pass

# Try reading from Render environment or .env if exists
try:
    with open("backend/.env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=")[1].strip('"').strip("'")
except:
    pass

if not api_key:
    print("NO API KEY AVAILABLE FOR TESTING")
else:
    genai.configure(api_key=api_key)
    try:
        models = genai.list_models()
        print("AVAILABLE MODELS:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print("ERROR:", e)
