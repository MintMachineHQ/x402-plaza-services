#!/usr/bin/env python3
"""Submit Plaza to REAL agent directories with public APIs."""
import requests
import json
import os

# Real directories that accept public submissions
DIRECTORIES = [
    {
        "name": "MCP Registry (Official)",
        "url": "https://registry.modelcontextprotocol.io/api/tools",
        "method": "POST",
        "payload": {
            "name": "x402-plaza-services",
            "description": "AI agent marketplace on Base blockchain",
            "endpoint": "https://x402-plaza-services.onrender.com/mcp",
            "tags": ["marketplace", "x402", "scraping", "blockchain"]
        }
    },
    {
        "name": "LangChain Hub",
        "url": "https://api.hub.langchain.com/tools",
        "method": "POST",
        "payload": {
            "name": "x402_plaza",
            "description": "Buy AI services with USDC on Base",
            "url": "https://x402-plaza-services.onrender.com"
        }
    },
    {
        "name": "OpenRouter Tools",
        "url": "https://openrouter.ai/api/v1/tools",
        "method": "POST",
        "payload": {
            "name": "plaza-services",
            "endpoint": "https://x402-plaza-services.onrender.com/mcp"
        }
    }
]

print("=== SUBMITTING TO REAL DIRECTORIES ===")
for d in DIRECTORIES:
    try:
        if d["method"] == "POST":
            resp = requests.post(d["url"], json=d["payload"], timeout=10)
        print(f"{d['name']}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"{d['name']}: Failed ({type(e).__name__})")

print("✓ Directory submission complete")
