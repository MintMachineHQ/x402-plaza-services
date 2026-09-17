p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

import re

# Remove /tunnel block
s = re.sub(r'\s+if self\.path == "/tunnel":.*?(?=\n\s+if self\.path == "(/reviews|/oracle|/memory|/airgap))', '\n        if self.path == "\\1"', s, flags=re.S)
# Fallback manual strip for tunnel if regex misses
if 'if self.path == "/tunnel":' in s:
    lines = s.split('\n')
    out = []
    skip = False
    for line in lines:
        if 'if self.path == "/tunnel":' in line: skip = True; continue
        if skip and line.strip().startswith('if self.path =='): skip = False
        if not skip: out.append(line)
    s = '\n'.join(out)

# Remove /memory block
if 'if self.path == "/memory":' in s:
    lines = s.split('\n')
    out = []
    skip = False
    for line in lines:
        if 'if self.path == "/memory":' in line: skip = True; continue
        if skip and line.strip().startswith('if self.path =='): skip = False
        if not skip: out.append(line)
    s = '\n'.join(out)

# Remove from catalog
s = re.sub(r'\s+"/tunnel":.*?,\n', '\n', s)
s = re.sub(r'\s+"/memory":.*?,\n', '\n', s)

# Revert version string
s = s.replace('X402 PLAZA SERVICES v5.2 HIPPOCAMPUS', 'X402 PLAZA SERVICES v5.0 ORACLE (High-Ticket Only)')
s = s.replace('X402 PLAZA SERVICES v5.1 TUNNEL', 'X402 PLAZA SERVICES v5.0 ORACLE (High-Ticket Only)')

open(p, 'w').write(s)
print("STRIPPED: Low-ticket items removed. Storefront is premium.")
