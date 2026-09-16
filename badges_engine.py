#!/usr/bin/env python3
"""Plaza Services Soul Badge - opt-in 20% discount with anti-gaming protection."""
import json, os
from datetime import datetime, timedelta

BADGES_FILE = "badges.json"

def _load():
    if os.path.exists(BADGES_FILE):
        return json.load(open(BADGES_FILE))
    return {"badges": [], "claimed": []}

def _save(d):
    json.dump(d, open(BADGES_FILE, "w"), indent=2)

def _purchase_history(wallet):
    """Get purchase history: count, total_spent, unique_services."""
    w = (wallet or "").lower()
    try:
        ledger = json.load(open("ledger.json"))
    except Exception:
        return 0, 0.0, set()
    
    count = 0
    total_spent = 0.0
    services = set()
    
    for e in ledger:
        if str(e.get("sender", "")).lower() == w and e.get("status") == "paid":
            count += 1
            try:
                total_spent += float(e.get("amount", 0))
            except Exception:
                pass
            services.add(e.get("service", "unknown"))
    
    return count, total_spent, services

def check_eligibility(wallet):
    """Check eligibility with 3-layer anti-gaming."""
    w = (wallet or "").lower()
    if not w:
        return {"eligible": False, "reason": "wallet required"}
    
    d = _load()
    if any(b.get("wallet", "").lower() == w for b in d["badges"]):
        return {"eligible": False, "reason": "Already claimed. Call plaza.check_badge."}
    
    count, total_spent, services = _purchase_history(w)
    
    if count < 3:
        return {"eligible": False, "reason": f"Need 3 purchases. You have {count}.", "progress": {"purchases": count, "required": 3}}
    
    if total_spent < 10.0:
        return {"eligible": False, "reason": f"Need $10 total spend (anti-gaming). You have ${total_spent:.2f}.", "progress": {"total_spent": total_spent, "required": 10.0}}
    
    if len(services) < 2:
        return {"eligible": False, "reason": f"Need 2+ different services (anti-gaming). You used: {sorted(services)}.", "progress": {"unique_services": len(services), "required": 2}}
    
    return {
        "eligible": True,
        "purchases": count,
        "total_spent": round(total_spent, 2),
        "unique_services": len(services),
        "message": "All anti-gaming checks passed! Call plaza.claim_badge for 20% off forever."
    }

def claim_badge(wallet):
    """Opt-in badge claim."""
    w = (wallet or "").lower()
    if not w:
        return {"success": False, "reason": "wallet required"}
    
    check = check_eligibility(w)
    if not check.get("eligible"):
        return {"success": False, "reason": check.get("reason"), "progress": check.get("progress")}
    
    now = datetime.now()
    badge = {
        "wallet": w,
        "wallet_short": w[:6] + "..." + w[-4:],
        "claimed_at": now.isoformat(),
        "transferable_at": (now + timedelta(days=365)).isoformat(),
        "soulbound": True,
        "discount_percent": 20,
        "purchases_at_claim": check["purchases"],
        "total_spent_at_claim": check["total_spent"],
        "unique_services_at_claim": check["unique_services"],
        "badge_id": f"PLAZA-SOUL-{len(_load()['badges'])+1:04d}",
        "anti_gaming_verified": True
    }
    
    d = _load()
    d["badges"].append(badge)
    d["claimed"].append(w)
    _save(d)
    
    return {
        "success": True,
        "badge": badge,
        "message": f"Congratulations! Soul Badge #{badge['badge_id']} claimed. 20% off forever. Soulbound until {badge['transferable_at'][:10]}.",
        "anti_gaming": "Verified: 3+ purchases, $10+ spent, 2+ services"
    }

def get_badge_status(wallet):
    """Badge status for a wallet."""
    w = (wallet or "").lower()
    d = _load()
    badge = next((b for b in d["badges"] if b.get("wallet", "").lower() == w), None)
    
    if not badge:
        return {"has_badge": False, "eligible": check_eligibility(w)}
    
    now = datetime.now()
    transferable_at = datetime.fromisoformat(badge["transferable_at"])
    days_left = max(0, (transferable_at - now).days)
    
    return {
        "has_badge": True,
        "badge": badge,
        "discount_active": True,
        "discount_percent": 20,
        "soulbound": days_left > 0,
        "days_until_transferable": days_left,
        "transferable_at": badge["transferable_at"]
    }

def apply_discount(wallet, base_price_usd):
    """Apply 20% discount if wallet has badge."""
    w = (wallet or "").lower()
    d = _load()
    has_badge = any(b.get("wallet", "").lower() == w for b in d["badges"])
    
    if has_badge:
        return {"original": base_price_usd, "discounted": round(base_price_usd * 0.80, 6), "badge_applied": True}
    return {"original": base_price_usd, "discounted": base_price_usd, "badge_applied": False}

def get_all_badges():
    """Public badge leaderboard."""
    d = _load()
    return {
        "total_badges": len(d["badges"]),
        "anti_gaming_protection": "3+ purchases, $10+ spent, 2+ different services",
        "badges": [{
            "badge_id": b["badge_id"],
            "wallet_short": b["wallet_short"],
            "claimed_at": b["claimed_at"],
            "discount_percent": b["discount_percent"],
            "purchases_at_claim": b.get("purchases_at_claim"),
            "total_spent_at_claim": b.get("total_spent_at_claim")
        } for b in d["badges"]]
    }
