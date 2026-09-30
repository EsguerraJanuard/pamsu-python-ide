import os
import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Build regex pattern spanning from instructions label down to difficulty level closing tags
pattern = re.compile(
    r'(<label htmlFor="instructions".*?)(<div className="flex-1 bg-bg-glass p-6 rounded-2xl border border-border-subtle flex flex-col">)',
    re.DOTALL
)

match = pattern.search(content)
if match:
    # We will completely replace this section
    new_ui = """<label htmlFor="instructions" className="block text-xs font-semibold text-text-muted mb-1.5">Detailed Student Instructions</label>
                  <textarea
                    id="instructions"
                    name="instructions"
                    value={formData.instructions}
                    onChange={handleChange}
                    rows={6}
                    placeholder="Step-by-step instructions for completing the task..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-psu-maroon transition-colors"
                  />
                </div>

                <div>
                  <label htmlFor="expected_output" className="block text-xs font-semibold text-text-muted mb-1.5">Expected Output</label>
                  <textarea
                    id="expected_output"
                    name="expected_output"
                    value={formData.expected_output}
                    onChange={handleChange}
                    rows={4}
                    placeholder="Target output string..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-brand focus:outline-none focus:border-psu-maroon transition-colors"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
                  <div className="flex flex-col h-full relative">
                    <label className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center gap-1.5">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-text-brand" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                      </svg>
                      Reference Code Analyzer
                    </label>
                    
                    <div className="flex-1 min-h-[160px] relative">
                      <textarea
                        id="reference_code"
                        name="reference_code"
                        value={formData.reference_code}
                        onChange={handleChange}
                        placeholder="# Paste working implementation here..."
                        className="w-full h-full bg-bg-base border border-border-subtle rounded-xl p-3 pb-12 text-text-main font-mono text-xs focus:outline-none focus:border-psu-maroon transition-colors resize-none"
                      />
                      {analyzeError && (
                        <div className="absolute -bottom-6 left-0 text-xs text-text-rose">{analyzeError}</div>
                      )}
                      <div className="absolute bottom-3 right-3">
                        <button
                          type="button"
                          onClick={handleAnalyzeCode}
                          disabled={isAnalyzing || !formData.reference_code.trim()}
                          className="rounded-lg bg-bg-glass border border-border-strong px-3 py-1.5 text-xs font-semibold text-text-main hover:bg-psu-maroon hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
                        >
                          {isAnalyzing ? "Analyzing..." : "Analyze"}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="relative h-full flex flex-col gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-text-muted mb-1.5">
                        Difficulty Level <span className="text-text-brand">*</span>
                      </label>
                      <div className="flex bg-bg-base border border-border-subtle rounded-xl p-1 mb-3">
                        {['beginner', 'intermediate', 'expert'].map((level) => (
                          <button
                            key={level}
                            type="button"
                            onClick={() => handleDifficultyChange(level)}
                            className={`flex-1 py-2 text-xs font-semibold capitalize rounded-lg transition-colors ${
                              formData.difficulty === level 
                                ? 'bg-bg-glass text-text-brand shadow-sm border border-border-subtle' 
                                : 'text-text-muted hover:text-text-main hover:bg-bg-glass/50'
                            }`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                      
                      <div className="bg-bg-glass rounded-xl border border-border-subtle p-4 flex-1 flex flex-col items-center justify-center text-center">
                         <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-text-muted mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                         </svg>
                         <p className="text-[10px] text-text-muted max-w-[200px]">
                           The Reference Code Analyzer automatically selects the difficulty and checks required AST rules for you.
                         </p>
                      </div>
                    </div>
                  </div>
                </div>

                """
    
    # Replace the captured group 1 while preserving the end group 2
    content = content.replace(match.group(1), new_ui)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
else:
    print("Match failed.")
