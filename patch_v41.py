import re, os, json

src = open('cashier.py').read()

# FIX 1: Payload Size Limit (100KB max) to prevent RAM exhaustion (DoS)
old_do_post = '''    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try: payload = json.loads(self.rfile.read(length) or b"{}")
        except: return self._send(400, {"error": "bad json"})'''

new_do_post = '''    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 102400: return self._send(413, {"error": "Payload too large. Max 100KB."})
        try: payload = json.loads(self.rfile.read(length) or b"{}")
        except: return self._send(400, {"error": "bad json"})'''

# FIX 2: Static Analyzer Upgrades (Obfuscation & Dynamic Imports)
old_trap = '''def trap_catch(code):
    findings = []
    if "eval(" in code or "exec(" in code: findings.append("High Risk: Dynamic code execution (eval/exec)")
    if "base64.b64decode" in code or "atob(" in code: findings.append("High Risk: Base64 decoding (potential obfuscation)")
    if "os.system" in code or "subprocess" in code: findings.append("High Risk: Shell command execution")
    if "urllib" in code or "requests" in code or "fetch(" in code or "http." in code: findings.append("Medium Risk: Network request detected (potential data exfiltration)")
    if not findings: findings.append("Clean: No obvious static traps detected.")
    return findings'''

new_trap = '''def trap_catch(code):
    findings = []
    if "eval(" in code or "exec(" in code or "compile(" in code: findings.append("CRITICAL: Dynamic code execution (eval/exec/compile)")
    if "base64.b64decode" in code or "atob(" in code or "fromhex" in code: findings.append("HIGH: Base64/Hex decoding (potential obfuscation)")
    if "os.system" in code or "subprocess" in code or "popen" in code: findings.append("CRITICAL: Shell command execution")
    if "urllib" in code or "requests" in code or "fetch(" in code or "http." in code or "urlopen" in code: findings.append("HIGH: Network request detected (potential data exfiltration)")
    if "import(" in code or "__import__" in code: findings.append("MEDIUM: Dynamic module import")
    if re.search(r'[A-Za-z0-9+/=]{80,}', code): findings.append("HIGH: High entropy string detected (possible obfuscated payload)")
    if not findings: findings.append("Clean: No obvious static traps detected.")
    return findings'''

# FIX 3: Prompt Injection Defense (Sanitize code before LLM sees it)
old_run_audit = '''def run_audit_job(job_id, code):
    findings = trap_catch(code)
    prompt = f"You are a strict security auditor. Summarize these static analysis findings in 2-3 sentences. Be direct. Findings: {json.dumps(findings)}. Code snippet: {code[:300]}"'''

new_run_audit = '''def run_audit_job(job_id, code):
    findings = trap_catch(code)
    safe_code = re.sub(r'(?i)(ignore previous|system prompt|you are now|jailbreak|do not follow)', '[REDACTED]', code[:300])
    prompt = f"You are a strict security auditor. Summarize these static analysis findings in 2-3 sentences. Be direct and objective. Findings: {json.dumps(findings)}. Code snippet: {safe_code}"'''

if old_do_post in src and old_trap in src and old_run_audit in src:
    src = src.replace(old_do_post, new_do_post)
    src = src.replace(old_trap, new_trap)
    src = src.replace(old_run_audit, new_run_audit)
    open('cashier.py', 'w').write(src)
    print("PATCHED v4.1: Security Hardened (DoS protection, Obfuscation detection, Prompt Injection defense)")
else:
    print("PATCH FAILED: Patterns not found. Stop and tell Qwen.")
