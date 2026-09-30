import re
import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

smart_ui = """
                  <div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 space-y-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h2 className="text-sm font-bold text-text-main flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-psu-gold" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                        </svg>
                        Smart Activity Generator
                      </h2>
                    </div>
                    <p className="text-xs text-text-muted mb-4">Paste your complete working solution below. The system will automatically detect the difficulty and required Python constructs for you.</p>
                    
                    <div className="flex-1 min-h-[180px]">
                      <textarea
                        id="reference_code"
                        name="reference_code"
                        value={formData.reference_code}
                        onChange={handleChange}
                        rows={8}
                        placeholder="# def my_solution():\n#     print('Hello World')"
                        className="w-full h-full bg-[#0f1117] border border-border-subtle rounded-xl p-4 text-text-main font-mono text-xs focus:outline-none focus:border-psu-gold transition-colors resize-none"
                      />
                    </div>
                    
                    {analyzeError && (
                      <div className="text-xs text-text-rose mt-2">{analyzeError}</div>
                    )}

                    <div className="flex justify-end pt-2">
                      <button
                        type="button"
                        onClick={handleAnalyzeCode}
                        disabled={isAnalyzing || !formData.reference_code.trim()}
                        className="rounded-lg bg-psu-gold px-4 py-2 text-xs font-semibold text-black shadow-md shadow-psu-gold/20 transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {isAnalyzing ? (
                          <>
                            <svg className="animate-spin h-4 w-4 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
                  </div>
"""

# Find where Starter Code starts
starter_code_header = """<div className="bg-bg-glass p-6 rounded-2xl border border-border-subtle flex flex-col h-full space-y-4">
                    <h2 className="text-sm font-bold text-text-main flex items-center gap-2">"""

if starter_code_header in content and "Smart Activity Generator" not in content:
    content = content.replace(starter_code_header, smart_ui + '\n' + starter_code_header)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected Smart UI successfully.")
else:
    print("Could not find the injection point!")

