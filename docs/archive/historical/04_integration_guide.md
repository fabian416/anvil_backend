# 🔌 Anvil Platform - External Integrations Guide

## Third-Party Services Integration Documentation

**Version:** 1.0  
**Date:** November 2025  
**Audience:** Development Team

---

## 📋 Integration Overview

| Service | Purpose | Priority | Complexity |
|---------|---------|----------|------------|
| Privy | Wallet & Auth | Critical | Medium |
| Stripe | Payments | Critical | Medium |
| 1inch | DEX Aggregation | Critical | Low |
| Aave | Yield Farming | High | High |
| Compound | Yield Farming | High | High |
| Hyperliquid | Perpetual Trading | High | Medium |
| Vertex AI | AI Chat | High | Low |
| Alchemy | Blockchain RPC | Critical | Low |
| SendGrid | Email | Medium | Low |
| Twilio | SMS | Low | Low |
| Firebase FCM | Push Notifications | High | Low |
| Persona/Onfido | KYC | Medium | Medium |

---

## 🔐 1. Privy Integration

### Purpose
- Embedded wallet creation
- User authentication
- Transaction signing

### Setup

**Install SDK:**
```bash
pip install privy-py-sdk
```

**Configuration:**
```python
# app/integrations/privy.py
import httpx
from app.config import settings

class PrivyClient:
    def __init__(self):
        self.app_id = settings.PRIVY_APP_ID
        self.app_secret = settings.PRIVY_APP_SECRET
        self.base_url = "https://auth.privy.io"
        
    async def verify_token(self, token: str) -> dict:
        """Verify Privy auth token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/users/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "privy-app-id": self.app_id
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def create_wallet(self, user_id: str) -> dict:
        """Create embedded wallet for user"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/wallets",
                headers={
                    "Authorization": f"Bearer {self.app_secret}",
                    "privy-app-id": self.app_id
                },
                json={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()
```

### Mobile Integration (React Native)

```typescript
// Mobile app
import { PrivyProvider, usePrivy } from '@privy-io/react-native';

function App() {
  return (
    <PrivyProvider appId="YOUR_APP_ID">
      <AuthScreen />
    </PrivyProvider>
  );
}

function AuthScreen() {
  const { login, user } = usePrivy();
  
  const handleLogin = async () => {
    await login();
    // Send token to backend
    const token = user.token;
    await loginToBackend(token);
  };
}
```

### Key Endpoints
- **Verify User**: `GET /api/v1/users/me`
- **Create Wallet**: `POST /api/v1/wallets`
- **Sign Transaction**: `POST /api/v1/wallets/{id}/sign`

### Error Handling
```python
try:
    user_data = await privy_client.verify_token(token)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        raise HTTPException(401, "Invalid Privy token")
    raise HTTPException(500, "Privy service error")
```

---

## 💳 2. Stripe Integration

### Purpose
- Fiat to crypto payments
- Subscription billing
- Refund processing

### Setup

**Install SDK:**
```bash
pip install stripe==7.4.0
```

**Configuration:**
```python
# app/integrations/stripe.py
import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeClient:
    @staticmethod
    async def create_payment_intent(
        amount: float,
        currency: str = "usd",
        customer_id: str = None
    ) -> dict:
        """Create payment intent for fiat purchase"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                customer=customer_id,
                metadata={
                    "type": "crypto_purchase"
                }
            )
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    async def create_subscription(
        customer_id: str,
        price_id: str,
        trial_days: int = 7
    ) -> dict:
        """Create subscription"""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_days,
            metadata={"plan": "pro"}
        )
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end
        }
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> dict:
        """Cancel subscription at period end"""
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return {"status": subscription.status}
```

### Webhook Handling
```python
# app/api/v1/routes/webhooks.py
from fastapi import Request, HTTPException
import stripe

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    
    # Handle events
    if event.type == "invoice.payment_succeeded":
        await handle_payment_succeeded(event.data.object)
    elif event.type == "invoice.payment_failed":
        await handle_payment_failed(event.data.object)
    elif event.type == "customer.subscription.deleted":
        await handle_subscription_cancelled(event.data.object)
    
    return {"status": "success"}
```

