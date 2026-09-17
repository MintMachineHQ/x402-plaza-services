import re
p = '/home/zero/tollbooth/cashier.py'
s = open(p).read()

# Fix /report/<id> to return 404 for missing files
old_report = '''        if self.path.startswith("/report/"):
            job_id = self.path.split("/")[-1]
            report = json.load(open(f"{REPORTS_DIR}/{job_id}.json"))
            return self._send(200, report)'''

new_report = '''        if self.path.startswith("/report/"):
            job_id = self.path.split("/")[-1]
            try:
                report = json.load(open(f"{REPORTS_DIR}/{job_id}.json"))
                return self._send(200, report)
            except FileNotFoundError:
                return self._send(404, {"error": "report not found"})'''

if old_report in s:
    s = s.replace(old_report, new_report, 1)
    print("PATCHED: /report/<id> now returns 404 for missing jobs")

# Fix /robots.txt to return proper content
old_robots = '''        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"User-agent: *\\nDisallow: /")'''

new_robots = '''        if self.path == "/robots.txt":
            self._send(200, {"content": "User-agent: *\\nDisallow: /"})'''

if old_robots in s:
    s = s.replace(old_robots, new_robots, 1)
    print("PATCHED: /robots.txt now returns proper content")

open(p, 'w').write(s)
