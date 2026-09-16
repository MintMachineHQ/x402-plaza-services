#!/usr/bin/env python3
"""Dynamic Confirmation Policy - wait for block confirmations on expensive tools."""

# Confirmation requirements based on price
CONFIRMATION_TIERS = {
    "low": {"min_price": 0, "max_price": 10, "confirmations": 1, "wait_seconds": 10},
    "medium": {"min_price": 10, "max_price": 100, "confirmations": 3, "wait_seconds": 30},
    "high": {"min_price": 100, "max_price": 500, "confirmations": 6, "wait_seconds": 60},
    "critical": {"min_price": 500, "max_price": float('inf'), "confirmations": 12, "wait_seconds": 120}
}

def get_confirmation_requirement(price_usd):
    """Get required confirmations based on price."""
    for tier, config in CONFIRMATION_TIERS.items():
        if config["min_price"] <= price_usd < config["max_price"]:
            return {
                "tier": tier,
                "required_confirmations": config["confirmations"],
                "estimated_wait_seconds": config["wait_seconds"],
                "price_usd": price_usd
            }
    return CONFIRMATION_TIERS["critical"]

def check_confirmations(tx_hash, chain, required):
    """
    Check if transaction has enough confirmations.
    NOTE: This is a stub. In production, query block explorer API.
    Returns: (has_enough, current_confirmations, message)
    """
    # STUB: In production, call:
    # - Base: https://api.basescan.org/api?module=proxy&action=eth_getTransactionReceipt
    # - Ethereum: https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt
    # - Solana: https://api.mainnet-beta.solana.com (getSignatureStatuses)
    
    # For now, simulate that all transactions have enough confirmations
    # In production, replace this with real API calls
    current_confirmations = required  # STUB
    has_enough = current_confirmations >= required
    
    message = f"Transaction has {current_confirmations}/{required} confirmations"
    if not has_enough:
        message += f". Waiting for {required - current_confirmations} more."
    
    return has_enough, current_confirmations, message

def get_policy():
    """Get full confirmation policy."""
    return {
        "tiers": CONFIRMATION_TIERS,
        "note": "Expensive tools require more block confirmations to prevent double-spend attacks"
    }
