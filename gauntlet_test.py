import stealth_engine
import time

print("=" * 60)
print("🛡️ PLAZA STEALTH ENGINE: THE GAUNTLET TEST 🛡️")
print("=" * 60)

targets = [
    ("Tier 1: Baseline", "https://example.com"),
    ("Tier 2: Basic Cloudflare", "https://www.scrapingcourse.com/cloudflare-challenge"),
    ("Tier 3: Akamai / DataDome (Nike)", "https://www.nike.com/"),
    ("Tier 4: Enterprise 'Under Attack' Mode", "https://www.corporatefinanceinstitute.com/"),
]

for name, url in targets:
    print(f"\n🎯 Testing {name}: {url}")
    print("-" * 40)
    start = time.time()
    result = stealth_engine.scrape_stealth(url, wallet="0xGAUNTLET_TESTER")
    elapsed = time.time() - start
    
    if result["success"]:
        print(f"✅ SUCCESS in {elapsed:.1f}s")
        print(f"   Layer Used: {result['layer']} ({result['method']})")
        print(f"   Confidence: {result.get('confidence', '?')}% | Freshness: {result.get('freshness', '?')}")
        print(f"   Bytes Retrieved: {result['bytes']}")
        # Show a tiny snippet of the text to prove it's not HTML boilerplate
        snippet = result["html"][:150].replace("\n", " ")
        print(f"   Snippet: {snippet}...")
    else:
        print(f"❌ BLOCKED in {elapsed:.1f}s at Layer {result['layer']}")
        print(f"   Reason: {result['reason']}")
        if result.get("retry_credit_granted"):
            print(f"   🎁 Retry credit granted for 24h (Goodwill saved!)")

print("\n" + "=" * 60)
print("GAUNTLET COMPLETE")
print("=" * 60)
