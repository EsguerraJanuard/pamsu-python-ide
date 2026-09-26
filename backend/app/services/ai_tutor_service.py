import google.generativeai as genai
import os

def generate_pedagogical_hint(task_instructions: str, student_code: str, error_output: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI Tutor is currently unavailable (missing API key)."
    
    try:
        genai.configure(api_key=api_key)
        # We can use flash for faster tutor responses
        model = genai.GenerativeModel('gemini-3.8-flash')
        
        prompt = f'''You are an AI coding tutor helping a beginner Python student.
Analyze their code and the execution error, then provide a guiding hint using Markdown.

CRITICAL RULES:
1. **Be extremely concise** (2-3 short sentences maximum). 
2. **NEVER give the direct answer** or write the corrected code.
3. Point out the exact line or concept they misunderstood.
4. Use Markdown formatting (bold keywords, use bullet points if helpful, format code concepts in backticks).
5. Cut the fluff. Do not lecture, do not roleplay, and do not say things like "Take a breath" or "Let's look at this." Just deliver the hint directly.

Task Instructions:
{task_instructions}

Student Code:
{student_code}

Execution Error:
{error_output}
'''
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Tutor encountered an error: {str(e)}"