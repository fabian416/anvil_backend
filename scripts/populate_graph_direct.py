#!/usr/bin/env python3
"""
Direct GraphRAG Population Script

Populates the graph directly using correct Cypher syntax for Apache AGE.
Bypasses the GraphRepositoryAge adapter issue with JSON property formatting.

Usage:
    python scripts/populate_graph_direct.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# Protocol data - 55+ protocols
PROTOCOLS = [
    # Lending (10)
    {"name": "Aave", "category": "Lending", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 10500000000, "risk_score": 2.5, "description": "Leading decentralized lending protocol with flash loans"},
    {"name": "Compound", "category": "Lending", "chains": ["Ethereum", "Arbitrum", "Base"], "tvl": 2800000000, "risk_score": 2.3, "description": "Algorithmic money market protocol"},
    {"name": "Morpho", "category": "Lending", "chains": ["Ethereum", "Base"], "tvl": 1500000000, "risk_score": 4.5, "description": "Peer-to-peer lending optimizer"},
    {"name": "Spark", "category": "Lending", "chains": ["Ethereum"], "tvl": 3200000000, "risk_score": 3.0, "description": "MakerDAO lending protocol fork of Aave"},
    {"name": "Radiant", "category": "Lending", "chains": ["Arbitrum", "BSC"], "tvl": 150000000, "risk_score": 5.5, "description": "Cross-chain money market"},
    {"name": "Venus", "category": "Lending", "chains": ["BSC"], "tvl": 800000000, "risk_score": 4.0, "description": "BSC lending protocol"},
    {"name": "Benqi", "category": "Lending", "chains": ["Avalanche"], "tvl": 200000000, "risk_score": 4.2, "description": "Avalanche native lending"},
    {"name": "Silo", "category": "Lending", "chains": ["Ethereum", "Arbitrum"], "tvl": 120000000, "risk_score": 5.0, "description": "Isolated risk lending markets"},
    {"name": "Euler", "category": "Lending", "chains": ["Ethereum"], "tvl": 50000000, "risk_score": 6.5, "description": "Permissionless lending protocol"},
    {"name": "Notional", "category": "Lending", "chains": ["Ethereum", "Arbitrum"], "tvl": 80000000, "risk_score": 4.8, "description": "Fixed rate lending protocol"},
    
    # DEX (12)
    {"name": "Uniswap", "category": "DEX", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 5200000000, "risk_score": 2.8, "description": "Leading decentralized exchange"},
    {"name": "Curve", "category": "DEX", "chains": ["Ethereum", "Arbitrum", "Polygon"], "tvl": 2100000000, "risk_score": 3.0, "description": "Stablecoin and pegged asset exchange"},
    {"name": "SushiSwap", "category": "DEX", "chains": ["Ethereum", "Arbitrum", "Polygon", "Avalanche"], "tvl": 300000000, "risk_score": 4.5, "description": "Multi-chain AMM DEX"},
    {"name": "Balancer", "category": "DEX", "chains": ["Ethereum", "Arbitrum", "Polygon"], "tvl": 800000000, "risk_score": 3.2, "description": "Programmable liquidity protocol"},
    {"name": "1inch", "category": "DEX", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 50000000, "risk_score": 3.5, "description": "DEX aggregator"},
    {"name": "PancakeSwap", "category": "DEX", "chains": ["BSC", "Ethereum", "Arbitrum"], "tvl": 1500000000, "risk_score": 3.8, "description": "Multi-chain DEX with farming"},
    {"name": "Velodrome", "category": "DEX", "chains": ["Optimism"], "tvl": 200000000, "risk_score": 4.0, "description": "Optimism native ve(3,3) DEX"},
    {"name": "Aerodrome", "category": "DEX", "chains": ["Base"], "tvl": 500000000, "risk_score": 4.2, "description": "Base native ve(3,3) DEX"},
    {"name": "Camelot", "category": "DEX", "chains": ["Arbitrum"], "tvl": 100000000, "risk_score": 4.5, "description": "Arbitrum native DEX with NFT incentives"},
    {"name": "TraderJoe", "category": "DEX", "chains": ["Avalanche", "Arbitrum"], "tvl": 120000000, "risk_score": 4.3, "description": "Multi-chain DEX with Liquidity Book"},
    {"name": "Quickswap", "category": "DEX", "chains": ["Polygon"], "tvl": 80000000, "risk_score": 4.0, "description": "Polygon native DEX"},
    {"name": "Maverick", "category": "DEX", "chains": ["Ethereum", "Base", "zkSync"], "tvl": 60000000, "risk_score": 5.0, "description": "Dynamic distribution AMM"},
    
    # Staking (8)
    {"name": "Lido", "category": "Staking", "chains": ["Ethereum"], "tvl": 25000000000, "risk_score": 2.2, "description": "Largest liquid staking protocol"},
    {"name": "Rocket Pool", "category": "Staking", "chains": ["Ethereum"], "tvl": 3500000000, "risk_score": 2.5, "description": "Decentralized staking pool"},
    {"name": "Frax ETH", "category": "Staking", "chains": ["Ethereum"], "tvl": 1200000000, "risk_score": 3.5, "description": "Frax liquid staking derivative"},
    {"name": "Swell", "category": "Staking", "chains": ["Ethereum"], "tvl": 800000000, "risk_score": 4.0, "description": "Liquid restaking protocol"},
    {"name": "Mantle LSP", "category": "Staking", "chains": ["Ethereum", "Mantle"], "tvl": 600000000, "risk_score": 4.5, "description": "Mantle ecosystem liquid staking"},
    {"name": "Ankr", "category": "Staking", "chains": ["Ethereum", "BSC", "Polygon"], "tvl": 150000000, "risk_score": 4.2, "description": "Multi-chain liquid staking"},
    {"name": "Stakewise", "category": "Staking", "chains": ["Ethereum"], "tvl": 200000000, "risk_score": 3.8, "description": "Non-custodial ETH staking"},
    {"name": "Stader", "category": "Staking", "chains": ["Ethereum", "Polygon", "BSC"], "tvl": 300000000, "risk_score": 4.0, "description": "Multi-chain liquid staking"},
    
    # CDP (5)
    {"name": "MakerDAO", "category": "CDP", "chains": ["Ethereum"], "tvl": 7500000000, "risk_score": 2.5, "description": "DAI stablecoin issuer"},
    {"name": "Liquity", "category": "CDP", "chains": ["Ethereum"], "tvl": 500000000, "risk_score": 3.0, "description": "Interest-free borrowing against ETH"},
    {"name": "Frax", "category": "CDP", "chains": ["Ethereum"], "tvl": 700000000, "risk_score": 4.0, "description": "Fractional algorithmic stablecoin"},
    {"name": "Prisma", "category": "CDP", "chains": ["Ethereum"], "tvl": 200000000, "risk_score": 5.0, "description": "LST-backed stablecoin"},
    {"name": "crvUSD", "category": "CDP", "chains": ["Ethereum"], "tvl": 400000000, "risk_score": 3.5, "description": "Curve overcollateralized stablecoin"},
    
    # Derivatives (6)
    {"name": "GMX", "category": "Derivatives", "chains": ["Arbitrum", "Avalanche"], "tvl": 500000000, "risk_score": 4.5, "description": "Decentralized perpetual exchange"},
    {"name": "dYdX", "category": "Derivatives", "chains": ["Ethereum", "dYdX Chain"], "tvl": 300000000, "risk_score": 3.5, "description": "Decentralized derivatives exchange"},
    {"name": "Synthetix", "category": "Derivatives", "chains": ["Ethereum", "Optimism", "Base"], "tvl": 400000000, "risk_score": 4.0, "description": "Synthetic assets protocol"},
    {"name": "Gains Network", "category": "Derivatives", "chains": ["Arbitrum", "Polygon"], "tvl": 100000000, "risk_score": 5.0, "description": "Leveraged trading platform"},
    {"name": "Hyperliquid", "category": "Derivatives", "chains": ["Hyperliquid"], "tvl": 800000000, "risk_score": 5.5, "description": "High performance perpetual DEX"},
    {"name": "Vertex", "category": "Derivatives", "chains": ["Arbitrum"], "tvl": 80000000, "risk_score": 5.2, "description": "Cross-margin DEX"},
    
    # Yield (6)
    {"name": "Pendle", "category": "Yield", "chains": ["Ethereum", "Arbitrum"], "tvl": 300000000, "risk_score": 4.5, "description": "Yield trading protocol"},
    {"name": "Yearn", "category": "Yield", "chains": ["Ethereum", "Arbitrum", "Optimism"], "tvl": 300000000, "risk_score": 3.5, "description": "Automated yield strategies"},
    {"name": "Convex", "category": "Yield", "chains": ["Ethereum"], "tvl": 1500000000, "risk_score": 3.0, "description": "Curve yield optimizer"},
    {"name": "Beefy", "category": "Yield", "chains": ["BSC", "Polygon", "Arbitrum", "Optimism"], "tvl": 150000000, "risk_score": 4.5, "description": "Multi-chain yield optimizer"},
    {"name": "Sommelier", "category": "Yield", "chains": ["Ethereum"], "tvl": 100000000, "risk_score": 5.0, "description": "Active DeFi strategy vaults"},
    {"name": "Origin Dollar", "category": "Yield", "chains": ["Ethereum"], "tvl": 80000000, "risk_score": 4.0, "description": "Yield-bearing stablecoin"},
    
    # Bridges (5)
    {"name": "Stargate", "category": "Bridge", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 400000000, "risk_score": 4.0, "description": "Cross-chain bridge by LayerZero"},
    {"name": "Across", "category": "Bridge", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 150000000, "risk_score": 3.5, "description": "Fast cross-chain bridge"},
    {"name": "Hop Protocol", "category": "Bridge", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism"], "tvl": 50000000, "risk_score": 4.0, "description": "Token bridge for rollups"},
    {"name": "Synapse", "category": "Bridge", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Avalanche"], "tvl": 80000000, "risk_score": 4.5, "description": "Cross-chain communication"},
    {"name": "Socket", "category": "Bridge", "chains": ["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], "tvl": 30000000, "risk_score": 5.0, "description": "Bridge aggregator"},
    
    # Restaking (3)
    {"name": "EigenLayer", "category": "Restaking", "chains": ["Ethereum"], "tvl": 15000000000, "risk_score": 3.5, "description": "Restaking for shared security"},
    {"name": "Ether.fi", "category": "Restaking", "chains": ["Ethereum"], "tvl": 5000000000, "risk_score": 4.0, "description": "Liquid restaking protocol"},
    {"name": "Renzo", "category": "Restaking", "chains": ["Ethereum"], "tvl": 2000000000, "risk_score": 4.5, "description": "Liquid restaking token"},
]


async def main():
    """Populate graph directly using asyncpg."""
    import asyncpg
    
    print("=" * 70)
    print("GRAPHRAG DIRECT POPULATION")
    print("=" * 70)
    
    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="changethis",
        database="anvil_db",
    )
    
    print("\n✅ Connected to database")
    
    # Setup AGE
    await conn.execute("LOAD 'age'")
    await conn.execute("SET search_path = ag_catalog, '$user', public")
    
    print("✅ Apache AGE loaded")
    
    # Check if graph exists
    result = await conn.fetchrow(
        "SELECT name FROM ag_graph WHERE name = 'defi_knowledge_graph'"
    )
    
    if not result:
        print("Creating graph 'defi_knowledge_graph'...")
        await conn.execute(
            "SELECT create_graph('defi_knowledge_graph')"
        )
        print("✅ Graph created")
    else:
        print("✅ Graph exists")
    
    # Count existing protocols
    result = await conn.fetchrow("""
        SELECT * FROM cypher('defi_knowledge_graph', $$
            MATCH (p:Protocol) RETURN count(p) as cnt
        $$) as (cnt agtype)
    """)
    existing = int(str(result['cnt']).strip('"')) if result else 0
    print(f"📊 Existing protocols: {existing}")
    
    # Clear existing protocols if any
    if existing > 0:
        print("🗑️ Clearing existing protocols...")
        await conn.execute("""
            SELECT * FROM cypher('defi_knowledge_graph', $$
                MATCH (p:Protocol) DETACH DELETE p
            $$) as (result agtype)
        """)
        await conn.execute("""
            SELECT * FROM cypher('defi_knowledge_graph', $$
                MATCH (c:Chain) DETACH DELETE c
            $$) as (result agtype)
        """)
        print("✅ Cleared")
    
    # Create chains first
    chains = set()
    for p in PROTOCOLS:
        chains.update(p["chains"])
    
    print(f"\n📍 Creating {len(chains)} chains...")
    for chain in chains:
        try:
            await conn.execute(f"""
                SELECT * FROM cypher('defi_knowledge_graph', $$
                    CREATE (c:Chain {{name: '{chain}'}})
                    RETURN c
                $$) as (c agtype)
            """)
        except Exception as e:
            if "already exists" not in str(e):
                print(f"   ⚠️ Chain {chain}: {e}")
    print("✅ Chains created")
    
    # Create protocols
    print(f"\n📦 Creating {len(PROTOCOLS)} protocols...")
    success = 0
    for i, p in enumerate(PROTOCOLS):
        try:
            # Escape single quotes in description
            desc = p["description"].replace("'", "''")
            
            # Create protocol node with correct Cypher syntax
            await conn.execute(f"""
                SELECT * FROM cypher('defi_knowledge_graph', $$
                    CREATE (p:Protocol {{
                        name: '{p["name"]}',
                        category: '{p["category"]}',
                        tvl: {p["tvl"]},
                        risk_score: {p["risk_score"]},
                        description: '{desc}'
                    }})
                    RETURN p
                $$) as (p agtype)
            """)
            
            # Create relationships to chains
            for chain in p["chains"]:
                try:
                    await conn.execute(f"""
                        SELECT * FROM cypher('defi_knowledge_graph', $$
                            MATCH (p:Protocol {{name: '{p["name"]}'}}), (c:Chain {{name: '{chain}'}})
                            CREATE (p)-[:DEPLOYED_ON]->(c)
                            RETURN p, c
                        $$) as (p agtype, c agtype)
                    """)
                except Exception as e:
                    pass  # Ignore relationship errors
            
            success += 1
            if (i + 1) % 10 == 0:
                print(f"   ... {i + 1}/{len(PROTOCOLS)} created")
        except Exception as e:
            print(f"   ❌ {p['name']}: {e}")
    
    print(f"\n✅ Created {success}/{len(PROTOCOLS)} protocols")
    
    # Verify
    result = await conn.fetchrow("""
        SELECT * FROM cypher('defi_knowledge_graph', $$
            MATCH (p:Protocol) RETURN count(p) as cnt
        $$) as (cnt agtype)
    """)
    final_count = int(str(result['cnt']).strip('"')) if result else 0
    
    result = await conn.fetchrow("""
        SELECT * FROM cypher('defi_knowledge_graph', $$
            MATCH (c:Chain) RETURN count(c) as cnt
        $$) as (cnt agtype)
    """)
    chain_count = int(str(result['cnt']).strip('"')) if result else 0
    
    result = await conn.fetchrow("""
        SELECT * FROM cypher('defi_knowledge_graph', $$
            MATCH ()-[r:DEPLOYED_ON]->() RETURN count(r) as cnt
        $$) as (cnt agtype)
    """)
    rel_count = int(str(result['cnt']).strip('"')) if result else 0
    
    print("\n" + "=" * 70)
    print("📊 FINAL STATS")
    print("=" * 70)
    print(f"   Protocols: {final_count}")
    print(f"   Chains: {chain_count}")
    print(f"   Relationships: {rel_count}")
    print("=" * 70)
    
    await conn.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
