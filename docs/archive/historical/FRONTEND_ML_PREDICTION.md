# FRONTEND_ML_PREDICTION

## ML Prediction Module

**User Type:** Authenticated User  
**Module:** ML Prediction - Machine Learning Risk Prediction  
**Route:** `/ml/prediction`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**ML Prediction** - AI-Powered Protocol Risk Prediction

### Description
Machine learning-powered risk prediction system using graph features, market data, and historical risk patterns to predict protocol risk scores, detect anomalies, and forecast future risk trends.

### Key Capabilities
- ✅ Single protocol risk prediction
- ✅ Batch risk prediction
- ✅ Anomaly detection
- ✅ Risk forecasting
- ✅ Confidence scoring
- ✅ Model versioning

---

## 🔌 API Integration

### 1. Predict Protocol Risk

```typescript
// GET /api/v1/ml/prediction/{protocol_id}
// Description: Predict protocol risk using ML models
// Authentication: Required (Bearer token)

interface RiskPredictionResponse {
  protocol_id: string;
  protocol_name: string;
  predicted_risk_score: number; // 0-10
  confidence: number; // 0-1
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_trend: 'increasing' | 'stable' | 'decreasing';
  contributing_factors: string[];
  recommendations: string[];
  prediction_timestamp: string;
  model_version: string;
}

const predictRisk = async (protocolId: string): Promise<RiskPredictionResponse> => {
  const response = await api.get(`/api/v1/ml/prediction/${protocolId}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "protocol_id": "aave-uuid",
  "protocol_name": "Aave V3",
  "predicted_risk_score": 3.2,
  "confidence": 0.89,
  "risk_level": "low",
  "risk_trend": "stable",
  "contributing_factors": [
    "Strong TVL growth (+15% last 30 days)",
    "High audit score (8+ audits)",
    "Low dependency risk",
    "Stable oracle connections"
  ],
  "recommendations": [
    "Monitor oracle health regularly",
    "Watch for sudden TVL changes",
    "Review smart contract upgrades"
  ],
  "prediction_timestamp": "2025-12-01T12:00:00Z",
  "model_version": "v2.1.0"
}
```

### 2. Batch Predict Risks

```typescript
// POST /api/v1/ml/prediction/batch
// Description: Predict risk for multiple protocols
// Authentication: Required (Bearer token)

interface BatchRiskPredictionRequest {
  protocol_ids: string[];
}

interface BatchRiskPredictionResponse {
  predictions: RiskPredictionResponse[];
  total: number;
}

