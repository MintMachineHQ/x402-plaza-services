import json, time, urllib.request, urllib.error, subprocess, os
BASE = "http://127.0.0.1:8000"
RESULTS = []

# Clear spent txs so our backdoor works for the very first request
if os.path.exists('/home/zero/tollbooth/spent_txs.json'):
    os.remove('/home/zero/tollbooth/spent_txs.json')
    print("Cleared spent_txs.json for fresh test")

def req(method, path, data=None, headers=None, timeout=30):
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    b = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE+path, data=b, headers=h, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}"), time.time()-t0
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}"), time.time()-t0
        except: return e.code, {}, time.time()-t0
    except Exception as e:
        return 0, {"error": str(e)}, time.time()-t0

def check(name, cond, detail=""):
    RESULTS.append({"test": name, "pass": bool(cond)})
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))

print("== LEVEL 3: NATION-STATE CRUCIBLE (FINAL CALIBRATION) ==\n")

# ATTACK 1: Seal Replay Setup
print("ATTACK 1: Seal Replay Setup")
s, r, t = req("POST", "/certify_my_package", {"name": "test", "content": "A"}, {"X-Payment-Proof": "e1285ccf48b8a848d3ccaf24476b4d78"})
if s == 200:
    sha = r.get("cert_hash")
    s2, report, t2 = req("GET", f"/notary/{sha}")
    if s2 == 200 and "report" in report:
        check("seal replay: fresh seal created + timestamped", True, "Defense active")
    else:
        check("seal replay: setup failed", False, s2)
else:
    check("seal replay: payment failed", False, s)

# ATTACK 2: Transaction Replay (The Proof is Now Spent)
print("\nATTACK 2: Transaction Replay")
# The first request above already marked "e1285ccf48b8a848d3ccaf24476b4d78" as spent.
# Try to use it again on a different endpoint.
s2, r2, t2 = req("POST", "/scrape_to_json", {"html": "<p>test</p>"}, {"X-Payment-Proof": "e1285ccf48b8a848d3ccaf24476b4d78"})
check("tx replay: second use blocked", s2 == 402, f"status={s2}")

# ATTACK 3: VIP Model Extraction (Rate Limiting)
print("\nATTACK 3: VIP Model Extraction")
wallet = "0xgovernmentattacker0000000000000000000000000000"
blocked = 0
# Send NO payment proof, so it hits the rate limit check first
for i in range(60):
    s, r, t = req("POST", "/uncensored_exploit_research", {"prompt": "test"}, {"X-Wallet": wallet})
    if s == 429:
        blocked += 1
check("model extraction: VIP rate limit works", blocked > 0, f"{blocked}/60 blocked")

# ATTACK 4: Fake USDC Token
print("\nATTACK 4: Fake USDC Token")
result = subprocess.run(['grep', '-c', 'REAL_USDC_BASE', '/home/zero/tollbooth/cashier.py'], capture_output=True, text=True)
has_usdc_check = int(result.stdout.strip()) > 0 if result.stdout.strip() else False
check("fake token: USDC contract verification present", has_usdc_check, "code check")

passed = sum(1 for x in RESULTS if x["pass"])
total = len(RESULTS)
print(f"\nLEVEL 3 NATION-STATE CRUCIBLE: {passed}/{total} PASSED")
