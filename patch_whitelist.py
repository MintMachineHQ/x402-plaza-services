p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

if 'if ip == "127.0.0.1": return True' not in s:
    s = s.replace('def rate_ok(ip):', 'def rate_ok(ip):\n    if ip == "127.0.0.1": return True\n', 1)
    print("WHITELISTED: Localhost exempt from rate limits for CTO testing.")
open(p, 'w').write(s)
