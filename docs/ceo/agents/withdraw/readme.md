# 🔧 Hyperliquid ↔ Privy — Withdraw Agent & Position Sync

## Slack Update para Tech Group

---

### 📍 Status Actual

USDC está en **Perps balance** de Hyperliquid (normal post-bridge). Sin el agente de withdraw, los usuarios no pueden hacer swaps porque los fondos quedan atrapados en Perps sin ruta automática hacia Privy.

### 🎯 Solución Propuesta

Dos componentes nuevos:

1. **HyperliquidWithdrawAgent** — Agente que mueve fondos de Hyperliquid (Perps/Spot) → Privy wallet
2. **Celery Position Sync Worker** — Background task que monitorea posiciones, balances y tokens disponibles entre Privy ↔ Hyperliquid

---

## Roadmap de Ejecución

### Fase 1: Hyperliquid Client Core (2 días)

**Día 1 — HyperliquidClient base**

```
src/app/infrastructure/clients/hyperliquid/
├── __init__.py
├── client.py              # HyperliquidClient (Info + Exchange API)
├── models.py              # PerpsState, SpotState, TransferResult
├── constants.py           # API URLs, supported tokens
└── exceptions.py          # HyperliquidAPIError, InsufficientBalance
```

Scope:
- `GET userState` — Query balances Perps + Spot
- `POST spotTransfer` — Internal transfer Perps → Spot
- `POST withdraw` — Withdraw from Spot → Arbitrum L1
- Error handling con retry (3 retries, exponential backoff)
- Rate limiting: 1200 req/min info, 100 req/min exchange

**Día 2 — Tests + Integration**
- Unit tests con mocks de Hyperliquid API
- Integration test contra testnet
- Validación de firma (Hyperliquid usa EIP-712)

---

### Fase 2: Withdraw Agent (2 días)

**Día 3 — WithdrawAgent implementation**

```
src/app/infrastructure/agents/hyperliquid_withdraw_agent.py
src/app/application/chat/handlers/hyperliquid_handler.py
```

Flow del agente:

```
User: "Withdraw 10 USDC to my wallet"
│
├─ 1. Query Hyperliquid balances (Perps + Spot)
│   └─ API: POST /info { type: "userState" }
│
├─ 2. Si funds en Perps → Transfer interno Perps → Spot
│   └─ API: POST /exchange { type: "spotTransfer" }
│   └─ Tiempo: ~2 segundos, gas: 0
│
├─ 3. Withdraw Spot → Arbitrum (Privy wallet address)
│   └─ API: POST /exchange { type: "withdraw3" }
│   └─ Tiempo: 10-30 min
│
├─ 4. (Opcional) Bridge Arbitrum → Base via LiFi
│   └─ Usa LiFiClient existente
│   └─ Tiempo: ~5 min
│
└─ 5. Log transaction + Notify user
    └─ WebSocket update con status
```

Integration con SwapHandler existente:

```python
class SwapHandler:
    """
    Swap routing per CEO spec:
    - Same-chain: Uses 1inch (best rates)
    - Cross-chain: Uses LiFi
    - Perps: Uses Hyperliquid  ← EXTEND THIS
    """
    
    async def handle_hyperliquid_withdraw(
        self,
        user_wallet: str,       # Privy wallet address
        amount: Decimal,
        token: str = "USDC",
        target_chain: str = "arbitrum",  # or "base"
    ) -> WithdrawResult:
        # 1. Check balances
        state = await self._hyperliquid.get_user_state(hl_wallet)
        
        perps_balance = Decimal(state.perps.account_value)
        spot_balance = Decimal(state.spot.get("USDC", "0"))
        
        total_available = perps_balance + spot_balance
        if total_available < amount:
            raise InsufficientBalance(available=total_available, requested=amount)
        
        # 2. Move from Perps to Spot if needed
        if spot_balance < amount:
            transfer_amount = amount - spot_balance
            await self._hyperliquid.spot_transfer(
                coin="USDC",
                amount=str(transfer_amount),
                direction="perps_to_spot"
            )
        
        # 3. Withdraw to Arbitrum
        withdraw_tx = await self._hyperliquid.withdraw(
            destination=user_wallet,
            amount=str(amount),
            token="USDC"
        )
        
        # 4. Optional: Bridge to target chain
        if target_chain != "arbitrum":
            bridge_tx = await self._lifi.bridge(
                from_chain="arbitrum",
                to_chain=target_chain,
                token="USDC",
                amount=str(amount),
                to_address=user_wallet
            )
        
        return WithdrawResult(
            status="processing",
            tx_hash=withdraw_tx.hash,
            estimated_time_minutes=30,
            from_balance="perps" if perps_balance > 0 else "spot",
            target_chain=target_chain,
        )
```

