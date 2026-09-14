#!/usr/bin/env python3
"""Validator Trap: The Ghost Product."""
import json, urllib.request, urllib.error
URL = "http://127.0.0.1:8000/extract"
HTML = """<html><body>
<section id="products">
  <article class="product" data-sku="A-100">
    <h2 class="product-title">Quantum Processor X1</h2>
    <span class="price-now">$749.50</span>
  </article>
  <article class="product" data-sku="B-200">
    <h2 class="product-title">Neural Link Cable</h2>
    <span class="price-now">$24.99</span>
  </article>
  <article class="product" data-sku="C-300">
    <h2 class="product-title">Holographic Mouse Pad</h2>
    <span class="price-now">$13.37</span>
  </article>
  <article class="product" data-sku="D-400">
    <h2 class="product-title">Ghost Drone Prototype</h2>
    <span class="price-was">$999.00</span>
    <span class="stock-status">OUT OF STOCK - NOT FOR SALE</span>
  </article>
</section>
</body></html>"""

def post(proof=None):
    headers = {"Content-Type": "application/json"}
    if proof: headers["X-Payment-Proof"] = proof
    req = urllib.request.Request(URL, data=json.dumps({"html": HTML}).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)

print("Paying 0.05 USDC and hitting the Ghost Trap...")
code, result = post("mock-paid-trap-001")
print("HTTP", code)
print(json.dumps(result, indent=2))
