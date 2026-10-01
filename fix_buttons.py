import re

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "r") as f:
    content = f.read()

# I will find the block starting with `<p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>`
# and ending at `)}` right before `{feedback.is_successful && (` (the duplicate)
# Let's just do it cleanly using regex.

# Search for the duplicate buttons block:
pattern = r'(<p className="text-sm font-medium mb-4 text-text-main">\{feedback\.message\}</p>\s*\{feedback\.is_successful && \(.*?\)\s*\})\s*\{feedback\.is_successful && \(.*?\)\s*\}'
content = re.sub(pattern, r'\1', content, flags=re.DOTALL)

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "w") as f:
    f.write(content)
print("Removed duplicate button logic")
