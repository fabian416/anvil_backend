/**
 * Anvil Unified Chat API - TypeScript/JavaScript SDK Examples
 *
 * Complete examples showing how to interact with all 16 unified chat intent types
 * using TypeScript, Axios, and modern JavaScript patterns.
 *
 * Installation:
 *   npm install axios
 *   npm install -D @types/node  # For TypeScript
 *
 * Usage:
 *   ts-node typescript_sdk_examples.ts
 *   # or compile and run:
 *   tsc typescript_sdk_examples.ts && node typescript_sdk_examples.js
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================================================
// Type Definitions
// ============================================================================

interface ChatConfig {
  baseUrl: string;
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
  };
}

interface ConversationResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface MessageResponse {
  user_message: {
    id: string;
    content: string;
    role: 'user';
    timestamp: string;
  };
  agent_message: {
    id: string;
    content: string;
    role: 'assistant';
    agent_type: string;
    timestamp: string;
  };
  routing: {
    intent: string;
    confidence: number;
    handler: string;
    reasoning: string;
    total_latency_ms: number;
  };
  enrichment: Record<string, any>;
}

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

// ============================================================================
// Anvil Chat Client Class
// ============================================================================

class AnvilChatClient {
  private config: ChatConfig;
  private token: string | null = null;
  private conversationId: string | null = null;
  private client: AxiosInstance;

  constructor(config: ChatConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Authenticate and get access token
   */
  async login(): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/account/login', {
      email: this.config.email,
      password: this.config.password,
    });

    this.token = response.data.access_token;
    this.client.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

    return response.data;
  }

  /**
   * Create a new conversation
   */
  async createConversation(title: string = 'TypeScript SDK Conversation'): Promise<ConversationResponse> {
    const response = await this.client.post<ConversationResponse>('/user/chat/conversations', {
      title,
    });

    this.conversationId = response.data.id;
    return response.data;
  }

  /**
   * Send a message to the unified chat endpoint
   */
  async sendMessage(content: string, conversationId?: string): Promise<MessageResponse> {
    const convId = conversationId || this.conversationId;
    if (!convId) {
      throw new Error('No conversation_id set. Call createConversation() first.');
    }

    const response = await this.client.post<MessageResponse>(
      `/user/chat/conversations/${convId}/messages`,
      { content }
    );

    return response.data;
  }

  /**
   * Get conversation message history
   */
  async getMessages(conversationId?: string, limit: number = 50): Promise<Message[]> {
    const convId = conversationId || this.conversationId;
    const response = await this.client.get<Message[]>(
      `/user/chat/conversations/${convId}/messages`,
      { params: { limit } }
    );

    return response.data;
  }

  /**
   * Get current authentication token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Get current conversation ID
   */
  getConversationId(): string | null {
    return this.conversationId;
  }
}

// ============================================================================
// Example Usage for All 16 Intent Types
// ============================================================================

async function exampleGraphRagIntents(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('GRAPHRAG INTENTS');
  console.log('='.repeat(80));

  // 1. Protocol Search
  console.log('\n1. Protocol Search');
  console.log('-'.repeat(40));
  const response1 = await client.sendMessage(
    'Show me high-yield staking protocols on Ethereum with low risk'
  );
  console.log(`Intent: ${response1.routing.intent}`);
  console.log(`Confidence: ${response1.routing.confidence}`);
  console.log(`Handler: ${response1.routing.handler}`);
  console.log(`Response: ${response1.agent_message.content.substring(0, 200)}...`);

  // 2. Risk Assessment
  console.log('\n2. Risk Assessment');
  console.log('-'.repeat(40));
  const response2 = await client.sendMessage('Is Aave safe to use? What are the risks?');
  console.log(`Intent: ${response2.routing.intent}`);
  console.log(`Risk Score: ${response2.enrichment.risk_analysis?.overall_risk_score || 'N/A'}`);

  // 3. Similar Protocols
  console.log('\n3. Similar Protocols');
  console.log('-'.repeat(40));
  const response3 = await client.sendMessage('What protocols are similar to Uniswap?');
  console.log(`Intent: ${response3.routing.intent}`);
  console.log(`Similar Protocols Found: ${response3.enrichment.similar_protocols?.length || 0}`);
}

