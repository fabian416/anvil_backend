# Hunter AI Bot - Frontend Integration Guide

Complete guide for integrating Hunter AI Bot features into your frontend application.

---

## Overview

Hunter AI Bot provides 6 main modules:
1. **Sentiment Analysis** - Multi-source DeFi sentiment
2. **Price Predictions** - LSTM-based price forecasting
3. **Risk Analysis** - ML-powered risk scoring
4. **Trading Signals** - AI-generated trading recommendations
5. **Portfolio Optimization** - Modern Portfolio Theory optimization
6. **Pattern Recognition** - Chart & candlestick pattern detection

---

## 1. Sentiment Analysis

### Get Token Sentiment

```typescript
// Get aggregated sentiment for a token
const getSentiment = async (tokenSymbol: string) => {
  const response = await apiClient.get(
    `/api/v1/hunter/sentiment/${tokenSymbol}`
  );
  
  return response; // SentimentAnalysis
};

// Response Type
interface SentimentAnalysis {
  token_symbol: string;
  overall_score: number;  // -100 to 100
  overall_confidence: number;  // 0 to 1
  sentiment_label: 'very_bearish' | 'bearish' | 'neutral' | 'bullish' | 'very_bullish';
  timestamp: string;
  sources: {
    twitter?: { score: number; confidence: number; };
    reddit?: { score: number; confidence: number; };
    discord?: { score: number; confidence: number; };
    news?: { score: number; confidence: number; };
  };
}
```

### UI Component Example (React)

```tsx
// components/SentimentCard.tsx
import { useEffect, useState } from 'react';

export function SentimentCard({ token }: { token: string }) {
  const [sentiment, setSentiment] = useState<SentimentAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    getSentiment(token).then(setSentiment).finally(() => setLoading(false));
  }, [token]);
  
  if (loading) return <LoadingSpinner />;
  if (!sentiment) return <ErrorMessage />;
  
  const getSentimentColor = (score: number) => {
    if (score >= 60) return 'text-green-500';
    if (score >= 20) return 'text-blue-500';
    if (score >= -20) return 'text-gray-500';
    if (score >= -60) return 'text-orange-500';
    return 'text-red-500';
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">
        Sentiment Analysis - {sentiment.token_symbol}
      </h3>
      
      <div className="space-y-4">
        {/* Overall Sentiment */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Overall Sentiment</span>
          <div className="flex items-center space-x-2">
            <span className={`text-2xl font-bold ${getSentimentColor(sentiment.overall_score)}`}>
              {sentiment.overall_score.toFixed(1)}
            </span>
            <span className="text-sm text-gray-500">
              ({sentiment.sentiment_label})
            </span>
          </div>
        </div>
        
        {/* Confidence */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Confidence</span>
          <div className="w-32 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full"
              style={{ width: `${sentiment.overall_confidence * 100}%` }}
            />
          </div>
        </div>
        
        {/* Source Breakdown */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Sources</h4>
          {Object.entries(sentiment.sources).map(([source, data]) => (
            <div key={source} className="flex items-center justify-between text-sm">
              <span className="capitalize">{source}</span>
              <span className={getSentimentColor(data.score)}>
                {data.score.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 2. Price Predictions

### Get Price Forecast

```typescript
const getPricePrediction = async (
  tokenSymbol: string,
  horizonHours: number = 24
) => {
  const response = await apiClient.get(
    `/api/v1/hunter/price-prediction/${tokenSymbol}`,
    { horizon_hours: horizonHours }
  );
  
  return response; // PricePrediction
};

