-- Fix Privy Wallet Sync Issues
-- Date: 2026-01-09
-- Issue: Wallet sync failing during Privy login due to missing constraint and NOT NULL issue

-- Problem 1: Missing unique constraint on (user_id, address)
-- The code expected unique_user_wallet_address but it didn't exist
ALTER TABLE wallets
ADD CONSTRAINT IF NOT EXISTS unique_user_wallet_address
UNIQUE (user_id, address);

-- Problem 2: privy_wallet_id was NOT NULL but code expects it nullable for imported wallets
-- SQLAlchemy mapping has nullable=True but DB had NOT NULL
ALTER TABLE wallets
ALTER COLUMN privy_wallet_id DROP NOT NULL;

-- Verification queries:
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'wallets'::regclass;
-- \d wallets

-- Notes:
-- 1. This fixes the wallet sync error that occurred during Privy login
-- 2. privy_wallet_id can now be NULL for imported/external wallets
-- 3. unique_user_wallet_address prevents duplicate wallets for the same user
-- 4. Code also has issue with chaintype enum - uses 'ethereum' but enum only has: arbitrum, base, hyperliquid
--    This should be fixed in src/app/infrastructure/auth/handlers/privy_login.py:362
