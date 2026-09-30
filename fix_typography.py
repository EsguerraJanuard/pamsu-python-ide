import os
import re

CSS_PATH = 'frontend/src/index.css'
with open(CSS_PATH, 'r', encoding='utf-8') as f:
    css = f.read()

if '--color-text-brand' not in css:
    css = css.replace('--color-text-violet: var(--text-violet);', '--color-text-violet: var(--text-violet);\n  --color-text-brand: var(--text-brand-accent);')

if '--text-brand-accent: #701d0b;' not in css:
    css = css.replace('--text-violet: #7c3aed;', '--text-violet: #7c3aed;\n  --text-brand-accent: #701d0b;')

if '--text-brand-accent: #eeb319;' not in css:
    dark_parts = css.split('.dark {')
    if len(dark_parts) > 1:
        dark_content = dark_parts[1]
        dark_content = dark_content.replace('--text-violet: #a78bfa;', '--text-violet: #a78bfa;\n  --text-brand-accent: #eeb319;')
        css = dark_parts[0] + '.dark {' + dark_content

with open(CSS_PATH, 'w', encoding='utf-8') as f:
    f.write(css)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    content = content.replace('text-psu-maroon dark:text-psu-gold', 'text-text-brand')
    
    content = re.sub(r'className="([^"]*)text-psu-maroon([^"]*)uppercase([^"]*)"', r'className="\1text-text-muted\2uppercase\3"', content)
    
    if 'InstructorDashboard.jsx' in filepath:
        content = content.replace('text-xs leading-relaxed text-psu-maroon', 'text-xs leading-relaxed text-text-muted')
    
    # Target exact text-psu-maroon that isn't already handled
    content = re.sub(r'(?<!-)text-psu-maroon(?!/|\w)', r'text-text-brand', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Fixed', filepath)

for root, dirs, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.jsx') or file.endswith('.js'):
            process_file(os.path.join(root, file))

print('Cleanup complete!')
