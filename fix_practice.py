import re

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "r") as f:
    content = f.read()

# 1. Add output state
content = re.sub(r'(const \[triggerRun, setTriggerRun\] = useState\(0\);)',
                 r'\1\n  const [output, setOutput] = useState("");', content)

# 2. Add setOutput in submit handler
# Look for setFeedback(res);
content = re.sub(r'setFeedback\(res\);',
                 r'setFeedback(res);\n      setOutput(res.execution_feedback || "Execution completed without output.");', content)

# 3. Replace InteractiveTerminal
term_pattern = r'<InteractiveTerminal code=\{code\} triggerRun=\{triggerRun\} onRunFinished=\{\(\) => setIsSubmitting\(false\)\} />'
term_replacement = r'''<div className="w-full h-full min-h-[150px] bg-slate-900/50 p-4 rounded font-mono text-sm text-slate-300 whitespace-pre-wrap overflow-auto border border-slate-700/50">
                   {output || "Output will appear here..."}
                 </div>'''
content = re.sub(term_pattern, term_replacement, content)

# Remove the import just to be clean
content = re.sub(r'import InteractiveTerminal from "../workspace/InteractiveTerminal";\n', '', content)

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "w") as f:
    f.write(content)
print("PracticeWorkspace.jsx updated")
