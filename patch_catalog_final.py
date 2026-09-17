import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

vip_endpoints = """
            "/oracle": {"price": "2.5% (min 0.05 USDC)", "desc": "Cryptographic Proof of Action (Escrow Oracle). Double-sealed verdict."},
            "/redteam": {"price": "150.00 USDC", "desc": "Red-Team Range: uncensored attack research (air-gapped). Refunds on refusal."},
            "/forensics": {"price": "300.00 USDC", "desc": "Black Box Forensics: post-hack autopsy (air-gapped). Refunds on failure."},
"""

# Find the start of the "/airgap" endpoint in the catalog dictionary
if '"/oracle"' not in s:
    # Inject right before /airgap
    s = s.replace('"/airgap": {', vip_endpoints + '            "/airgap": {', 1)
    print("PATCHED: 3 VIP spines added to the storefront catalog!")
else:
    print("ALREADY PATCHED: VIPs are in the catalog.")

open(p, 'w').write(s)
