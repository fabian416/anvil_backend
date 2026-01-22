#!/usr/bin/env python3
"""Test Money Market API connections - Morpho, Aave, Compound, DeFiLlama."""

import asyncio
import sys
sys.path.insert(0, "src")

async def test_morpho():
    """Test Morpho GraphQL API."""
    print("\n" + "="*60)
    print("Testing MORPHO API")
    print("="*60)
    
    from app.infrastructure.adapters.external.morpho_client import MorphoClient, BASE_USDC_ADDRESS
    
    client = MorphoClient()
    try:
        # Test Base USDC vaults
        print("\n📊 Fetching Base USDC vaults (whitelisted)...")
        vaults = await client.get_base_usdc_vaults(whitelisted=True, first=5)
        
        if vaults:
            print(f"✅ Found {len(vaults)} vaults")
            for i, v in enumerate(vaults[:3], 1):
                apy = float(v.net_apy) * 100 if v.net_apy else 0
                print(f"   {i}. {v.name}: {apy:.2f}% APY (TVL: {v.total_assets})")
        else:
            print("⚠️ No vaults found, trying without whitelist filter...")
            vaults = await client.get_base_usdc_vaults(whitelisted=False, first=5)
            if vaults:
                print(f"✅ Found {len(vaults)} vaults (non-whitelisted)")
                for i, v in enumerate(vaults[:3], 1):
                    apy = float(v.net_apy) * 100 if v.net_apy else 0
                    print(f"   {i}. {v.name}: {apy:.2f}% APY")
            else:
                print("❌ No vaults found")
        
        # Test Ethereum vaults
        print("\n📊 Fetching Ethereum USDC vaults...")
        eth_vaults = await client.get_vaults(chain_id=1, whitelisted=True, first=3)
        if eth_vaults:
            print(f"✅ Found {len(eth_vaults)} Ethereum vaults")
            for v in eth_vaults[:2]:
                apy = float(v.net_apy) * 100 if v.net_apy else 0
                print(f"   - {v.name}: {apy:.2f}% APY")
        
    except Exception as e:
        print(f"❌ Morpho error: {e}")
    finally:
        await client.close()


async def test_compound():
    """Test Compound V3 RPC calls."""
    print("\n" + "="*60)
    print("Testing COMPOUND V3 API")
    print("="*60)
    
    from app.infrastructure.adapters.external.compound_client import CompoundClient
    
    client = CompoundClient()
    try:
        # Test Base USDC market
        print("\n📊 Fetching Base USDC market...")
        market = await client.get_market(asset="USDC", chain="base")
        
        if market:
            print(f"✅ Base USDC Market:")
            print(f"   Supply APY: {market.supply_apy:.2f}%")
            print(f"   Borrow APY: {market.borrow_apy:.2f}%")
            print(f"   Utilization: {market.utilization*100:.1f}%")
            print(f"   Total Supply: ${market.total_supply:,.0f}")
        else:
            print("❌ Failed to fetch Base USDC market")
        
        # Test Ethereum USDC market
        print("\n📊 Fetching Ethereum USDC market...")
        eth_market = await client.get_market(asset="USDC", chain="ethereum")
        
        if eth_market:
            print(f"✅ Ethereum USDC Market:")
            print(f"   Supply APY: {eth_market.supply_apy:.2f}%")
            print(f"   Borrow APY: {eth_market.borrow_apy:.2f}%")
            print(f"   Utilization: {eth_market.utilization*100:.1f}%")
        else:
            print("❌ Failed to fetch Ethereum USDC market")
            
    except Exception as e:
        print(f"❌ Compound error: {e}")
    finally:
        await client.close()


async def test_defillama():
    """Test DeFiLlama API."""
    print("\n" + "="*60)
    print("Testing DEFILLAMA API")
    print("="*60)
    
    from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
    
    client = DefiLlamaClient()
    try:
        # Test Aave yields
        print("\n📊 Fetching Aave V3 yields...")
        aave_yields = await client.get_protocol_yields(protocol="aave-v3")
        
        if aave_yields:
            # Filter for Base USDC
            base_usdc = [y for y in aave_yields if y.chain.lower() == "base" and "usdc" in y.symbol.lower()]
            print(f"✅ Found {len(aave_yields)} Aave pools, {len(base_usdc)} on Base with USDC")
            
            if base_usdc:
                for y in base_usdc[:3]:
                    print(f"   - {y.symbol}: {y.apy:.2f}% APY (TVL: ${y.tvl_usd:,.0f})")
            else:
                # Show any Base yields
                base_yields = [y for y in aave_yields if y.chain.lower() == "base"][:3]
                for y in base_yields:
                    print(f"   - {y.symbol}: {y.apy:.2f}% APY (TVL: ${y.tvl_usd:,.0f})")
        else:
            print("❌ No Aave yields found")
        
        # Test Compound yields
        print("\n📊 Fetching Compound V3 yields...")
        compound_yields = await client.get_protocol_yields(protocol="compound-v3")
        
        if compound_yields:
            base_yields = [y for y in compound_yields if y.chain.lower() == "base"]
            print(f"✅ Found {len(compound_yields)} Compound pools, {len(base_yields)} on Base")
            
            for y in base_yields[:3]:
                print(f"   - {y.symbol}: {y.apy:.2f}% APY (TVL: ${y.tvl_usd:,.0f})")
        else:
            print("❌ No Compound yields found")
        
        # Test Morpho yields
        print("\n📊 Fetching Morpho yields...")
        morpho_yields = await client.get_protocol_yields(protocol="morpho-blue")
        
        if morpho_yields:
            base_yields = [y for y in morpho_yields if y.chain.lower() == "base"]
            print(f"✅ Found {len(morpho_yields)} Morpho pools, {len(base_yields)} on Base")
            
            for y in base_yields[:3]:
                print(f"   - {y.symbol}: {y.apy:.2f}% APY (TVL: ${y.tvl_usd:,.0f})")
        else:
            print("⚠️ No Morpho-Blue yields, trying morpho-aave...")
            morpho_yields = await client.get_protocol_yields(protocol="morpho-aave")
            if morpho_yields:
                print(f"✅ Found {len(morpho_yields)} Morpho-Aave pools")
        
    except Exception as e:
        print(f"❌ DeFiLlama error: {e}")
    finally:
        await client.close()


async def test_aave():
    """Test Aave RPC calls."""
    print("\n" + "="*60)
    print("Testing AAVE V3 API")
    print("="*60)
    
    from app.infrastructure.adapters.external.aave_client import AaveClient
    
    # Test Base
    client = AaveClient(chain="base")
    try:
        print("\n📊 Testing Aave V3 on Base...")
        
        # Test user position (sample address)
        test_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        position = await client.get_user_position(test_address)
        
        if position:
            print(f"✅ User position found:")
            print(f"   Collateral: ${position['total_collateral_usd']}")
            print(f"   Debt: ${position['total_debt_usd']}")
            print(f"   Health Factor: {position['health_factor']}")
        else:
            print("ℹ️ No position for test address (expected)")
        
        # Test protocol stats
        stats = await client.get_protocol_stats()
        print(f"\n📊 Protocol Stats:")
        print(f"   TVL: ${stats.get('tvl_usd', 0)}")
        print(f"   Total Markets: {stats.get('total_markets', 0)}")
        
    except Exception as e:
        print(f"❌ Aave error: {e}")
    finally:
        await client.close()


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MONEY MARKET API CONNECTION TEST")
    print("="*60)
    
    await test_morpho()
    await test_compound()
    await test_defillama()
    await test_aave()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