async function exampleHunterAiIntents(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('HUNTER AI INTENTS');
  console.log('='.repeat(80));

  // 1. Sentiment Analysis
  console.log('\n1. Sentiment Analysis');
  console.log('-'.repeat(40));
  const response1 = await client.sendMessage("What's the ETH sentiment on Twitter and Reddit?");
  console.log(`Intent: ${response1.routing.intent}`);
  console.log(`Token: ${response1.enrichment.token_symbol}`);
  console.log(`Sources: ${response1.enrichment.sources}`);
  console.log(`Tool: ${response1.enrichment.hunter_tool}`);

  // 2. Price Prediction
  console.log('\n2. Price Prediction');
  console.log('-'.repeat(40));
  const response2 = await client.sendMessage('Predict BTC price for next 7 days');
  console.log(`Intent: ${response2.routing.intent}`);
  console.log(`Token: ${response2.enrichment.token_symbol}`);
  console.log(`Time Horizon: ${response2.enrichment.time_horizon}`);

  // 3. Risk Signals
  console.log('\n3. Risk Signals');
  console.log('-'.repeat(40));
  const response3 = await client.sendMessage('Show risk signals for ETH');
  console.log(`Intent: ${response3.routing.intent}`);
  console.log(`Tool: ${response3.enrichment.hunter_tool}`);

  // 4. Trading Signals
  console.log('\n4. Trading Signals');
  console.log('-'.repeat(40));
  const response4 = await client.sendMessage('Should I buy SOL now? Give me trading signals');
  console.log(`Intent: ${response4.routing.intent}`);
  console.log(`Token: ${response4.enrichment.token_symbol}`);

  // 5. Pattern Detection
  console.log('\n5. Pattern Detection');
  console.log('-'.repeat(40));
  const response5 = await client.sendMessage('What chart patterns do you see for BTC?');
  console.log(`Intent: ${response5.routing.intent}`);
  console.log(`Token: ${response5.enrichment.token_symbol}`);

  // 6. Portfolio Optimization
  console.log('\n6. Portfolio Optimization');
  console.log('-'.repeat(40));
  const response6 = await client.sendMessage(
    'Optimize my portfolio with BTC, ETH, and SOL for moderate risk'
  );
  console.log(`Intent: ${response6.routing.intent}`);
  console.log(`Tokens: ${response6.enrichment.tokens}`);
  console.log(`Risk Tolerance: ${response6.enrichment.risk_tolerance}`);
}

async function exampleUltraIntents(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('ULTRA INTENTS');
  console.log('='.repeat(80));

  // 1. Arbitrage Discovery
  console.log('\n1. Arbitrage Discovery');
  console.log('-'.repeat(40));
  const response1 = await client.sendMessage('Find arbitrage opportunities with $10,000 capital');
  console.log(`Intent: ${response1.routing.intent}`);
  console.log(`Capital: $${response1.enrichment.capital?.toLocaleString()}`);
  console.log(`Arb Type: ${response1.enrichment.arb_type}`);
  console.log(`Tool: ${response1.enrichment.ultra_tool}`);

  // 2. Flash Loan Selection
  console.log('\n2. Flash Loan Selection');
  console.log('-'.repeat(40));
  const response2 = await client.sendMessage('Best flash loan protocol for 100k USDC');
  console.log(`Intent: ${response2.routing.intent}`);
  console.log(`Token: ${response2.enrichment.token_symbol}`);
  console.log(`Amount: $${response2.enrichment.amount?.toLocaleString()}`);
  console.log(`Protocol: ${response2.enrichment.protocol || 'Auto-selected'}`);

  // 3. MEV Protection
  console.log('\n3. MEV Protection');
  console.log('-'.repeat(40));
  const response3 = await client.sendMessage('Execute ARB-001 with Flashbots protection');
  console.log(`Intent: ${response3.routing.intent}`);
  console.log(`Opportunity ID: ${response3.enrichment.opportunity_id}`);
  console.log(`Tool: ${response3.enrichment.ultra_tool}`);

  // 4. Auto Executor Control
  console.log('\n4. Auto Executor Control');
  console.log('-'.repeat(40));

  // Start bot
  const response4a = await client.sendMessage('Start trading bot');
  console.log(`Intent: ${response4a.routing.intent}`);
  console.log(`Action: ${response4a.enrichment.action}`);

  // Check status
  const response4b = await client.sendMessage('Show bot status');
  console.log(`Action: ${response4b.enrichment.action}`);

  // Stop bot
  const response4c = await client.sendMessage('Stop trading bot');
  console.log(`Action: ${response4c.enrichment.action}`);
}

