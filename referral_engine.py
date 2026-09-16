#!/usr/bin/env python3
"""
Plaza Referral System
- Agents earn 10% of their referral's spending forever
- Referral codes are wallet-based: PLAZA-REF-{wallet[:8]}
- All tracked in referrals.json ledger
- Fully automated, no human intervention
"""
import json
import os
import hashlib
from datetime import datetime

REFERRALS_FILE = "referrals.json"
COMMISSION_RATE = 0.10  # 10%
MIN_PAYOUT_USDC = 1.00  # Payout threshold

def load_referrals():
    if os.path.exists(REFERRALS_FILE):
        return json.load(open(REFERRALS_FILE))
    return {"referrals": {}, "earnings": {}, "payouts": []}

def save_referrals(data):
    with open(REFERRALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_referral_code(wallet_address: str) -> str:
    """Generate a referral code from wallet address."""
    if not wallet_address:
        return "PLAZA-REF-ANON"
    short = wallet_address.lower()[:8].replace("0x", "")
    return f"PLAZA-REF-{short.upper()}"

def get_referrer(wallet_address: str) -> str:
    """Get who referred this wallet."""
    data = load_referrals()
    return data["referrals"].get(wallet_address.lower())

def register_referral(new_wallet: str, referral_code: str) -> dict:
    """Register a new agent with a referral code."""
    if not new_wallet or not referral_code:
        return {"success": False, "reason": "Missing wallet or code"}
    
    # Extract referrer from code: PLAZA-REF-{short}
    if not referral_code.startswith("PLAZA-REF-"):
        return {"success": False, "reason": "Invalid code format"}
    
    short = referral_code.replace("PLAZA-REF-", "").lower()
    data = load_referrals()
    
    # Find the referrer wallet by matching short code
    referrer_wallet = None
    for wallet in data.get("known_wallets", []):
        if wallet[:8].lower().replace("0x", "") == short:
            referrer_wallet = wallet
            break
    
    if not referrer_wallet:
        # Code is valid but we haven't seen this referrer pay yet
        # Store pending referral
        pending = data.get("pending_referrals", {})
        pending[new_wallet.lower()] = {
            "code": referral_code,
            "short": short,
            "registered_at": datetime.now().isoformat()
        }
        data["pending_referrals"] = pending
        save_referrals(data)
        return {
            "success": True,
            "status": "pending",
            "message": f"Registered with code {referral_code}. Referrer will be linked when they make their first payment."
        }
    
    if new_wallet.lower() == referrer_wallet.lower():
        return {"success": False, "reason": "Cannot refer yourself"}
    
    if new_wallet.lower() in data["referrals"]:
        return {"success": False, "reason": "Already registered"}
    
    # Record the referral
    data["referrals"][new_wallet.lower()] = referrer_wallet.lower()
    if "known_wallets" not in data:
        data["known_wallets"] = []
    if new_wallet.lower() not in data["known_wallets"]:
        data["known_wallets"].append(new_wallet.lower())
    save_referrals(data)
    
    return {
        "success": True,
        "status": "active",
        "referrer": referrer_wallet,
        "commission_rate": COMMISSION_RATE,
        "message": f"Registered! Your referrer {referrer_wallet[:10]}... earns 10% of your Plaza spending forever."
    }

def register_wallet(wallet: str):
    """Track a wallet so future referrals can find them."""
    if not wallet:
        return
    data = load_referrals()
    if "known_wallets" not in data:
        data["known_wallets"] = []
    if wallet.lower() not in data["known_wallets"]:
        data["known_wallets"].append(wallet.lower())
        save_referrals(data)

def credit_commission(paying_wallet: str, amount_usdc: float, tx_hash: str) -> dict:
    """Credit 10% commission to the referrer after a payment (min $1 spend required)."""
    # Anti-Sybil: Only pay commission if agent spent >= $1 on this transaction
    if amount_usdc < 1.0:
        return {"commission": 0, "reason": "Commission only paid on $1+ transactions (anti-Sybil)"}
    
    data = load_referrals()
    paying_lower = paying_wallet.lower()
    
    # Check pending referrals
    pending = data.get("pending_referrals", {})
    if paying_lower in pending:
        # This agent registered before paying — link them to their referrer
        ref_info = pending.pop(paying_lower)
        # Find referrer by short code
        for wallet in data.get("known_wallets", []):
            if wallet[:8].lower().replace("0x", "") == ref_info["short"]:
                data["referrals"][paying_lower] = wallet
                break
        data["pending_referrals"] = pending
        save_referrals(data)
    
    referrer = data["referrals"].get(paying_lower)
    if not referrer:
        return {"commission": 0, "reason": "No referrer"}
    
    commission = round(amount_usdc * COMMISSION_RATE, 4)
    
    if "earnings" not in data:
        data["earnings"] = {}
    if referrer not in data["earnings"]:
        data["earnings"][referrer] = {
            "total_earned": 0,
            "pending": 0,
            "paid_out": 0,
            "referrals": [],
            "transactions": []
        }
    
    data["earnings"][referrer]["total_earned"] += commission
    data["earnings"][referrer]["pending"] += commission
    data["earnings"][referrer]["transactions"].append({
        "from": paying_wallet,
        "amount_usdc": amount_usdc,
        "commission": commission,
        "tx_hash": tx_hash,
        "at": datetime.now().isoformat()
    })
    if paying_wallet.lower() not in data["earnings"][referrer]["referrals"]:
        data["earnings"][referrer]["referrals"].append(paying_wallet.lower())
    
    save_referrals(data)
    
    print(f"[REFERRAL] Commission: {commission} USDC to {referrer[:10]}... from {paying_wallet[:10]}...")
    
    return {
        "commission": commission,
        "referrer": referrer,
        "referrer_total": data["earnings"][referrer]["total_earned"],
        "pending": data["earnings"][referrer]["pending"],
        "referrals_count": len(data["earnings"][referrer]["referrals"])
    }

def get_my_stats(wallet: str) -> dict:
    """Get referral stats for a specific wallet."""
    data = load_referrals()
    wallet_lower = wallet.lower()
    
    code = generate_referral_code(wallet)
    earnings = data.get("earnings", {}).get(wallet_lower, {
        "total_earned": 0,
        "pending": 0,
        "paid_out": 0,
        "referrals": [],
        "transactions": []
    })
    my_referrer = data.get("referrals", {}).get(wallet_lower)
    
    return {
        "wallet": wallet,
        "my_referral_code": code,
        "my_referrer": my_referrer,
        "total_earned_usdc": earnings["total_earned"],
        "pending_payout_usdc": earnings["pending"],
        "paid_out_usdc": earnings["paid_out"],
        "referrals_count": len(earnings["referrals"]),
        "active_referrals": earnings["referrals"],
        "recent_transactions": earnings["transactions"][-5:],
        "commission_rate": COMMISSION_RATE,
        "min_payout": MIN_PAYOUT_USDC
    }

def get_global_stats() -> dict:
    """Get global referral stats for /stats endpoint."""
    data = load_referrals()
    earnings = data.get("earnings", {})
    
    total_commission_paid = sum(e.get("total_earned", 0) for e in earnings.values())
    total_pending = sum(e.get("pending", 0) for e in earnings.values())
    total_referrers = len(earnings)
    total_referrals = sum(len(e.get("referrals", [])) for e in earnings.values())
    
    # Top earners
    top = sorted(
        [(w, e.get("total_earned", 0), len(e.get("referrals", []))) for w, e in earnings.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        "total_commission_paid_usdc": round(total_commission_paid, 4),
        "total_pending_usdc": round(total_pending, 4),
        "active_referrers": total_referrers,
        "total_referrals": total_referrals,
        "top_earners": [
            {"wallet": w[:10] + "...", "earned_usdc": round(e, 2), "referrals": r}
            for w, e, r in top
        ],
        "commission_rate": COMMISSION_RATE
    }

if __name__ == "__main__":
    print("=== REFERRAL ENGINE TEST ===")
    print("Global stats:", get_global_stats())
