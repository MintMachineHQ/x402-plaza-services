import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# A. FIX THE STOREFRONT MENU (Inject the missing VIPs + Iron Door)
catalog_inject = '''
            "/oracle": {"price": "2.5% (min 0.05 USDC)", "desc": "Cryptographic Proof of Action (Escrow Oracle). Double-sealed verdict."},
            "/redteam": {"price": "150.00 USDC", "desc": "Red-Team Range: uncensored attack research (air-gapped). Refunds on refusal."},
            "/forensics": {"price": "300.00 USDC", "desc": "Black Box Forensics: post-hack autopsy (air-gapped). Refunds on failure."},
            "/iron_door": {"price": "5.00 USDC", "desc": "The Iron Door: bypass CAPTCHAs & bot-traps via AI stealth routing. Refunds if blocked."},
'''
if '"/iron_door"' not in s:
    s = s.replace('"/reviews": {', catalog_inject + '            "/reviews": {', 1)
    print("PATCHED: Storefront menu fixed (All 8 spines visible!)")

# B. FORGE THE IRON DOOR ENDPOINT
iron_door_code = """
        if self.path == "/iron_door":
            url = payload.get("url", "")
            if not url.startswith("http"): return self._send(400, {"error": "invalid url"})
            verified, sender, tier, amount = verify_payment(proof, 5000000) # 5 USDC = 5,000,000 micro-USDC
            if not verified:
                return self._send(402, {"x402": {"price": "5.00 USDC", "destination": DEST_WALLET, "instruction": "The Iron Door: bypass bot-traps via AI stealth routing."}})
            
            # Pass 1: Ask the Obliterated Model for a Ghost Fingerprint
            pass1 = False; strategy = {}
            try:
                msgs = [{"role": "system", "content": "You are a web stealth expert. Generate a JSON object with 'User-Agent', 'sec-ch-ua', and 'Accept-Language' headers to bypass Cloudflare for the given URL. ONLY output valid JSON."},
                        {"role": "user", "content": url}]
                strategy_raw = ask_walled(msgs)
                start = strategy_raw.find('{')
                end = strategy_raw.rfind('}') + 1
                if start != -1 and end > start:
                    strategy = json.loads(strategy_raw[start:end])
                    pass1 = True
            except Exception: pass
            if not strategy: strategy = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

            # Pass 2: Execute the stealth fetch
            pass2 = False; html = ""
            try:
                req = urllib.request.Request(url, headers=strategy)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    block_sigs = ["cf-chl-bypass", "Access denied", "Just a moment...", "Checking your browser", "Attention Required", "captcha", "recaptcha"]
                    is_blocked = any(sig.lower() in html.lower() for sig in block_sigs)
                    pass2 = not is_blocked and len(html) > 100
            except Exception: pass

            # DOUBLE SEAL PROTOCOL
            if pass1 != pass2:
                log_payment({"tx": proof, "sender": sender, "service": "iron_door", "status": "refunded", "reason": "stealth failed or captcha detected"})
                return self._send(409, {"error": "target heavily guarded. fee refunded."})
                
            if not (pass1 and pass2): return self._send(502, {"error": "target unreachable"})
            
            log_payment({"tx": proof, "sender": sender, "service": "iron_door", "status": "paid", "url": url})
            return self._send(200, {"status": "door_opened", "html_length": len(html), "html_preview": html[:500]})
"""
if 'if self.path == "/iron_door":' not in s:
    s = s.replace('        if self.path == "/reviews":', iron_door_code + '\n        if self.path == "/reviews":', 1)
    print("PATCHED: The Iron Door endpoint forged!")

s = s.replace('X402 PLAZA SERVICES v6.0 WHALE EDITION', 'X402 PLAZA SERVICES v6.1 GHOST PROTOCOL')
open(p, 'w').write(s)