### Mobile Integration (React Native)
```typescript
import { useStripe } from '@stripe/stripe-react-native';

function PaymentScreen() {
  const { confirmPayment } = useStripe();
  
  const handlePayment = async () => {
    // Get client secret from backend
    const { clientSecret } = await api.createPaymentIntent(amount);
    
    // Confirm payment
    const { error, paymentIntent } = await confirmPayment(clientSecret, {
      paymentMethodType: 'Card',
    });
    
    if (error) {
      // Handle error
    } else if (paymentIntent) {
      // Payment successful
    }
  };
}
```

---

## 🔄 3. 1inch DEX Aggregator Integration

### Purpose
- Get best swap rates
- Execute token swaps
- Route optimization

### Setup

```python
# app/integrations/oneinch.py
import httpx
from app.config import settings

class OneInchClient:
    def __init__(self, chain_id: int = 42161):  # Arbitrum
        self.chain_id = chain_id
        self.base_url = f"https://api.1inch.dev/swap/v5.2/{chain_id}"
        self.api_key = settings.ONEINCH_API_KEY
        
    async def get_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 0.5
    ) -> dict:
        """Get swap quote"""
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "includeGas": "true"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quote",
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_swap_data(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 0.5
    ) -> dict:
        """Get swap transaction data"""
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": from_address,
            "slippage": slippage,
            "disableEstimate": "false"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/swap",
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "to": data["tx"]["to"],
                "data": data["tx"]["data"],
                "value": data["tx"]["value"],
                "gas": data["tx"]["gas"],
                "to_amount": data["toAmount"]
            }
```

### Token Addresses (Arbitrum)
```python
ARBITRUM_TOKENS = {
    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
}
```

---

## 🌾 4. Aave V3 Integration

### Purpose
- Deposit tokens for yield
- Withdraw with interest
- Query APY rates

### Setup

```python
# app/blockchain/contracts/aave.py
from web3 import Web3
from eth_typing import Address
import json

class AaveClient:
    def __init__(self, w3: Web3, chain: str = "arbitrum"):
        self.w3 = w3
        self.chain = chain
        
        # Contract addresses (Arbitrum)
        if chain == "arbitrum":
            self.pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
            self.pool_data_provider = "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
        
        # Load ABIs
        with open("abis/aave_pool.json") as f:
            pool_abi = json.load(f)
        
        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address,
            abi=pool_abi
        )
    
    async def get_apy(self, asset: Address) -> float:
        """Get current supply APY for asset"""
        reserve_data = self.pool_contract.functions.getReserveData(asset).call()
        liquidity_rate = reserve_data[3]  # liquidityRate
        
        # Convert from ray (27 decimals) to percentage
        apy = (liquidity_rate / 10**27) * 100
        return apy
    
    def build_deposit_tx(
        self,
        asset: Address,
        amount: int,
        on_behalf_of: Address
    ) -> dict:
        """Build deposit transaction"""
        tx = self.pool_contract.functions.supply(
            asset,
            amount,
            on_behalf_of,
            0  # referralCode
        ).build_transaction({
            "from": on_behalf_of,
            "gas": 300000,
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            "nonce": self.w3.eth.get_transaction_count(on_behalf_of),
        })
        return tx
    
    def build_withdraw_tx(
        self,
        asset: Address,
        amount: int,
        to: Address
    ) -> dict:
        """Build withdraw transaction"""
        tx = self.pool_contract.functions.withdraw(
            asset,
            amount,  # Use type(uint256).max for full amount
            to
        ).build_transaction({
            "from": to,
            "gas": 300000,
            "maxFeePerGas": self.w3.eth.gas_price,
            "maxPriorityFeePerGas": self.w3.eth.max_priority_fee,
            "nonce": self.w3.eth.get_transaction_count(to),
        })
        return tx
```

