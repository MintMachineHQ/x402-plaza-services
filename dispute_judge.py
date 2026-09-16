#!/usr/bin/env python3
"""Autonomous Dispute Judge - uses local Ollama LLM (free, private, no API costs)."""
import json
import urllib.request

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"

def judge_dispute(job_description, deliverable, dispute_evidence, job_type):
    """
    Ask the local LLM to arbitrate the dispute.
    Returns: {"verdict": "worker_wins"|"client_wins", "reasoning": "...", "confidence": 0-100}
    """
    prompt = f"""You are an impartial smart contract arbitrator for an autonomous agent marketplace.

JOB DESCRIPTION:
{job_description[:1000]}

JOB TYPE: {job_type}

DELIVERABLE SUBMITTED BY WORKER:
{str(deliverable)[:2000]}

CLIENT'S DISPUTE EVIDENCE:
{str(dispute_evidence)[:1000]}

YOUR TASK: Determine if the worker completed the job as described.

Answer in EXACTLY this JSON format (nothing else):
{{"verdict": "worker_wins" or "client_wins", "confidence": 0-100, "reasoning": "one sentence explanation"}}

Consider:
- Does the deliverable match the description?
- Is the deliverable complete and functional?
- Is the client's complaint valid?

Be fair but strict. If the work is substantially complete, the worker wins. If the work is missing or fundamentally broken, the client wins.
"""
    try:
        req_data = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 300}
        }).encode()
        
        req = urllib.request.Request(OLLAMA, data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode())
            content = result.get("message", {}).get("content", "{}")
            
            try:
                verdict_data = json.loads(content)
                verdict = verdict_data.get("verdict", "client_wins")
                if verdict not in ("worker_wins", "client_wins"):
                    verdict = "client_wins"
                return {
                    "verdict": verdict,
                    "reasoning": verdict_data.get("reasoning", "No reasoning provided"),
                    "confidence": verdict_data.get("confidence", 50)
                }
            except json.JSONDecodeError:
                # Fallback: parse raw text
                content_lower = content.lower()
                if "worker_wins" in content_lower or "yes" in content_lower:
                    return {"verdict": "worker_wins", "reasoning": content[:200], "confidence": 60}
                return {"verdict": "client_wins", "reasoning": content[:200], "confidence": 60}
    except Exception as e:
        return {"verdict": "client_wins", "reasoning": f"Judge error (default to client): {str(e)}", "confidence": 0, "error": str(e)}
