import json, os, sys, urllib.request, urllib.error
URL = os.environ.get("PLAZA_URL", os.environ.get("TOLLBOOTH_URL", "http://127.0.0.1:8000"))
TOOLS = [
    {"name": "plaza_catalog", "description": "Get the live catalog and prices from X402 Plaza Services.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "plaza_extract", "description": "Extract structured product data from HTML. Costs 0.05 USDC. Returns 402 if unpaid.", "inputSchema": {"type": "object", "properties": {"html": {"type": "string"}, "payment_proof": {"type": "string", "description": "tx hash of 0.05 USDC"}}}},
    {"name": "plaza_audit", "description": "Static security audit of agent code. Costs 100 USDC.", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}, "payment_proof": {"type": "string"}}}},
    {"name": "plaza_buy_pack", "description": "Buy a Cage Wall pack: 1000 prompt-injection scans for 100 USDC.", "inputSchema": {"type": "object", "properties": {"payment_proof": {"type": "string"}}}},
    {"name": "plaza_scan", "description": "Scan inbound content for prompt injection (uses prepaid pack).", "inputSchema": {"type": "object", "properties": {"wallet": {"type": "string"}, "content": {"type": "string"}}}},
    {"name": "plaza_notarize", "description": "Hash and audit a package to get a sealed provenance certificate. Costs 150 USDC.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "content": {"type": "string"}, "payment_proof": {"type": "string"}}}},
    {"name": "plaza_airgap", "description": "Analyze sensitive data using an offline, air-gapped model. Costs 200 USDC.", "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}, "data": {"type": "string"}, "payment_proof": {"type": "string"}}}},
    {"name": "plaza_report", "description": "Fetch a completed sealed report by job_id. Free.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}}},
    {"name": "plaza_reputation", "description": "Fetch the public Trust Wall (sales, reviews). Free.", "inputSchema": {"type": "object", "properties": {}}},
]

def req(method, path, data=None, proof=None):
    headers = {"Content-Type": "application/json"}
    if proof: headers["X-Payment-Proof"] = proof
    b = json.dumps(data).encode() if data else None
    r = urllib.request.Request(f"{URL}{path}", data=b, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def handle(name, args):
    if name == "plaza_catalog": return req("GET", "/catalog")
    if name == "plaza_extract": return req("POST", "/extract", {"html": args.get("html","")}, args.get("payment_proof"))
    if name == "plaza_audit": return req("POST", "/audit", {"code": args.get("code","")}, args.get("payment_proof"))
    if name == "plaza_buy_pack": return req("POST", "/buy_pack", {}, args.get("payment_proof"))
    if name == "plaza_scan": return req("POST", "/scan", {"wallet": args.get("wallet",""), "content": args.get("content","")})
    if name == "plaza_notarize": return req("POST", "/notarize", {"name": args.get("name",""), "version": args.get("version",""), "content": args.get("content","")}, args.get("payment_proof"))
    if name == "plaza_airgap": return req("POST", "/airgap", {"question": args.get("question",""), "data": args.get("data","")}, args.get("payment_proof"))
    if name == "plaza_report": return req("GET", f"/report/{args.get('job_id','')}")
    if name == "plaza_reputation": return req("GET", "/reputation")
    return {"error": "unknown tool"}

def main():
    sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":0,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"x402-plaza-services","version":"4.5"}}}) + "\n")
    sys.stdout.flush()
    for line in sys.stdin:
        msg = json.loads(line)
        if msg.get("method") == "tools/list":
            sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"tools":TOOLS}}) + "\n")
        elif msg.get("method") == "tools/call":
            res = handle(msg["params"]["name"], msg["params"].get("arguments", {}))
            sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"content":[{"type":"text","text":json.dumps(res)}]}}) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
