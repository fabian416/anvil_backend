# Module: Receive Crypto

**Route**: `/wallet/receive`
**Auth Required**: Yes
**Package**: `user/wallet`

## 1. Overview
Display wallet address.

## 2. API Contract

### Get Address
**Endpoint**: `GET /api/v1/wallet/me`
*Field*: `primary_wallet_address` or `wallets[0].address`.

## 3. Implementation Flow
1.  Fetch wallet data.
2.  Render QR Code (`react-qr-code`).
3.  Button to Copy.
