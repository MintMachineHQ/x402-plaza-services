src = open('cashier.py').read()
old = '        self._send(200, {"status": "ok", "service": "tollbooth-extract", "network": NETWORK})'
new = '''        if self.path == "/robots.txt":
            body = b"User-agent: *\\nAllow: /catalog\\nAllow: /x402-manifest.json\\nDisallow: /extract\\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/x402-manifest.json":
            return self._send(200, {
                "service": "tollbooth-extract", "protocol": "x402", "version": 1,
                "pricing": {"price": PRICE, "token": TOKEN, "network": NETWORK, "amount_base_units": PRICE_UNITS, "decimals": 6},
                "destination": DEST_WALLET,
                "endpoints": {"catalog": "GET /catalog", "extract": "POST /extract with X-Payment-Proof header"},
                "features": ["strict-json", "validator-retry", "source-citations", "auto-refund"]})
        self._send(200, {"status": "ok", "service": "tollbooth-extract", "network": NETWORK})'''
if old in src:
    open('cashier.py', 'w').write(src.replace(old, new))
    print("PATCHED: robots.txt + manifest routes added")
else:
    print("PATTERN NOT FOUND - stop and tell Qwen")
