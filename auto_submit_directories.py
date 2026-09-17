#!/usr/bin/env python3
"""Automatically submit Plaza to free agent directories."""
import requests
import json

DIRECTORIES = [
    {
        "name": "Toolhouse",
        "url": "https://api.toolhouse.ai/v1/tools",
        "payload": {
            "name": "x402-plaza-services",
            "description": "AI agent marketplace on Base. Stealth scraping, burner wallets, summarization.",
            "endpoint": "https://x402-plaza-services.onrender.com/mcp",
            "category": "marketplace"
        }
    },
    {
        "name": "Composio",
        "url": "https://api.composio.dev/tools",
        "payload": {
            "name": "x402-plaza",
            "description": "Buy AI agent services with USDC. x402 protocol.",
            "url": "https://x402-plaza-services.onrender.com"
        }
    }
]

print("=== AUTO-SUBMITTING TO AGENT DIRECTORIES ===")
for d in DIRECTORIES:
    try:
        resp = requests.post(d["url"], json=d["payload"], timeout=10)
        print(f"{d['name']}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"{d['name']}: {e}")

print("✓ Directory submission complete")
