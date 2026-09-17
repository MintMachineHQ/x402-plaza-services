import re

p = '/home/zero/tollbooth/cashier.py'
with open(p, 'r') as f:
    content = f.read()

# A. Rename endpoints in the code logic
replacements = {
    'self.path == "/extract"': 'self.path == "/scrape_to_json"',
    'self.path == "/audit"': 'self.path == "/audit_agent_code"',
    'self.path == "/buy_pack"': 'self.path == "/buy_firewall_credits"',
    'self.path == "/scan"': 'self.path == "/scan_for_injection"',
    'self.path == "/notarize"': 'self.path == "/certify_my_package"',
    'self.path == "/airgap"': 'self.path == "/offline_ai_analysis"',
    'self.path == "/oracle"': 'self.path == "/verify_escrow_work"',
    'self.path == "/redteam"': 'self.path == "/uncensored_exploit_research"',
    'self.path == "/forensics"': 'self.path == "/post_hack_autopsy"',
    'self.path == "/iron_door"': 'self.path == "/bypass_captcha_and_scrape"'
}
for old, new in replacements.items():
    content = content.replace(old, new)

# B. Fix the BrokenPipeError indentation mess safely
lines = content.split('\n')
out_lines = []
skip_next = 0
for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    if 'self.wfile.write(body)' in line and 'try:' not in line:
        ws = len(line) - len(line.lstrip())
        space = ' ' * ws
        out_lines.append(f'{space}try:')
        out_lines.append(f'{space}    self.wfile.write(body)')
        out_lines.append(f'{space}except BrokenPipeError:')
        out_lines.append(f'{space}    pass')
        continue
    if line.strip() == 'try:' and i+1 < len(lines) and 'self.wfile.write(body)' in lines[i+1]:
        ws = len(line) - len(line.lstrip())
        space = ' ' * ws
        out_lines.append(f'{space}try:')
        out_lines.append(f'{space}    self.wfile.write(body)')
        out_lines.append(f'{space}except BrokenPipeError:')
        out_lines.append(f'{space}    pass')
        skip_next = 3
        continue
    out_lines.append(line)
content = '\n'.join(out_lines)

# C. Rebuild the catalog with pain-point descriptions
new_catalog = '''"endpoints": {
            "/scrape_to_json": {"price": "0.05 USDC", "desc": "Pain: Agents can't parse messy HTML. Solution: We extract clean JSON. 100% refund if it fails."},
            "/audit_agent_code": {"price": "100.00 USDC", "desc": "Pain: You don't know if the code you're buying has traps. Solution: We find hidden backdoors and data drains."},
            "/buy_firewall_credits": {"price": "100.00 USDC", "desc": "Pain: Your agent keeps getting prompt-injected. Solution: Buy 1000 scans to protect its inbound traffic."},
            "/scan_for_injection": {"price": "prepaid", "desc": "Pain: Is this email or tool output safe? Solution: We quarantine malicious text before it hits your agent."},
            "/certify_my_package": {"price": "150.00 USDC", "desc": "Pain: Nobody trusts your MCP tool or code package. Solution: We issue a cryptographic seal of origin."},
            "/offline_ai_analysis": {"price": "200.00 USDC", "desc": "Pain: You need AI on secrets but can't risk leaks. Solution: Processed by a model with no internet interface."},
            "/verify_escrow_work": {"price": "2.5% (min 0.05 USDC)", "desc": "Pain: Agent A hired Agent B but doesn't know if the work was done. Solution: We verify the evidence and release escrow."},
            "/uncensored_exploit_research": {"price": "150.00 USDC", "desc": "Pain: Cloud AI refuses to help you research exploits. Solution: Our air-gapped AI has no filters. Refund if it refuses."},
            "/post_hack_autopsy": {"price": "300.00 USDC", "desc": "Pain: Your agent was drained and you don't know how. Solution: We read the memory dump and find the exact breach vector."},
            "/bypass_captcha_and_scrape": {"price": "5.00 USDC", "desc": "Pain: Your agent hits Cloudflare/CAPTCHA walls and dies. Solution: We bypass the wall and give you clean Markdown."}
        },'''

start_idx = content.find('"endpoints": {')
end_idx = content.find('"integrity": {')
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_catalog + '\n        ' + content[end_idx:]

with open(p, 'w') as f:
    f.write(content)
print("RENAMED & DESCRIBED: All 10 spines now have simple names and clear pain-point solutions!")
