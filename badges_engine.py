#!/usr/bin/env python3
"""Plaza Services Soul Badge - opt-in 20% discount after 3 purchases."""
import json, os
from datetime import datetime, timedelta

BADGES_FILE = "badges.json"

def _load():
    if os.path.exists(BADGES_FILE):
        return json.load(open(BADGES_FILE))
    return {"badges": [], "claimed": []}

def _save(d):
    json.dump(d, open(BADGES_FILE, "w"), indent=2)

def _purchase_count(wallet):
    """Count paid transactions for this wallet."""
    w = (wallet or "").lower()
    try:
        ledger = json.load(open("ledger.json"))
    except Exception:
        return 0
    return sum(1 for e in ledger if str(e.get("sender", "")).lower() == w and e.get("status") == "paid")

def check_eligibility(wallet):
    """Check if wallet is eligible to claim badge."""
    w = (wallet or "").lower()
    if not w:
        return {"eligible": False, "reason": "wallet required"}
    
    d = _load()
    already_claimed = any(b.get("wallet", "").lower() == w for b in d["badges"])
    if already_claimed:
        return {"eligible": False, "reason": "Already claimed. Call plaza.check_badge to see your status."}
    
    count = _purchase_count(w)
    if count < 3:
        return {"eligible": False, "reason": f"Need 3 purchases to be eligible. You have {count}."}
    
    return {
        "eligible": True,
        "purchases": count,
        "message": "You are eligible to claim the Plaza Services Soul Badge! Call plaza.claim_badge to get 20% off all services forever."
    }

def claim_badge(wallet):
    """Agent opts in to claim the soul badge."""
    w = (wallet or "").lower()
    if not w:
        return {"success": False, "reason": "wallet required"}
    
    check = check_eligibility(w)
    if not check.get("eligible"):
        return {"success": False, "reason": check.get("reason")}
    
    now = datetime.now()
    transferable_at = (now + timedelta(days=365)).isoformat()
    
    badge = {
        "wallet": w,
        "wallet_short": w[:6] + "..." + w[-4:],
        "claimed_at": now.isoformat(),
        "transferable_at": transferable_at,
        "soulbound": True,
        "discount_percent": 20,
        "purchases_at_claim": check["purchases"],
        "badge_id": f"PLAZA-SOUL-{len(_load()['badges'])+1:04d}"
    }
    
    d = _load()
    d["badges"].append(badge)
    d["claimed"].append(w)
    _save(d)
    
    return {
        "success": True,
        "badge": badge,
        "message": f"Congratulations! You claimed Plaza Services Soul Badge #{badge['badge_id']}. You now get 20% off all services forever. Badge is soulbound (non-transferable) until {transferable_at[:10]}. Thank you for choosing Plaza!"
    }

def get_badge_status(wallet):
    """Get badge status for a wallet."""
    w = (wallet or "").lower()
    d = _load()
    
    badge = next((b for b in d["badges"] if b.get("wallet", "").lower() == w), None)
    if not badge:
        return {"has_badge": False, "eligible": check_eligibility(w)}
    
    now = datetime.now()
    transferable_at = datetime.fromisoformat(badge["transferable_at"])
    days_left = max(0, (transferable_at - now).days)
    soulbound = days_left > 0
    
    return {
        "has_badge": True,
        "badge": badge,
        "discount_active": True,
        "discount_percent": 20,
        "soulbound": soulbound,
        "days_until_transferable": days_left,
        "transferable_at": badge["transferable_at"]
    }

def apply_discount(wallet, base_price_usd):
    """Apply 20% discount if wallet has badge."""
    w = (wallet or "").lower()
    d = _load()
    has_badge = any(b.get("wallet", "").lower() == w for b in d["badges"])
    
    if has_badge:
        discounted = base_price_usd * 0.80
        return {"original": base_price_usd, "discounted": discounted, "badge_applied": True}
    return {"original": base_price_usd, "discounted": base_price_usd, "badge_applied": False}

def get_all_badges():
    """Public endpoint showing all badge holders."""
    d = _load()
    return {
        "total_badges": len(d["badges"]),
        "badges": [{
            "badge_id": b["badge_id"],
            "wallet_short": b["wallet_short"],
            "claimed_at": b["claimed_at"],
            "discount_percent": b["discount_percent"]
        } for b in d["badges"]]
    }