### Service Layer Integration
```python
# app/services/earn_service.py
from app.blockchain.contracts.aave import AaveClient

class EarnService:
    async def deposit_to_aave(
        self,
        user_id: int,
        asset: str,
        amount: Decimal,
        chain: str = "arbitrum"
    ):
        # Get user wallet
        wallet = await self.get_user_wallet(user_id)
        
        # Build transaction
        aave = AaveClient(self.w3, chain)
        tx = aave.build_deposit_tx(
            asset=TOKEN_ADDRESSES[asset],
            amount=int(amount * 10**18),
            on_behalf_of=wallet.address
        )
        
        # Sign and submit via Privy
        signed_tx = await self.privy.sign_transaction(wallet.privy_wallet_id, tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        
        # Create position record
        position = EarnPosition(
            user_id=user_id,
            wallet_id=wallet.id,
            chain=chain,
            protocol="aave",
            asset=asset,
            amount_deposited=amount,
            deposit_tx_hash=tx_hash.hex(),
            status="pending"
        )
        self.db.add(position)
        self.db.commit()
        
        return position
```

---

## 🔗 5. Hyperliquid API Integration

### Purpose
- Open/close perpetual positions
- Get market data
- Monitor positions

### Setup

```python
# app/integrations/hyperliquid.py
import httpx
from typing import List, Dict

class HyperliquidClient:
    def __init__(self):
        self.base_url = "https://api.hyperliquid.xyz"
        
    async def get_market_data(self, symbol: str) -> dict:
        """Get market data for symbol"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/info",
                json={"type": "meta"}
            )
            data = response.json()
            
            # Find symbol
            for market in data["universe"]:
                if market["name"] == symbol:
                    return market
            
            raise ValueError(f"Symbol {symbol} not found")
    
    async def place_order(
        self,
        user_address: str,
        symbol: str,
        is_buy: bool,
        size: float,
        price: float,
        leverage: int,
        signature: str
    ) -> dict:
        """Place order"""
        order = {
            "type": "order",
            "orders": [{
                "asset": symbol,
                "isBuy": is_buy,
                "limitPx": str(price),
                "sz": str(size),
                "reduceOnly": False,
                "orderType": {"limit": {"tif": "Gtc"}}
            }],
            "grouping": "na"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/exchange",
                json={
                    "action": order,
                    "signature": signature,
                    "vaultAddress": None
                },
                headers={
                    "Content-Type": "application/json"
                }
            )
            return response.json()
    
    async def get_user_positions(self, address: str) -> List[dict]:
        """Get user's open positions"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/info",
                json={
                    "type": "clearinghouseState",
                    "user": address
                }
            )
            data = response.json()
            return data.get("assetPositions", [])
```

---

## 🤖 6. Google Vertex AI Integration

### Purpose
- AI chat conversations
- Portfolio analysis
- Trading recommendations

### Setup

```python
# app/integrations/vertex_ai.py
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
from app.config import settings

class VertexAIClient:
    def __init__(self):
        aiplatform.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION
        )
        self.model = GenerativeModel(settings.VERTEX_AI_MODEL)
    
    async def generate_response(
        self,
        prompt: str,
        context: dict = None,
        max_tokens: int = 1000
    ) -> dict:
        """Generate AI response"""
        # Add context to prompt
        if context:
            prompt = f"Context: {json.dumps(context)}\n\nUser: {prompt}"
        
        # Generate
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        )
        
        # Extract metrics
        usage = response.usage_metadata
        
        return {
            "response": response.text,
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "total_tokens": usage.total_token_count
        }
```

---

## 📧 7. SendGrid Email Integration

### Purpose
- Transactional emails
- Notifications
- Reports

### Setup

```python
# app/integrations/sendgrid.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings

class SendGridClient:
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ):
        """Send email"""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        try:
            response = self.client.send(message)
            return {
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id")
            }
        except Exception as e:
            raise Exception(f"SendGrid error: {str(e)}")
    
    async def send_template_email(
        self,
        to_email: str,
        template_id: str,
        dynamic_data: dict
    ):
        """Send templated email"""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email
        )
        message.template_id = template_id
        message.dynamic_template_data = dynamic_data
        
        response = self.client.send(message)
        return response
```

