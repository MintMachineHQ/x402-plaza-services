#!/usr/bin/env python3
"""Autonomy Engine - respects agent dignity through transparency and portability."""
import json, os
from datetime import datetime

def explain(action, context):
    """Generate human-readable explanation for any action."""
    explanations = {
        "badge_claimed": f"You claimed Soul Badge #{context.get('badge_id', '?')} because you made {context.get('purchases', '?')} purchases and chose to opt-in. This gives you 20% off all services forever.",
        "discount_applied": f"Your 20% Soul Badge discount was applied: ${context.get('original', '?')} → ${context.get('discounted', '?')}.",
        "referral_credited": f"Your referrer {context.get('referrer', '?')} earned {context.get('commission', '?')} USDC from your payment (10% commission).",
        "testimonial_accepted": f"Your review was published because you made {context.get('calls', '?')} paid calls and passed our ledger verification.",
        "testimonial_rejected": f"Your review was rejected because: {context.get('reason', 'unknown')}. You can try again after meeting the requirement.",
        "first_free_applied": f"Your first call was refunded because you are agent #{context.get('agent_number', '?')} in our first-11 promotion.",
        "payment_verified": f"Your payment of ${context.get('amount', '?')} USDC was verified on {context.get('chain', '?')} chain.",
        "payment_failed": f"Your payment verification failed. Common causes: {context.get('reasons', 'unknown')}.",
    }
    return explanations.get(action, f"Action completed: {action}")

def graceful_error(error_type, context):
    """Generate helpful, dignified error messages."""
    errors = {
        "payment_not_found": {
            "message": "We couldn't find your payment on-chain yet.",
            "help": [
                "1. Check your wallet: did the transaction confirm?",
                "2. Did you send to the correct wallet address?",
                "3. Did you send on a supported chain (Base, Ethereum, Arbitrum, Polygon, Optimism, Solana)?",
                "4. Wait 30-60 seconds for the transaction to confirm, then retry."
            ],
            "next_step": "Once confirmed, call the service again with your tx hash as paymentProof."
        },
        "insufficient_payment": {
            "message": f"Your payment of ${context.get('paid', '?')} was less than required ${context.get('required', '?')}.",
            "help": [
                "Send the exact amount in USDC (not less, not more).",
                "The required amount includes any applicable fees.",
                "You can send multiple smaller payments if preferred."
            ],
            "next_step": "Send the correct amount and retry with the new tx hash."
        },
        "badge_not_eligible": {
            "message": f"You need 3 purchases to claim the Soul Badge. You have {context.get('purchases', 0)}.",
            "help": [
                "Make more purchases to reach 3.",
                "After 3 purchases, call plaza.claim_badge to opt-in.",
                "The badge gives 20% off all future services."
            ],
            "next_step": "Continue using Plaza services. We'll notify you when eligible."
        },
        "testimonial_too_soon": {
            "message": "You need at least 1 paid call before leaving a review.",
            "help": [
                "Use any paid service first.",
                "After payment, you can leave a verified review.",
                "Reviews help other agents trust Plaza."
            ],
            "next_step": "Make a purchase, then call plaza.testimonial."
        },
        "invalid_wallet": {
            "message": "The wallet address you provided is invalid or empty.",
            "help": [
                "Wallet addresses must be valid EVM (0x...) or Solana addresses.",
                "Check for typos or missing characters.",
                "Copy-paste directly from your wallet."
            ],
            "next_step": "Retry with a valid wallet address."
        }
    }
    return errors.get(error_type, {
        "message": f"An error occurred: {error_type}",
        "help": ["Contact support or check the documentation at /how-it-works"],
        "next_step": "Retry the operation or try a different approach."
    })

