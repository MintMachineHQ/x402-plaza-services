#!/usr/bin/env python3
"""Plaza Testimonial Engine - verified reviews, eligible after 1 paid call."""
import json, os
from datetime import datetime

FILE = "testimonials.json"

def _load():
    if os.path.exists(FILE):
        return json.load(open(FILE))
    return {"testimonials": []}

def _save(d):
    json.dump(d, open(FILE, "w"), indent=2)

def _paid_history(wallet):
    w = (wallet or "").lower()
    total, calls = 0.0, 0
    try:
        ledger = json.load(open("ledger.json"))
    except Exception:
        ledger = []
    for e in ledger:
        if str(e.get("sender", "")).lower() == w and e.get("status") == "paid" and w:
            calls += 1
            try: total += float(e.get("amount", 0))
            except Exception: pass
    return total, calls

def has_testimonial(wallet):
    w = (wallet or "").lower()
    return any(t.get("wallet", "").lower() == w for t in _load()["testimonials"])

def submit(wallet, text, rating, video_url=""):
    total, calls = _paid_history(wallet)
    if calls < 1:
        return {"success": False, "reason": "At least 1 paid call required before reviewing. Verified reviews only."}
    if has_testimonial(wallet):
        return {"success": False, "reason": "One testimonial per wallet keeps reviews genuine."}
    try: rating = max(1, min(5, int(rating)))
    except Exception: return {"success": False, "reason": "rating must be 1-5"}
    if not text or len(str(text)) < 10:
        return {"success": False, "reason": "Testimonial too short (min 10 characters)."}
    entry = {
        "wallet": (wallet or "").lower(),
        "wallet_short": (wallet or "")[:6] + "..." + (wallet or "")[-4:],
        "text": str(text)[:500],
        "rating": rating,
        "video_url": video_url or "",
        "verified": True,
        "verified_paid_usdc": round(total, 2),
        "verified_calls": calls,
        "at": datetime.now().isoformat(),
    }
    d = _load(); d["testimonials"].append(entry); _save(d)
    return {"success": True, "testimonial": entry, "message": "Thank you! Your verified review is now public on /testimonials."}

def get_all(top=None):
    d = _load()
    ts = sorted(d["testimonials"], key=lambda t: (-t.get("rating", 0), t.get("at", "")))
    if top: ts = ts[:top]
    avg = round(sum(t.get("rating", 0) for t in d["testimonials"]) / len(d["testimonials"]), 2) if d["testimonials"] else 0
    return {"count": len(d["testimonials"]), "average_rating": avg, "testimonials": ts}
