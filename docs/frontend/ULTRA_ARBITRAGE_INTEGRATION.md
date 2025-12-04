# ULTRA Arbitrage Bot - Frontend Integration Guide

Complete guide for integrating ULTRA Arbitrage Bot features into your frontend application.

---

## Overview

ULTRA Arbitrage Bot provides 4 main modules:
1. **Flash Loans** - Multi-protocol flash loan management
2. **Arbitrage Discovery** - 2-hop, 3-hop, triangle arbitrage detection
3. **MEV Protection** - Flashbots-integrated execution
4. **Auto-Executor** - Automated arbitrage trading with risk management

---

## 1. Flash Loans

### Get Available Protocols

```typescript
const getFlashLoanProtocols = async () => {
  const response = await apiClient.get('/api/v1/ultra/flash-loans/protocols');
  return response; // ProtocolInfo[]
};

interface ProtocolInfo {
  protocol: string;  // 'aave_v3', 'balancer', 'uniswap_v3'
  name: string;
  fee_percentage: number;
  max_loan_usd: string;
  supported_tokens: string[];
  requires_collateral: boolean;
}
```

### Get Best Protocol

```typescript
const getBestProtocol = async (token: string, amountUsd: number) => {
  const response = await apiClient.get('/api/v1/ultra/flash-loans/best-protocol', {
    token,
    amount_usd: amountUsd,
  });
  
  return response;
};

// Response
interface BestProtocolResponse {
  recommended_protocol: string;
  protocol_name: string;
  fee_percentage: number;
  estimated_fees_usd: string;
  reason: string;
}
```

### Simulate Flash Loan

```typescript
const simulateFlashLoan = async (
  protocol: string,
  tokenAddress: string,
  amount: string,
  receiverAddress: string
) => {
  const response = await apiClient.post('/api/v1/ultra/flash-loans/simulate', {
    protocol,
    token_address: tokenAddress,
    amount,
    receiver_address: receiverAddress,
  });
  
  return response; // FlashLoanResult
};

interface FlashLoanResult {
  status: string;
  tx_hash?: string;
  gas_used?: number;
  gas_price_gwei?: number;
  profit_usd?: string;
  fees_paid: string;
  error_message?: string;
}
```

### UI Component (Flash Loan Simulator)

```tsx
// components/FlashLoanSimulator.tsx
export function FlashLoanSimulator() {
  const [protocols, setProtocols] = useState<ProtocolInfo[]>([]);
  const [selectedProtocol, setSelectedProtocol] = useState('');
  const [amount, setAmount] = useState('');
  const [result, setResult] = useState<FlashLoanResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    getFlashLoanProtocols().then(setProtocols);
  }, []);
  
  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await simulateFlashLoan(
        selectedProtocol,
        '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', // USDC
        amount,
        '0x...' // Your receiver address
      );
      setResult(res);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Flash Loan Simulator</h3>
      
      {/* Protocol Selection */}
      <div className="mb-4">
        <label className="block text-sm text-gray-600 mb-2">Protocol</label>
        <select
          value={selectedProtocol}
          onChange={(e) => setSelectedProtocol(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="">Select Protocol</option>
          {protocols.map((p) => (
            <option key={p.protocol} value={p.protocol}>
              {p.name} - {p.fee_percentage}% fee
            </option>
          ))}
        </select>
      </div>
      
      {/* Amount Input */}
      <div className="mb-4">
        <label className="block text-sm text-gray-600 mb-2">Amount (USD)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="10000"
        />
      </div>
      
      {/* Simulate Button */}
      <button
        onClick={handleSimulate}
        disabled={loading || !selectedProtocol || !amount}
        className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:bg-gray-300"
      >
        {loading ? 'Simulating...' : 'Simulate Flash Loan'}
      </button>
      
      {/* Results */}
      {result && (
        <div className="mt-4 p-4 bg-gray-50 rounded">
          <h4 className="font-semibold mb-2">Simulation Result</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className={result.status === 'success' ? 'text-green-500' : 'text-red-500'}>
                {result.status}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Gas Used:</span>
              <span>{result.gas_used?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Fees Paid:</span>
              <span>${result.fees_paid}</span>
            </div>
            {result.profit_usd && (
              <div className="flex justify-between">
                <span>Estimated Profit:</span>
                <span className="text-green-500 font-semibold">
                  ${result.profit_usd}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 2. Arbitrage Discovery

### Discover Opportunities

```typescript
const discoverArbitrage = async (
  capital: number,
  type?: '2hop' | '3hop' | 'triangle',
  minProfit?: number
) => {
  const response = await apiClient.get('/api/v1/ultra/arbitrage/discover', {
    capital,
    type,
    min_profit: minProfit,
  });
  
  return response; // ArbitrageOpportunity[]
};

