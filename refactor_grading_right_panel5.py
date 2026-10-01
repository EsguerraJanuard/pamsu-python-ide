import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the "Anti-Cheating / Telemetry Indicators" header and wrapper with the new Violations section
content = content.replace(
    "{/* Anti-Cheating / Telemetry Indicators */}",
    "                <div className=\"bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm mb-6\">\n                  <h3 className=\"text-lg font-bold text-psu-red dark:text-psu-gold mb-4 flex items-center gap-2\">\n                    <svg className=\"w-5 h-5\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z\" /></svg>\n                    Student Violations & Analysis\n                  </h3>\n                  {/* Anti-Cheating / Telemetry Indicators */}"
)

# 2. Add AST Analysis and Execution Logs right after the telemetry indicators end.
telemetry_end = "              )}\n  \n              {selectedSub ? ("
ast_and_logs = """              )}
              {selectedSub && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                     <div>
                       <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">AST Analysis</h4>
                       <pre className="bg-bg-panel p-4 rounded-lg text-sm text-text-main overflow-x-auto border border-border-strong whitespace-pre-wrap min-h-[120px]">
                         {detailedSub?.ast_feedback && detailedSub.ast_feedback.length > 0 ? detailedSub.ast_feedback.join('\\n') : 'Passed all structural requirements.'}
                       </pre>
                     </div>
                     <div>
                       <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Execution Logs</h4>
                       <pre className="bg-bg-panel p-4 rounded-lg text-sm text-text-main overflow-x-auto border border-border-strong whitespace-pre-wrap min-h-[120px]">
                         {detailedSub?.execution_log || 'Execution logs not available for this submission.'}
                       </pre>
                     </div>
                  </div>
                </div>
              )}
              
              {selectedSub ? ("""
content = content.replace(telemetry_end, ast_and_logs)

# 3. Remove the old AST Analysis and Execution Logs from inside selectedSub
old_logs = """                  <div className="bg-bg-glass border border-border-subtle rounded-lg p-4">
                    <h3 className="text-lg font-medium text-text-main mb-2">Execution Logs</h3>
                    <pre className="bg-bg-panel p-4 rounded text-sm text-text-muted overflow-x-auto border border-border-subtle whitespace-pre-wrap mb-4">
                      {detailedSub?.execution_log || 'Execution logs not available for this submission.'}
                    </pre>
  
                    <h3 className="text-lg font-medium text-text-main mb-2">AST Analysis</h3>
                    <pre className="bg-bg-panel p-4 rounded text-sm text-text-muted overflow-x-auto border border-border-subtle whitespace-pre-wrap">
                      {detailedSub?.ast_feedback ? detailedSub.ast_feedback.join('\\n') : 'No structural requirements found.'}
                    </pre>
                  </div>"""

content = content.replace(old_logs, "")

# 4. Modify the Grading Form to include the Suggested Grade
old_form_start = '<form onSubmit={handleSubmitGrade} className="bg-bg-glass border border-border-subtle rounded-lg p-4 flex flex-col gap-4">'
new_form_start = """<form onSubmit={handleSubmitGrade} className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col gap-6 mb-6">
                    <h3 className="text-lg font-bold text-text-main border-b border-border-subtle pb-4">Activity Grading Assessment</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                       <div className="bg-psu-maroon/5 border border-psu-maroon/20 dark:bg-psu-gold/5 dark:border-psu-gold/20 rounded-lg p-5">
                          <label className="block text-xs font-bold text-psu-maroon dark:text-psu-gold mb-2 uppercase tracking-wider">Suggested Grade</label>
                          <div className="text-5xl font-black text-text-main tracking-tight">
                            {(() => {
                                if (!detailedSub) return '0';
                                if (detailedSub.jaccard_score >= 70) return '0';
                                let score = 100;
                                if (detailedSub.ast_feedback && detailedSub.ast_feedback.length > 0) {
                                    const fails = detailedSub.ast_feedback.filter(f => f.includes('missing') || f.includes('failed') || f.includes('Missing'));
                                    score -= (fails.length * 20);
                                }
                                if (score < 0) score = 0;
                                return score;
                            })()}
                          </div>
                          <p className="text-xs text-text-muted mt-3">Calculated from AST rule satisfaction.</p>
                       </div>
                       <div className="flex flex-col justify-center">
"""
content = content.replace(old_form_start + '\n                    <h3 className="text-lg font-medium text-text-main">Manual Grading</h3>', new_form_start)

# Close the new grid col div before the feedback text area
content = content.replace(
    '                    <div>\n                      <label className="block text-sm font-medium text-text-muted mb-1">Feedback</label>',
    '                       </div>\n                    </div>\n\n                    <div>\n                      <label className="block text-sm font-medium text-text-muted mb-1">Feedback</label>'
)

# 5. Move the form BEFORE the Code Editor
# We know currently Code Editor is right before the form (since we removed logs).
code_editor_start = '                  <div className="bg-bg-glass border border-border-subtle rounded-lg p-4">\n                    <h3 className="text-lg font-medium text-text-main mb-2">Submitted Code</h3>'
code_editor_end = '                    {/*\n                      {detailedSub?.raw_code || detailedSub?.code || \'# Loading code... or No code provided\'}\n                    */}\n                  </div>'
code_editor_end2 = '                  </div>' # The actual div closing

code_block_start = content.find(code_editor_start)
# we need to find the end of this div.
code_block_end = content.find('</form>', code_block_start) # wait, if form is after it, we can swap them easily.

# Let's extract the form block
form_start_idx = content.find('<form onSubmit={handleSubmitGrade}')
form_end_idx = content.find('</form>') + 7

form_block = content[form_start_idx:form_end_idx]

# Extract code block
# Actually, the code block is right before the form now.
# So we can just replace the code block + form with form + code block.
code_block = content[code_block_start:form_start_idx].strip()

# Now swap them
content = content[:code_block_start] + form_block + '\n\n' + code_block + '\n' + content[form_end_idx:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Refactored Right Panel UI using targeted replacements")
