import re
with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add import
c = c.replace('import remarkGfm from "remark-gfm";', 'import remarkGfm from "remark-gfm";\nimport remarkBreaks from "remark-breaks";')

# Add remarkBreaks
c = c.replace('remarkPlugins={[remarkGfm]}', 'remarkPlugins={[remarkGfm, remarkBreaks]}')

# Fix light mode prose styles (from `prose-invert` to `dark:prose-invert`)
c = c.replace('className="prose prose-invert prose-emerald max-w-none mb-12"', 'className="prose dark:prose-invert prose-emerald max-w-none mb-12"')
c = c.replace('className="prose prose-invert prose-sm max-w-none text-text-main"', 'className="prose dark:prose-invert prose-sm max-w-none text-text-main"')
c = c.replace('className="prose prose-invert prose-sm max-w-none text-indigo-100"', 'className="prose dark:prose-invert prose-sm max-w-none text-indigo-900 dark:text-indigo-100"')

with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)