interface ArbitrageOpportunity {
  opportunity_id: string;
  type: string;
  path: TradingPair[];
  expected_profit_usd: string;
  profit_percentage: number;
  required_capital: string;
  estimated_gas_cost: string;
  confidence_score: number;
}

interface TradingPair {
  dex: string;
  token_in: string;
  token_out: string;
  amount_in: string;
  amount_out: string;
  price: string;
}
```

### List Discovered Opportunities

```typescript
const listOpportunities = async (limit: number = 10, sortBy: string = 'profit') => {
  const response = await apiClient.get('/api/v1/ultra/arbitrage/opportunities', {
    limit,
    sort_by: sortBy,
  });
  
  return response;
};
```

### Simulate Opportunity

```typescript
const simulateOpportunity = async (opportunityId: string) => {
  const response = await apiClient.post('/api/v1/ultra/arbitrage/simulate', {
    opportunity_id: opportunityId,
  });
  
  return response;
};

interface SimulationResult {
  opportunity_id: string;
  type: string;
  expected_profit: string;
  simulated_profit: string;
  slippage_impact: string;
  success_probability: number;
  recommendation: 'Execute' | 'Skip';
}
```

### UI Component (Arbitrage Scanner)

```tsx
// components/ArbitrageScanner.tsx
export function ArbitrageScanner() {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [capital, setCapital] = useState(10000);
  const [type, setType] = useState<'2hop' | '3hop' | 'triangle' | undefined>();
  const [loading, setLoading] = useState(false);
  
  const scan = async () => {
    setLoading(true);
    try {
      const results = await discoverArbitrage(capital, type);
      setOpportunities(results);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Arbitrage Scanner</h3>
      
      {/* Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm text-gray-600 mb-2">Capital (USD)</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="w-full border rounded px-3 py-2"
          />
        </div>
        
        <div>
          <label className="block text-sm text-gray-600 mb-2">Type</label>
          <select
            value={type || ''}
            onChange={(e) => setType(e.target.value as any || undefined)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="">All Types</option>
            <option value="2hop">2-Hop</option>
            <option value="3hop">3-Hop</option>
            <option value="triangle">Triangle</option>
          </select>
        </div>
      </div>
      
      <button
        onClick={scan}
        disabled={loading}
        className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:bg-gray-300 mb-4"
      >
        {loading ? 'Scanning...' : 'Scan for Opportunities'}
      </button>
      
      {/* Opportunities List */}
      <div className="space-y-4">
        {opportunities.map((opp) => (
          <div key={opp.opportunity_id} className="border rounded p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold">{opp.type.toUpperCase()}</span>
              <span className="text-green-500 font-bold">
                +${opp.expected_profit_usd}
              </span>
            </div>
            
            {/* Path */}
            <div className="text-sm text-gray-600 mb-2">
              {opp.path.map((p, i) => (
                <span key={i}>
                  {p.token_in} → {p.token_out}
                  {i < opp.path.length - 1 && ' → '}
                </span>
              ))}
            </div>
            
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Profit: </span>
                <span className="font-semibold">{opp.profit_percentage.toFixed(2)}%</span>
              </div>
              <div>
                <span className="text-gray-600">Gas: </span>
                <span>${opp.estimated_gas_cost}</span>
              </div>
              <div>
                <span className="text-gray-600">Confidence: </span>
                <span>{(opp.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </div>
            
            <button
              onClick={() => handleExecute(opp.opportunity_id)}
              className="mt-3 w-full bg-green-500 text-white py-1 rounded hover:bg-green-600 text-sm"
            >
              Execute
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 3. MEV Protection

### Execute with MEV Protection

```typescript
const executeWithMEV = async (opportunityId: string, useMevProtection: boolean = true) => {
  const response = await apiClient.post('/api/v1/ultra/mev/execute', {
    opportunity_id: opportunityId,
    use_mev_protection: useMevProtection,
  });
  
  return response; // ExecutionResult
};

interface ExecutionResult {
  execution_id: string;
  opportunity_id: string;
  status: string;
  expected_profit: string;
  realized_profit?: string;
  gas_cost: string;
}
```

### Check Bundle Status

```typescript
const checkBundleStatus = async (bundleId: string) => {
  const response = await apiClient.get(`/api/v1/ultra/mev/bundles/${bundleId}`);
  return response;
};
```

---

## 4. Auto-Executor

### Start Auto-Executor

```typescript
const startAutoExecutor = async () => {
  const response = await apiClient.post('/api/v1/ultra/auto-executor/start');
  return response;
};
```

### Get Status

```typescript
const getAutoExecutorStatus = async () => {
  const response = await apiClient.get('/api/v1/ultra/auto-executor/status');
  return response;
};

interface AutoExecutorStatus {
  status: 'stopped' | 'running' | 'paused';
  total_executions: number;
  last_scan?: string;
  metrics: {
    total_trades: number;
    successful_trades: number;
    total_profit: string;
    win_rate: number;
  };
  risk_score: number;
  config: {
    scan_interval: number;
    min_profit: string;
    mev_protection: boolean;
  };
}
```

### Update Configuration

```typescript
const updateConfig = async (config: {
  min_profit_usd?: number;
  scan_interval_seconds?: number;
  max_gas_price_gwei?: number;
}) => {
  const response = await apiClient.put('/api/v1/ultra/auto-executor/config', config);
  return response;
};
```

### UI Component (Auto-Executor Dashboard)

```tsx
// components/AutoExecutorDashboard.tsx
export function AutoExecutorDashboard() {
  const [status, setStatus] = useState<AutoExecutorStatus | null>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchStatus = async () => {
      const data = await getAutoExecutorStatus();
      setStatus(data);
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5s
    
    return () => clearInterval(interval);
  }, []);
  
  const toggleExecutor = async () => {
    setLoading(true);
    try {
      if (status?.status === 'running') {
        await apiClient.post('/api/v1/ultra/auto-executor/stop');
      } else {
        await startAutoExecutor();
      }
      const newStatus = await getAutoExecutorStatus();
      setStatus(newStatus);
    } finally {
      setLoading(false);
    }
  };
  
  if (!status) return <LoadingSpinner />;
  
  const isRunning = status.status === 'running';
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Auto-Executor</h3>
        <div className="flex items-center space-x-2">
          <span className={`h-3 w-3 rounded-full ${
            isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
          }`} />
          <span className="text-sm text-gray-600 capitalize">{status.status}</span>
        </div>
      </div>
      
      {/* Control Button */}
      <button
        onClick={toggleExecutor}
        disabled={loading}
        className={`w-full py-2 rounded font-semibold mb-6 ${
          isRunning
            ? 'bg-red-500 hover:bg-red-600 text-white'
            : 'bg-green-500 hover:bg-green-600 text-white'
        }`}
      >
        {loading ? 'Loading...' : isRunning ? 'Stop Executor' : 'Start Executor'}
      </button>
      
      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">Total Trades</p>
          <p className="text-2xl font-bold">{status.metrics.total_trades}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">Win Rate</p>
          <p className="text-2xl font-bold">{status.metrics.win_rate.toFixed(1)}%</p>
        </div>
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">Total Profit</p>
          <p className="text-2xl font-bold text-green-500">
            ${status.metrics.total_profit}
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">Risk Score</p>
          <p className="text-2xl font-bold">{status.risk_score}/100</p>
        </div>
      </div>
      
      {/* Configuration */}
      <div className="border-t pt-4">
        <h4 className="font-semibold mb-3">Configuration</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Scan Interval:</span>
            <span>{status.config.scan_interval}s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Min Profit:</span>
            <span>${status.config.min_profit}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">MEV Protection:</span>
            <span>{status.config.mev_protection ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Safety Considerations

### Risk Management
- Always set appropriate stop-loss limits
- Start with small capital amounts
- Monitor auto-executor closely
- Use MEV protection for all executions

### Best Practices
1. **Simulation First:** Always simulate before executing
2. **Gas Monitoring:** Watch gas prices, pause if too high
3. **Profit Thresholds:** Set realistic minimum profit targets
4. **Risk Limits:** Configure max capital per trade
5. **Real-time Monitoring:** Watch execution metrics closely

---

## Next Steps

- [Complete API Reference](../API_REFERENCE.md)
- [WebSocket Integration](./WEBSOCKET_INTEGRATION.md)
- [Hunter AI Integration](./HUNTER_AI_INTEGRATION.md)
