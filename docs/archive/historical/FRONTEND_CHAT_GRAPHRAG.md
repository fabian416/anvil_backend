# FRONTEND_CHAT_GRAPHRAG

## Chat GraphRAG Integration Module

**User Type:** Authenticated User  
**Module:** Chat - GraphRAG Enhanced Chat Features  
**Route:** `/chat`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Chat GraphRAG** - AI-Enhanced Protocol Discovery & Risk Analysis

### Description
GraphRAG-enhanced chat features providing intelligent protocol search, ML-powered risk analysis, and similar protocol discovery directly within conversation context.

### Key Capabilities
- ✅ Contextual protocol search
- ✅ ML-powered risk analysis from chat
- ✅ Similar protocol discovery
- ✅ Safer alternative recommendations
- ✅ Conversational risk insights

---

## 🔌 API Integration

### 1. Search Protocols from Chat

```typescript
// POST /api/v1/chat/search-protocols
interface ChatProtocolSearchRequest {
  query: string;
  conversation_id?: string;
  user_preferences?: Record<string, any>;
}

interface ChatProtocolSearchResponse {
  results: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    risk_score: number;
    risk_level: string;
    tvl: number;
    apy: number;
    audit_count: number;
    description: string;
    category: string;
    chain: string;
    why_relevant: string;
  }>;
  search_context: string;
  recommendations: string[];
}

const searchProtocolsFromChat = async (request: ChatProtocolSearchRequest): Promise<ChatProtocolSearchResponse> => {
  const response = await api.post('/api/v1/chat/search-protocols', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 2. Analyze Risk from Chat

```typescript
// POST /api/v1/chat/analyze-risk
interface ChatRiskAnalysisRequest {
  protocol_name: string;
  conversation_id?: string;
  operation_type?: string;
  amount_usd?: number;
}

interface ChatRiskAnalysisResponse {
  risk_analysis: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;
    risk_level: string;
    confidence: number;
    contributing_factors: Array<{
      factor: string;
      impact: number;
      description: string;
      is_critical: boolean;
    }>;
    recommendations: string[];
    should_warn: boolean;
    warning_message?: string;
  };
  alternatives: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    risk_score: number;
    risk_level: string;
    tvl: number;
    apy: number;
    why_better: string;
  }>;
  contextual_message: string;
}

const analyzeRiskFromChat = async (request: ChatRiskAnalysisRequest): Promise<ChatRiskAnalysisResponse> => {
  const response = await api.post('/api/v1/chat/analyze-risk', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 3. Get Similar Protocols from Chat

```typescript
// POST /api/v1/chat/similar-protocols
interface ChatSimilarProtocolsRequest {
  protocol_name: string;
  conversation_id?: string;
  limit?: number;
}

interface ChatSimilarProtocolsResponse {
  base_protocol: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;
    risk_level: string;
    tvl: number;
    category: string;
  };
  similar_protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    risk_score: number;
    risk_level: string;
    tvl: number;
    why_similar: string;
  }>;
}

const getSimilarProtocolsFromChat = async (request: ChatSimilarProtocolsRequest): Promise<ChatSimilarProtocolsResponse> => {
  const response = await api.post('/api/v1/chat/similar-protocols', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function useChatProtocolSearch() {
  return useMutation({
    mutationFn: searchProtocolsFromChat,
  });
}

export function useChatRiskAnalysis() {
  return useMutation({
    mutationFn: analyzeRiskFromChat,
  });
}

export function useChatSimilarProtocols() {
  return useMutation({
    mutationFn: getSimilarProtocolsFromChat,
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Chat GraphRAG Integration*  
*Backend Status: ✅ 100% Implemented (3 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