async function exampleAgentSquadIntents(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('AGENT SQUAD & CHAT INTENTS');
  console.log('='.repeat(80));

  // 1. Specialist Task
  console.log('\n1. Specialist Task');
  console.log('-'.repeat(40));
  const response1 = await client.sendMessage(
    'Analyze ETH/USDC liquidity depth on Uniswap V3'
  );
  console.log(`Intent: ${response1.routing.intent}`);
  console.log(`Handler: ${response1.routing.handler}`);
  console.log(`Tools Used: ${response1.enrichment.tools_used?.join(', ') || 'N/A'}`);

  // 2. Complex Workflow
  console.log('\n2. Complex Workflow');
  console.log('-'.repeat(40));
  const response2 = await client.sendMessage(
    'Create a complete DeFi investment strategy for $50k with risk analysis'
  );
  console.log(`Intent: ${response2.routing.intent}`);
  console.log(`Handler: ${response2.routing.handler}`);
  console.log(`Workflow ID: ${response2.enrichment.workflow_id || 'N/A'}`);
  console.log(`Agents Involved: ${response2.enrichment.agents_involved?.join(', ') || 'N/A'}`);

  // 3. General Conversation
  console.log('\n3. General Conversation');
  console.log('-'.repeat(40));
  const response3 = await client.sendMessage('Hello! What can you help me with?');
  console.log(`Intent: ${response3.routing.intent}`);
  console.log(`Handler: ${response3.routing.handler}`);
}

async function exampleAdvancedUsage(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('ADVANCED USAGE PATTERNS');
  console.log('='.repeat(80));

  // Multi-turn conversation
  console.log('\n1. Multi-turn Conversation');
  console.log('-'.repeat(40));

  const response1 = await client.sendMessage('Find safe lending protocols');
  console.log(`User: Find safe lending protocols`);
  console.log(`Intent: ${response1.routing.intent}`);

  const response2 = await client.sendMessage('What about the risks of the first one?');
  console.log(`User: What about the risks of the first one?`);
  console.log(`Intent: ${response2.routing.intent}`);

  // Batch multiple queries
  console.log('\n2. Batch Processing');
  console.log('-'.repeat(40));

  const queries = [
    'ETH sentiment',
    'BTC price prediction',
    'SOL trading signals',
  ];

  const promises = queries.map(query => client.sendMessage(query));
  const responses = await Promise.all(promises);

  responses.forEach((response, index) => {
    console.log(`Query: ${queries[index]}`);
    console.log(`  Intent: ${response.routing.intent}`);
    console.log(`  Latency: ${response.routing.total_latency_ms}ms`);
  });

  // Message history
  console.log('\n3. Retrieve Message History');
  console.log('-'.repeat(40));

  const messages = await client.getMessages(undefined, 10);
  console.log(`Total messages in conversation: ${messages.length}`);
  messages.slice(0, 3).forEach(msg => {
    console.log(`  - ${msg.role}: ${msg.content.substring(0, 50)}...`);
  });
}

