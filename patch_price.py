p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# Bump the payment gate from 1000 to 50000
s = s.replace('verify_payment(proof, 1000)', 'verify_payment(proof, 50000)')
# Update the 402 gate instruction
s = s.replace('"instruction": "Hippocampus: store a memory permanently."', '"instruction": "Hippocampus: store a memory permanently (0.05 USDC)."')
# Update the catalog
s = s.replace('"price": "0.001 USDC (store)"', '"price": "0.05 USDC (store)"')
open(p, 'w').write(s)
print("REPRICED: Hippocampus bumped to 0.05 USDC (50x more profitable)")
