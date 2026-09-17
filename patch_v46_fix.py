import re
s = open('/home/zero/tollbooth/cashier.py').read()

# Wrap the RPC urlopen in a try/except so it never crashes the thread
s = re.sub(
    r'(\s+)with urllib\.request\.urlopen\(req, timeout=\d+\) as resp:\n\1    return json\.loads\(resp\.read\(\)\)',
    r'\1try:\n\1    with urllib.request.urlopen(req, timeout=10) as resp:\n\1        return json.loads(resp.read())\n\1except Exception:\n\1    return None',
    s
)

# Update verify_payment to safely handle a failed RPC call
s = re.sub(
    r'(tx\s*=\s*rpc\([^\)]+\))\n',
    r'\1\n    if not tx or "result" not in tx: return False, "", 0, 0\n',
    s
)

open('/home/zero/tollbooth/cashier.py', 'w').write(s)
print("HOTFIX APPLIED: RPC crash shield installed.")
