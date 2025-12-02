# FRONTEND_ADMIN_ML_MANAGEMENT

## Admin ML Model Management Module

**User Type:** Admin  
**Module:** ML Model & Prediction Management  
**Route:** `/admin/ml`  
**Platform:** Web (Admin Panel)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**ML Management** - Model Monitoring & Control

### Description
Administrative control panel for managing ML risk prediction models, monitoring prediction quality, analyzing model performance, and managing training data.

### Key Capabilities
- Model performance monitoring
- Prediction accuracy tracking
- Feature importance analysis
- Anomaly detection tuning
- Model version management
- Training data quality
- Prediction audit logs
- A/B testing controls

---

## 🖼️ Wireframes

### View 1: ML Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Admin Home          ML Management          [Refresh]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Model Performance                           🟢 Excellent  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Risk Prediction Model v1.2.0                  Active  ││
│  │  Accuracy: 89%  |  Predictions Today: 3,456           ││
│  │  Avg Confidence: 92%  |  Last Updated: 2 days ago     ││
│  │  ────────────────────────────────────────────────────  ││
│  │  Anomaly Detection Model v1.0.1               Active  ││
│  │  Detection Rate: 87%  |  Alerts Today: 12             ││
│  │  False Positives: 3%  |  Last Updated: 1 week ago    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ⚠️ Performance Alerts (2)                     [View All →] │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟡 Risk model accuracy decreased by 3% this week       ││
│  │     Potential cause: Market volatility spike            ││
│  │     [Investigate] [Retrain]                             ││
│  ├─────────────────────────────────────────────────────────┤│
│  │  🟢 Anomaly detection improved by 5%                    ││
│  │     Recent tuning changes effective                     ││
│  │     [View Details]                                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Quick Actions                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Trigger    │ │   Export     │ │   View       │        │
│  │   Retraining │ │   Metrics    │ │   Logs       │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌───────────────────────────────┬───────────────────────┐ │
│  │  Prediction Statistics        │  Feature Importance   │ │
│  │                               │                       │ │
│  │  Total Predictions: 1.2M      │  1. TVL Stability    │ │
│  │  Avg Latency: 45ms            │     Weight: 28%      │ │
│  │  Cache Hit Rate: 82%          │  2. Audit History    │ │
│  │  Errors: 3                    │     Weight: 22%      │ │
│  │  Confidence >90%: 87%         │  3. Network Position │ │
│  │                               │     Weight: 18%      │ │
│  │  [View Details →]             │  [View All 12 →]     │ │
│  └───────────────────────────────┴───────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 2: Model Performance Analytics

```
┌─────────────────────────────────────────────────────────────┐
│  [←] ML Dashboard        Model Performance Analytics        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Risk Prediction Model v1.2.0                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Accuracy Over Time (30 Days)                           ││
│  │                                                         ││
│  │  95%┤                      ╭──────                     ││
│  │     │                  ╭───╯                           ││
│  │  90%┤              ╭───╯                               ││
│  │     │          ╭───╯                                   ││
│  │  85%┤──────────╯                                       ││
│  │     │                                                  ││
│  │  80%┼──────────────────────────────────────────────▶  ││
│  │      0d    7d    14d   21d   28d                      ││
│  │                                                         ││
│  │  Current: 89%  |  Best: 92%  |  Avg: 88%              ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Prediction Distribution                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Risk Score Range    Count     Avg Confidence          ││
│  │  0.0 - 2.0 (LOW)     45,234    94% ████████████████   ││
│  │  2.1 - 4.0 (MED)     28,567    91% █████████████░     ││
│  │  4.1 - 7.0 (HIGH)    8,234     88% ███████████░░      ││
│  │  7.1 - 10.0 (CRIT)   1,456     85% ██████████░░░      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Confidence Calibration                                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Predicted vs Actual Accuracy                           ││
│  │                                                         ││
│  │  100%┤                              ╱                  ││
│  │      │                          ╱                      ││
│  │   80%┤                      ╱                          ││
│  │      │                  ╱                              ││
│  │   60%┤              ╱                                  ││
│  │      │          ╱                                      ││
│  │   40%┤      ╱                                          ││
│  │      │  ╱                                              ││
│  │   20%┼──────────────────────────────────────────────▶  ││
│  │      20%   40%   60%   80%   100%                      ││
│  │                                                         ││
│  │  Calibration Score: 0.92 (Excellent)                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Error Analysis                                             │
│  • Over-predictions: 234 (28% of errors)                    │
│  • Under-predictions: 612 (72% of errors)                   │
│  • Most common: Missed black swan events                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 3: Feature Importance & Tuning

```
┌─────────────────────────────────────────────────────────────┐
│  [←] ML Dashboard        Feature Importance & Tuning        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Feature Weights (Risk Prediction Model)                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Rank  Feature Name            Weight    Change         ││
│  │  ────────────────────────────────────────────────────   ││
│  │  #1    TVL Stability            28.3%    ↑ +2.1%       ││
│  │  #2    Audit History            22.1%    → 0%          ││
│  │  #3    Network Centrality       17.8%    ↓ -1.5%       ││
│  │  #4    Historical Risk          12.4%    ↑ +0.8%       ││
│  │  #5    Market Volatility        9.2%     ↑ +1.2%       ││
│  │  #6    Code Quality Score       5.8%     → 0%          ││
│  │  #7    Community Activity       4.4%     ↓ -0.5%       ││
│  │  ...   8 more features                                  ││
│  │                                                         ││
│  │  [Export Weights] [Compare Versions]                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Anomaly Detection Thresholds                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Metric                Current    Recommended           ││
│  │  ─────────────────────────────────────────────────────  ││
│  │  TVL Change Rate       15%/hour   12%/hour   [Apply]   ││
│  │  Withdrawal Volume     3σ         2.5σ        [Apply]   ││
│  │  Transaction Count     3.5σ       3σ          [Apply]   ││
│  │  Price Volatility      20%/hour   15%/hour   [Apply]   ││
│  │                                                         ││
│  │  Last Tuning: 5 days ago                                ││
│  │  Performance Since: +5% detection rate                  ││
│  │                                                         ││
│  │  [Apply All Recommended] [Reset to Defaults]            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Model Hyperparameters                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Learning Rate:        0.001      [Edit]                ││
│  │  Batch Size:           32         [Edit]                ││
│  │  Regularization (L2):  0.01       [Edit]                ││
│  │  Dropout Rate:         0.2        [Edit]                ││
│  │  Max Epochs:           100        [Edit]                ││
│  │                                                         ││
│  │  ⚠️ Changes require model retraining                    ││
│  │  Est. Training Time: 2.5 hours                          ││
│  │                                                         ││
│  │  [Save Changes] [Trigger Retrain]                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Admin API Endpoints

