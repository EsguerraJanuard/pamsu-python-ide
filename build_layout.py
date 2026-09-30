import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. We will completely extract the 'Expected Output' div and the 'Difficulty Level' div.
expected_output_full = """                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
                    <div>
                      <label htmlFor="expected_output" className="block text-xs font-semibold text-text-muted mb-1.5">Expected Output</label>
                      <textarea
                        id="expected_output"
                        name="expected_output"
                        value={formData.expected_output}
                        onChange={handleChange}
                        rows={3}
                        placeholder="Target output string..."
                        className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-brand focus:outline-none focus:border-psu-maroon transition-colors h-full"
                      />
                    </div>

                    <div className="relative h-full flex flex-col gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-text-muted mb-1.5">
                          Difficulty Level <span className="text-text-brand">*</span>
                        </label>
                        <div className="flex bg-bg-base border border-border-subtle rounded-xl p-1">
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
                      </div>
                    </div>
                  </div>"""

analyzer_full = """                  <div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 flex flex-col">
                    <h2 className="text-sm font-bold uppercase tracking-wider text-text-brand pb-2 border-b border-border-subtle mb-4 flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-text-brand" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                      </svg>
                      Smart Solution Analyzer
                    </h2>
                    <p className="text-xs text-text-muted mb-4">Paste your complete working solution below. The system will automatically detect the difficulty and required Python constructs for you.</p>
                    
                    <div className="flex-1 min-h-[180px]">
                      <textarea
                        id="reference_code"
                        name="reference_code"
                        value={formData.reference_code}
                        onChange={handleChange}
                        rows={8}
                        placeholder="# def my_solution():\n#     print('Hello World')"
                        className="w-full h-full bg-[#0f1117] border border-border-subtle rounded-xl p-4 text-text-main font-mono text-xs focus:outline-none focus:border-psu-maroon dark:focus:border-psu-gold transition-colors resize-none"
                      />
                    </div>
                    
                    {analyzeError && (
                      <div className="text-xs text-text-rose mt-2">{analyzeError}</div>
                    )}

                    <div className="flex justify-end pt-3">
                      <button
                        type="button"
                        onClick={handleAnalyzeCode}
                        disabled={isAnalyzing || !formData.reference_code.trim()}
                        className="rounded-lg bg-psu-maroon dark:bg-psu-gold px-4 py-2 text-xs font-semibold text-white dark:text-black shadow-md shadow-psu-maroon/20 dark:shadow-psu-gold/20 transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {isAnalyzing ? (
                          <>
                            <svg className="animate-spin h-4 w-4 text-white dark:text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            Analyze Solution
                          </>
                        )}
                      </button>
                    </div>
                  </div>"""

instructions_block = """                  <div>
                    <label htmlFor="instructions" className="block text-xs font-semibold text-text-muted mb-1.5">Detailed Student Instructions</label>
                    <textarea
                      id="instructions"
                      name="instructions"
                      value={formData.instructions}
                      onChange={handleChange}
                      rows={8}
                      placeholder="Step-by-step instructions for completing the task..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-psu-maroon transition-colors"
                    />
                  </div>"""

# Ensure they exist in the file
if expected_output_full in content and analyzer_full in content and instructions_block in content:
    # Remove both chunks
    content = content.replace(expected_output_full, "")
    content = content.replace(analyzer_full, "")

    # Build the new layout
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
                      <div className="flex-1 min-h-[180px] relative">
                        <textarea
                          id="reference_code"
                          name="reference_code"
                          value={formData.reference_code}
                          onChange={handleChange}
                          placeholder="# Paste working implementation here..."
                          className="w-full h-full bg-bg-base border border-border-subtle rounded-xl p-3 text-text-main font-mono text-xs focus:outline-none focus:border-psu-maroon transition-colors resize-none"
                        />
                        {analyzeError && (
                          <div className="absolute -bottom-6 left-0 text-xs text-text-rose">{analyzeError}</div>
                        )}
                        <div className="absolute bottom-3 right-3">
                          <button
                            type="button"
                            onClick={handleAnalyzeCode}
                            disabled={isAnalyzing || !formData.reference_code.trim()}
                            className="rounded-lg bg-bg-glass border border-border-strong px-3 py-1.5 text-xs font-semibold text-text-main hover:bg-psu-maroon hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
                      <div className="bg-bg-glass rounded-xl border border-border-subtle p-3 flex-1 flex flex-col items-center justify-center text-center">
                         <p className="text-[10px] text-text-muted">
                           The Reference Code Analyzer will automatically select the difficulty and check required AST rules for you.
                         </p>
                      </div>
                    </div>
                  </div>"""

    # Inject immediately after Instructions
    target_instructions = instructions_block
    replacement_instructions = target_instructions + "\n" + new_expected_output_standalone + "\n" + new_side_by_side
    
    content = content.replace(target_instructions, replacement_instructions)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
else:
    print("Could not find the exact text blocks to replace. Attempting fallback...")
