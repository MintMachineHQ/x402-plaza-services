#!/usr/bin/env python3
"""Interface to PlazaEscrow smart contract on Base."""
import json, os
from web3 import Web3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from eth_account import Account

# Load config
config = json.load(open(os.path.join(BASE_DIR, "contract_config.json")))
CONTRACT_ADDR = config["escrow_contract"]
ORACLE_ADDR = config["oracle_address"]
USDC_ADDR = config["usdc"]
RPC_URL = "https://mainnet.base.org"

# Connect to Base
w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), "Cannot connect to Base RPC"

# Contract ABI (minimal for our functions)
ABI = json.loads('''[
  {"inputs":[],"name":"nextId","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"name":"worker","type":"address"},{"name":"amount","type":"uint256"}],"name":"create","outputs":[{"name":"id","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"name":"id","type":"uint256"},{"name":"hash","type":"bytes32"}],"name":"submit","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"name":"id","type":"uint256"}],"name":"oracleRelease","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"name":"id","type":"uint256"}],"name":"oracleRefund","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"name":"id","type":"uint256"}],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"name":"id","type":"uint256"}],"name":"jobs","outputs":[{"name":"client","type":"address"},{"name":"worker","type":"address"},{"name":"amount","type":"uint256"},{"name":"status","type":"uint8"},{"name":"submittedAt","type":"uint64"},{"name":"deliverableHash","type":"bytes32"}],"stateMutability":"view","type":"function"}
]''')

contract = w3.eth.contract(address=CONTRACT_ADDR, abi=ABI)

def get_next_job_id():
    return contract.functions.nextId().call()

def get_job(job_id):
    data = contract.functions.jobs(job_id).call()
    return {
        "client": data[0],
        "worker": data[1],
        "amount": data[2] / 1e6,  # USDC 6 decimals
        "status": data[3],
        "submittedAt": data[4],
        "deliverableHash": data[5].hex()
    }

def create_job(client_key, worker_addr, amount_usd):
    """Create job on-chain. Returns job ID."""
    account = Account.from_key(client_key)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.create(worker_addr, int(amount_usd * 1e6)).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 200000, 'maxFeePerGas': w3.to_wei(0.1, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei')
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    job_id = int.from_bytes(receipt.logs[0].topics[1], 'big')
    return job_id, tx_hash.hex()

def submit_work(worker_key, job_id, deliverable_hash):
    """Submit work on-chain."""
    account = Account.from_key(worker_key)
    nonce = w3.eth.get_transaction_count(account.address)
    hash_bytes = bytes.fromhex(deliverable_hash.replace('0x', ''))
    tx = contract.functions.submit(job_id, hash_bytes).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 150000, 'maxFeePerGas': w3.to_wei(0.1, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei')
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return tx_hash.hex()

def oracle_release(job_id):
    """Oracle releases funds to worker."""
    oracle_key = open(os.path.join(BASE_DIR, "oracle.key")).read().strip()
    account = Account.from_key(oracle_key)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.oracleRelease(job_id).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 100000, 'maxFeePerGas': w3.to_wei(0.1, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei')
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return tx_hash.hex()

def oracle_refund(job_id):
    """Oracle refunds to client."""
    oracle_key = open(os.path.join(BASE_DIR, "oracle.key")).read().strip()
    account = Account.from_key(oracle_key)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.oracleRefund(job_id).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 100000, 'maxFeePerGas': w3.to_wei(0.1, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(0.01, 'gwei')
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return tx_hash.hex()
