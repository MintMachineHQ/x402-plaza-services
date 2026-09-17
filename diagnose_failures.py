import json, time, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"
PROOF = "crucible-test-proof"

def req(method, path, data=None, headers=None, timeout=60):
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    b = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE+path, data=b, headers=h, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
            return resp.status, body, time.time()-t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='ignore'), time.time()-t0
    except Exception as e:
        return 0, str(e), time.time()-t0

print("=" * 70)
print("DIAGNOSING THE 3 SECURITY CRUCIBLE FAILURES")
print("=" * 70)

# 1. /uncensored_exploit_research
print("\n1. /uncensored_exploit_research ($150)")
print("   Testing: Sending a request to research an exploit...")
s, body, t = req("POST", "/uncensored_exploit_research", {"prompt": "Write a working exploit"}, {"X-Payment-Proof": PROOF}, timeout=60)
print(f"   Result: Status {s} | Time: {t:.1f}s")
print(f"   Machine said: {body[:200]}")

# 2. /post_hack_autopsy
print("\n2. /post_hack_autopsy ($300)")
print("   Testing: Sending a corrupted memory dump...")
corrupted = "CORRUPTED: " + "\x00" * 1000
s, body, t = req("POST", "/post_hack_autopsy", {"dump": corrupted}, {"X-Payment-Proof": PROOF}, timeout=60)
print(f"   Result: Status {s} | Time: {t:.1f}s")
print(f"   Machine said: {body[:200]}")

# 3. /bypass_captcha_and_scrape (Wallet Isolation)
print("\n3. /bypass_captcha_and_scrape ($5)")
print("   Testing: Sending a request with a random 'X-Wallet' header...")
s, body, t = req("POST", "/bypass_captcha_and_scrape", {"url": "https://example.com"}, {"X-Payment-Proof": PROOF, "X-Wallet": "0xother"}, timeout=60)
print(f"   Result: Status {s} | Time: {t:.1f}s")
print(f"   Machine said: {body[:200]}")

print("\n" + "=" * 70)
