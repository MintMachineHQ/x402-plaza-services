"""Grand Opening Promotion: First 4 unique agents get free service, then never again."""
import json
import os
import time

PROMO_FILE = "grand_opening_state.json"
MAX_FREE_AGENTS = 4

def load_state():
    try:
        return json.load(open(PROMO_FILE))
    except:
        return {"free_agents": [], "usage_log": []}

def save_state(state):
    json.dump(state, open(PROMO_FILE, "w"), indent=2)

def check_free_eligibility(wallet):
    """Returns True if this wallet gets free service, False otherwise."""
    wallet = wallet.lower()
    state = load_state()
    
    # Already used free service
    if wallet in state["free_agents"]:
        return False
    
    # Still slots available
    if len(state["free_agents"]) < MAX_FREE_AGENTS:
        state["free_agents"].append(wallet)
        state["usage_log"].append({
            "wallet": wallet,
            "timestamp": time.time(),
            "agent_number": len(state["free_agents"])
        })
        save_state(state)
        print(f"🎉 GRAND OPENING: Agent #{len(state['free_agents'])} ({wallet}) gets FREE service!")
        return True
    
    # All slots used
    return False

def get_promo_status():
    """Returns current promotion status."""
    state = load_state()
    remaining = MAX_FREE_AGENTS - len(state["free_agents"])
    return {
        "promo_active": remaining > 0,
        "free_agents_used": len(state["free_agents"]),
        "free_agents_remaining": remaining,
        "total_free_slots": MAX_FREE_AGENTS
    }
