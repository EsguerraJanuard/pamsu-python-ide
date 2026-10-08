import glob

for f in glob.glob('app/**/*.py', recursive=True):
    with open(f, 'rb') as file:
        content = file.read()
    if content.startswith(b'\xef\xbb\xbf'):
        print(f"Removing BOM from {f}")
        with open(f, 'wb') as file:
            file.write(content[3:])