### Get Model Performance

```typescript
// GET /api/v1/admin/ml/models/performance
interface ModelPerformanceResponse {
  models: Array<{
    name: string;
    version: string;
    status: 'active' | 'training' | 'retired';
    accuracy: number; // 0-1
    predictions_today: number;
    avg_confidence: number; // 0-1
    last_updated: string;
  }>;
  alerts: Array<{
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    message: string;
    model_name: string;
  }>;
}
```

### Get Feature Importance

```typescript
// GET /api/v1/admin/ml/models/:name/features
interface FeatureImportanceResponse {
  model_name: string;
  model_version: string;
  features: Array<{
    rank: number;
    name: string;
    weight: number; // 0-1
    change_from_previous: number;
    description: string;
  }>;
  total_features: number;
}
```

### Trigger Model Retraining

```typescript
// POST /api/v1/admin/ml/models/:name/retrain
interface RetrainRequest {
  hyperparameters?: Record<string, any>;
  training_data_filter?: {
    start_date?: string;
    end_date?: string;
    min_protocols?: number;
  };
}

interface RetrainResponse {
  job_id: string;
  status: 'queued' | 'running';
  estimated_duration_minutes: number;
  started_at: string;
}
```

### Get Prediction Audit Log

```typescript
// GET /api/v1/admin/ml/predictions/audit?limit=100
interface PredictionAuditResponse {
  predictions: Array<{
    id: string;
    protocol_id: string;
    protocol_name: string;
    predicted_risk: number;
    confidence: number;
    actual_risk?: number; // If available
    prediction_error?: number;
    predicted_at: string;
    model_version: string;
  }>;
  statistics: {
    total_predictions: number;
    avg_error: number;
    accuracy: number;
  };
}
```

---

## 🎨 Component Specifications

```typescript
interface MLDashboardProps {
  refreshInterval?: number;
}

interface ModelPerformanceChartProps {
  modelName: string;
  timeRange: '7d' | '30d' | '90d' | '1y';
  metrics: Array<{
    timestamp: string;
    accuracy: number;
    confidence: number;
  }>;
}

interface FeatureImportanceTableProps {
  features: FeatureImportance[];
  onExport: () => void;
}

interface AnomalyThresholdControlsProps {
  thresholds: Record<string, number>;
  recommended: Record<string, number>;
  onApply: (metric: string, value: number) => void;
}

interface ModelRetrainingDialogProps {
  modelName: string;
  currentVersion: string;
  estimatedDuration: number;
  onTrigger: (params: RetrainRequest) => void;
}
```

---

## ⚠️ Error Handling

```typescript
const mlAdminErrors = {
  ML_ADMIN_001: 'Model not found',
  ML_ADMIN_002: 'Retraining already in progress',
  ML_ADMIN_003: 'Invalid hyperparameters',
  ML_ADMIN_004: 'Insufficient training data',
  ML_ADMIN_005: 'Model performance degraded below threshold',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin ML Management*
