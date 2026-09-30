import os
import re

filepath = "frontend/src/features/dashboard/InstructorDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

needs_grading_ui = """
              <div className="mb-6 mt-6 h-px bg-border-subtle" />

              <section className="flex-1 flex flex-col">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-text-muted">Needs Grading</h2>
                  {reviewQueue.length > 5 && (
                    <button 
                      onClick={() => navigate("/instructor/bench")}
                      className="text-[10px] text-psu-gold hover:underline"
                    >
                      View all ({reviewQueue.length})
                    </button>
                  )}
                </div>

                <div className="flex flex-col gap-3 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                  {reviewQueue.length === 0 ? (
                    <div className="text-center py-8 bg-bg-glass rounded-xl border border-dashed border-border-subtle">
                      <p className="text-xs text-text-muted">All caught up!</p>
                    </div>
                  ) : (
                    reviewQueue.slice(0, 5).map((sub) => (
                      <div key={sub.id} className="group flex flex-col gap-2 rounded-xl bg-bg-glass p-3 border border-border-subtle hover:border-psu-gold/30 transition-colors">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-xs font-semibold text-text-main line-clamp-1">{sub.task?.title || 'Unknown Task'}</p>
                            <p className="text-[10px] text-text-muted mt-0.5">{sub.user?.full_name || sub.user?.name || 'Student'}</p>
                          </div>
                          <span className="shrink-0 rounded bg-psu-maroon/20 px-1.5 py-0.5 text-[9px] font-bold text-psu-gold uppercase">
                            New
                          </span>
                        </div>
                        
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-subtle/50">
                          <div className="flex items-center gap-2">
                            {sub.similarity_score > 70 ? (
                              <span className="text-[10px] text-psu-red font-medium flex items-center gap-1" title="High Similarity Flag">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                Flagged
                              </span>
                            ) : (
                              <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                AST Pass
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => navigate(`/instructor/submissions/${sub.id}`)}
                            className="text-[10px] bg-psu-gold/10 hover:bg-psu-gold/20 text-psu-gold px-2 py-1 rounded transition-colors font-semibold"
                          >
                            Grade Now
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
"""

if "Needs Grading" not in content:
    content = content.replace('</aside>', needs_grading_ui + '\n            </aside>')
    content = re.sub(r'const auditLogs = useMemo\(\(\) => \{.*?\n  \}, \[reviewQueue\]\);', '', content, flags=re.DOTALL)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected!")
