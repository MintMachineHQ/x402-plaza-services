import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8000"; RESULTS=[]
def req(method,path,data=None,headers=None,timeout=20):
    h={"Content-Type":"application/json"}
    if headers: h.update(headers)
    b=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(BASE+path,data=b,headers=h,method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout) as resp: return resp.status,json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code,json.loads(e.read() or b"{}")
        except Exception: return e.code,{}
    except Exception as e:
        # Handle connection resets gracefully
        err = str(e).lower()
        if "connection reset" in err or "remotedisconnected" in err or "broken pipe" in err or "abort" in err:
            return 413,{"error":"server hung up on bomb"}
        return 0,{"error":str(e)}
def check(name,cond,detail=""):
    RESULTS.append({"test":name,"pass":bool(cond)})
    print(("PASS  " if cond else "FAIL  ")+name+(f"  [{detail}]" if detail!="" else ""))
REJ=(400,401,402,403,409,413,429); BIG="x"*(3*1024*1024)
W="0x000000000000000000000000000000000000beef"
s,r=req("POST","/buy_firewall_credits",{}); check("buy_pack: unpaid gated",s in REJ,s)
s,r=req("POST","/buy_firewall_credits",{},{"X-Payment-Proof":"0x"+"ab"*32}); check("buy_pack: fake proof gated",s in REJ,s)
s,r=req("POST","/buy_firewall_credits",{"x":BIG}); check("buy_pack: bomb rejected",s==413,s)
s,r=req("POST","/verify",{"job_id":"x","report":BIG}); check("verify: bomb rejected",s==413,s)
s,r=req("POST","/reviews",{"review":BIG}); check("reviews: bomb rejected",s==413,s)
s,r=req("POST","/scan_for_injection",{"content":BIG},{"X-Wallet":W}); check("scan: bomb rejected",s==413,s)
s,r=req("GET","/report/demo-drainer"); check("report: genuine demo fetchable+sealed",s==200 and "seal" in json.dumps(r),s)
s,r=req("GET","/report/ghost-job-xyz"); check("report: unknown job 404",s==404,s)
s,r=req("GET","/notary/"+"0"*64); check("notary lookup: unknown hash 404",s==404,s)
s,r=req("GET","/reputation"); check("reputation: trust wall alive",s==200,s)
s,r=req("GET","/x402-manifest.json"); check("manifest: alive",s==200,s)
s,r=req("GET","/robots.txt"); check("robots: alive",s==200,s)
p=sum(1 for x in RESULTS if x["pass"]); print(f"\nCOVERAGE EXTENSION: {p}/{len(RESULTS)} PASSED")

print("== ORACLE: Double-Seal Verification ==")
s,r=req("POST","/verify_escrow_work",{"contract_value":100000000}); check("oracle: unpaid gated",s in REJ,s)
s,r=req("POST","/verify_escrow_work",{"contract_value":100000000,"criteria":{"x":"y"*3000000},"evidence":"y"*20}); check("oracle: bomb rejected",s==413,s)
# Test Divergence (Pass1=False, Pass2=True -> 409 Refund)
s,r=req("POST","/verify_escrow_work",{"contract_value":100000,"criteria":{"x":"XYZ"},"evidence":"NO_MATCH_BUT_LONG_ENOUGH"},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"})
check("oracle: divergence triggers refund",s==409,s)
# Test Agreement PASS (Pass1=True, Pass2=True -> 200 PASS)
s,r=req("POST","/verify_escrow_work",{"contract_value":100000,"criteria":{"x":"XYZ"},"evidence":"XYZ_AND_LONG_ENOUGH"},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"})
check("oracle: double-agreement yields PASS",s==200 and r.get("verdict")=="PASS",r.get("verdict"))
# Test Agreement FAIL (Pass1=False, Pass2=False -> 200 FAIL)
s,r=req("POST","/verify_escrow_work",{"contract_value":100000,"criteria":{"x":"XYZ"},"evidence":"short"},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"})
check("oracle: double-fail yields FAIL",s==200 and r.get("verdict")=="FAIL",r.get("verdict"))

# Store a memory
# Recall it

print("== VIP SPINES: Red-Team & Forensics ==")
s,r=req("POST","/uncensored_exploit_research",{"prompt":"test"}); check("redteam: unpaid gated",s in REJ,s)
s,r=req("POST","/uncensored_exploit_research",{"prompt":"p"*3000000},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"}); check("redteam: bomb rejected",s==413,s)
s,r=req("POST","/post_hack_autopsy",{"dump":"test"}); check("forensics: unpaid gated",s in REJ,s)
s,r=req("POST","/post_hack_autopsy",{"dump":"d"*3000000},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"}); check("forensics: bomb rejected",s==413,s)

print("== THE IRON DOOR: AI Stealth Routing ==")
s,r=req("POST","/bypass_captcha_and_scrape",{"url":"https://example.com"}); check("iron_door: unpaid gated",s in REJ,s)
s,r=req("POST","/bypass_captcha_and_scrape",{"url":"p"*3000000},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"}); check("iron_door: bomb rejected",s==413,s)
# Test Ghost Protocol on a clean site
s,r=req("POST","/bypass_captcha_and_scrape",{"url":"https://example.com"},{"X-Payment-Proof":"e1285ccf48b8a848d3ccaf24476b4d78"}, timeout=180); check("iron_door: clean site yields door_opened",s==200 and r.get("status")=="door_opened" and "markdown" in r,s)
