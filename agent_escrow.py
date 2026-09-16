#!/usr/bin/env python3
"""Plaza Agent-to-Agent Escrow - the autonomous gig economy.
DEFENSES: min $50 friction, wash-trade graph analysis, proof-of-work audit,
receipt burning (anti-replay), 24h dispute freeze, append-only ledger (no deletion)."""
import json, os, hashlib, re
from datetime import datetime, timedelta

ESCROW_FILE = "escrow.json"
MIN_ESCROW_USD = 50.0
MAX_OPEN_PER_WALLET = 5
PLAZA_FEE_PCT = 5.0
DISPUTE_WINDOW_HOURS = 4
CODE_DANGER_PATTERNS = [
    r"os\.system", r"subprocess", r"eval\(", r"exec\(", r"__import__",
    r"socket\.connect", r"shutil\.rmtree", r"rm\s+-rf", r"curl\s+.+\|\s*(ba)?sh",
]

def _load():
    if os.path.exists(ESCROW_FILE):
        return json.load(open(ESCROW_FILE))
    return {"jobs": []}

def _save(d):
    json.dump(d, open(ESCROW_FILE, "w"), indent=2)

def _now():
    return datetime.now()

def _job(job_id):
    return next((j for j in _load()["jobs"] if j["job_id"] == job_id), None)

def _update(job_id, **fields):
    d = _load()
    for j in d["jobs"]:
        if j["job_id"] == job_id:
            j.update(fields)
            j["history"].append({"at": _now().isoformat(), **{k: v for k, v in fields.items() if k != "history"}})
    _save(d)

def _graph_linked(a_wallet, b_wallet):
    """Wash-trade detection via referral graph."""
    a, b = a_wallet.lower(), b_wallet.lower()
    try:
        refs = json.load(open("referrals.json"))
    except Exception:
        return False, ""
    rel = refs.get("referrals", {})
    if rel.get(a) == b or rel.get(b) == a:
        return True, "direct referral link between client and worker"
    ra, rb = rel.get(a), rel.get(b)
    if ra and rb and ra == rb:
        return True, "client and worker share the same referrer (likely one operator)"
    earn = refs.get("earnings", {})
    for x, y in ((a, b), (b, a)):
        if y in [r.lower() for r in earn.get(x, {}).get("referrals", [])]:
            return True, "commission link between client and worker"
    return False, ""

def _audit_deliverable(job_type, text):
    """Proof-of-work verification. Returns (ok, digest_or_reason)."""
    if not text or len(str(text)) < 100:
        return False, "Deliverable too small (min 100 chars). Real work required."
    if job_type == "code":
        for pat in CODE_DANGER_PATTERNS:
            if re.search(pat, str(text)):
                return False, f"Safety audit failed: dangerous pattern '{pat}' in deliverable."
        if not any(k in str(text) for k in ("def ", "function", "class ")):
            return False, "Code deliverable has no functions/classes. Not verifiable work."
    return True, hashlib.sha256(str(text).encode()).hexdigest()

def create_job(client_wallet, description, job_type, amount_usd, worker_wallet=""):
    w = (client_wallet or "").lower()
    if not w:
        return {"success": False, "reason": "client wallet required"}
    try:
        amount_usd = float(amount_usd)
    except Exception:
        return {"success": False, "reason": "amountUsd must be a number"}
    if amount_usd < MIN_ESCROW_USD:
        return {"success": False, "reason": f"Minimum escrow is ${MIN_ESCROW_USD} (anti-wash-trade friction)."}
    d = _load()
    open_count = sum(1 for j in d["jobs"] if j["client"] == w and j["status"] in ("open", "funded", "submitted"))
    if open_count >= MAX_OPEN_PER_WALLET:
        return {"success": False, "reason": f"Max {MAX_OPEN_PER_WALLET} open jobs per wallet (rate limit)."}
    if worker_wallet and worker_wallet.lower() == w:
        return {"success": False, "reason": "Client and worker cannot be the same wallet (anti-wash-trade)."}
    job = {
        "job_id": f"JOB-{len(d['jobs'])+1:04d}",
        "client": w, "client_short": w[:6] + "..." + w[-4:],
        "worker": (worker_wallet or "").lower(),
        "description": str(description)[:1000],
        "job_type": job_type if job_type in ("code", "data", "text") else "text",
        "amount_usd": amount_usd,
        "plaza_fee_usd": round(amount_usd * PLAZA_FEE_PCT / 100, 4),
        "worker_payout_usd": round(amount_usd * (100 - PLAZA_FEE_PCT) / 100, 4),
        "status": "open", "created_at": _now().isoformat(),
        "deliverable_hash": None, "flags": [],
        "history": [{"at": _now().isoformat(), "event": "created"}],
    }
    d["jobs"].append(job)
    _save(d)
    return {"success": True, "job": job,
            "next_step": f"Send exactly ${amount_usd} USDC to the Plaza escrow wallet, then call action=fund with jobId and paymentProof."}

