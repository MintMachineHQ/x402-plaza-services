import re

with open('/home/zero/tollbooth/cashier.py', 'r') as f:
    content = f.read()

# Show the buy_firewall_credits endpoint
print("=" * 60)
print("FIREWALL ENDPOINT (looking for credits validation):")
print("=" * 60)
match = re.search(r'if self\.path == "/buy_firewall_credits":(.*?)(?=\n        if self\.path ==|\n    def )', content, re.DOTALL)
if match:
    print(match.group(0)[:500])
else:
    print("NOT FOUND")

# Show the redteam endpoint
print("\n" + "=" * 60)
print("REDTEAM ENDPOINT:")
print("=" * 60)
match = re.search(r'if self\.path == "/uncensored_exploit_research":(.*?)(?=\n        if self\.path ==|\n    def )', content, re.DOTALL)
if match:
    print(match.group(0)[:500])
else:
    print("NOT FOUND")

# Show the forensics endpoint
print("\n" + "=" * 60)
print("FORENSICS ENDPOINT:")
print("=" * 60)
match = re.search(r'if self\.path == "/post_hack_autopsy":(.*?)(?=\n        if self\.path ==|\n    def )', content, re.DOTALL)
if match:
    print(match.group(0)[:500])
else:
    print("NOT FOUND")

# Show the certify endpoint
print("\n" + "=" * 60)
print("CERTIFY ENDPOINT (to see what field it returns):")
print("=" * 60)
match = re.search(r'if self\.path == "/certify_my_package":(.*?)(?=\n        if self\.path ==|\n    def )', content, re.DOTALL)
if match:
    print(match.group(0)[:500])
else:
    print("NOT FOUND")
