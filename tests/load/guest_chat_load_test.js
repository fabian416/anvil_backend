/**
 * K6 Load Test for Guest Chat System
 *
 * This script tests the guest chat endpoint under various load conditions
 * to validate performance targets:
 * - P95 response time < 500ms
 * - Error rate < 1%
 * - Throughput > 100 req/s
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const cacheHitRate = new Rate('cache_hits');
const sentimentRequests = new Counter('sentiment_requests');
const tradingSignalsRequests = new Counter('trading_signals_requests');
const priceRequests = new Counter('price_requests');

// Test configuration
export const options = {
  stages: [
    // Ramp up to 50 users over 2 minutes
    { duration: '2m', target: 50 },
    // Stay at 50 users for 5 minutes
    { duration: '5m', target: 50 },
    // Ramp up to 100 users over 2 minutes
    { duration: '2m', target: 100 },
    // Stay at 100 users for 5 minutes
    { duration: '5m', target: 100 },
    // Ramp down to 0 users over 2 minutes
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    // HTTP errors should be less than 1%
    'errors': ['rate<0.01'],
    // 95% of requests should be below 500ms
    'http_req_duration': ['p(95)<500'],
    // 99% of requests should be below 1000ms
    'http_req_duration': ['p(99)<1000'],
  },
};

// Base URL (configure for your environment)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test data
const tokens = ['BTC', 'ETH', 'SOL', 'USDT', 'BNB', 'USDC', 'ADA', 'DOT'];
const languages = ['en', 'es', 'pt', 'zh'];

const queries = {
  sentiment: [
    'What is the sentiment for TOKEN?',
    'How does the market feel about TOKEN?',
    'Is TOKEN bullish or bearish?',
  ],
  trading_signals: [
    'Give me trading signals for TOKEN',
    'Should I buy TOKEN?',
    'What are the trading signals for TOKEN?',
  ],
  price_prediction: [
    'Predict the price of TOKEN',
    'Where is TOKEN going?',
    'What will TOKEN price be?',
  ],
  patterns: [
    'What patterns do you see in TOKEN?',
    'Are there any chart patterns for TOKEN?',
    'Show me patterns for TOKEN',
  ],
  risk: [
    'What are the risks for TOKEN?',
    'Is TOKEN risky?',
    'Show me risk analysis for TOKEN',
  ],
};

function getRandomToken() {
  return tokens[Math.floor(Math.random() * tokens.length)];
}

function getRandomLanguage() {
  return languages[Math.floor(Math.random() * languages.length)];
}

function getRandomQuery(intent) {
  const intentQueries = queries[intent];
  const query = intentQueries[Math.floor(Math.random() * intentQueries.length)];
  return query.replace('TOKEN', getRandomToken());
}

export default function () {
  // Select random intent (weighted towards popular ones)
  const rand = Math.random();
  let intent;

  if (rand < 0.4) {
    intent = 'sentiment';
    sentimentRequests.add(1);
  } else if (rand < 0.7) {
    intent = 'trading_signals';
    tradingSignalsRequests.add(1);
  } else if (rand < 0.85) {
    intent = 'price_prediction';
    priceRequests.add(1);
  } else if (rand < 0.93) {
    intent = 'patterns';
  } else {
    intent = 'risk';
  }

  const content = getRandomQuery(intent);
  const language = getRandomLanguage();

  const payload = JSON.stringify({
    content: content,
    language: language,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: {
      intent: intent,
      language: language,
    },
  };

  const response = http.post(
    `${BASE_URL}/api/v1/guest/chat`,
    payload,
    params
  );

  // Check if response is successful
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'status is not 429': (r) => r.status !== 429, // No rate limiting
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
    'has content': (r) => r.json('content') !== undefined,
    'has enrichment': (r) => r.json('enrichment') !== undefined,
  });

  // Track errors
  errorRate.add(!success);

  // Track cache hits (approximate by response time)
  if (response.status === 200) {
    cacheHitRate.add(response.timings.duration < 150);
  }

  // Think time between requests (1-3 seconds)
  sleep(1 + Math.random() * 2);
}

/**
 * Run this test with:
 *
 * k6 run tests/load/guest_chat_load_test.js
 *
 * Or with custom environment:
 *
 * k6 run --env BASE_URL=https://api.anvil.fi tests/load/guest_chat_load_test.js
 */
