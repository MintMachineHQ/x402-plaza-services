import re

p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

# FIX 1: Wrap redteam ask_ollama in try/except
# Find the pattern: analysis = ask_ollama(...
content = re.sub(
    r'(analysis = ask_ollama\(messages\))',
    r'''try:
                \1
            except Exception as e:
                return self._send(500, {"error": "redteam analysis failed"})''',
    content
)

# FIX 2: Wrap forensics ask_ollama in try/except
# Find the pattern: autopsy = ask_ollama(...
content = re.sub(
    r'(autopsy = ask_ollama\(messages\))',
    r'''try:
                \1
            except Exception as e:
                return self._send(500, {"error": "forensics analysis failed"})''',
    content
)

with open(p, 'w') as f:
    f.write(content)

print("PATCHED: redteam and forensics endpoints now handle crashes gracefully")
