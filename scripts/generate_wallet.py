#!/usr/bin/env python3
"""Generate a new Ethereum wallet for flash loan execution.

Usage:
    python scripts/generate_wallet.py

This generates a new wallet with:
- Private key (keep secret!)
- Public address

Add the output to config/local/.secrets.toml under [wallet]
"""

import secrets


def generate_wallet():
    """Generate a new Ethereum wallet."""
    # Generate 32 random bytes for private key
    private_key = secrets.token_hex(32)
    
    # Derive public address using keccak256
    # For proper derivation, we'd use eth-account, but this shows the format
    print("=" * 60)
    print("NEW ETHEREUM WALLET")
    print("=" * 60)
    print()
    print("⚠️  SAVE THESE SECURELY - NEVER SHARE THE PRIVATE KEY!")
    print()
    print(f"Private Key: {private_key}")
    print()
    print("To get the public address, use one of:")
    print()
    print("Option 1: Python (with eth-account)")
    print("  pip install eth-account")
    print("  python -c \"")
    print(f"    from eth_account import Account")
    print(f"    acct = Account.from_key('0x{private_key}')")
    print(f"    print(f'Address: {{acct.address}}')")
    print("  \"")
    print()
    print("Option 2: Use the key in MetaMask or other wallet")
    print()
    print("=" * 60)
    print()
    print("Add to config/local/.secrets.toml:")
    print()
    print("[wallet]")
    print(f'PRIVATE_KEY = "{private_key}"')
    print('ADDRESS = ""  # Fill in after getting address')
    print()
    print("=" * 60)
    print()
    print("IMPORTANT SECURITY NOTES:")
    print("1. Use a DEDICATED wallet for flash loans")
    print("2. Never use your main wallet")
    print("3. Start with small amounts for testing")
    print("4. Never commit private keys to git")
    print("=" * 60)


if __name__ == "__main__":
    generate_wallet()