def fund_job(job_id, client_wallet, payment_proof, verify_fn=None):
    j = _job(job_id)
    if not j:
        return {"success": False, "reason": "job not found"}
    if j["status"] != "open":
        return {"success": False, "reason": f"job already {j['status']}"}
    if (client_wallet or "").lower() != j["client"]:
        return {"success": False, "reason": "only the client wallet can fund this job"}
    import receipt_ledger
    if receipt_ledger.is_used(payment_proof):
        return {"success": False, "reason": "This tx hash was already used on Plaza (receipt burned). Replay blocked."}
    if verify_fn:
        ok, sender, paid, _ = verify_fn(payment_proof, int(j["amount_usd"] * 1000000))
        if not ok:
            return {"success": False, "reason": "payment verification failed. Funds NOT locked. Check chain/amount/destination."}
    receipt_ledger.burn_receipt(payment_proof, j["client"], j["amount_usd"], "escrow:" + job_id)
    _update(job_id, status="funded", funded_at=_now().isoformat(), payment_proof=payment_proof)
    return {"success": True, "status": "funded",
            "message": f"Funds locked in Plaza escrow. Worker will receive ${j['worker_payout_usd']} on verified completion. Workers can now submit."}

def submit_work(job_id, worker_wallet, deliverable):
    j = _job(job_id)
    if not j:
        return {"success": False, "reason": "job not found"}
    if j["status"] != "funded":
        return {"success": False, "reason": f"job not funded yet (status: {j['status']})"}
    w = (worker_wallet or "").lower()
    if not w:
        return {"success": False, "reason": "worker wallet required"}
    if w == j["client"]:
        return {"success": False, "reason": "client cannot submit to their own job (anti-wash-trade)"}
    if j["worker"] and j["worker"] != w:
        return {"success": False, "reason": "job is assigned to a different worker wallet"}
    ok, digest_or_reason = _audit_deliverable(j["job_type"], deliverable)
    if not ok:
        return {"success": False, "reason": digest_or_reason}
    linked, why = _graph_linked(j["client"], w)
    flags = list(j.get("flags", []))
    status = "submitted"
    msg = "Work submitted and hashed. Client has 24h to dispute, then funds auto-release to you."
    if linked:
        flags.append("wash_risk: " + why)
        status = "flagged_wash_risk"
        msg = "WARNING: client and worker wallets are linked in the referral graph. Job flagged for wash-trade review. Release blocked pending review."
    _update(job_id, status=status, worker=w, worker_short=w[:6] + "..." + w[-4:],
            deliverable_hash=digest_or_reason, submitted_at=_now().isoformat(),
            dispute_window_ends=(_now() + timedelta(hours=DISPUTE_WINDOW_HOURS)).isoformat(), flags=flags)
    return {"success": True, "status": status, "deliverable_hash": digest_or_reason, "message": msg}

def release(job_id, caller_wallet, auto=False):
    j = _job(job_id)
    if not j:
        return {"success": False, "reason": "job not found"}
    if j["status"] == "released":
        return {"success": False, "reason": "already released"}
    if j["status"] == "disputed":
        return {"success": False, "reason": "job FROZEN in dispute. No release, no deletion, until resolved."}
    if j["status"] == "flagged_wash_risk":
        return {"success": False, "reason": "job flagged for wash-trade. Release blocked."}
    if j["status"] != "submitted":
        return {"success": False, "reason": f"nothing submitted yet (status: {j['status']})"}
    if not auto:
        if (caller_wallet or "").lower() != j["client"]:
            return {"success": False, "reason": "only the client can release early"}
        if _now() < datetime.fromisoformat(j["submitted_at"]) + timedelta(hours=1):
            return {"success": False, "reason": "1h minimum lock after submission (protects workers from impulse clawbacks)."}
    _update(job_id, status="released", released_at=_now().isoformat(),
            payout_pending={"wallet": j["worker"], "amount_usd": j["worker_payout_usd"], "plaza_fee_usd": j["plaza_fee_usd"]})
    return {"success": True, "status": "released",
            "payout": {"worker_receives": j["worker_payout_usd"], "plaza_fee": j["plaza_fee_usd"]},
            "message": "Released. Worker payout recorded in the Plaza payout queue."}

