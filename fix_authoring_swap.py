import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Rename "Smart Activity Generator" to "Smart Solution Analyzer"
content = content.replace("Smart Activity Generator", "Smart Solution Analyzer")

# 2. Swap positions
expected_output_start = content.find('<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">')
smart_analyzer_start = content.find('<div className="bg-bg-glass p-6 rounded-2xl border border-psu-maroon/20')

if expected_output_start != -1 and smart_analyzer_start != -1:
    # Find the end of the Expected Output div
    # The Expected Output div ends right before the Smart Analyzer div starts
    expected_output_block = content[expected_output_start:smart_analyzer_start]
    
    # Find the end of the Smart Analyzer block
    # It ends right before the "Starter Code Template"
    starter_code_start = content.find('<div className="flex-1 bg-bg-glass p-6 rounded-2xl border border-border-subtle flex flex-col">')
    
    if starter_code_start != -1:
        smart_analyzer_block = content[smart_analyzer_start:starter_code_start]
        
        # Now construct the new content
        new_content = (
            content[:expected_output_start] + 
            smart_analyzer_block + 
            expected_output_block + 
            content[starter_code_start:]
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Swapped positions and renamed.")
    else:
        print("Could not find starter_code_start")
else:
    print("Could not find start indices")
