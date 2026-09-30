import os
import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Extract the Expected Output div
expected_output_match = re.search(r'(<div>\s*<label htmlFor="expected_output".*?</label>\s*<textarea[^>]*id="expected_output"[^>]*/>\s*</div>)', content, re.DOTALL)
if expected_output_match:
    expected_output_html = expected_output_match.group(1)
    
    # Remove it from its original grid
    content = content.replace(expected_output_html, '')
    
    # Wrap it nicely and put it after Instructions
    new_expected = f"""
                  <div>
                    {expected_output_html.replace('<div>', '').replace('</div>', '')}
                  </div>
"""
    instructions_end = '<textarea\n                      id="instructions"\n                      name="instructions"\n                      value={formData.instructions}\n                      onChange={handleChange}\n                      rows={8}\n                      placeholder="Step-by-step instructions for completing the task..."\n                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-psu-maroon transition-colors"\n                    />\n                  </div>'
    
    if instructions_end in content:
        content = content.replace(instructions_end, instructions_end + new_expected)

# 2. Extract and fix the Smart Analyzer
analyzer_match = re.search(r'(<div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 flex flex-col">.*?</div>\n                  </div>)', content, re.DOTALL)

if analyzer_match:
    analyzer_html = analyzer_match.group(1)
    
    # Simplify styling and change names
    analyzer_html = analyzer_html.replace('bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20 shadow-md shadow-psu-maroon/5 flex flex-col', 'flex flex-col h-full')
    analyzer_html = analyzer_html.replace('Smart Solution Analyzer', 'Reference Code Analyzer')
    analyzer_html = analyzer_html.replace('bg-[#0f1117] border border-border-subtle rounded-xl p-4 text-text-main', 'bg-bg-base border border-border-subtle rounded-xl p-3 text-text-main')
    analyzer_html = analyzer_html.replace('border-b border-border-subtle mb-4', 'mb-2')
    analyzer_html = analyzer_html.replace('pb-2 ', '')
    
    # Adjust padding of the title
    analyzer_html = analyzer_html.replace('<h2 className="text-sm font-bold uppercase tracking-wider text-text-brand mb-2 flex items-center gap-2">', '<label className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center gap-1.5">')
    analyzer_html = analyzer_html.replace('</h2>', '</label>')
    analyzer_html = analyzer_html.replace('<p className="text-xs text-text-muted mb-4">Paste your complete working solution below. The system will automatically detect the difficulty and required Python constructs for you.</p>', '')
    
    # Place it inside the grid alongside Difficulty Level
    # The grid was: <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
    # Wait, the Expected Output was there. We removed it, leaving an empty spot.
    
    # Remove the old standalone analyzer block
    content = content.replace(analyzer_match.group(1), '')
    
    # Find the grid:
    grid_match = re.search(r'(<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\s*<div className="relative h-full flex flex-col gap-4">)', content)
    if grid_match:
        content = content.replace(
            grid_match.group(1), 
            '<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\n                    ' + analyzer_html + '\n\n                    <div className="relative h-full flex flex-col gap-4">'
        )
    else:
        # Fallback if structure slightly differs
        content = content.replace('<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">', '<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\n                    ' + analyzer_html)

# Also fix the label if there was any left over Expected output div that we emptied
content = content.replace('<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\n                    \n\n                    <div className="relative h-full flex flex-col gap-4">', '<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">\n                    <div className="relative h-full flex flex-col gap-4">')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("UI Refactored!")