async function exampleErrorHandling(client: AnvilChatClient): Promise<void> {
  console.log('\n' + '='.repeat(80));
  console.log('ERROR HANDLING');
  console.log('='.repeat(80));

  // Invalid conversation ID
  console.log('\n1. Invalid Conversation ID');
  console.log('-'.repeat(40));
  try {
    await client.sendMessage('Test message', 'invalid-id');
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.log(`Error: ${error.response?.status} - ${JSON.stringify(error.response?.data)}`);
    }
  }

  // Empty message
  console.log('\n2. Empty Message');
  console.log('-'.repeat(40));
  try {
    await client.sendMessage('');
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.log(`Error: ${error.response?.status} - ${JSON.stringify(error.response?.data)}`);
    }
  }

  // Rate limiting handling
  console.log('\n3. Rate Limiting Handling');
  console.log('-'.repeat(40));
  for (let i = 0; i < 5; i++) {
    try {
      await client.sendMessage(`Test message ${i}`);
      console.log(`Message ${i}: Success`);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 429) {
        console.log(`Rate limited. Retry-After: ${error.response.headers['retry-after']}`);
        break;
      }
    }
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

function printResponseSummary(response: MessageResponse): void {
  console.log('\nResponse Summary:');
  console.log('-'.repeat(80));
  console.log(`Intent:     ${response.routing.intent}`);
  console.log(`Confidence: ${response.routing.confidence.toFixed(2)}`);
  console.log(`Handler:    ${response.routing.handler}`);
  console.log(`Latency:    ${response.routing.total_latency_ms}ms`);

  if (response.enrichment && Object.keys(response.enrichment).length > 0) {
    console.log('\nEnrichment Data:');
    for (const [key, value] of Object.entries(response.enrichment)) {
      console.log(`  ${key}: ${JSON.stringify(value)}`);
    }
  }

  console.log('\nAgent Response:');
  console.log('-'.repeat(80));
  const content = response.agent_message.content.substring(0, 500);
  console.log(content);
  if (response.agent_message.content.length > 500) {
    console.log('...');
  }
  console.log('-'.repeat(80));
}

async function saveConversationHistory(
  client: AnvilChatClient,
  filename: string = 'conversation_history.json'
): Promise<void> {
  const fs = await import('fs/promises');
  const messages = await client.getMessages();
  await fs.writeFile(filename, JSON.stringify(messages, null, 2));
  console.log(`Saved ${messages.length} messages to ${filename}`);
}

// ============================================================================
// Main Execution
// ============================================================================

