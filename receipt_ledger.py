#!/usr/bin/env python3
"""One-Time Receipt Ledger - prevents tx hash replay attacks."""
import json, os
from datetime import datetime

FILE = "used_receipts.json"

def _load():
    if os.path.exists(FILE):
        return json.load(open(FILE))
    return {"receipts": []}

def _save(d):
    json.dump(d, open(FILE, "w"), indent=2)

def is_used(tx_hash):
    """Check if tx hash has already been used."""
    d = _load()
    return any(r.get("tx_hash") == tx_hash for r in d["receipts"])

def burn_receipt(tx_hash, wallet, amount, service):
    """Mark tx hash as used (burn it)."""
    if is_used(tx_hash):
        return {"success": False, "reason": "Receipt already burned"}
    
    d = _load()
    d["receipts"].append({
        "tx_hash": tx_hash,
        "wallet": wallet,
        "amount_usd": amount,
        "service": service,
        "burned_at": datetime.now().isoformat()
    })
    _save(d)
    return {"success": True, "message": f"Receipt {tx_hash[:10]}... burned. Cannot be reused."}

def get_stats():
    """Get receipt ledger stats."""
    d = _load()
    return {
        "total_receipts_burned": len(d["receipts"]),
        "unique_wallets": len(set(r.get("wallet") for r in d["receipts"])),
        "total_usd_protected": sum(float(r.get("amount_usd", 0)) for r in d["receipts"])
    }