const predictBatchRisk = async (
  protocolIds: string[]
): Promise<BatchRiskPredictionResponse> => {
  const response = await api.post('/api/v1/ml/prediction/batch', {
    protocol_ids: protocolIds
  }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Request:
{
  "protocol_ids": ["aave-uuid", "compound-uuid", "uniswap-uuid"]
}

// Example Response (200 OK):
{
  "predictions": [
    { /* Risk prediction for Aave */ },
    { /* Risk prediction for Compound */ },
    { /* Risk prediction for Uniswap */ }
  ],
  "total": 3
}
```

### 3. Detect Anomalies

```typescript
// GET /api/v1/ml/prediction/{protocol_id}/anomalies
// Description: Detect anomalous risk patterns
// Authentication: Required (Bearer token)

interface AnomalyDetectionParams {
  lookback_days?: number; // Default: 7, min: 1, max: 90
}

interface AnomalyDetectionResponse {
  protocol_id: string;
  protocol_name: string;
  anomalies_detected: boolean;
  anomaly_count: number;
  anomalies: Array<{
    timestamp: string;
    risk_score: number;
    expected_range: [number, number];
    deviation_magnitude: number;
    severity: 'low' | 'medium' | 'high';
    description: string;
  }>;
  lookback_days: number;
  analysis_timestamp: string;
}

const detectAnomalies = async (
  protocolId: string,
  params: AnomalyDetectionParams = { lookback_days: 7 }
): Promise<AnomalyDetectionResponse> => {
  const response = await api.get(
    `/api/v1/ml/prediction/${protocolId}/anomalies`,
    {
      params,
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "protocol_id": "euler-uuid",
  "protocol_name": "Euler Finance",
  "anomalies_detected": true,
  "anomaly_count": 2,
  "anomalies": [
    {
      "timestamp": "2025-11-28T14:30:00Z",
      "risk_score": 8.5,
      "expected_range": [3.0, 5.0],
      "deviation_magnitude": 3.5,
      "severity": "high",
      "description": "Sudden risk score spike detected - significantly above expected range"
    },
    {
      "timestamp": "2025-11-29T09:15:00Z",
      "risk_score": 7.2,
      "expected_range": [3.0, 5.0],
      "deviation_magnitude": 2.2,
      "severity": "medium",
      "description": "Risk score remains elevated above normal patterns"
    }
  ],
  "lookback_days": 7,
  "analysis_timestamp": "2025-12-01T12:00:00Z"
}
```

### 4. Forecast Risk

```typescript
// GET /api/v1/ml/prediction/{protocol_id}/forecast
// Description: Forecast protocol risk trajectory
// Authentication: Required (Bearer token)

interface RiskForecastParams {
  forecast_days?: number; // Default: 7, min: 1, max: 30
}

interface RiskForecastResponse {
  protocol_id: string;
  forecast: Array<{
    date: string;
    predicted_risk_score: number;
    confidence_lower: number;
    confidence_upper: number;
    trend: 'increasing' | 'stable' | 'decreasing';
  }>;
  forecast_days: number;
}

const forecastRisk = async (
  protocolId: string,
  params: RiskForecastParams = { forecast_days: 7 }
): Promise<RiskForecastResponse> => {
  const response = await api.get(
    `/api/v1/ml/prediction/${protocolId}/forecast`,
    {
      params,
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "protocol_id": "aave-uuid",
  "forecast": [
    {
      "date": "2025-12-02",
      "predicted_risk_score": 3.3,
      "confidence_lower": 2.8,
      "confidence_upper": 3.8,
      "trend": "stable"
    },
    {
      "date": "2025-12-03",
      "predicted_risk_score": 3.4,
      "confidence_lower": 2.7,
      "confidence_upper": 4.1,
      "trend": "stable"
    }
    // ... more forecast days
  ],
  "forecast_days": 7
}
```

---

## 🔗 React Hooks

```typescript
export function useRiskPrediction(protocolId: string) {
  return useQuery({
    queryKey: ['ml', 'prediction', protocolId],
    queryFn: () => predictRisk(protocolId),
    staleTime: 300000, // 5 minutes
  });
}

export function useBatchRiskPrediction() {
  return useMutation({
    mutationFn: predictBatchRisk,
  });
}

export function useAnomalyDetection(protocolId: string, lookbackDays: number = 7) {
  return useQuery({
    queryKey: ['ml', 'anomalies', protocolId, lookbackDays],
    queryFn: () => detectAnomalies(protocolId, { lookback_days: lookbackDays }),
  });
}

export function useRiskForecast(protocolId: string, forecastDays: number = 7) {
  return useQuery({
    queryKey: ['ml', 'forecast', protocolId, forecastDays],
    queryFn: () => forecastRisk(protocolId, { forecast_days: forecastDays }),
  });
}
```

---

## 🎨 React Components

```typescript
export function RiskPredictionCard({ protocolId }: { protocolId: string }) {
  const { data: prediction, isLoading } = useRiskPrediction(protocolId);
  
  if (isLoading) return <Skeleton />;
  if (!prediction) return null;
  
  const riskColors = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-orange-600',
    critical: 'text-red-600',
  };
  
  return (
    <div className="risk-prediction-card">
      <h3>{prediction.protocol_name}</h3>
      <div className={`risk-score ${riskColors[prediction.risk_level]}`}>
        {prediction.predicted_risk_score.toFixed(1)}/10
      </div>
      <div className="confidence">
        Confidence: {(prediction.confidence * 100).toFixed(0)}%
      </div>
      <div className="trend">{prediction.risk_trend}</div>
      
      <div className="factors">
        <h4>Contributing Factors:</h4>
        <ul>
          {prediction.contributing_factors.map((factor, i) => (
            <li key={i}>{factor}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function RiskForecastChart({ protocolId }: { protocolId: string }) {
  const { data: forecast } = useRiskForecast(protocolId, 7);
  
  if (!forecast) return null;
  
  return (
    <LineChart data={forecast.forecast}>
      <Line dataKey="predicted_risk_score" stroke="#3b82f6" />
      <Line dataKey="confidence_upper" stroke="#9ca3af" strokeDasharray="5 5" />
      <Line dataKey="confidence_lower" stroke="#9ca3af" strokeDasharray="5 5" />
    </LineChart>
  );
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: ML Prediction*  
*Backend Status: ✅ 100% Implemented (4 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
