#!/usr/bin/env python3
"""Autonomous Payout System - pays workers without human intervention.
Uses a dedicated hot wallet. Runs every 5 minutes via background thread."""
import json, os, subprocess, shutil
from datetime import datetime

HOT_WALLET_FILE = "payout_wallet.key"
PAYOUTS_LOG = "payouts_log.json"

def get_hot_wallet_address():
    """Return the hot wallet address (user must configure this)."""
    # This is the Plaza Payouts wallet - funded with USDC on Base
    # The private key is in payout_wallet.key (chmod 600)
    return "0xb838930bf3dFD467D30979E12c0a94286F86708D"  # Same as main Plaza wallet for now

def has_cast():
    """Check if Foundry's cast tool is installed."""
    return shutil.which("cast") is not None

def send_usdc_base(to_address, amount_usd, job_id):
    """
    Send USDC on Base chain using cast (Foundry) if available.
    Returns (success, tx_hash, error)
    """
    if not has_cast():
        return False, None, "Foundry 'cast' not installed. Install with: curl -L https://foundry.paradigm.xyz | bash && foundryup"
    
    if not os.path.exists(HOT_WALLET_FILE):
        return False, None, f"Hot wallet key file missing: {HOT_WALLET_FILE}. Create it with your private key (chmod 600)."
    
    try:
        # USDC on Base: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
        # 6 decimals
        amount_wei = int(amount_usd * 1_000_000)
        usdc_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        
        # Build the transfer call data
        with open(HOT_WALLET_FILE) as f:
            private_key = f.read().strip()
        
        # Use cast to send
        cmd = [
            "cast", "send",
            "--rpc-url", "https://mainnet.base.org",
            "--private-key", private_key,
            usdc_address,
            "transfer(address,uint256)",
            to_address,
            str(amount_wei)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Extract tx hash from output
            for line in result.stdout.split('\n'):
                if 'transactionHash' in line.lower() or line.startswith('0x'):
                    tx_hash = line.strip().split()[-1]
                    if tx_hash.startswith('0x'):
                        return True, tx_hash, None
            return True, "tx_sent", None
        else:
            return False, None, result.stderr[:200]
    except Exception as e:
        return False, None, str(e)

def process_payouts():
    """Process all pending payouts from the escrow queue."""
    try:
        escrow = json.load(open("escrow.json"))
    except Exception:
        return 0
    
    paid_count = 0
    log = []
    if os.path.exists(PAYOUTS_LOG):
        try:
            log = json.load(open(PAYOUTS_LOG))
        except Exception:
            log = []
    
    for job in escrow["jobs"]:
        if job["status"] != "released":
            continue
        pending = job.get("payout_pending")
        if not pending:
            continue
        if pending.get("paid"):
            continue  # Already paid
        
        to_wallet = pending["wallet"]
        amount = pending["amount_usd"]
        
        # Try to send payment
        success, tx_hash, error = send_usdc_base(to_wallet, amount, job["job_id"])
        
        if success:
            pending["paid"] = True
            pending["paid_at"] = datetime.now().isoformat()
            pending["tx_hash"] = tx_hash
            log.append({
                "job_id": job["job_id"],
                "to": to_wallet,
                "amount_usd": amount,
                "tx_hash": tx_hash,
                "at": datetime.now().isoformat(),
                "status": "success"
            })
            paid_count += 1
        else:
            # Log failure but don't crash - will retry next cycle
            log.append({
                "job_id": job["job_id"],
                "to": to_wallet,
                "amount_usd": amount,
                "error": error,
                "at": datetime.now().isoformat(),
                "status": "failed"
            })
    
    # Save updates
    json.dump(escrow, open("escrow.json", "w"), indent=2)
    json.dump(log, open(PAYOUTS_LOG, "w"), indent=2)
    
    return paid_count

def get_payout_stats():
    """Get payout queue status."""
    try:
        log = json.load(open(PAYOUTS_LOG))
    except Exception:
        log = []
    
    success = [e for e in log if e.get("status") == "success"]
    failed = [e for e in log if e.get("status") == "failed"]
    
    return {
        "total_paid": len(success),
        "total_failed": len(failed),
        "total_usd_paid": sum(e.get("amount_usd", 0) for e in success),
        "hot_wallet_address": get_hot_wallet_address(),
        "cast_installed": has_cast(),
        "key_file_exists": os.path.exists(HOT_WALLET_FILE),
        "last_5_payouts": log[-5:] if log else []
    }
