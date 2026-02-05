Withdraw Hyperliquid → Base USDC (API Wallet NO puede)
CRÍTICO: API Wallet NO tiene permisos de withdraw. Solo puede trading + transfers internos. Para sacar fondos → Privy Master Wallet firma directo.

🔄 Flujo Completo: Spot → Perps → Arbitrum → Base
text
✅ **API Wallet**: Spot trading + Perps→Spot transfers
❌ **API Wallet NO**: Withdraw L1 (solo master wallet)
✅ **Privy Master**: Firma withdraw final
📋 Pasos Preciso (Tu App)
1. Preparar Fondos (API Wallet - Automático)
javascript
// Backend ejecuta (ya tienes API key)
await hyperliquidAPI.exchange({
  privateKey: vault.get(`hyperliquid/api/${userId}`),
  action: {
    type: 'spotSwap',     // PURR → USDC
    coin: 'USDC',
    sz: amount
  }
});

await hyperliquidAPI.exchange({
  action: {
    type: 'spotTransfer', // Spot → Perps
    coin: 'USDC',
    size: amount,
    toPerps: true
  }
});
2. Withdraw L1 (Privy Firma - Manual)
jsx
function WithdrawToBaseButton({ userId, amount }) {
  const { sendTransaction } = usePrivy();
  
  const withdrawToArbitrum = async () => {
    // PASO 1: Backend confirma fondos en Perps
    await fetch('/api/hyperliquid/prepare-withdraw', {
      method: 'POST',
      body: JSON.stringify({ userId, amount })
    });
    
    // PASO 2: Privy firma withdraw (Hyperliquid web signature)
    const withdrawRequest = {
      type: 'hyperliquid_withdraw',
      destination: user.privyAddress, // Arbitrum address
      amount,
      nonce: Date.now()
    };
    
    // HYPERLIQUID REQUIERE EIP-712 signature del MASTER wallet
    const signature = await user.wallet.signTypedData(withdrawRequest);
    
    // PASO 3: Backend envía signed request
    const result = await fetch('/api/hyperliquid/submit-withdraw', {
      method: 'POST',
      body: JSON.stringify({ 
        signature, 
        userId, 
        destination: user.privyAddress,
        amount 
      })
    });
  };
  
  return <Button>Withdraw {amount} USDC → Base</Button>;
}
3. Arbitrum → Base (Privy Normal)
jsx
// Después de 15min, USDC llega Arbitrum
// Bridge normal BaseBridge o Across
await privy.sendTransaction({
  to: BASE_BRIDGE_CONTRACT,
  data: bridgeData,
  value: 0
});
⏱️ Timeline Usuario
text
1. "Withdraw 100 USDC → Base"
2. [Auto] Backend: Spot→USDC→Perps (3s)
3. [Privy Modal] Firma withdraw L1 (2s)  
4. ⏳ 15min processing → USDC Arbitrum
5. [Privy Modal] Bridge Arbitrum→Base (2s)
6. ⏳ 5min → USDC Base wallet
✅ UX en Tu Chat Agent
text
User: "Quiero retirar 100 USDC a Base"
Agent: "Ruta completa:
1️⃣ [Auto] Preparar USDC Perps ✅
2️⃣ [Firma Privy] Withdraw Arbitrum
3️⃣ [Auto] Bridge Base (15min después)"

[Firma Button] → "¡Enviado! Trackea en 15min"
🔒 ¿Por qué API Wallet NO puede withdraw?
text
**Seguridad Hyperliquid**:
✅ API Wallet = "trading permissions only"
✅ Master Wallet = "withdraw permissions only" 
✅ Doble firma = máxima seguridad
✅ Si API key leak → solo grief-trading
🚀 Backend Final
javascript
// /api/hyperliquid/submit-withdraw
app.post('/api/hyperliquid/submit-withdraw', async (req, res) => {
  const { signature, destination, amount } = req.body;
  
  // Verify signature del MASTER wallet
  const isValid = await verifyHyperliquidSignature(signature, destination);
  if (!isValid) throw new Error('Invalid signature');
  
  // Submit a Hyperliquid API
  const result = await fetch('https://api.hyperliquid.xyz/exchange', {
    method: 'POST',
    body: JSON.stringify({
      action: { type: 'withdrawL1', destination, amount },
      signature
    })
  });
  
  res.json(result);
});
API Wallet = trading engine. Withdraw = Privy Master firma. 2 pasos UX perfecta. 15min Arbitrum → 5min Base.