**Día 4 — ExecuteAction integration + Intent detection**

Agregar `hyperliquid_withdraw` como nueva acción en ExecuteActionCommand:

```python
# execute_action.py - Add to routing
├── Step 4: Action Routing
│   ├── swap → _handle_swap()
│   ├── deposit → _handle_deposit()
│   ├── withdraw → _handle_withdraw()
│   ├── transfer → _handle_transfer()
│   ├── approve → _handle_approve()
│   ├── bridge → _handle_bridge()
│   └── hyperliquid_withdraw → _handle_hyperliquid_withdraw()  # NEW
```

Intent detection keywords:
- "withdraw from hyperliquid"
- "move usdc from perps"
- "transfer from hyperliquid to wallet"
- "sacar plata de hyperliquid"

---

### Fase 3: Celery Position Sync (2 días)

**Día 5 — Position Monitor Tasks**

```
src/app/infrastructure/celery/tasks/hyperliquid_tasks.py
```

#### Task 1: Sync Hyperliquid Positions (cada 60s)

```python
@celery_app.task(
    name="hyperliquid.sync_positions",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def sync_hyperliquid_positions(self, limit: int = 100):
    """
    Sync Hyperliquid positions for all active users.
    
    1. Get all users with Hyperliquid wallets linked
    2. Query Hyperliquid API for each wallet
    3. Update local DB with current positions
    4. Detect changes and log events
    """
    async def runner(container):
        hl_client = await container.get(HyperliquidClient)
        wallet_repo = await container.get(WalletRepository)
        position_repo = await container.get(HyperliquidPositionRepository)
        
        # Get wallets with Hyperliquid integration
        wallets = await wallet_repo.get_by_provider(
            provider="hyperliquid", limit=limit
        )
        
        results = {"synced": 0, "errors": 0, "positions_updated": 0}
        
        for wallet in wallets:
            try:
                # Query Hyperliquid
                state = await hl_client.get_user_state(wallet.address)
                
                # Update positions
                await position_repo.upsert_positions(
                    wallet_id=wallet.id,
                    perps_balance=state.perps.account_value,
                    spot_balances=state.spot.balances,
                    open_positions=state.perps.asset_positions,
                    updated_at=datetime.utcnow(),
                )
                
                results["synced"] += 1
                results["positions_updated"] += len(state.perps.asset_positions)
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"Failed to sync {wallet.address}: {e}")
        
        return results
    
    return asyncio.run(_run_task(runner))


# Schedule: Every 60 seconds
celery_app.conf.beat_schedule["hyperliquid-sync-positions"] = {
    "task": "hyperliquid.sync_positions",
    "schedule": 60.0,
}
```

#### Task 2: Monitor Withdraw Status (cada 30s)

```python
@celery_app.task(name="hyperliquid.check_withdrawals")
def check_pending_withdrawals(self):
    """
    Check status of pending Hyperliquid withdrawals.
    
    1. Query DB for pending withdrawals
    2. Check Arbitrum RPC for transaction confirmation
    3. Update status: processing → confirmed → bridging → complete
    4. Notify user via WebSocket when complete
    """
    async def runner(container):
        tx_repo = await container.get(TransactionRepository)
        rpc = await container.get(ArbitrumRPCClient)
        ws_manager = await container.get(WebSocketManager)
        
        pending = await tx_repo.get_pending_withdrawals(
            provider="hyperliquid",
            older_than_seconds=30
        )
        
        for tx in pending:
            receipt = await rpc.get_transaction_receipt(tx.tx_hash)
            
            if receipt and receipt.status == 1:
                await tx_repo.update_status(
                    tx_id=tx.id,
                    status="confirmed",
                    block_number=receipt.block_number,
                    confirmed_at=datetime.utcnow(),
                )
                
                # Notify user
                await ws_manager.send_to_user(
                    user_id=tx.user_id,
                    event="withdrawal_confirmed",
                    data={"tx_hash": tx.tx_hash, "amount": tx.amount}
                )
        
        return {"checked": len(pending)}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["hyperliquid-check-withdrawals"] = {
    "task": "hyperliquid.check_withdrawals",
    "schedule": 30.0,
}
```

