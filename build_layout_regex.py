import os
import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove Expected Output grid wrapper
expected_output_match = re.search(r'<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">.*?<label htmlFor="expected_output".*?</textarea>\s*</div>', content, re.DOTALL)

if expected_output_match:
    expected_html = expected_output_match.group(0)
    # The grid also contains Difficulty Level. Let's extract the whole grid.
    full_grid_match = re.search(r'<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">.*?<div className="relative h-full flex flex-col gap-4">.*?Difficulty Level.*?</div>\s*</div>\s*</div>\s*</div>', content, re.DOTALL)
    
    if full_grid_match:
        grid_html = full_grid_match.group(0)
        content = content.replace(grid_html, '')
        
        # Also find Smart Analyzer
        analyzer_match = re.search(r'<div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 flex flex-col">.*?Smart Solution Analyzer.*?</div>\s*</div>', content, re.DOTALL)
        if analyzer_match:
            content = content.replace(analyzer_match.group(0), '')
        
        # Find Instructions
        inst_match = re.search(r'(<div>\s*<label htmlFor="instructions".*?</textarea>\s*</div>)', content, re.DOTALL)
        if inst_match:
            inst_html = inst_match.group(1)
            
            new_expected_output_standalone = """
                  <div>
                    <label htmlFor="expected_output" className="block text-xs font-semibold text-text-muted mb-1.5">Expected Output</label>
                    <textarea
                      id="expected_output"
                      name="expected_output"
                      value={formData.expected_output}
                      onChange={handleChange}
                      rows={4}
                      placeholder="Target output string..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-main focus:outline-none focus:border-psu-maroon transition-colors"
                    />
                  </div>"""

            new_side_by_side = """
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
                    <div className="flex flex-col h-full">
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

                    <div className="flex flex-col">
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
                           The Reference Code Analyzer will automatically select the difficulty and check required AST rules for you.
                         </p>
                      </div>
                    </div>
                  </div>"""
            
            content = content.replace(inst_html, inst_html + "\n" + new_expected_output_standalone + "\n" + new_side_by_side)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully refactored using regex.")
        else:
            print("Could not find instructions block.")
    else:
        print("Could not find full grid block.")
else:
    print("Could not find expected output block.")
