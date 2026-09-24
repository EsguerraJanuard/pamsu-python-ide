import re
with open('backend/Dockerfile', 'r', encoding='utf-8') as f:
    c = f.read()

t = '''# Copy requirements and install'''
r = '''# Install Docker CLI so the FastAPI app can spawn sandbox containers
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Copy requirements and install'''

c = c.replace(t, r)
with open('backend/Dockerfile', 'w', encoding='utf-8') as f:
    f.write(c)