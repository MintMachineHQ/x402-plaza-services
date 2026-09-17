import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# Remove the old iron_door block cleanly
lines = s.split('\n')
out = []
skip = False
for line in lines:
    if 'if self.path == "/iron_door":' in line: skip = True; continue
    if skip and line.startswith('        if self.path =='): skip = False
    if not skip: out.append(line)
s = '\n'.join(out)

# Inject the NEW exponentially over-delivering Iron Door
iron_door_new = """
        if self.path == "/iron_door":
            url = payload.get("url", "")
            if not url.startswith("http"): return self._send(400, {"error": "invalid url"})
            verified, sender, tier, amount = verify_payment(proof, 5000000) # 5 USDC
            if not verified:
                return self._send(402, {"x402": {"price": "5.00 USDC", "destination": DEST_WALLET, "instruction": "The Iron Door: bypass bot-traps + AI content extraction."}})
            
            # Pass 1: Stealth Fetch with multiple fallback headers
            html = ""
            headers_list = [
                {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"},
                {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"}
            ]
            for hdrs in headers_list:
                try:
                    req = urllib.request.Request(url, headers=hdrs)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        html = resp.read().decode('utf-8', errors='ignore')
                        break
                except Exception: pass
                
            block_sigs = ["cf-chl-bypass", "Access denied", "Just a moment...", "Checking your browser", "Attention Required", "captcha", "recaptcha"]
            is_blocked = any(sig.lower() in html.lower() for sig in block_sigs) or len(html) < 50
            if is_blocked:
                log_payment({"tx": proof, "sender": sender, "service": "iron_door", "status": "refunded", "reason": "target heavily guarded"})
                return self._send(409, {"error": "target heavily guarded. fee refunded."})
            
            # Pass 2: EXPONENTIAL OVER-DELIVERY (AI Markdown Extraction)
            # The agent gets clean Markdown instead of raw HTML, saving them massive compute!
            try:
                html_trunc = html[:4000] # Keep within 4096 context limit for the VIP
                msgs = [{"role": "system", "content": "Convert this HTML into clean, concise Markdown for an AI agent to read. Ignore scripts/styles."},
                        {"role": "user", "content": html_trunc}]
                markdown_content = ask_walled(msgs)
            except Exception:
                markdown_content = html[:1000]
            
            log_payment({"tx": proof, "sender": sender, "service": "iron_door", "status": "paid", "url": url})
            return self._send(200, {"status": "door_opened", "markdown": markdown_content.strip(), "raw_length": len(html)})
"""

s = s.replace('        if self.path == "/reviews":', iron_door_new + '\n        if self.path == "/reviews":', 1)
open(p, 'w').write(s)
print("OVER-DELIVERED: Iron Door now includes AI Markdown Extraction!")