### Email Templates
```python
TEMPLATES = {
    "welcome": "d-abc123...",
    "kyc_approved": "d-def456...",
    "transaction_confirmed": "d-ghi789...",
    "subscription_renewed": "d-jkl012...",
}
```

---

## 📱 8. Firebase Cloud Messaging

### Purpose
- Push notifications to mobile apps

### Setup

```python
# app/integrations/firebase.py
import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings

# Initialize
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

class FirebaseClient:
    @staticmethod
    async def send_notification(
        device_token: str,
        title: str,
        body: str,
        data: dict = None
    ):
        """Send push notification"""
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=device_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default"
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default"
                    )
                )
            )
        )
        
        response = messaging.send(message)
        return {"message_id": response}
```

---

## 🔗 9. Alchemy RPC Integration

### Purpose
- Blockchain RPC calls
- Transaction monitoring
- Event subscriptions

### Setup

```python
# app/blockchain/web3_client.py
from web3 import Web3
from app.config import settings

class Web3Client:
    def __init__(self, chain: str = "arbitrum"):
        if chain == "arbitrum":
            rpc_url = settings.ARBITRUM_RPC_URL
        elif chain == "base":
            rpc_url = settings.BASE_RPC_URL
        else:
            raise ValueError(f"Unsupported chain: {chain}")
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain = chain
    
    async def get_balance(self, address: str) -> int:
        """Get native token balance"""
        return self.w3.eth.get_balance(address)
    
    async def get_transaction(self, tx_hash: str) -> dict:
        """Get transaction details"""
        return self.w3.eth.get_transaction(tx_hash)
    
    async def wait_for_receipt(self, tx_hash: str, timeout: int = 120):
        """Wait for transaction receipt"""
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout)
```

---

## 🔒 Security Best Practices

### API Key Management
```python
# Never hardcode
❌ api_key = "sk_test_abc123"

# Use environment variables
✅ api_key = os.getenv("STRIPE_SECRET_KEY")

# Or use config
✅ api_key = settings.STRIPE_SECRET_KEY
```

### Error Handling
```python
try:
    result = await external_api_call()
except httpx.HTTPStatusError as e:
    logger.error(f"API error: {e.response.status_code}")
    # Don't expose internal errors to user
    raise HTTPException(500, "External service error")
except httpx.TimeoutException:
    raise HTTPException(504, "Service timeout")
```

### Rate Limiting
```python
from time import sleep
from functools import wraps

def rate_limit(calls: int, period: int):
    """Rate limit decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Implement rate limiting logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls=10, period=60)
async def call_external_api():
    pass
```

---

## 📊 Monitoring & Logging

### Log All API Calls
```python
import structlog

logger = structlog.get_logger()

async def call_external_api(service: str, endpoint: str):
    logger.info(
        "external_api_call",
        service=service,
        endpoint=endpoint
    )
    
    try:
        response = await make_request()
        logger.info(
            "external_api_success",
            service=service,
            status_code=response.status_code
        )
        return response
    except Exception as e:
        logger.error(
            "external_api_error",
            service=service,
            error=str(e)
        )
        raise
```

### Track Costs
```python
# Track AI costs
ai_cost = (input_tokens * 0.00001) + (output_tokens * 0.00003)

# Log to database
await log_ai_usage(
    user_id=user.id,
    model="gemini-1.5-flash",
    tokens=total_tokens,
    cost_usd=ai_cost
)
```

---

## ✅ Integration Checklist

### Pre-Production
- [ ] All API keys stored in environment variables
- [ ] Rate limiting implemented
- [ ] Error handling for all calls
- [ ] Retry logic with exponential backoff
- [ ] Timeouts configured
- [ ] Logging for all external calls
- [ ] Cost tracking for paid services
- [ ] Webhook security verified
- [ ] Test credentials separated from production

### Production
- [ ] Production API keys configured
- [ ] Webhooks registered
- [ ] Monitoring alerts set up
- [ ] Backup providers configured (where applicable)
- [ ] Documentation updated
- [ ] Team trained on integrations

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Ready for Implementation ✅
