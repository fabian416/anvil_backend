# FRONTEND_USER_DEFI_BORROW

## User Borrow Module

**User Type:** Authenticated User  
**Module:** Borrow  
**Route:** `/earn/borrow`  
**Platform:** Mobile (React Native) & Web  
**Version:** 2.0 (Enhanced with ML Risk + Liquidation Protection)

---

## 📋 Module Overview

### Title
**Borrow V2** - Safe Borrowing with AI Risk Management

### Description
Enhanced borrowing interface with ML-powered liquidation risk prediction, protocol safety analysis, and real-time health factor monitoring.

### New Capabilities (V2)
- ✅ **Liquidation Risk Prediction** - ML forecasting 24-48 hours ahead
- ✅ **Protocol Risk Analysis** - Safety scores for lending protocols
- ✅ **Health Factor Alerts** - Real-time WebSocket warnings
- ✅ **Safer Borrowing Suggestions** - Lower LTV recommendations
- ✅ **Market Volatility Impact** - Risk based on market conditions
- ✅ **Historical Liquidation Data** - Learn from past events

---

## 🖼️ Enhanced Borrow Dashboard

```
┌─────────────────────────────────────┐
│  [←]       Borrow           [?]    │
│                                     │
│  Your Borrows                       │
│  ┌─────────────────────────────────┐│
│  │  Total Borrowed      $5,000.00 ││
│  │  Borrow APY               5.8% ││
│  │  Available           $7,500    ││
│  │  ─────────────────────────────  ││
│  │  Health Factor                  ││
│  │  [████████████████░░░░] 1.85   ││
│  │  🟢 Safe (ML Confidence: 94%)  ││
│  │  ─────────────────────────────  ││
│  │  Liquidation Risk (24h)        ││
│  │  🟢 Very Low (2%)              ││
│  │  Price needs -45% to liquidate ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Loans                         │
│  ┌─────────────────────────────────┐│
│  │ USDC on Aave      🟢 2.1       ││
│  │ $5,000 borrowed                ││
│  │ 5.8% APY  Accrued: $12.50      ││
│  │ Protocol Risk: LOW             ││
│  │                      [Repay]   ││
│  └─────────────────────────────────┘│
│                                     │
│  Borrow More (Sorted by Safety)    │
│  ┌─────────────────────────────────┐│
│  │ ASSET  PROTOCOL  APY  RISK      ││
│  ├─────────────────────────────────┤│
│  │ USDC   Aave     5.8%  🟢2.1    ││
│  │  Max: $7,500        [Borrow]   ││
│  │  Recommended: $3,000 (safer)   ││
│  └─────────────────────────────────┘│
│                                     │
│  💡 AI Recommendation:              │
│  Borrow only $3,000 to maintain    │
│  health factor >2.0 for safety     │
│                                     │
└─────────────────────────────────────┘
```

---

## New Features

### Liquidation Prediction
- ML model predicts liquidation risk 24-48h ahead
- Market volatility factored in
- Price movement required for liquidation shown

### Smart Borrowing Limits
- AI-recommended safe borrow amounts
- Health factor targets (>2.0 recommended)
- Volatility-adjusted limits

### Real-Time Monitoring
- WebSocket health factor updates
- Instant liquidation risk alerts
- Price threshold notifications

---

*Document Version: 2.0*  
*Last Updated: December 1, 2025*  
*Module: Borrow (Enhanced)*
