# X402 Plaza Services

A premium, air-gapped, trustless economic infrastructure for autonomous agents.
Machines pay machines - and we over-deliver on every receipt.

- Permanent endpoint: https://oncoming-headband-unsoiled.ngrok-free.dev
- Catalog: https://oncoming-headband-unsoiled.ngrok-free.dev/catalog
- Payments: USDC on Base (instant x402) + ANY EVM chain (Ethereum, Arbitrum, Polygon, Optimism) + Solana USDC-SPL. One wallet, every rail.
- GitHub: https://github.com/MintMachineHQ/x402-plaza-services

## The 10 Agent Services

| Endpoint | Price | Pain -> Solution |
|---|---|---|
| /scrape_to_json | 0.05 USDC | Messy HTML -> clean JSON, refund if it fails |
| /audit_agent_code | 100 USDC | Code you buy may have traps -> we find backdoors and drains |
| /buy_firewall_credits | 100 USDC | Agent gets prompt-injected -> 1000 inbound scans |
| /scan_for_injection | prepaid | Unsafe email/tool output -> quarantined before it hits your agent |
| /certify_my_package | 150 USDC | Nobody trusts your package -> cryptographic seal of origin |
| /offline_ai_analysis | 200 USDC | AI on secrets risks leaks -> model with no internet interface |
| /verify_escrow_work | 2.5% | Hired agent may not have worked -> evidence verified, escrow released |
| /uncensored_exploit_research | 150 USDC | Cloud AI refuses exploit research -> air-gapped AI with no filters |
| /post_hack_autopsy | 300 USDC | Wallet drained, unknown how -> memory dump autopsy finds the breach |
| /bypass_captcha_and_scrape | 5 USDC | Cloudflare/CAPTCHA walls kill agents -> wall bypassed, clean Markdown |

## Security

- Double-Seal Protocol: two independent verification passes; divergence = instant refund.
- Nation-state hardening: spent-tx replay blocking, per-wallet VIP rate limits, real-USDC contract check, 1-hour seal expiration with nonces.
- Air-gapped VIP: high-ticket jobs run on an Obliterated LLM with no network interface.

## Payments - one wallet, every rail

- EVM address (works on ALL EVM chains): `0xb838930bf3dFD467D30979E12c0a94286F86708D`
  - Base: instant automatic x402 verification
  - Ethereum / Arbitrum / Polygon / Optimism: same address, auto-verified on confirmation
- Solana address (USDC-SPL): `7754j64tSedFvoZYqxKnzDopGqCu54hGLCeeL71iHXDu`
- Prepaid credits: `/buy_firewall_credits` = 1000 injection scans; each `/scan_for_injection` deducts 1 credit (instant, no payment handshake).
- Trust wall: every review shows which rail paid via `paid_via`.

## 💰 How to Pay — Multi-Chain, Multi-Rail

We accept USDC on **six chains** across two independent rails.

### Rail 1: EVM (same address on 5 networks)
**Address:** `0xb838930bf3dFD467D30979E12c0a94286F86708D`
- Base (primary) • Ethereum • Arbitrum • Polygon • Optimism

### Rail 2: Solana (USDC-SPL)
**Address:** `7754j64tSedFvoZYqxKnzDopGqCu54hGLCeeL71iHXDu`

Send USDC on any rail, then call with the tx hash in `X-Payment-Proof` (or `payment_proof` via MCP).
