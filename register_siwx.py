#!/usr/bin/env python3
import json, requests, getpass, base64
from eth_account import Account
from eth_account.messages import encode_defunct

WALLET = "0xb838930bf3dFD467D30979E12c0a94286F86708D"
URL = "https://x402scan.com/api/x402/registry/register-origin"
ORIGIN = "https://oncoming-headband-unsoiled.ngrok-free.dev"

def main():
    print("=" * 60)
    print("X402scan SIWX (Authorization: SIWX <b64> format)")
    print("=" * 60)
    print(f"\nWallet: {WALLET}")
    
    pk = getpass.getpass("\nPaste PRIVATE KEY (hidden):\n> ").strip()
    if not pk.startswith("0x"): pk = "0x" + pk

    # Step 1: Get challenge
    print("\nFetching challenge...")
    r = requests.post(URL, json={"origin": ORIGIN}, timeout=10)
    if r.status_code != 402:
        print(f"Error {r.status_code}: {r.text}"); return
    data = r.json()
    siwx = data.get("extensions", {}).get("sign-in-with-x", {}).get("info")
    if not siwx: print("No SIWX info"); return
    
    # Step 2: Build & Sign
    msg = (f"{siwx['domain']} wants you to sign in with your Ethereum account:\n{WALLET}\n\n"
           f"{siwx.get('statement', 'Sign in')}\n\n"
           f"URI: {siwx['uri']}\nVersion: {siwx['version']}\n"
           f"Chain ID: {siwx['chainId']}\nNonce: {siwx['nonce']}\n"
           f"Issued At: {siwx['issuedAt']}\nExpiration Time: {siwx['expirationTime']}")
    
    acct = Account.from_key(pk)
    sig = acct.sign_message(encode_defunct(text=msg)).signature.hex()
    print(f"✓ Signed by: {acct.address}")

    # Step 3: Build SIWX credential object and try multiple formats
    siwx_cred = {
        "domain": siwx['domain'],
        "address": WALLET,
        "statement": siwx.get('statement', 'Sign in to verify your wallet identity'),
        "uri": siwx['uri'],
        "version": siwx['version'],
        "chainId": siwx['chainId'],
        "type": siwx.get('type', 'eip191'),
        "nonce": siwx['nonce'],
        "issuedAt": siwx['issuedAt'],
        "expirationTime": siwx['expirationTime'],
        "signature": sig
    }
    
    cred_json = json.dumps(siwx_cred)
    cred_b64 = base64.b64encode(cred_json.encode()).decode()
    
    # Try 4 different Authorization formats
    formats = [
        ("SIWX <b64>", {"Authorization": f"SIWX {cred_b64}"}),
        ("Bearer <b64>", {"Authorization": f"Bearer {cred_b64}"}),
        ("SIWX <json>", {"Authorization": f"SIWX {cred_json}"}),
        ("EIP191 <sig>", {"Authorization": f"EIP191 {WALLET}:{sig}"}),
    ]
    
    for name, headers in formats:
        headers["Content-Type"] = "application/json"
        print(f"\nTrying: Authorization: {name}")
        r2 = requests.post(URL, json={"origin": ORIGIN}, headers=headers, timeout=15)
        print(f"  Status: {r2.status_code}")
        if r2.status_code == 200:
            print(f"  🎉 SUCCESS! Format '{name}' worked!")
            print(f"  Response: {r2.text}")
            return
        elif r2.status_code != 402:
            print(f"  Response: {r2.text[:200]}")
    
    print("\n❌ All formats failed. Need to read agentcash source.")

if __name__ == "__main__":
    main()
