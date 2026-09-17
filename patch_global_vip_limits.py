p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

vip_endpoints = [
    '"/offline_ai_analysis"', 
    '"/verify_escrow_work"', 
    '"/uncensored_exploit_research"', 
    '"/post_hack_autopsy"', 
    '"/bypass_captcha_and_scrape"'
]

for ep in vip_endpoints:
    # Inject rate limit check right after the endpoint path match
    target = f'if self.path == {ep}:'
    if target in content and 'wallet_rate_check' not in content.split(target)[1].split('if self.path ==')[0]:
        content = content.replace(
            target,
            f'{target}\n            if not wallet_rate_check((self.headers.get("X-Wallet") or "").lower(), limit=50): return self._send(429, {{"error": "VIP wallet rate limit"}})'
        )

with open(p, 'w') as f:
    f.write(content)
print("GLOBAL: Wallet rate limit (50/hr) wired to all 5 VIP AI endpoints!")
