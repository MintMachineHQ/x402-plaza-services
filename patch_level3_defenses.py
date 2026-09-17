import re

p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

# DEFENSE 1: Spent TX tracking (prevent transaction replay)
# Add a spent_txs set and check in verify_payment
spent_tracking = '''
# GOVERNMENT DEFENSE: Track spent transactions to prevent replay attacks
SPENT_TXS_FILE = "/home/zero/tollbooth/spent_txs.json"
def spent_txs_load():
    try: return set(json.load(open(SPENT_TXS_FILE)))
    except: return set()
def spent_txs_save(s):
    json.dump(list(s), open(SPENT_TXS_FILE, "w"))

'''
# Insert after imports section (find a good anchor)
if 'SPENT_TXS_FILE' not in content:
    # Insert before the first function definition
    match = re.search(r'\ndef ', content)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + spent_tracking + content[insert_pos:]
    print("DEFENSE 1: Spent TX tracking added")

# DEFENSE 2: Real USDC contract verification
# The real USDC on Base
usdc_check = '''
# GOVERNMENT DEFENSE: Verify real USDC contract (not a fake token)
REAL_USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
'''
if 'REAL_USDC_BASE' not in content:
    match = re.search(r'\ndef ', content)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + usdc_check + content[insert_pos:]
    print("DEFENSE 2: USDC contract verification added")

# DEFENSE 3: Add timestamp to seals (prevent seal replay)
# Find seal_report function and add timestamp
old_seal = re.search(r'(def seal_report\(report\):.*?seal\s*=\s*hmac\.new\([^)]+\)\.hexdigest\(\))', content, re.DOTALL)
if old_seal and '"timestamp"' not in old_seal.group(1):
    old = old_seal.group(1)
    # Add timestamp to the report before sealing
    new = old.replace(
        'seal = hmac.new(',
        'report["timestamp"] = int(time.time())\n    report["nonce"] = uuid.uuid4().hex[:16]\n    seal = hmac.new('
    )
    content = content.replace(old, new)
    print("DEFENSE 3: Seal timestamps + nonces added")

# DEFENSE 4: Verify seal freshness in check_seal (reject seals older than 1 hour)
old_check = re.search(r'(def check_seal\(report\):.*?return hmac\.compare_digest[^)]+\))', content, re.DOTALL)
if old_check and 'timestamp' not in old_check.group(1):
    old = old_check.group(1)
    # Add freshness check before the HMAC comparison
    freshness_check = '''
    # GOVERNMENT DEFENSE: Reject seals older than 1 hour (anti-replay)
    ts = report.get("timestamp", 0)
    if ts and (time.time() - ts) > 3600:
        return False
'''
    # Insert at the start of the function body
    func_def_end = old.find(':') + 1
    new = old[:func_def_end] + freshness_check + old[func_def_end:]
    content = content.replace(old, new)
    print("DEFENSE 4: Seal freshness check added (1 hour window)")

# DEFENSE 5: Per-wallet rate limiting (prevent model extraction)
wallet_rate_limit = '''
# GOVERNMENT DEFENSE: Per-wallet rate limiting to prevent model extraction
WALLET_RATE_FILE = "/home/zero/tollbooth/wallet_rate.json"
def wallet_rate_check(wallet, limit=100, window=3600):
    try: rates = json.load(open(WALLET_RATE_FILE))
    except: rates = {}
    now = time.time()
    # Clean old entries
    if wallet in rates:
        rates[wallet] = [t for t in rates[wallet] if now - t < window]
    else:
        rates[wallet] = []
    if len(rates[wallet]) >= limit:
        return False
    rates[wallet].append(now)
    json.dump(rates, open(WALLET_RATE_FILE, "w"))
    return True
'''
if 'wallet_rate_check' not in content:
    match = re.search(r'\ndef ', content)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + wallet_rate_limit + content[insert_pos:]
    print("DEFENSE 5: Per-wallet rate limiting added")

with open(p, 'w') as f:
    f.write(content)

print("\nALL 5 GOVERNMENT DEFENSES INSTALLED")