#### Task 3: Token Availability Snapshot (cada 5 min)

```python
@celery_app.task(name="hyperliquid.token_snapshot")
def snapshot_available_tokens(self):
    """
    Snapshot available tokens across Privy + Hyperliquid.
    
    For each user:
    1. Get Privy wallet balances (Arbitrum, Base, Ethereum)
    2. Get Hyperliquid balances (Perps + Spot)
    3. Build unified token availability map
    4. Store in Redis for fast access by agents
    """
    async def runner(container):
        wallet_repo = await container.get(WalletRepository)
        hl_client = await container.get(HyperliquidClient)
        rpc_client = await container.get(MultiChainRPCClient)
        redis = await container.get(Redis)
        
        users = await wallet_repo.get_active_users_with_wallets()
        
        for user in users:
            token_map = {
                "privy": {},
                "hyperliquid": {"perps": {}, "spot": {}},
                "total_usd": Decimal("0"),
                "swappable_tokens": [],
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            # Privy balances per chain
            for chain in ["arbitrum", "base", "ethereum"]:
                balances = await rpc_client.get_token_balances(
                    address=user.privy_address,
                    chain=chain
                )
                token_map["privy"][chain] = balances
            
            # Hyperliquid balances
            if user.hyperliquid_address:
                state = await hl_client.get_user_state(user.hyperliquid_address)
                token_map["hyperliquid"]["perps"] = {
                    "USDC": state.perps.account_value
                }
                token_map["hyperliquid"]["spot"] = state.spot.balances
            
            # Build swappable list
            for chain, balances in token_map["privy"].items():
                for token, amount in balances.items():
                    if Decimal(amount) > 0:
                        token_map["swappable_tokens"].append({
                            "token": token,
                            "chain": chain,
                            "amount": amount,
                            "source": "privy"
                        })
            
            # Cache in Redis (TTL 10 min)
            await redis.setex(
                f"token_availability:{user.id}",
                600,
                json.dumps(token_map, default=str)
            )
        
        return {"users_processed": len(users)}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["hyperliquid-token-snapshot"] = {
    "task": "hyperliquid.token_snapshot",
    "schedule": crontab(minute="*/5"),
}
```

**Día 6 — DB Models + Repository**

```python
# New model: hyperliquid_positions
class HyperliquidPosition(Base):
    __tablename__ = "hyperliquid_positions"

    id: Mapped[UUID]            # PK
    user_id: Mapped[UUID]       # FK → users
    wallet_address: Mapped[str] # Hyperliquid wallet
    
    # Balances
    perps_equity: Mapped[Decimal]
    perps_margin_used: Mapped[Decimal]
    spot_balances: Mapped[dict]  # JSONB {"USDC": "10.0", "ETH": "0.5"}
    
    # Open Positions
    open_positions: Mapped[dict] # JSONB [{symbol, size, entry_px, unrealized_pnl}]
    position_count: Mapped[int]
    
    # Withdraw tracking
    pending_withdrawals: Mapped[dict] # JSONB [{tx_hash, amount, status, initiated_at}]
    last_withdrawal_at: Mapped[datetime | None]
    
    # Sync
    last_synced_at: Mapped[datetime]
    sync_errors: Mapped[int]
    
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

---

## Tiempos de Ejecución

| Fase | Scope | Días | Blocker? |
|------|-------|------|----------|
| **Fase 1** | HyperliquidClient (Info + Exchange API) | 2 días | ✅ Desbloquea todo |
| **Fase 2** | WithdrawAgent + ExecuteAction integration | 2 días | ✅ Habilita swaps |
| **Fase 3** | Celery tasks (position sync, withdrawals, tokens) | 2 días | ❌ Puede ir en paralelo |
| **Total** | | **5-6 días** | |

### Dependencias

| Item | Status | Nota |
|------|--------|------|
| Hyperliquid API Key | ⚠️ Pendiente | Necesario para Exchange API (EIP-712 signing) |
| Wallet address mapping | ⚠️ Definir | ¿Se linkea HL wallet al user o usamos Privy address directo? |
| LiFi bridge (Arb→Base) | ✅ Existe | Ya implementado en `LiFiClient` |
| Celery + Redis | ✅ Existe | Infraestructura lista |
| Transaction logging | ✅ Existe | `TransactionRepository` + confirmation worker |

### Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Hyperliquid withdraw delay (30min) | UX | Notificación proactiva + status tracking |
| EIP-712 signing desde backend | Seguridad | Vault/KMS para private keys, nunca en .env |
| Rate limits Hyperliquid (1200/min) | Escalabilidad | Queue con backoff, batch sync |
| Bridge failure Arb→Base | Fondos stuck | Retry automático + manual fallback alert |

---

## Mensaje Sugerido para Slack Tech Group

```
🔧 Hyperliquid Withdraw Agent — Roadmap

