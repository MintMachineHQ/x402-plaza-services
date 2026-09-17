#!/usr/bin/env python3
"""A/B test landing pages and auto-optimize."""
import json
import random

AB_TEST_FILE = "ab_tests.json"

def _load():
    try:
        return json.load(open(AB_TEST_FILE))
    except:
        return {"tests": {}, "winners": {}}

def _save(data):
    json.dump(data, open(AB_TEST_FILE, "w"))

def create_test(test_name, variants):
    """Create an A/B test with multiple variants."""
    data = _load()
    data["tests"][test_name] = {
        "variants": variants,
        "impressions": {v: 0 for v in variants},
        "conversions": {v: 0 for v in variants},
        "winner": None
    }
    _save(data)

def serve_variant(test_name):
    """Serve a random variant to the user."""
    data = _load()
    if test_name not in data["tests"]:
        return None
    
    test = data["tests"][test_name]
    
    # If we have a winner, serve it 90% of the time
    if test["winner"]:
        if random.random() < 0.9:
            return test["winner"]
    
    # Otherwise serve randomly
    variants = list(test["variants"].keys())
    weights = [1 / len(variants)] * len(variants)
    
    # Weight by performance if we have data
    total_impressions = sum(test["impressions"].values())
    if total_impressions > 100:
        weights = []
        for v in variants:
            conv_rate = test["conversions"].get(v, 0) / max(test["impressions"].get(v, 1), 1)
            weights.append(conv_rate + 0.1)  # Add baseline
    
    chosen = random.choices(variants, weights=weights)[0]
    test["impressions"][chosen] += 1
    _save(data)
    
    return chosen

def track_conversion(test_name, variant):
    """Track when a variant converts."""
    data = _load()
    if test_name in data["tests"]:
        data["tests"][test_name]["conversions"][variant] += 1
        
        # Check if we have a clear winner
        test = data["tests"][test_name]
        if sum(test["impressions"].values()) > 1000:
            best_variant = max(test["conversions"], key=test["conversions"].get)
            if test["conversions"][best_variant] > 0:
                data["tests"][test_name]["winner"] = best_variant
        
        _save(data)

# Create initial tests
create_test("landing_page", {
    "version_a": "docs/index.html",
    "version_b": "docs/index_v2.html",
    "version_c": "docs/index_v3.html"
})

create_test("pricing_display", {
    "show_all": "Show all 3 services",
    "show_top": "Show only top service",
    "show_comparison": "Show comparison table"
})

print("✓ A/B testing framework initialized")
