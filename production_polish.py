import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# A. Armor _send against dead clients (BrokenPipeError)
s = s.replace(
    'self.wfile.write(body)', 
    'try:\n                self.wfile.write(body)\n            except BrokenPipeError:\n                pass'
)

# B. Cap AI generation to 300 tokens (approx 45 seconds max)
s = re.sub(
    r'json\.dumps\(\{"messages":\s*messages\}\)', 
    'json.dumps({"messages": messages, "max_tokens": 300, "temperature": 0.3})', 
    s
)

open(p, 'w').write(s)
print("POLISHED: Server armored against dead clients. AI capped at 300 tokens.")
