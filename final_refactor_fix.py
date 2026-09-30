import os
import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the Smart Activity Generator block completely
analyzer_standalone_pattern = re.compile(
    r'<div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 flex flex-col">\s*<h2.*?Smart Activity Generator.*?</div>\s*</div>',
    re.DOTALL
)
content = re.sub(analyzer_standalone_pattern, '', content)

# 2. Extract Expected Output from the grid using the correct self-closing tag syntax
grid_pattern = re.compile(
    r'<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\s*<div>\s*<label htmlFor="expected_output".*?/>\s*</div>',
    re.DOTALL
)

new_analyzer_in_grid = """<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
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
                    </div>"""

content = re.sub(grid_pattern, new_analyzer_in_grid, content)

# 3. Add Expected Output standalone below Instructions (also self-closing)
inst_pattern = re.compile(
    r'(<div>\s*<label htmlFor="instructions".*?/>\s*</div>)',
    re.DOTALL
)

new_eo_standalone = """                  <div>
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

def repl(m):
    return m.group(1) + "\n\n" + new_eo_standalone

content = re.sub(inst_pattern, repl, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fix Complete.")