Problema: USDC queda en Perps balance de Hyperliquid post-bridge.
Sin agente de withdraw, los swaps están bloqueados.

Solución: 2 componentes nuevos
1. WithdrawAgent: Perps → Spot → Arbitrum → Privy (automático)
2. Celery Position Sync: Monitor de balances HL ↔ Privy cada 60s

Timeline:
- Fase 1 (2d): HyperliquidClient base — DESBLOQUEA swaps
- Fase 2 (2d): WithdrawAgent + integration con ExecuteAction
- Fase 3 (2d): Celery workers para sync y monitoring
- Total: 5-6 días hábiles

Dependencias que necesito:
⚠️ Hyperliquid API Key / wallet signing strategy
⚠️ Definir: ¿wallet mapping HL ↔ Privy por user?

¿Quién puede validar la strategy de signing? 
Necesito 30min para alinear antes de arrancar.
```

---

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYPERLIQUID ↔ PRIVY FLOW                      │
└─────────────────────────────────────────────────────────────────┘

  User: "Withdraw 10 USDC"
           │
           ▼
  ┌─────────────────┐
  │  Intent Detect   │  → HYPERLIQUID_WITHDRAW
  │  (LLM/Keywords)  │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────┐     ┌──────────────────────────────────┐
  │  SwapHandler     │────►│  HyperliquidClient               │
  │  (extended)      │     │                                   │
  └────────┬─────────┘     │  1. GET userState (balances)      │
           │               │  2. POST spotTransfer (perps→spot)│
           │               │  3. POST withdraw3 (spot→arb)     │
           │               └──────────────────────────────────┘
           │
           ▼
  ┌─────────────────┐     ┌──────────────────────────────────┐
  │  LiFi Bridge     │────►│  Arbitrum → Base                  │
  │  (existing)      │     │  (if target_chain != arbitrum)    │
  └────────┬─────────┘     └──────────────────────────────────┘
           │
           ▼
  ┌─────────────────┐
  │  Privy Wallet    │  ← USDC available for swaps ✅
  │  (Base/Arb)      │
  └──────────────────┘


  ┌─────────────────────────────────────────────────────────────┐
  │                 CELERY BACKGROUND TASKS                      │
  ├─────────────────────────────────────────────────────────────┤
  │                                                              │
  │  ⏰ Every 60s:  sync_hyperliquid_positions                   │
  │     → Query HL API → Update DB → Detect changes             │
  │                                                              │
  │  ⏰ Every 30s:  check_pending_withdrawals                    │
  │     → Check Arbitrum RPC → Update tx status → Notify user   │
  │                                                              │
  │  ⏰ Every 5min: snapshot_available_tokens                    │
  │     → Privy balances + HL balances → Redis cache             │
  │     → Agents use this for "what can I swap?" queries        │
  │                                                              │
  └─────────────────────────────────────────────────────────────┘
```