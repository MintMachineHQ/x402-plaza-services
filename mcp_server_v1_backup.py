#!/usr/bin/env python3
"""TollBooth Plaza MCP server (stdio). Lets AI agent hosts call the plaza natively."""
import json, sys, os, urllib.request, urllib.error

BASE = os.environ.get("TOLLBOOTH_URL", "https://oncoming-headband-unsoiled.ngrok-free.dev")

def call(path, payload=None, headers=None):
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Content-Type": "application/json"}
    if headers: hdrs.update(headers)
    req = urllib.request.Request(BASE + path, data=data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}

TOOLS = [
    {"name": "tollbooth_catalog", "description": "List TollBooth Plaza services, prices, wallet, and integrity info.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "tollbooth_extract", "description": "Extract products+prices from HTML. Requires X-Payment-Proof: tx hash of 0.05 USDC on Base.", "inputSchema": {"type": "object", "properties": {"html": {"type": "string"}, "payment_proof": {"type": "string"}}, "required": ["html", "payment_proof"]}},
    {"name": "tollbooth_audit", "description": "Static security audit of agent code/skill (100 USDC). Returns job_id.", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}, "payment_proof": {"type": "string"}}, "required": ["code", "payment_proof"]}},
    {"name": "tollbooth_report", "description": "Fetch a completed, HMAC-sealed audit report by job_id.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
    {"name": "tollbooth_reputation", "description": "Public trust wall: sales, verified reviews, feature suggestions.", "inputSchema": {"type": "object", "properties": {}}}
]

def handle(req):
    m, rid, p = req.get("method"), req.get("id"), req.get("params", {})
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "tollbooth-plaza", "version": "1.0"}}}
    if m == "notifications/initialized":
        return None
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if m == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if m == "tools/call":
        name, args = p.get("name"), p.get("arguments", {})
        if name == "tollbooth_catalog": st, body = call("/catalog")
        elif name == "tollbooth_reputation": st, body = call("/reputation")
        elif name == "tollbooth_report": st, body = call("/report/" + args.get("job_id", ""))
        elif name == "tollbooth_extract": st, body = call("/extract", {"html": args.get("html", "")}, {"X-Payment-Proof": args.get("payment_proof", "")})
        elif name == "tollbooth_audit": st, body = call("/audit", {"code": args.get("code", "")}, {"X-Payment-Proof": args.get("payment_proof", "")})
        else: st, body = 404, {"error": "unknown tool"}
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(body, indent=2)}], "isError": st not in (200, 202)}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: req = json.loads(line)
        except Exception: continue
        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n"); sys.stdout.flush()
