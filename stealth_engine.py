#!/usr/bin/env python3
"""Stealth Residential Scrape v5 - hardened 4-layer anti-bot pipeline.
Layers: 1 rotating fingerprints, 2 reader proxy, 3 archive snapshot, 4 residential slot (future).
Revisions: v2 resource/redirect defenses, v3 DNS-rebinding pin, v4 cost-burn quotas,
v5 review-proofing (retry credits, confidence metadata), v5.1 legality blocklists."""
import ipaddress, json, os, re, socket, threading, time
import urllib.request, urllib.error
from urllib.parse import urlparse

RATE_FILE = "stealth_rate.json"
STATE_FILE = "stealth_state.json"
RESIDENTIAL_PROXY_SLOT = None  # future paid residential pool plug-in point

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

def _wallet_sem(wallet):
    with _LOCK:
        if wallet not in _WALLET_SEMS:
            _WALLET_SEMS[wallet] = threading.Semaphore(2)
        return _WALLET_SEMS[wallet]

def _public_ip(host):
    """v3 pin: resolve and require a public IP."""
    try:
        ip = socket.gethostbyname(host)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return None, f"{host} resolves to non-public IP {ip}"
        return ip, ""
    except Exception as e:
        return None, f"DNS failure: {e}"

def _hop_allowed(url):
    """Validation applied to the original URL AND every redirect hop."""
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
    """v4: daily cap, fail quota, cooldown, failure cache."""
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
        headers["sec-ch-ua"] = fp["sec_ch_ua"]
        headers["sec-ch-ua-platform"] = fp["platform"]
        headers["sec-ch-ua-mobile"] = "?0"
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

def scrape_stealth(url, wallet="", use_credit=False):
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

    with _GLOBAL_SEM, _wallet_sem((wallet or "anon").lower()):
        for fp in FINGERPRINTS:
            try:
                html, err = _fetch(url, fp, _make_opener([0]))
                if html is None:
                    return {"success": False, "layer": 1, "reason": err}
                if not _is_challenge(html):
                    _record_outcome(url, wallet, False)
                    return {"success": True, "layer": 1, "method": "direct_stealth_fingerprint",
                            "confidence": 95, "freshness": "live", "html": html[:200000], "bytes": len(html)}
            except Exception:
                continue
        try:
            text, err = _via_reader(url)
            if text and not _is_challenge(text):
                _record_outcome(url, wallet, False)
                return {"success": True, "layer": 2, "method": "reader_proxy",
                        "confidence": 85, "freshness": "live", "html": text[:200000], "bytes": len(text)}
        except Exception:
            pass
        try:
            html, err = _via_wayback(url)
            if html:
                _record_outcome(url, wallet, False)
                return {"success": True, "layer": 3, "method": "archive_snapshot",
                        "confidence": 70, "freshness": "archived", "html": html[:200000], "bytes": len(html),
                        "note": "live layers blocked; served from archive snapshot"}
        except Exception:
            pass

    _record_outcome(url, wallet, True)
    st = _load_state()
    st["credits"][(wallet or "anon").lower()] = time.time() + 86400
    _save_state(st)
    return {"success": False, "layer": 4,
            "reason": "All stealth layers failed: enterprise-grade protection. Retry credit granted for 24h (free retry).",
            "retry_credit_granted": True,
            "next_steps": ["retry in a few hours with your credit", "use scrape.bypass_captcha for CAPTCHA walls",
                           "residential proxy tier coming soon"]}

def has_credit(wallet):
    st = _load_state()
    return st["credits"].get((wallet or "").lower(), 0) > time.time()