interface PricePrediction {
  token_symbol: string;
  current_price: number;
  predicted_price: number;
  change_percent: number;
  confidence: number;
  direction: 'up' | 'down';
  prediction_time: string;
  forecast_time: string;
  horizon_hours: number;
}
```

### UI Component Example

```tsx
// components/PricePredictionCard.tsx
export function PricePredictionCard({ token }: { token: string }) {
  const [prediction, setPrediction] = useState<PricePrediction | null>(null);
  const [horizon, setHorizon] = useState(24);
  
  useEffect(() => {
    getPricePrediction(token, horizon).then(setPrediction);
  }, [token, horizon]);
  
  if (!prediction) return <LoadingSpinner />;
  
  const isPositive = prediction.direction === 'up';
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Price Prediction</h3>
        <select 
          value={horizon}
          onChange={(e) => setHorizon(Number(e.target.value))}
          className="text-sm border rounded px-2 py-1"
        >
          <option value={1}>1 hour</option>
          <option value={6}>6 hours</option>
          <option value={24}>24 hours</option>
          <option value={168}>7 days</option>
        </select>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Current Price</p>
          <p className="text-xl font-bold">${prediction.current_price.toFixed(2)}</p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600">Predicted Price</p>
          <p className={`text-xl font-bold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            ${prediction.predicted_price.toFixed(2)}
          </p>
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`text-2xl ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {isPositive ? '↑' : '↓'} {Math.abs(prediction.change_percent).toFixed(2)}%
          </span>
        </div>
        
        <div className="text-sm">
          <span className="text-gray-600">Confidence: </span>
          <span className="font-medium">{(prediction.confidence * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
```

---

## 3. Risk Analysis

### Get Risk Score

```typescript
const getRiskAnalysis = async (tokenSymbol: string) => {
  const response = await apiClient.get(
    `/api/v1/hunter/risk-analysis/${tokenSymbol}`
  );
  
  return response; // RiskAssessment
};

interface RiskAssessment {
  token_symbol: string;
  overall_risk_score: number;  // 0-10
  risk_level: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  factors: {
    volatility: { score: number; weight: number; };
    liquidity: { score: number; weight: number; };
    smart_contract: { score: number; weight: number; };
    market_correlation: { score: number; weight: number; };
  };
  timestamp: string;
}
```

### UI Component (Risk Dashboard)

```tsx
// components/RiskDashboard.tsx
export function RiskDashboard({ token }: { token: string }) {
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  
  useEffect(() => {
    getRiskAnalysis(token).then(setRisk);
  }, [token]);
  
  if (!risk) return <LoadingSpinner />;
  
  const getRiskColor = (score: number) => {
    if (score <= 3) return 'bg-green-500';
    if (score <= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Risk Analysis</h3>
      
      {/* Overall Risk */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-600">Overall Risk</span>
          <span className="font-bold text-lg">
            {risk.overall_risk_score.toFixed(1)}/10
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className={`${getRiskColor(risk.overall_risk_score)} h-3 rounded-full transition-all`}
            style={{ width: `${(risk.overall_risk_score / 10) * 100}%` }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-1 capitalize">
          {risk.risk_level.replace('_', ' ')}
        </p>
      </div>
      
      {/* Risk Factors */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-700">Risk Factors</h4>
        {Object.entries(risk.factors).map(([factor, data]) => (
          <div key={factor}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="capitalize">{factor.replace('_', ' ')}</span>
              <span>{data.score.toFixed(1)}/10</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`${getRiskColor(data.score)} h-2 rounded-full`}
                style={{ width: `${(data.score / 10) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 4. Trading Signals

### Get Trading Signal

```typescript
const getTradingSignal = async (tokenSymbol: string) => {
  const response = await apiClient.get(
    `/api/v1/hunter/trading-signals/generate/${tokenSymbol}`
  );
  
  return response; // TradingSignal
};

interface TradingSignal {
  token_symbol: string;
  signal_type: 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';
  confidence: number;
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  take_profit: number;
  position_size_percent: number;
  reasoning: string;
  timeframe: string;
  timestamp: string;
}
```

### UI Component (Trading Signal Card)

```tsx
// components/TradingSignalCard.tsx
export function TradingSignalCard({ token }: { token: string }) {
  const [signal, setSignal] = useState<TradingSignal | null>(null);
  
  useEffect(() => {
    getTradingSignal(token).then(setSignal);
  }, [token]);
  
  if (!signal) return <LoadingSpinner />;
  
  const getSignalColor = (type: string) => {
    if (type.includes('buy')) return 'text-green-500';
    if (type.includes('sell')) return 'text-red-500';
    return 'text-gray-500';
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Trading Signal</h3>
        <span className={`text-xl font-bold ${getSignalColor(signal.signal_type)}`}>
          {signal.signal_type.toUpperCase().replace('_', ' ')}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Entry Price</p>
          <p className="font-bold">${signal.entry_price.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Exit Price</p>
          <p className="font-bold">${signal.exit_price.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Stop Loss</p>
          <p className="font-bold text-red-500">${signal.stop_loss.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Take Profit</p>
          <p className="font-bold text-green-500">${signal.take_profit.toFixed(2)}</p>
        </div>
      </div>
      
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-1">Position Size</p>
        <p className="font-bold">{signal.position_size_percent}% of portfolio</p>
      </div>
      
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-1">Confidence</p>
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full"
              style={{ width: `${signal.confidence * 100}%` }}
            />
          </div>
          <span className="text-sm font-medium">{(signal.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      <div className="border-t pt-4">
        <p className="text-sm text-gray-600 mb-2">Reasoning</p>
        <p className="text-sm">{signal.reasoning}</p>
      </div>
    </div>
  );
}
```

---

## 5. Portfolio Optimization

### Optimize Portfolio

```typescript
const optimizePortfolio = async (
  tokens: string[],
  strategy: 'balanced' | 'conservative' | 'aggressive' = 'balanced'
) => {
  const response = await apiClient.post(
    `/api/v1/hunter/portfolio/optimize`,
    {
      tokens,
      strategy,
      risk_tolerance: strategy === 'aggressive' ? 0.8 : strategy === 'conservative' ? 0.3 : 0.5,
    }
  );
  
  return response; // OptimizedPortfolio
};

interface OptimizedPortfolio {
  strategy: string;
  allocations: Array<{
    token: string;
    weight: number;  // 0-1
    amount_usd: number;
  }>;
  expected_return: number;
  expected_volatility: number;
  sharpe_ratio: number;
  metrics: {
    total_value: number;
    diversification_score: number;
  };
}
```

### UI Component (Portfolio Optimizer)

```tsx
// components/PortfolioOptimizer.tsx
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

export function PortfolioOptimizer() {
  const [tokens, setTokens] = useState<string[]>(['ETH', 'BTC', 'USDC']);
  const [strategy, setStrategy] = useState<'balanced' | 'conservative' | 'aggressive'>('balanced');
  const [portfolio, setPortfolio] = useState<OptimizedPortfolio | null>(null);
  
  const optimize = async () => {
    const result = await optimizePortfolio(tokens, strategy);
    setPortfolio(result);
  };
  
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Portfolio Optimizer</h3>
      
      {/* Strategy Selection */}
      <div className="mb-4">
        <label className="text-sm text-gray-600 mb-2 block">Strategy</label>
        <div className="flex space-x-2">
          {['conservative', 'balanced', 'aggressive'].map((s) => (
            <button
              key={s}
              onClick={() => setStrategy(s as any)}
              className={`px-4 py-2 rounded ${
                strategy === s
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Optimize Button */}
      <button
        onClick={optimize}
        className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 mb-4"
      >
        Optimize Portfolio
      </button>
      
      {/* Results */}
      {portfolio && (
        <div className="space-y-4">
          {/* Allocation Chart */}
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={portfolio.allocations}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.token}: ${(entry.weight * 100).toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="weight"
              >
                {portfolio.allocations.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          
          {/* Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Expected Return</p>
              <p className="font-bold">{(portfolio.expected_return * 100).toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Volatility</p>
              <p className="font-bold">{(portfolio.expected_volatility * 100).toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Sharpe Ratio</p>
              <p className="font-bold">{portfolio.sharpe_ratio.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Diversification</p>
              <p className="font-bold">{portfolio.metrics.diversification_score.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Best Practices

1. **Cache Results:** Hunter AI responses can be cached for 5-15 minutes
2. **Error Handling:** Always handle API errors gracefully
3. **Loading States:** Show loading indicators for ML operations
4. **Refresh Data:** Update predictions every 15-30 minutes
5. **User Feedback:** Show confidence scores to set expectations
6. **Rate Limits:** Respect API rate limits (1000 req/min/user)

---

## Next Steps

- [ULTRA Arbitrage Integration](./ULTRA_ARBITRAGE_INTEGRATION.md)
- [WebSocket Real-time Updates](./WEBSOCKET_INTEGRATION.md)
- [Complete API Reference](../API_REFERENCE.md)
