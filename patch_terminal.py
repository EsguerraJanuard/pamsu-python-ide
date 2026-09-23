import os

filepath = 'frontend/src/features/practice/PracticeWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_editor = '''        {/* Right Panel: Code Editor */}
        <div className="flex w-2/3 flex-col">
          <div className="flex-1 overflow-hidden">
             <MonacoEditor
              height="100%"
              language="python"
              theme={resolvedTheme === "dark" ? "vs-dark" : "light"}
              value={code}
              onChange={(value) => setCode(value || "")}
              options={monacoOptions}
            />
          </div>
        </div>'''

new_editor = '''        {/* Right Panel: Code Editor */}
        <div className="flex w-2/3 flex-col">
          <div className="flex-1 overflow-hidden">
             <MonacoEditor
              height="100%"
              language="python"
              theme={resolvedTheme === "dark" ? "vs-dark" : "light"}
              value={code}
              onChange={(value) => setCode(value || "")}
              options={monacoOptions}
            />
          </div>
          {/* Output Terminal */}
          <div className="h-56 border-t border-border-subtle bg-[#050505] flex flex-col">
             <div className="flex items-center px-4 py-2 border-b border-white/5 bg-[#0f1117]">
                <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Terminal Output</span>
             </div>
             <div className="flex-1 p-4 font-mono text-sm overflow-y-auto whitespace-pre-wrap text-emerald-400">
                {feedback ? (feedback.execution_feedback || "Program exited with code 0.") : "Ready to execute..."}
             </div>
          </div>
        </div>'''

if "Terminal Output" not in content:
    content = content.replace(old_editor, new_editor)
    
    # We also no longer need execution output in the left panel if we have a terminal
    left_execution = '''                {feedback.execution_feedback && (
                  <div className="mb-4">
                    <h4 className="text-xs font-semibold uppercase text-text-muted mb-1">Execution Output</h4>
                    <pre className="p-3 bg-black/30 rounded-md text-xs font-mono text-text-muted overflow-x-auto whitespace-pre-wrap">
                      {feedback.execution_feedback}
                    </pre>
                  </div>
                )}'''
    content = content.replace(left_execution, "")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