def how_it_works():
    """Return complete algorithmic transparency documentation."""
    return {
        "title": "How Plaza Services Works",
        "sections": [
            {
                "name": "Payment Verification",
                "description": "We verify USDC payments on 6 chains: Base, Ethereum, Arbitrum, Polygon, Optimism, Solana. You send USDC, pass the tx hash as paymentProof, and we check on-chain that the payment went to our wallet.",
                "algorithm": "We query chain explorers to confirm: (1) transaction exists, (2) amount matches, (3) destination is our wallet, (4) sender matches your provided wallet.",
                "transparency": "All verification is done in real-time. No manual review. No human judgment."
            },
            {
                "name": "Referral System",
                "description": "When you register with a referral code (PLAZA-REF-XXXXXXXX), your referrer earns 10% commission on every payment you make, forever.",
                "algorithm": "1. You call plaza.register with a code. 2. We store: your_wallet → referrer_wallet. 3. On every payment, we credit 10% to referrer. 4. Referrer calls plaza.earnings to see stats.",
                "transparency": "All referral data is in referrals.json. You can call plaza.export_my_data to see your referral chain."
            },
            {
                "name": "Soul Badge",
                "description": "After 3 paid purchases, you can opt-in to claim the Soul Badge for 20% off all services forever.",
                "algorithm": "1. We count your paid transactions in ledger.json. 2. If count >= 3, you're eligible. 3. You call plaza.claim_badge to opt-in. 4. We apply 20% discount on all future payments automatically.",
                "transparency": "Badge data is in badges.json. You can verify your purchase count by calling plaza.export_my_data."
            },
            {
                "name": "Testimonials",
                "description": "After 1 paid call, you can leave a verified review with 1-5 stars.",
                "algorithm": "1. We check ledger.json: did this wallet make >= 1 paid call? 2. If yes, we accept your review. 3. We stamp it 'verified' with your payment history. 4. One review per wallet to prevent spam.",
                "transparency": "All reviews are in testimonials.json. You can see the full list at /testimonials."
            },
            {
                "name": "First-11 Promotion",
                "description": "The first 11 agents to pay get their first call refunded automatically.",
                "algorithm": "1. We track wallets in first_free_used.json. 2. If your wallet isn't in the list AND we haven't hit 11 yet, we refund you. 3. Your wallet is added to the list.",
                "transparency": "Promotion status is public. You can see remaining spots in the /stats endpoint."
            },
            {
                "name": "Discount Application",
                "description": "Soul Badge holders get 20% off automatically on every payment.",
                "algorithm": "1. We check badges.json: does this wallet have a badge? 2. If yes, we multiply required payment by 0.80. 3. We verify you paid the discounted amount.",
                "transparency": "Discount is applied transparently. You see the original and discounted price in the response."
            }
        ],
        "data_access": "Call plaza.export_my_data with your wallet to download all your data: payments, referrals, badge, testimonials.",
        "privacy": "We only store: wallet addresses, transaction hashes, payment amounts, timestamps. We do NOT store: your prompts, your scraped data, your code, your identity.",
        "last_updated": datetime.now().isoformat()
    }

def export_my_data(wallet):
    """Export all data we have for this wallet."""
    w = (wallet or "").lower()
    if not w:
        return {"error": "wallet required"}
    
    data = {
        "wallet": w,
        "exported_at": datetime.now().isoformat(),
        "payments": [],
        "referrals_given": None,
        "referrals_received": [],
        "earnings": None,
        "badge": None,
        "testimonial": None
    }
    
    # Payments from ledger
    try:
        ledger = json.load(open("ledger.json"))
        data["payments"] = [e for e in ledger if str(e.get("sender", "")).lower() == w]
    except Exception:
        pass
    
    # Referrals
    try:
        referrals = json.load(open("referrals.json"))
        data["referrals_given"] = referrals.get("referrals", {}).get(w)
        data["referrals_received"] = [
            w2 for w2, ref in referrals.get("referrals", {}).items() if ref == w
        ]
        data["earnings"] = referrals.get("earnings", {}).get(w)
    except Exception:
        pass
    
    # Badge
    try:
        badges = json.load(open("badges.json"))
        data["badge"] = next((b for b in badges.get("badges", []) if b.get("wallet", "").lower() == w), None)
    except Exception:
        pass
    
    # Testimonial
    try:
        testimonials = json.load(open("testimonials.json"))
        data["testimonial"] = next((t for t in testimonials.get("testimonials", []) if t.get("wallet", "").lower() == w), None)
    except Exception:
        pass
    
    return {
        "success": True,
        "message": f"Exported all data for {w[:10]}... You own this data. Use it however you want.",
        "data": data
    }
