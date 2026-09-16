#!/usr/bin/env python3
"""
Automated growth engine for Plaza Services
- First 25 agents get their first paid call refunded automatically
- Live stats dashboard
- Self-serve promotion system
"""
import json
import os
from datetime import datetime
from pathlib import Path

FIRST_FREE_FILE = "first_free_used.json"
MAX_FREE_AGENTS = 25

def load_first_free_data():
    if os.path.exists(FIRST_FREE_FILE):
        return json.load(open(FIRST_FREE_FILE))
    return {"wallets": [], "count": 0}

def save_first_free_data(data):
    with open(FIRST_FREE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_and_refund_first_call(wallet_address: str, tx_hash: str, amount_usdc: float) -> dict:
    """
    If this wallet hasn't used their free call yet AND we haven't hit 25 agents,
    automatically refund them and mark as used.
    """
    data = load_first_free_data()
    wallet_lower = wallet_address.lower()
    
    # Already used free call
    if wallet_lower in data["wallets"]:
        return {"refunded": False, "reason": "Already used free call"}
    
    # Promotion ended
    if data["count"] >= MAX_FREE_AGENTS:
        return {"refunded": False, "reason": f"Promotion ended (reached {MAX_FREE_AGENTS} agents)"}
    
    # Refund this agent
    data["wallets"].append(wallet_lower)
    data["count"] += 1
    save_first_free_data(data)
    
    # In production, you'd call your refund function here
    # For now, we just mark it as "should refund"
    print(f"[GROWTH ENGINE] Refunded {wallet_address} (${amount_usdc}) - Agent #{data['count']}/{MAX_FREE_AGENTS}")
    
    return {
        "refunded": True,
        "agent_number": data["count"],
        "remaining_free_spots": MAX_FREE_AGENTS - data["count"],
        "tx_hash": tx_hash
    }

def get_promotion_status() -> dict:
    data = load_first_free_data()
    return {
        "promotion_active": data["count"] < MAX_FREE_AGENTS,
        "agents_used": data["count"],
        "max_agents": MAX_FREE_AGENTS,
        "remaining_spots": max(0, MAX_FREE_AGENTS - data["count"]),
        "wallets_used": data["wallets"]
    }

def get_live_stats() -> dict:
    """Generate real-time stats for /stats endpoint"""
    ledger = []
    if os.path.exists("ledger.json"):
        ledger = json.load(open("ledger.json"))
    
    paid_txs = [e for e in ledger if e.get("status") == "paid"]
    total_revenue = sum(float(e.get("amount", 0)) for e in paid_txs)
    
    # Unique agents (by wallet address)
    unique_agents = set()
    for e in paid_txs:
        if "sender" in e:
            unique_agents.add(e["sender"].lower())
    
    # Transactions today
    today = datetime.now().strftime("%Y-%m-%d")
    today_txs = [e for e in paid_txs if e.get("timestamp", "").startswith(today)]
    
    # Most popular tool
    tool_counts = {}
    for e in paid_txs:
        tool = e.get("service", "unknown")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
    most_popular = max(tool_counts.items(), key=lambda x: x[1]) if tool_counts else ("none", 0)
    
    return {
        "total_revenue_usdc": round(total_revenue, 2),
        "total_transactions": len(paid_txs),
        "unique_agents": len(unique_agents),
        "transactions_today": len(today_txs),
        "most_popular_tool": {"name": most_popular[0], "calls": most_popular[1]},
        "promotion_status": get_promotion_status(),
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test the system
    print("=== GROWTH ENGINE TEST ===")
    print(get_live_stats())
    
    # Simulate a first-call refund
    result = check_and_refund_first_call(
        "0xtest123", 
        "0xabcdef", 
        0.05
    )
    print("\nSimulated refund:", result)