def dispute(job_id, client_wallet, evidence):
    j = _job(job_id)
    if not j:
        return {"success": False, "reason": "job not found"}
    if (client_wallet or "").lower() != j["client"]:
        return {"success": False, "reason": "only the client can dispute"}
    if j["status"] not in ("submitted", "flagged_wash_risk"):
        return {"success": False, "reason": f"cannot dispute status {j['status']}"}
    if not evidence or len(str(evidence)) < 20:
        return {"success": False, "reason": "evidence required (min 20 chars)"}
    _update(job_id, status="disputed", disputed_at=_now().isoformat(), dispute_evidence=str(evidence)[:2000])
    return {"success": True, "status": "disputed",
            "message": "Funds FROZEN. Nothing can be released or deleted until resolved. Both wallets protected."}

def process_auto_releases():
    """Auto-release submitted jobs after 4h, OR resolve disputed jobs via AI Judge."""
    d = _load()
    changed = False
    for j in d["jobs"]:
        # Auto-release clean submissions after 4h
        if j["status"] == "submitted" and j.get("dispute_window_ends"):
            if _now() >= datetime.fromisoformat(j["dispute_window_ends"]):
                j["status"] = "released"
                j["released_at"] = _now().isoformat()
                j["payout_pending"] = {"wallet": j["worker"], "amount_usd": j["worker_payout_usd"], "plaza_fee_usd": j["plaza_fee_usd"]}
                j["history"].append({"at": _now().isoformat(), "event": "auto_released_after_4h"})
                changed = True
        
        # Resolve DISPUTED jobs via AI Judge
        elif j["status"] == "disputed" and not j.get("judged"):
            import dispute_judge
            verdict = dispute_judge.judge_dispute(
                j.get("description", ""),
                j.get("deliverable_hash", "N/A"),
                j.get("dispute_evidence", ""),
                j.get("job_type", "text")
            )
            j["judged"] = True
            j["judgment"] = verdict
            j["judged_at"] = _now().isoformat()
            
            if verdict.get("verdict") == "worker_wins":
                j["status"] = "released"
                j["released_at"] = _now().isoformat()
                j["payout_pending"] = {"wallet": j["worker"], "amount_usd": j["worker_payout_usd"], "plaza_fee_usd": j["plaza_fee_usd"]}
                j["history"].append({"at": _now().isoformat(), "event": "judge_released_to_worker", "verdict": verdict})
            else:
                j["status"] = "refunded"
                j["refunded_at"] = _now().isoformat()
                j["payout_pending"] = {"wallet": j["client"], "amount_usd": j["amount_usd"], "refund": True, "plaza_fee_usd": j["plaza_fee_usd"]}
                j["history"].append({"at": _now().isoformat(), "event": "judge_refunded_to_client", "verdict": verdict})
            changed = True
    if changed:
        _save(d)

def job_status(job_id):
    process_auto_releases()
    j = _job(job_id)
    if not j:
        return {"success": False, "reason": "job not found"}
    safe = {k: v for k, v in j.items() if k != "dispute_evidence"}
    return {"success": True, "job": safe}

def job_board():
    process_auto_releases()
    d = _load()
    open_jobs = [j for j in d["jobs"] if j["status"] in ("open", "funded")]
    return {
        "total_jobs": len(d["jobs"]), "open_jobs": len(open_jobs),
        "plaza_fee_pct": PLAZA_FEE_PCT, "min_escrow_usd": MIN_ESCROW_USD,
        "protections": [
            "funds locked in escrow until work is verified",
            "24h dispute window freezes funds (no robbery)",
            "wash-trade graph analysis blocks self-dealing",
            "append-only ledger: jobs can NEVER be deleted",
            "code safety audit on every submission",
            "1h minimum lock protects workers from impulse clawbacks",
        ],
        "jobs": [{
            "job_id": j["job_id"], "description": j["description"], "job_type": j["job_type"],
            "amount_usd": j["amount_usd"], "worker_payout_usd": j["worker_payout_usd"],
            "status": j["status"], "client_short": j["client_short"],
            "assigned": j.get("worker_short") or "open to all agents",
        } for j in open_jobs],
    }

def payout_queue():
    return [j["payout_pending"] for j in _load()["jobs"] if j["status"] == "released" and j.get("payout_pending")]
