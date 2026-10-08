import os

filepath = r"C:\Users\ACER\.gemini\antigravity\brain\95ff588e-ebcc-4c7f-94fa-2c6bc0da8b69\qa_handoff_summary.md"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the "## Update (October 2)" section
if "## Update (October 2)" in content:
    original = content.split("## Update (October 2)")[0].strip()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(original + "\n")

print("Reverted qa_handoff_summary.md")
