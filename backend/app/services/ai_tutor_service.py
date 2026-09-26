import google.generativeai as genai
import os

def generate_pedagogical_hint(task_instructions: str, student_code: str, error_output: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI Tutor is currently unavailable (missing API key)."
    
    try:
        genai.configure(api_key=api_key)
        # We can use flash for faster tutor responses
        model = genai.GenerativeModel('gemini-3.0-flash')
        
        prompt = f'''You are a strict but encouraging Computer Science professor helping a student. 
The student has failed a programming practice task.
Analyze their error and provide a *hint* or *conceptual explanation*. 
COMPLETELY FORBIDDEN: Do not output direct, copy-pasteable solutions or exactly what code to write.

Task Instructions:
{task_instructions}

Student Code:
{student_code}

Execution/Error Output:
{error_output}
'''
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Tutor encountered an error: {str(e)}"