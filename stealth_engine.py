#!/usr/bin/env python3
"""Stealth Residential Scrape v6 - with AI extraction, smart retry, and batch processing."""
import ipaddress, json, os, re, socket, threading, time
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
import urllib.request, urllib.error
from urllib.parse import urlparse
from datetime import datetime

RATE_FILE = "stealth_rate.json"
STATE_FILE = "stealth_state.json"
RETRY_FILE = "stealth_retries.json"
RESIDENTIAL_PROXY_SLOT = None

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT = 12
MAX_HOPS = 3
DAILY_CAP = 50
FAIL_QUOTA = 5
FAIL_CACHE_TTL = 3600
COOLDOWN = 86400
_GLOBAL_SEM = threading.Semaphore(5)
_WALLET_SEMS = {}
_LOCK = threading.Lock()

FINGERPRINTS = [
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
     "sec_ch_ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"', "platform": '"Windows"'},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
     "sec_ch_ua": None, "platform": None},
    {"ua": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
     "sec_ch_ua": None, "platform": None},
]

BLOCKED_DOMAINS = [r"\.gov$", r"\.mil$", r"irs\.", r"ssa\.gov", r"bankofamerica", r"chase\.com",
    r"wellsfargo", r"citibank", r"paypal\.com", r"coinbase\.com", r"binance\.", r"kraken\.",
    r"\.bank$", r"login\.", r"secure\.", r"accounts\."]
BLOCKED_PATH_KEYWORDS = ["leaked", "leak-", "doxx", "swat", "csam", "warez", "torrent", "dump-"]
CHALLENGE_MARKERS = ["cf-browser-verification", "cf_chl_opt", "turnstile", "data-dome", "akamai",
    "px-captcha", "perimeterx", "just a moment", "checking your browser", "access denied",
    "are you a robot", "captcha", "attention required"]

def _load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"daily": {}, "failcache": {}, "credits": {}}

def _save_state(d):
    json.dump(d, open(STATE_FILE, "w"))

def _load_retries():
    try:
        return json.load(open(RETRY_FILE))
    except Exception:
        return {}

def _save_retries(d):
    json.dump(d, open(RETRY_FILE, "w"))

def _wallet_sem(wallet):
    with _LOCK:
        if wallet not in _WALLET_SEMS:
            _WALLET_SEMS[wallet] = threading.Semaphore(2)
        return _WALLET_SEMS[wallet]

def _public_ip(host):
    try:
        ip = socket.gethostbyname(host)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return None, f"{host} resolves to non-public IP {ip}"
        return ip, ""
    except Exception as e:
        return None, f"DNS failure: {e}"

