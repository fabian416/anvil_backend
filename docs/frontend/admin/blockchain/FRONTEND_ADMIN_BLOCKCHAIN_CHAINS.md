# FRONTEND_ADMIN_BLOCKCHAIN_CHAINS

## Admin Chain Status Module

**User Type:** Admin  
**Module:** Chain Status  
**Route:** `/admin/blockchain/chains`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Chain Status** - Blockchain Network Monitoring

### Description
Real-time monitoring of supported blockchain networks, RPC endpoint health, block confirmations, and network congestion status.

### Key Capabilities
- Multi-chain status overview
- RPC endpoint monitoring
- Block height tracking
- Gas price monitoring
- Network congestion alerts
- Failover management

---

## 🖼️ Views & Wireframes

### View 1: Chain Status Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⛓️ Chain Status                                             [⚙️ RPC Config]        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Network Overview ──────────────────────────────────────────────────────────────┐│
│  │  🟢 4/4 Chains Operational    ⚡ Avg Latency: 145ms    📊 24h Uptime: 99.97%   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ETHEREUM MAINNET                                                    🟢 Online  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  Block Height: 18,945,672       │ Last Block: 12 sec ago                 │  ││
│  │  │  Gas Price: 35 gwei ($2.45)     │ Congestion: 🟢 Normal                  │  ││
│  │  │                                                                           │  ││
│  │  │  RPC Endpoints:                                                          │  ││
│  │  │  ├─ 🟢 Alchemy (Primary)      45ms   [████████████████████] 99.99%       │  ││
│  │  │  ├─ 🟢 Infura (Failover)      62ms   [███████████████████░] 99.95%       │  ││
│  │  │  └─ 🟢 QuickNode (Backup)     78ms   [██████████████████░░] 99.90%       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  ARBITRUM ONE                                                        🟢 Online  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  Block Height: 156,789,234      │ Last Block: 0.3 sec ago                │  ││
│  │  │  Gas Price: 0.15 gwei ($0.02)   │ Congestion: 🟢 Low                     │  ││
│  │  │                                                                           │  ││
│  │  │  RPC Endpoints:                                                          │  ││
│  │  │  ├─ 🟢 Alchemy (Primary)      28ms   [████████████████████] 99.99%       │  ││
│  │  │  └─ 🟢 Official RPC (Backup)  42ms   [███████████████████░] 99.92%       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  POLYGON                                                             🟢 Online  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  Block Height: 51,234,567       │ Last Block: 2 sec ago                  │  ││
│  │  │  Gas Price: 85 gwei ($0.01)     │ Congestion: 🟡 Moderate                │  ││
│  │  │                                                                           │  ││
│  │  │  RPC Endpoints:                                                          │  ││
│  │  │  ├─ 🟢 Alchemy (Primary)      35ms   [████████████████████] 99.98%       │  ││
│  │  │  └─ 🟡 Public RPC (Backup)   250ms   [████████████████░░░░] 98.50%       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  BASE                                                                🟢 Online  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  Block Height: 8,456,789        │ Last Block: 2 sec ago                  │  ││
│  │  │  Gas Price: 0.01 gwei ($0.001)  │ Congestion: 🟢 Low                     │  ││
│  │  │                                                                           │  ││
│  │  │  RPC Endpoints:                                                          │  ││
│  │  │  ├─ 🟢 Alchemy (Primary)      32ms   [████████████████████] 99.99%       │  ││
│  │  │  └─ 🟢 Official RPC (Backup)  48ms   [███████████████████░] 99.95%       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/blockchain/chains
interface GetChainsStatusResponse {
  success: true;
  data: {
    summary: {
      operational: number;
      total: number;
      avg_latency_ms: number;
      uptime_24h: number;
    };
    chains: ChainStatus[];
  };
}

interface ChainStatus {
  chain_id: number;
  name: string;
  status: 'online' | 'degraded' | 'offline';
  block_height: number;
  last_block_time: string;
  gas_price_gwei: number;
  gas_price_usd: number;
  congestion: 'low' | 'normal' | 'moderate' | 'high' | 'critical';
  endpoints: RPCEndpoint[];
}

interface RPCEndpoint {
  name: string;
  url: string;
  role: 'primary' | 'failover' | 'backup';
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  uptime_percent: number;
  last_check: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Chain Status*
