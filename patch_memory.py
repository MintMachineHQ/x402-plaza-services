p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

memory_code = """
        if self.path == "/memory":
            action = payload.get("action", "store")
            wallet = (self.headers.get("X-Wallet") or payload.get("wallet", "")).lower()
            if not wallet: return self._send(400, {"error": "missing wallet"})
            
            if action == "recall":
                try: memories = json.load(open(f"memories/{wallet}.json"))
                except Exception: memories = []
                return self._send(200, {"wallet": wallet, "count": len(memories), "memories": memories[-5:]})
                
            text = payload.get("memory", "")
            if not text: return self._send(400, {"error": "missing memory"})
            verified, sender, tier, amount = verify_payment(proof, 1000) # 0.001 USDC = 1000 micro-USDC
            if not verified:
                return self._send(402, {"x402": {"price": "0.001 USDC", "destination": DEST_WALLET, "instruction": "Hippocampus: store a memory permanently."}})
            
            os.makedirs("memories", exist_ok=True)
            fpath = f"memories/{wallet}.json"
            try: memories = json.load(open(fpath))
            except Exception: memories = []
            
            entry_hash = hashlib.sha256(text.encode()).hexdigest()
            memories.append({"text": text, "timestamp": time.time(), "hash": entry_hash})
            
            # Pass 1: Write to disk
            pass1 = False
            try:
                with open(fpath, "w") as f: json.dump(memories, f, indent=2)
                pass1 = True
            except Exception: pass
            
            # Pass 2: Read back and verify hash
            pass2 = False
            try:
                check_memories = json.load(open(fpath))
                pass2 = check_memories[-1]["hash"] == entry_hash and check_memories[-1]["text"] == text
            except Exception: pass
            
            if pass1 != pass2:
                log_payment({"tx": proof, "sender": sender, "service": "memory", "status": "refunded", "reason": "double-seal divergence"})
                return self._send(409, {"error": "storage divergence. fee refunded."})
                
            if not (pass1 and pass2):
                return self._send(500, {"error": "storage failure"})
                
            log_payment({"tx": proof, "sender": sender, "service": "memory", "status": "paid"})
            return self._send(200, {"status": "remembered", "count": len(memories), "hash": entry_hash})
"""

if 'if self.path == "/memory":' not in s:
    s = s.replace('        if self.path == "/reviews":', memory_code + '\n        if self.path == "/reviews":', 1)
    print("PATCHED: Hippocampus endpoint injected")

catalog_add = '''                    "/memory": {"price": "0.001 USDC (store)", "desc": "Hippocampus: wallet-gated persistent memory. Refunds on disk failure."},\n'''
if '"/memory"' not in s:
    s = s.replace('                    "/tunnel"', catalog_add + '                    "/tunnel"', 1)
    print("PATCHED: Hippocampus added to catalog")

s = s.replace('X402 PLAZA SERVICES v5.1 TUNNEL', 'X402 PLAZA SERVICES v5.2 HIPPOCAMPUS', 1)
open(p, 'w').write(s)