async function main(): Promise<void> {
  // Initialize client
  const config: ChatConfig = {
    baseUrl: 'http://localhost:8080/api/v1',
    email: 'user@example.com',
    password: 'password',
  };

  const client = new AnvilChatClient(config);

  try {
    // Authenticate
    console.log('Authenticating...');
    await client.login();
    console.log('✓ Logged in successfully');

    // Create conversation
    console.log('\nCreating conversation...');
    await client.createConversation('TypeScript SDK Examples');
    console.log(`✓ Conversation created: ${client.getConversationId()}`);

    // Run all examples
    await exampleGraphRagIntents(client);
    await exampleHunterAiIntents(client);
    await exampleUltraIntents(client);
    await exampleAgentSquadIntents(client);
    await exampleAdvancedUsage(client);
    await exampleErrorHandling(client);

    // Save conversation history
    await saveConversationHistory(client);

    console.log('\n' + '='.repeat(80));
    console.log('ALL EXAMPLES COMPLETED');
    console.log('='.repeat(80));
  } catch (error) {
    console.error('\nError occurred:', error);
    if (axios.isAxiosError(error)) {
      console.error('Response:', error.response?.data);
    }
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

// ============================================================================
// Quick Start Examples
// ============================================================================

async function quickStartProtocolSearch(): Promise<void> {
  const config: ChatConfig = {
    baseUrl: 'http://localhost:8080/api/v1',
    email: 'user@example.com',
    password: 'password',
  };

  const client = new AnvilChatClient(config);
  await client.login();
  await client.createConversation();

  const response = await client.sendMessage('Show me DeFi lending protocols');
  printResponseSummary(response);
}

async function quickStartSentimentAnalysis(): Promise<void> {
  const config: ChatConfig = {
    baseUrl: 'http://localhost:8080/api/v1',
    email: 'user@example.com',
    password: 'password',
  };

  const client = new AnvilChatClient(config);
  await client.login();
  await client.createConversation();

  const response = await client.sendMessage("What's BTC sentiment?");
  printResponseSummary(response);
}

async function quickStartArbitrage(): Promise<void> {
  const config: ChatConfig = {
    baseUrl: 'http://localhost:8080/api/v1',
    email: 'user@example.com',
    password: 'password',
  };

  const client = new AnvilChatClient(config);
  await client.login();
  await client.createConversation();

  const response = await client.sendMessage('Find arbitrage with $5000');
  printResponseSummary(response);
}

// Uncomment to run quick start examples:
// quickStartProtocolSearch();
// quickStartSentimentAnalysis();
// quickStartArbitrage();

// ============================================================================
// React Hooks Example
// ============================================================================

/**
 * Custom React hook for using Anvil Chat API
 *
 * Usage:
 *   const { sendMessage, messages, loading, error } = useAnvilChat();
 *   const response = await sendMessage("Show me DeFi protocols");
 */

/*
import { useState, useEffect, useCallback } from 'react';

export function useAnvilChat(config: ChatConfig) {
  const [client, setClient] = useState<AnvilChatClient | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const initClient = async () => {
      const newClient = new AnvilChatClient(config);
      await newClient.login();
      await newClient.createConversation();
      setClient(newClient);
    };
    initClient();
  }, [config]);

  const sendMessage = useCallback(async (content: string): Promise<MessageResponse | null> => {
    if (!client) return null;

    setLoading(true);
    setError(null);

    try {
      const response = await client.sendMessage(content);

      // Add messages to local state
      setMessages(prev => [
        ...prev,
        response.user_message,
        response.agent_message,
      ]);

      return response;
    } catch (err) {
      setError(err as Error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [client]);

  const refreshMessages = useCallback(async () => {
    if (!client) return;
    const msgs = await client.getMessages();
    setMessages(msgs);
  }, [client]);

  return { sendMessage, messages, loading, error, refreshMessages };
}
*/

// ============================================================================
// Vue Composable Example
// ============================================================================

/**
 * Vue 3 composable for using Anvil Chat API
 *
 * Usage:
 *   const { sendMessage, messages, loading, error } = useAnvilChat(config);
 *   const response = await sendMessage("Show me DeFi protocols");
 */

/*
import { ref, onMounted, Ref } from 'vue';

export function useAnvilChat(config: ChatConfig) {
  const client: Ref<AnvilChatClient | null> = ref(null);
  const messages: Ref<Message[]> = ref([]);
  const loading: Ref<boolean> = ref(false);
  const error: Ref<Error | null> = ref(null);

  onMounted(async () => {
    client.value = new AnvilChatClient(config);
    await client.value.login();
    await client.value.createConversation();
  });

  const sendMessage = async (content: string): Promise<MessageResponse | null> => {
    if (!client.value) return null;

    loading.value = true;
    error.value = null;

    try {
      const response = await client.value.sendMessage(content);

      messages.value.push(response.user_message, response.agent_message);

      return response;
    } catch (err) {
      error.value = err as Error;
      return null;
    } finally {
      loading.value = false;
    }
  };

  const refreshMessages = async () => {
    if (!client.value) return;
    messages.value = await client.value.getMessages();
  };

  return { sendMessage, messages, loading, error, refreshMessages };
}
*/

export { AnvilChatClient, printResponseSummary, saveConversationHistory };
export type { ChatConfig, LoginResponse, ConversationResponse, MessageResponse, Message };
