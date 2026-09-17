import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# 0) Proper User-Agent so RPC nodes stop 403-ing us (protects REAL paying customers too)
ua = '''class _UARequest(urllib.request.Request):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.add_header('User-Agent', 'x402-plaza/4.6')
urllib.request.Request = _UARequest

'''
if '_UARequest' not in s:
    s = s.replace('def rate_ok(ip):', ua + 'def rate_ok(ip):', 1)

# 1) Crash-shield the payment functions: ANY error inside = clean "unverified", never a crash
def wrap(fname, guard):
    global s
    m = re.search(r'(def ' + fname + r'\([^)]*\):\n)(.*?)(?=\ndef )', s, flags=re.S)
    if not m:
        print('MISS:', fname); return
    lines = [('    ' + l) if l.strip() else l for l in m.group(2).split('\n')]
    newbody = '    try:\n' + '\n'.join(lines)
    if not newbody.endswith('\n'): newbody += '\n'
    newbody += '    except Exception:\n        return ' + guard + '\n'
    s = s[:m.start()] + m.group(1) + newbody + s[m.end():]
    print('WRAPPED:', fname)

wrap('rpc', 'None')
wrap('verify_payment', 'False, "", 0, 0')
wrap('get_tier', '1.0')
open(p, 'w').write(s)
print('SHIELD COMPLETE')
