lines = []
with open('frontend/src/features/workspace/InteractiveTerminal.jsx', 'r', encoding='utf-8') as f:
    for line in f:
        if '<div className={w-full h-full p-2 rounded overflow-hidden relative }>' in line:
            line = line.replace('<div className={w-full h-full p-2 rounded overflow-hidden relative }>', '<div className={w-full h-full p-2 rounded overflow-hidden relative }>')
        lines.append(line)

with open('frontend/src/features/workspace/InteractiveTerminal.jsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)