def _hop_allowed(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False, f"bad scheme {p.scheme}"
    host = (p.hostname or "").lower()
    for pat in BLOCKED_DOMAINS:
        if re.search(pat, host):
            return False, f"blocked category: {host}"
    low = p.path.lower()
    for kw in BLOCKED_PATH_KEYWORDS:
        if kw in low:
            return False, f"blocked path keyword: {kw}"
    ip, err = _public_ip(host)
    if not ip:
        return False, err
    return True, ""

def _rate_ok(url, wallet):
    key = ((wallet or "anon").lower() + "|" + url)[:300]
    now = time.time()
    try:
        d = json.load(open(RATE_FILE))
    except Exception:
        d = {}
    hits = [t for t in d.get(key, []) if now - t < 60]
    if len(hits) >= 3:
        return False
    hits.append(now)
    d[key] = hits[-10:]
    json.dump(d, open(RATE_FILE, "w"))
    return True

def _quotas_ok(url, wallet):
    w = (wallet or "anon").lower()
    st = _load_state()
    now = time.time()
    today = time.strftime("%Y-%m-%d")
    if st["failcache"].get(url, 0) > now:
        return False, "URL known-dead (failed at all layers recently). Refused for 1h (anti cost-burn)."
    rec = st["daily"].get(w, {"date": today, "calls": 0, "fails": 0, "cool": 0})
    if rec.get("date") != today:
        rec = {"date": today, "calls": 0, "fails": 0, "cool": 0}
    if rec.get("cool", 0) > now:
        return False, f"Wallet in 24h cooldown after {FAIL_QUOTA} layer-4 failures (anti cost-burn)."
    if rec["calls"] >= DAILY_CAP:
        return False, f"Daily cap reached ({DAILY_CAP} stealth calls/day/wallet)."
    st["daily"][w] = rec
    _save_state(st)
    return True, ""

def _record_outcome(url, wallet, failed_layer4):
    w = (wallet or "anon").lower()
    st = _load_state()
    today = time.strftime("%Y-%m-%d")
    rec = st["daily"].get(w, {"date": today, "calls": 0, "fails": 0, "cool": 0})
    if rec.get("date") != today:
        rec = {"date": today, "calls": 0, "fails": 0, "cool": 0}
    rec["calls"] += 1
    if failed_layer4:
        rec["fails"] += 1
        st["failcache"][url] = time.time() + FAIL_CACHE_TTL
        if rec["fails"] >= FAIL_QUOTA:
            rec["cool"] = time.time() + COOLDOWN
            st["credits"].pop(w, None)
    st["daily"][w] = rec
    _save_state(st)

def _is_challenge(html):
    low = html.lower()
    return any(m in low for m in CHALLENGE_MARKERS)

def _make_opener(hops):
    class RH(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if hops[0] >= MAX_HOPS:
                raise urllib.error.HTTPError(newurl, code, "Too many redirects", headers, fp)
            ok, reason = _hop_allowed(newurl)
            if not ok:
                raise urllib.error.HTTPError(newurl, code, "Redirect blocked: " + reason, headers, fp)
            hops[0] += 1
            return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)
    return urllib.request.build_opener(RH)

def _fetch(url, fp, opener):
    headers = {"User-Agent": fp["ua"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "identity",
        "Cache-Control": "no-cache", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1", "Upgrade-Insecure-Requests": "1"}
    if fp.get("sec_ch_ua"):
        headers["sec-ch_ua"] = fp["sec_ch_ua"]
        headers["sec-ch_ua-platform"] = fp["platform"]
        headers["sec-ch_ua-mobile"] = "?0"
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=TIMEOUT) as r:
        cl = r.headers.get("Content-Length")
        if cl and int(cl) > MAX_BYTES:
            return None, f"Content-Length {cl} exceeds 5MB cap - aborted (anti resource bomb)"
        ctype = r.headers.get("Content-Type", "")
        if not any(t in ctype for t in ("text/html", "text/plain", "json")):
            return None, f"Non-HTML response ({ctype}) - aborted (anti Proxy Cannon)"
        data = r.read(MAX_BYTES)
        return data.decode("utf-8", errors="replace"), ""

def _via_reader(url):
    req = urllib.request.Request("https://r.jina.ai/" + url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read(MAX_BYTES).decode("utf-8", errors="replace"), ""

def _via_wayback(url):
    with urllib.request.urlopen("http://archive.org/wayback/available?url=" + url, timeout=25) as r:
        d = json.loads(r.read().decode())
    snap = d.get("archived_snapshots", {}).get("closest", {})
    if not snap.get("available"):
        return None, "no archive snapshot"
    with urllib.request.urlopen(snap["url"], timeout=25) as r:
        return r.read(MAX_BYTES).decode("utf-8", errors="replace"), ""

def _extract_with_ai(html, extract_query, wallet):
    """Use Ollama to extract structured data from HTML."""
    try:
        prompt = f"""You are a web scraping assistant. Extract the requested information from this HTML content.

USER REQUEST: {extract_query}

HTML CONTENT (first 50000 chars):
{html[:50000]}

INSTRUCTIONS:
1. Extract ONLY what the user requested
2. Return a valid JSON object
3. If information is not found, use null or empty arrays
4. Do not include explanations, only JSON

EXAMPLE OUTPUT FORMAT:
{{"products": [{{"name": "Product Name", "price": 29.99, "in_stock": true}}], "total_items": 15}}

Return only the JSON object, no other text:"""

        req_data = json.dumps({
            "model": "qwen2.5:1.5b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 2000}
        }).encode()

        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode())
            content = result.get("message", {}).get("content", "{}")
            try:
                extracted = json.loads(content)
                return {"success": True, "data": extracted}
            except json.JSONDecodeError:
                return {"success": False, "reason": "AI returned invalid JSON", "raw": content[:500]}
    except Exception as e:
        return {"success": False, "reason": f"AI extraction failed: {str(e)}"}

def _via_curl_cffi(url):
    """Layer 0.5: curl_cffi with TLS fingerprint spoofing (fast, beats basic Cloudflare)."""
    if not HAS_CURL_CFFI:
        return None, "curl_cffi not installed"
    try:
        r = cffi_requests.get(url, impersonate="chrome124", timeout=15)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        html = r.text
        if _is_challenge(html):
            return None, "challenge detected"
        return html, ""
    except Exception as e:
        return None, f"curl_cffi error: {str(e)[:100]}"

def _via_playwright(url):
    """Layer 1.5: headless Chromium with anti-detection init scripts.
    Blocks images/media/fonts (saves bandwidth + time), masks webdriver flags,
    waits 2.5s so auto-solving challenges (Turnstile) can pass themselves."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, "playwright not installed"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox", "--disable-dev-shm-usage"])
            ctx = browser.new_context(
                user_agent=FINGERPRINTS[0]["ua"],
                viewport={"width": 1366, "height": 768},
                locale="en-US", timezone_id="America/New_York")
            ctx.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = {runtime: {}};
            """)
            page = ctx.new_page()
            page.route("**/*", lambda route: route.abort()
                       if route.request.resource_type in ("image", "media", "font")
                       else route.continue_())
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()
            return html, ""
    except Exception as e:
        return None, f"playwright error: {str(e)[:120]}"

def _attempt_scrape(url, wallet):
    """Single attempt using all 4 layers."""
        # Layer 0.5: curl_cffi (TLS fingerprint spoofing, fast)
        html, err = _via_curl_cffi(url)
        if html:
            return {"success": True, "layer": 0.5, "method": "curl_cffi_tls_spoofing",
                    "confidence": 92, "freshness": "live", "html": html, "bytes": len(html)}
    for fp in FINGERPRINTS:
        try:
            html, err = _fetch(url, fp, _make_opener([0]))
            if html is None:
                return {"success": False, "layer": 1, "reason": err}
            if not _is_challenge(html):
                return {"success": True, "layer": 1, "method": "direct_stealth_fingerprint",
                        "confidence": 95, "freshness": "live", "html": html, "bytes": len(html)}
        except Exception:
            continue
        # Layer 1.5: Playwright headless Chromium (beats JS challenges)
        html, err = _via_playwright(url)
        if html and not _is_challenge(html):
            return {"success": True, "layer": 1.5, "method": "playwright_stealth_chromium",
                    "confidence": 90, "freshness": "live", "html": html, "bytes": len(html)}
    try:
        text, err = _via_reader(url)
        if text and not _is_challenge(text):
            return {"success": True, "layer": 2, "method": "reader_proxy",
                    "confidence": 85, "freshness": "live", "html": text, "bytes": len(text)}
    except Exception:
        pass
    try:
        html, err = _via_wayback(url)
        if html:
            return {"success": True, "layer": 3, "method": "archive_snapshot",
                    "confidence": 70, "freshness": "archived", "html": html, "bytes": len(html),
                    "note": "live layers blocked; served from archive snapshot"}
    except Exception:
        pass
    return {"success": False, "layer": 4, "reason": "All stealth layers failed: enterprise-grade protection"}

def scrape_stealth(url, wallet="", extract=None, retries=1, batch_discount=False):
    """Enhanced scrape with AI extraction, smart retry, and batch support."""
    from security_quotas import validate_url
    ok, reason = validate_url(url)
    if not ok:
        return {"success": False, "layer": 0, "reason": reason}
    ok, reason = _hop_allowed(url)
    if not ok:
        return {"success": False, "layer": 0, "reason": reason}
    if not _rate_ok(url, wallet):
        return {"success": False, "layer": 0, "reason": "Rate limit: 3 stealth calls/min per wallet per URL (anti Proxy Cannon)."}
    ok, reason = _quotas_ok(url, wallet)
    if not ok:
        return {"success": False, "layer": 0, "reason": reason}

    attempts = []
    start_time = time.time()
    
    with _GLOBAL_SEM, _wallet_sem((wallet or "anon").lower()):
        for attempt_num in range(retries):
            if attempt_num > 0:
                wait_time = min(60 * (2 ** attempt_num), 300)  # 60s, 120s, 240s... max 5min
                time.sleep(wait_time)
            
            result = _attempt_scrape(url, wallet)
            attempts.append({
                "attempt": attempt_num + 1,
                "time": time.time() - start_time,
                "success": result["success"],
                "layer": result.get("layer")
            })
            
            if result["success"]:
                _record_outcome(url, wallet, False)
                
                # AI Extraction mode
                if extract:
                    ai_result = _extract_with_ai(result["html"], extract, wallet)
                    if ai_result["success"]:
                        return {
                            "success": True,
                            "mode": "ai_extraction",
                            "extracted_data": ai_result["data"],
                            "confidence": result.get("confidence", 0),
                            "freshness": result.get("freshness"),
                            "layer_used": result["layer"],
                            "method": result["method"],
                            "attempts": len(attempts),
                            "total_time_seconds": round(time.time() - start_time, 1),
                            "batch_discount_applied": batch_discount
                        }
                    else:
                        return {
                            "success": False,
                            "reason": f"Scrape succeeded but AI extraction failed: {ai_result['reason']}",
                            "attempts": len(attempts)
                        }
                
                # Raw mode
                return {
                    "success": True,
                    "mode": "raw_html",
                    "layer": result["layer"],
                    "method": result["method"],
                    "confidence": result.get("confidence"),
                    "freshness": result.get("freshness"),
                    "html": result["html"][:200000],
                    "bytes": result["bytes"],
                    "attempts": len(attempts),
                    "total_time_seconds": round(time.time() - start_time, 1),
                    "batch_discount_applied": batch_discount
                }

    # All attempts failed
    _record_outcome(url, wallet, True)
    st = _load_state()
    st["credits"][(wallet or "anon").lower()] = time.time() + 86400
    _save_state(st)
    
    return {
        "success": False,
        "layer": 4,
        "reason": f"All {retries} attempts failed over {round(time.time() - start_time, 1)}s",
        "retry_credit_granted": True,
        "attempts": attempts,
        "refund_eligible": retries >= 3,
        "next_steps": [
            "retry in a few hours with your credit",
            "use scrape.bypass_captcha for CAPTCHA walls",
            "residential proxy tier coming soon"
        ]
    }

def scrape_batch(urls, wallet="", extract=None, retries=1):
    """Batch scrape with 50% discount."""
    results = {}
    for url in urls[:10]:  # Max 10 URLs per batch
        result = scrape_stealth(url, wallet, extract, retries, batch_discount=True)
        results[url] = result
    
    return {
        "success": True,
        "mode": "batch",
        "results": results,
        "total_urls": len(urls),
        "successful": sum(1 for r in results.values() if r.get("success")),
        "failed": sum(1 for r in results.values() if not r.get("success")),
        "discount_applied": "50% batch discount",
        "note": "Each result is independent - partial failures don't refund successful scrapes"
    }

def has_credit(wallet):
    st = _load_state()
    return st["credits"].get((wallet or "").lower(), 0) > time.time()
