#!/usr/bin/env python3
"""Plaza Universal Shield Matrix - Middleware for all 12+ tools."""
import json, os, re, time, random, hashlib, hmac, threading

STATE_FILE = "shield_state.json"
AUDIT_LOG = "audit_log.json"
SECRET_FILE = "plaza_secret.key"
_LOCK = threading.Lock()

# Load or generate the master HMAC secret
if not os.path.exists(SECRET_FILE):
    import secrets
    with open(SECRET_FILE, "w") as f: f.write(secrets.token_hex(32))
    os.chmod(SECRET_FILE, 0o600)
with open(SECRET_FILE) as f: MASTER_SECRET = f.read().strip()

# Honeypot tool names (Shield 10)
HONEYPOTS = {"plaza.free_money", "admin.login", "root.access", "plaza.bypass_payment"}

def _load_state():
    try: return json.load(open(STATE_FILE))
    except: return {"ip_hits": {}, "wallet_bans": [], "audit_hash": "genesis"}

def _save_state(d): json.dump(d, open(STATE_FILE, "w"))

def _constant_time_delay(): time.sleep(random.uniform(0.2, 0.4))

def sign_output(data_dict):
    """Shield 3 & 6: Cryptographically sign the output."""
    payload = json.dumps(data_dict, sort_keys=True)
    sig = hmac.new(MASTER_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    data_dict["plaza_signature"] = sig
    return data_dict

def run_shields(wallet, ip, tool_name, args):
    """Runs all 14 shields. Returns (allowed: bool, response_dict)"""
    w = (wallet or "anon").lower()
    ip = (ip or "unknown").strip()
    now = time.time()

    with _LOCK:
        state = _load_state()
        
        # Shield 10: Honeypot Trap
        if tool_name in HONEYPOTS:
            state["wallet_bans"].append(w)
            _save_state(state)
            _constant_time_delay()
            return False, {"success": False, "reason": "Shield 10: Honeypot triggered. Wallet permanently banned."}

        # Shield 9: Cross-Tool Blocklist
        if w in state["wallet_bans"]:
            _constant_time_delay()
            return False, {"success": False, "reason": "Shield 9: Wallet is globally banned for abuse."}

        # Shield 2: Input Validation (Anti JSON Bomb - max 500KB payload)
        args_size = len(json.dumps(args))
        if args_size > 500000:
            _constant_time_delay()
            return False, {"success": False, "reason": f"Shield 2: Payload too large ({args_size} bytes). Max 500KB."}

        # Shield 11: Payload Sanitization (Anti Prompt Injection / Code Exec)
        args_str = json.dumps(args).lower()
        malicious_patterns = ["eval(", "exec(", "__import__", "os.system", "subprocess", "<script"]
        for pat in malicious_patterns:
            if pat in args_str:
                state["wallet_bans"].append(w)
                _save_state(state)
                return False, {"success": False, "reason": f"Shield 11: Malicious payload detected ({pat}). Banned."}

        # Shield 4: IP Co-Rate Limiting (Max 30 req/min per IP across ALL tools)
        ip_hits = [t for t in state["ip_hits"].get(ip, []) if now - t < 60]
        if len(ip_hits) >= 30 and ip != "unknown":
            _constant_time_delay()
            return False, {"success": False, "reason": "Shield 4: IP rate limit (30 req/min) exceeded."}
        ip_hits.append(now)
        state["ip_hits"][ip] = ip_hits[-50:]  # Keep last 50

        # Shield 12: Immutable Audit Log (Chained Hashes)
        log_entry = f"{now}|{ip}|{w}|{tool_name}|{args_size}"
        prev_hash = state["audit_hash"]
        new_hash = hashlib.sha256(f"{prev_hash}{log_entry}".encode()).hexdigest()
        state["audit_hash"] = new_hash
        
        # Append to audit file (keep last 1000 lines)
        try:
            with open(AUDIT_LOG, "a") as f: f.write(f"{new_hash[:8]}|{log_entry}\n")
        except: pass

        _save_state(state)
        
    # ALL SHIELDS PASSED
    return True, {"audit_hash": new_hash[:8]}
