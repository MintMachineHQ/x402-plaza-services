#!/usr/bin/env python3
"""Track marketing channel performance."""
import json
import time
from urllib.parse import urlparse, parse_qs

ANALYTICS_FILE = "marketing_analytics.json"

def _load():
    try:
        return json.load(open(ANALYTICS_FILE))
    except:
        return {"channels": {}, "conversions": []}

def _save(data):
    json.dump(data, open(ANALYTICS_FILE, "w"))

def track_referral(request_url, request_headers):
    """Track which channel brought this request."""
    parsed = urlparse(request_url)
    params = parse_qs(parsed.query)
    
    # Detect channel
    channel = "direct"
    if "ref" in params:
        channel = params["ref"][0]
    elif "utm_source" in params:
        channel = params["utm_source"][0]
    elif "referer" in request_headers:
        referer = request_headers["referer"]
        if "google" in referer:
            channel = "google"
        elif "twitter" in referer:
            channel = "twitter"
        elif "reddit" in referer:
            channel = "reddit"
        elif "smithery" in referer:
            channel = "smithery"
    
    data = _load()
    if channel not in data["channels"]:
        data["channels"][channel] = {"visits": 0, "conversions": 0}
    
    data["channels"][channel]["visits"] += 1
    _save(data)
    
    return channel

def track_conversion(wallet, channel):
    """Track when a visit becomes a paying customer."""
    data = _load()
    if channel in data["channels"]:
        data["channels"][channel]["conversions"] += 1
    data["conversions"].append({
        "wallet": wallet,
        "channel": channel,
        "timestamp": time.time()
    })
    _save(data)

def get_analytics():
    """Return marketing performance report."""
    data = _load()
    report = []
    for channel, stats in data["channels"].items():
        conv_rate = (stats["conversions"] / stats["visits"] * 100) if stats["visits"] > 0 else 0
        report.append({
            "channel": channel,
            "visits": stats["visits"],
            "conversions": stats["conversions"],
            "conversion_rate": f"{conv_rate:.1f}%"
        })
    return sorted(report, key=lambda x: x["conversions"], reverse=True)

if __name__ == "__main__":
    print("=== MARKETING ANALYTICS ===")
    for stat in get_analytics():
        print(f"{stat['channel']}: {stat['visits']} visits, {stat['conversions']} conversions ({stat['conversion_rate']})")
