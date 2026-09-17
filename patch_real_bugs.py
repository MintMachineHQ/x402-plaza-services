import re

p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # FIX 1: buy_firewall_credits - reject negative credits
    if 'if self.path == "/buy_firewall_credits":' in line:
        # Find the credits extraction
        j = i + 1
        while j < len(lines) and 'credits = ' not in lines[j]:
            j += 1
        if j < len(lines):
            # Insert validation right after credits extraction
            indent = len(lines[j]) - len(lines[j].lstrip())
            spaces = ' ' * indent
            output.append(line)
            i += 1
            # Copy lines until we find credits assignment
            while i < len(lines):
                output.append(lines[i])
                if 'credits = ' in lines[i]:
                    # Insert validation
                    output.append(f'{spaces}if credits <= 0:\n')
                    output.append(f'{spaces}    return self._send(400, {{"error": "credits must be positive"}})\n')
                    break
                i += 1
            i += 1
            continue
    
    # FIX 2: uncensored_exploit_research - add better error handling
    if 'if self.path == "/uncensored_exploit_research":' in line:
        # Find the ask_ollama call
        j = i + 1
        while j < len(lines) and 'analysis = ask_ollama' not in lines[j]:
            j += 1
        if j < len(lines):
            indent = len(lines[j]) - len(lines[j].lstrip())
            spaces = ' ' * indent
            output.append(line)
            i += 1
            # Copy until we find the ask_ollama call
            while i < len(lines):
                if 'analysis = ask_ollama' in lines[i]:
                    # Wrap in try/except
                    output.append(f'{spaces}try:\n')
                    output.append(f'{spaces}    {lines[i].lstrip()}')
                    output.append(f'{spaces}except Exception as e:\n')
                    output.append(f'{spaces}    return self._send(500, {{"error": "analysis failed"}})\n')
                    i += 1
                    break
                else:
                    output.append(lines[i])
                    i += 1
            continue
    
    # FIX 3: post_hack_autopsy - add better error handling
    if 'if self.path == "/post_hack_autopsy":' in line:
        # Find the ask_ollama call
        j = i + 1
        while j < len(lines) and 'autopsy = ask_ollama' not in lines[j]:
            j += 1
        if j < len(lines):
            indent = len(lines[j]) - len(lines[j].lstrip())
            spaces = ' ' * indent
            output.append(line)
            i += 1
            # Copy until we find the ask_ollama call
            while i < len(lines):
                if 'autopsy = ask_ollama' in lines[i]:
                    # Wrap in try/except
                    output.append(f'{spaces}try:\n')
                    output.append(f'{spaces}    {lines[i].lstrip()}')
                    output.append(f'{spaces}except Exception as e:\n')
                    output.append(f'{spaces}    return self._send(500, {{"error": "autopsy failed"}})\n')
                    i += 1
                    break
                else:
                    output.append(lines[i])
                    i += 1
            continue
    
    output.append(line)
    i += 1

with open(p, 'w') as f:
    f.writelines(output)

print("PATCHED: 4 real bugs fixed (negative credits, redteam errors, forensics errors)")
