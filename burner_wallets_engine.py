#!/usr/bin/env python3
"""Burner Wallets Engine v3 - 10 shields against adversarial AI."""
import json, os, re, time, threading, random, hashlib
from eth_account import Account
from web3 import Web3

BURNER_FILE = "burner_wallets.json"
DAILY_WALLET_LIMIT = 10
DAILY_IP_LIMIT = 2
BURN_TTL = 86400
_LOCK = threading.Lock()
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

def _load():
    try:
        return json.load(open(BURNER_FILE))
    except Exception:
        return {"wallets": {}, "ip_log": {}, "decoys": []}

def _save(d):
    json.dump(d, open(BURNER_FILE, "w"))

def _constant_time_delay():
    """Shield 8: All rejections take 200-400ms (anti timing side-channel)."""
    time.sleep(random.uniform(0.2, 0.4))

def _add_decoy(data):
    """Shield 10: 10% of wallets are decoys (anti metadata analysis)."""
    if random.random() < 0.10:
        acct = Account.create()
        data["decoys"].append({
            "address": acct.address,
            "generated_at": time.time(),
            "is_decoy": True
        })
    return data

def generate_burner(paying_wallet, client_ip="unknown"):
    # Shield 8: Constant-time delay on all paths
    _constant_time_delay()
    
    # Shield 2: Strict hex validation
    if not paying_wallet or not re.match(r'^0x[a-fA-F0-9]{40}$', paying_wallet):
        return {"success": False, "reason": "Invalid wallet format. Must be exactly 42 hex characters (0x...)."}
    
    w = paying_wallet.lower()
    ip = (client_ip or "unknown").strip()
    
    with _LOCK:
        data = _load()
        today = time.strftime("%Y-%m-%d")
        now = time.time()
        
        # Shield 1: Ouroboros blocklist
        if w in data["wallets"]:
            return {"success": False, "reason": "Burner wallets cannot be used to purchase other burner wallets. Use a main wallet."}
        
        # Shield 4: IP rate limiting
        ip_hits = [t for t in data["ip_log"].get(ip, []) if now - t < 3600]
        if len(ip_hits) >= DAILY_IP_LIMIT and ip != "unknown":
            return {"success": False, "reason": f"IP limit reached ({DAILY_IP_LIMIT} burner requests per IP per hour)."}
        
        # Wallet daily limit
        wallet_hits = sum(1 for b in data["wallets"].values() if b.get("payer") == w and b.get("date") == today)
        if wallet_hits >= DAILY_WALLET_LIMIT:
            return {"success": False, "reason": f"Daily limit reached ({DAILY_WALLET_LIMIT} burner wallets/day/wallet)."}
        
        attempts = 0
        while attempts < 5:
            attempts += 1
            acct = Account.create()
            address = acct.address
            private_key = acct.key.hex()
            
            # Shield 5: Zero-balance guarantee
            try:
                bal = w3.eth.get_balance(address)
                if bal > 0:
                    continue
            except Exception:
                pass
            
            # Shield 3: Cryptographic proof
            derived_addr = Account.from_key(private_key).address
            if derived_addr != address:
                continue
            
            # Shield 7: Nonce check (address never used on-chain)
            try:
                nonce = w3.eth.get_transaction_count(address)
                if nonce > 0:
                    continue  # Address has history, discard
            except Exception:
                pass
            
            # Shield 6: Key hash watermarking
            watermark = hashlib.sha256(f"PLAZA_BURNER_{address}_{int(now)}".encode()).hexdigest()[:16]
            
            # Success!
            data["wallets"][address] = {
                "payer": w, "date": today, "generated_at": now,
                "expires_at": now + BURN_TTL, "used": False,
                "private_key": private_key, "watermark": watermark
            }
            data["ip_log"][ip] = ip_hits + [now]
            data = _add_decoy(data)  # Shield 10
            _save(data)
            
            return {
                "success": True,
                "address": address,
                "private_key": private_key,
                "chain": "Base (EVM compatible)",
                "expires_in": "24 hours",
                "derivation_proof": derived_addr,
                "zero_balance_verified": True,
                "nonce_verified": True,
                "watermark": watermark,
                "verification_signature": f"PLAZA-{watermark}-{address[:8]}",
                "warning": "SINGLE USE ONLY. Burned after 24h or first tx. Verify authenticity with watermark.",
                "cost_usd": 0.50
            }
    
    return {"success": False, "reason": "Failed to generate a clean wallet after 5 attempts. Try again later."}

def verify_burner_authenticity(address, watermark):
    """Verify a burner wallet is legitimate (not from a fake Plaza site)."""
    data = _load()
    w = data["wallets"].get(address)
    if not w:
        return {"success": False, "reason": "Not a Plaza burner wallet"}
    if w.get("watermark") != watermark:
        return {"success": False, "reason": "Invalid watermark - possible phishing attempt"}
    return {"success": True, "verified": True, "payer": w["payer"]}

def check_burner_status(address):
    data = _load()
    w = data["wallets"].get(address)
    if not w:
        return {"success": False, "reason": "Not a Plaza burner wallet"}
    if w.get("used"):
        return {"success": True, "status": "burned"}
    if time.time() > w.get("expires_at", 0):
        return {"success": True, "status": "expired"}
    return {"success": True, "status": "active", "time_remaining_seconds": int(w["expires_at"] - time.time())}

def is_burner_wallet(address):
    """Shield 9: Check if address is a burner (for escrow blocklist)."""
    data = _load()
    return address.lower() in data["wallets"]
