# Module: Stake

**Route**: `/defi/stake`
**Auth Required**: Yes
**Package**: `user/defi`

## 1. Overview
Liquid Staking (Lido/RocketPool) integration.

## 2. API Contract
*Currently using Generic Market/Swap interfaces.*
*Future*: Specific `lido_router`.

## 3. Implementation Flow
1.  Uses **Swap** UI pattern.
2.  `ETH` -> `stETH` (Curve Swap or Lido Direct).
