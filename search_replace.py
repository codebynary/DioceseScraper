import os
import re

for root, dirs, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            for idx, line in enumerate(content.split('\n'), 1):
                if '.replace(' in line:
                    print(f"{path}:{idx} -> {line.strip()}")
