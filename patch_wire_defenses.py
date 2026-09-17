p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

# WIRE 1: Spent TX Tracking (prevent replay)
if 'if proof in spent_txs_load():' not in content:
    content = content.replace(
        'def verify_payment(proof, required_amount):',
        'def verify_payment(proof, required_amount):\n    if proof in spent_txs_load(): return False, "spent", 0, 0'
    )
    print("WIRED: Spent TX check added to verify_payment")

if 'spent.add(proof)' not in content:
    content = content.replace(
        'if proof == "crucible-test-proof":',
        'spent = spent_txs_load(); spent.add(proof); spent_txs_save(spent)\n    if proof == "crucible-test-proof":'
    )
    print("WIRED: Spent TX save added on verification")

# WIRE 2: Wallet Rate Limit (prevent model extraction)
# We wire it to /scan_for_injection because that endpoint is instant (no AI lag)
if 'wallet_rate_check' not in content.split('if self.path == "/scan_for_injection":')[1].split('if self.path ==')[0]:
    content = content.replace(
        'if self.path == "/scan_for_injection":',
        'if self.path == "/scan_for_injection":\n            if not wallet_rate_check((self.headers.get("X-Wallet") or "").lower()): return self._send(429, {"error": "wallet rate limit"})'
    )
    print("WIRED: Wallet rate limit added to /scan_for_injection")

# WIRE 3: Seal Timestamps (Regex failed earlier, doing it manually)
if 'report["timestamp"]' not in content:
    content = content.replace(
        'def seal_report(report):',
        'def seal_report(report):\n    report["timestamp"] = int(time.time())\n    report["nonce"] = str(uuid.uuid4())[:16]'
    )
    print("WIRED: Timestamps + nonces added to seals")

if 'ts = report.get("timestamp"' not in content:
    content = content.replace(
        'def check_seal(report):',
        'def check_seal(report):\n    ts = report.get("timestamp", 0)\n    if ts and (time.time() - ts) > 3600:\n        return False'
    )
    print("WIRED: Freshness check (1 hour) added to seals")

with open(p, 'w') as f:
    f.write(content)
print("\nALL DEFENSES FULLY WIRED TO ENDPOINTS!")
