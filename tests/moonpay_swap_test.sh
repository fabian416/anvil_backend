#!/bin/bash
echo "🚀 === MOONPAY SWAPS V4 QUOTE TEST ==="
API_KEY="pk_test_O4n4ZPtiXBbu..."  # Tu API key
PAIR="eth-btc"
AMOUNT="0.4"

echo "📊 Pair: $PAIR | Amount: $AMOUNT ETH"

echo "📥 PASO 1: Obteniendo quote..."
QUOTE_RESPONSE=$(curl -s "https://api-sandbox.moonpay.com/v4/swap/$PAIR/quote?apiKey=$API_KEY&baseCurrencyAmount=$AMOUNT")

QUOTE_ID=$(echo $QUOTE_RESPONSE | jq -r '.id')
QUOTE_AMOUNT=$(echo $QUOTE_RESPONSE | jq -r '.quoteCurrencyAmount')
EXPIRES=$(echo $QUOTE_RESPONSE | jq -r '.expiresAt')

echo "✅ Quote ID: $QUOTE_ID"
echo "💰 Recibes: $QUOTE_AMOUNT BTC"
echo "⏰ Expira: $EXPIRES"
echo ""
echo "⚠️  PASO BLOQUEADO: Execute requiere KYC via SDK widget"
echo "🎉 Quote OK - Usa MoonPaySwapsCustomerSetupWidget primero"
echo "📋 Quote ID para debug: $QUOTE_ID"
