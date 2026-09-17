p = '/home/zero/tollbooth/cashier.py'
lines = open(p).read().splitlines(True)
out = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # FIX 1: /report/<id> handler (catch missing files)
    if 'if self.path.startswith("/report/"):' in line:
        out.append(line)
        out.append('            job_id = self.path.split("/")[-1]\n')
        out.append('            try:\n')
        out.append('                report = json.load(open(f"{REPORTS_DIR}/{job_id}.json"))\n')
        out.append('                return self._send(200, report)\n')
        out.append('            except Exception:\n')
        out.append('                return self._send(404, {"error": "report not found"})\n')
        # Skip the original lines for this block
        i += 3
        continue
        
    # FIX 2: /robots.txt handler (ensure it returns proper content)
    elif 'if self.path == "/robots.txt":' in line:
        out.append(line)
        out.append('            return self._send(200, {"content": "User-agent: *\\nDisallow: /"})\n')
        # Skip the original lines until the next 'if' statement
        j = i + 1
        while j < len(lines) and 'if self.path' not in lines[j]:
            j += 1
        i = j
        continue
        
    out.append(line)
    i += 1

open(p, 'w').writelines(out)
print("PATCHED: /report/ and /robots.txt handlers rebuilt safely")
