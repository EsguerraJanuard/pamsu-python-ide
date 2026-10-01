import re

with open("backend/app/services/ai_tutor_service.py", "r") as f:
    content = f.read()

new_prompt = """        prompt = f'''You are an AI coding tutor helping a beginner Python student.
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
'''"""

# Replace everything from prompt = f''' up to the closing '''
pattern = r"        prompt = f'''You are a strict.*?\n'''"
content = re.sub(pattern, new_prompt, content, flags=re.DOTALL)

with open("backend/app/services/ai_tutor_service.py", "w") as f:
    f.write(content)

print("Prompt updated")
