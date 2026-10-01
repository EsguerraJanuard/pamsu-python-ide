with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()
import re
c = re.sub(r'import ReactMarkdown from "react-markdown";\s*import remarkGfm from "remark-gfm";\s*import ReactMarkdown from "react-markdown";\s*import remarkGfm from "remark-gfm";', 'import ReactMarkdown from "react-markdown";\nimport remarkGfm from "remark-gfm";', c)
with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
