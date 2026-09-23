import re

filepath = 'backend/app/routers/practice.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''            status_id = data.get("status", {}).get("id")
            if status_id == 3: # Accepted
                is_successful = True
            else:
                stderr = data.get("stderr")
                compile_output = data.get("compile_output")
                message = data.get("message")
                
                err_b64 = stderr or compile_output or message
                if err_b64:
                    # decode base64
                    try:
                        execution_feedback = base64.b64decode(err_b64).decode('utf-8')
                    except:
                        execution_feedback = str(err_b64)
                else:
                    execution_feedback = "Execution failed or output did not match expected output."'''

new_block = '''            status_id = data.get("status", {}).get("id")
            stdout_b64 = data.get("stdout")
            stderr_b64 = data.get("stderr")
            compile_output_b64 = data.get("compile_output")
            message = data.get("message")
            
            stdout_decoded = base64.b64decode(stdout_b64).decode('utf-8') if stdout_b64 else ""
            stderr_decoded = base64.b64decode(stderr_b64).decode('utf-8') if stderr_b64 else ""
            compile_decoded = base64.b64decode(compile_output_b64).decode('utf-8') if compile_output_b64 else ""
            
            if status_id == 3: # Accepted
                is_successful = True
                execution_feedback = stdout_decoded
            elif status_id == 4: # Wrong Answer
                is_successful = False
                execution_feedback = f"Output did not match expected output.\\nYour output:\\n{stdout_decoded}"
            else:
                is_successful = False
                err_text = stderr_decoded or compile_decoded or str(message)
                execution_feedback = f"Execution Error:\\n{err_text}"'''

content = content.replace(old_block, new_block)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
