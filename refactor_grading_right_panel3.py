import os

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace everything from {/* Anti-Cheating / Telemetry Indicators */}
# down to the end of the `selectedSub ? ( ... ) : ( ... )` block.

start_marker = "{/* Anti-Cheating / Telemetry Indicators */}"
end_marker = "No submission found for this student."

start_idx = content.find(start_marker)
end_idx = content.find('              )}', content.find(end_marker)) + 16

if start_idx == -1 or end_idx == -1:
    print(f"Could not find blocks. start: {start_idx}, end: {end_idx}")
    exit(1)

new_block = """{/* NEW LAYOUT (Violations -> Grading -> Code) */}
              {selectedSub ? (
                <>
                  {/* TOP SECTION: Student Violations & Activity Analysis */}
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm">
                     <h3 className="text-lg font-bold text-psu-red dark:text-psu-gold mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        Student Violations & Analysis
                     </h3>
                     
                     <div className="space-y-6">
                        {/* Telemetry Indicators */}
                        <div className="flex flex-wrap gap-4 border-b border-border-subtle pb-6">
                          {detailedSub?.jaccard_score !== undefined && detailedSub?.jaccard_score !== null && (
                            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${detailedSub?.jaccard_score >= 70 ? 'bg-psu-red/10 border-psu-red/30 text-psu-red' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                              <span className="text-sm font-semibold">Similarity: {detailedSub?.jaccard_score.toFixed(1)}%</span>
                            </div>
                          )}
                          {detailedSub?.coding_session && (
                            <>
                              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${detailedSub?.coding_session.tab_switch_count > 3 ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                <span className="text-sm font-semibold">Tab Switches: {detailedSub?.coding_session.tab_switch_count}</span>
                              </div>
                              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${detailedSub?.coding_session.blocked_paste_count > 0 ? 'bg-psu-red/10 border-psu-red/30 text-psu-red' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                <span className="text-sm font-semibold">Blocked Pastes: {detailedSub?.coding_session.blocked_paste_count}</span>
                              </div>
                              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${detailedSub?.coding_session.mouseleave_count > 5 ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400' : 'bg-bg-panel border-border-strong text-text-main'}`}>
                                <span className="text-sm font-semibold">Mouse Leaves: {detailedSub?.coding_session.mouseleave_count}</span>
                              </div>
                            </>
                          )}
                        </div>
                        
                        {/* AST Analysis & Execution Logs */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                           <div>
                             <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">AST Analysis</h4>
                             <pre className="bg-bg-panel p-4 rounded-lg text-sm text-text-main overflow-x-auto border border-border-strong whitespace-pre-wrap min-h-[120px]">
                               {detailedSub?.ast_feedback && detailedSub.ast_feedback.length > 0 ? detailedSub.ast_feedback.join('\\n') : '? Passed all structural requirements.'}
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
                  </div>

                  {/* MIDDLE SECTION: Grading Form */}
                  <form onSubmit={handleSubmitGrade} className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col gap-6 mt-6">
                    <h3 className="text-lg font-bold text-text-main border-b border-border-subtle pb-4">Activity Grading Assessment</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                       {/* Suggested Grade */}
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
                                    if (score < 0) score = 0;
                                }
                                if (detailedSub.execution_log && detailedSub.execution_log.toLowerCase().includes('error')) {
                                    score -= 30; 
                                }
                                return Math.max(0, score);
                            })()}
                          </div>
                          <p className="text-xs text-text-muted mt-3">Calculated from AST rule satisfaction and syntax validation.</p>
                       </div>

                       {/* Manual Grade */}
                       <div className="flex flex-col justify-center">
                          <label className="block text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Manual Score</label>
                          <input
                            type="number"
                            step="0.01"
                            value={gradeScore}
                            onChange={(e) => setGradeScore(e.target.value)}
                            className="w-full bg-bg-panel border border-border-strong rounded-lg px-4 py-3 text-2xl font-bold text-text-main focus:outline-none focus:border-psu-maroon focus:ring-2 focus:ring-psu-maroon/30 transition-all shadow-sm"
                            placeholder="e.g. 95"
                          />
                          <p className="text-xs text-text-muted mt-3">Override the suggested grade manually here.</p>
                       </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Instructor Feedback</label>
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        className="w-full bg-bg-panel border border-border-strong rounded-lg p-4 text-text-main h-32 focus:outline-none focus:border-psu-maroon focus:ring-2 focus:ring-psu-maroon/30 transition-all shadow-sm"
                        placeholder="Provide constructive feedback for the student..."
                      />
                    </div>

                    <div className="flex gap-4 pt-4 border-t border-border-subtle mt-2">
                      <button 
                        type="submit" 
                        disabled={savingGrade}
                        className="px-6 py-3 bg-psu-maroon hover:bg-psu-red text-white font-bold rounded-lg shadow-sm transition-all disabled:opacity-50 flex-1 flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        {savingGrade ? 'Saving Grade...' : 'Save Final Grade'}
                      </button>
                      
                      {detailedSub?.status === 'retake_requested' && (
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              await api.post(`/submissions/${detailedSub.id}/approve-retake`);
                              setNotice("Retake approved! Student can now resubmit.");
                              fetchSubmissions();
                            } catch (err) {
                              setNotice("Failed to approve retake.");
                            }
                          }}
                          className="px-6 py-3 bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 font-bold rounded-lg transition-all hover:bg-amber-500/20"
                        >
                          Approve Retake
                        </button>
                      )}
                    </div>
                  </form>

                  {/* BOTTOM SECTION: Submitted Code */}
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-6 shadow-sm flex flex-col mt-6">
                    <h3 className="text-lg font-bold text-text-main mb-4 border-b border-border-subtle pb-4">Submitted Code vs Starter Code</h3>
                    <div className="h-[500px] border border-border-strong rounded-lg overflow-hidden shadow-sm">
                      {!detailedSub ? (
                         <div className="flex items-center justify-center h-full text-sm text-text-muted animate-pulse">Loading submission code...</div>
                      ) : (
                        <DiffEditor
                          height="100%"
                          language="python"
                          theme={resolvedTheme === 'dark' ? 'vs-dark' : 'light'}
                          original={taskDetails?.data?.starter_code || taskDetails?.starter_code || detailedSub?.coding_session?.initial_code || '# No starter code available'}
                          modified={detailedSub?.raw_code || detailedSub?.code || '# No code provided'}
                          options={{
                            ...editorOptions,
                            readOnly: true,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            renderSideBySide: true,
                            wordWrap: "on"
                          }}
                        />
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-text-muted italic bg-bg-panel p-6 rounded-xl border border-border-subtle text-center">
                  No submission found for this student.
                </div>
              )}"""

content = content[:start_idx] + new_block + content[end_idx:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Right Panel UI 3")
