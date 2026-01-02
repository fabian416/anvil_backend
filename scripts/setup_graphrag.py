#!/usr/bin/env python3
"""
GraphRAG Setup Script

This script sets up the GraphRAG system:
1. Verifies Apache AGE extension is installed
2. Creates the knowledge graph if not exists
3. Populates with protocol data from DeFiLlama
4. Generates embeddings for semantic search
5. Validates the graph structure

Usage:
    python scripts/setup_graphrag.py [--populate] [--limit N] [--validate]

Examples:
    # Full setup with 50 protocols
    python scripts/setup_graphrag.py --populate --limit 50
    
    # Just verify setup
    python scripts/setup_graphrag.py --validate
    
    # Populate all protocols
    python scripts/setup_graphrag.py --populate
"""

import asyncio
import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def check_age_extension(session) -> bool:
    """Check if Apache AGE extension is installed."""
    from sqlalchemy import text
    
    result = await session.execute(text("""
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname = 'age'
    """))
    row = result.fetchone()
    
    if row:
        print(f"✅ Apache AGE extension: v{row[1]}")
        return True
    else:
        print("❌ Apache AGE extension NOT installed")
        print("   Run: CREATE EXTENSION IF NOT EXISTS age;")
        return False


async def check_graph_exists(session, graph_name: str = "defi_knowledge_graph") -> bool:
    """Check if the knowledge graph exists."""
    from sqlalchemy import text
    
    try:
        result = await session.execute(text(f"""
            SELECT name FROM ag_catalog.ag_graph 
            WHERE name = '{graph_name}'
        """))
        row = result.fetchone()
        
        if row:
            print(f"✅ Graph '{graph_name}' exists")
            return True
        else:
            print(f"⚠️ Graph '{graph_name}' does not exist")
            return False
    except Exception as e:
        print(f"⚠️ Could not check graph: {e}")
        return False


async def create_graph(session, graph_name: str = "defi_knowledge_graph") -> bool:
    """Create the knowledge graph."""
    from sqlalchemy import text
    
    try:
        # Load AGE
        await session.execute(text("LOAD 'age'"))
        await session.execute(text("SET search_path = ag_catalog, \"$user\", public"))
        
        # Create graph
        await session.execute(text(f"SELECT create_graph('{graph_name}')"))
        await session.commit()
        
        print(f"✅ Created graph '{graph_name}'")
        return True
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"✅ Graph '{graph_name}' already exists")
            return True
        print(f"❌ Failed to create graph: {e}")
        return False


async def count_nodes(session, graph_name: str = "defi_knowledge_graph") -> dict:
    """Count nodes in the graph by label."""
    from sqlalchemy import text
    
    stats = {
        "total": 0,
        "protocols": 0,
        "chains": 0,
        "tokens": 0,
        "audits": 0,
    }
    
    try:
        await session.execute(text("LOAD 'age'"))
        await session.execute(text("SET search_path = ag_catalog, \"$user\", public"))
        
        # Count total nodes
        result = await session.execute(text(f"""
            SELECT * FROM cypher('{graph_name}', $$
                MATCH (n) RETURN count(n) as cnt
            $$) as (cnt agtype)
        """))
        row = result.fetchone()
        stats["total"] = int(str(row[0]).strip('"')) if row else 0
        
        # Count by label
        for label in ["Protocol", "Chain", "Token", "Audit"]:
            try:
                result = await session.execute(text(f"""
                    SELECT * FROM cypher('{graph_name}', $$
                        MATCH (n:{label}) RETURN count(n) as cnt
                    $$) as (cnt agtype)
                """))
                row = result.fetchone()
                stats[label.lower() + "s"] = int(str(row[0]).strip('"')) if row else 0
            except Exception:
                pass
        
        return stats
    except Exception as e:
        print(f"⚠️ Could not count nodes: {e}")
        return stats


async def populate_graph(session, limit: int | None = None):
    """Populate the graph with protocol data."""
    from app.infrastructure.persistence_age.graph_repository_age import GraphRepositoryAge
    from app.application.graph.populate_graph import PopulateGraphInteractor
    
    # Create mock data provider for now (DeFiLlama integration)
    class MockDefiDataProvider:
        """Mock data provider with sample protocols."""
        
        async def get_all_protocols(self, limit: int | None = None):
            """Get sample protocols."""
            from dataclasses import dataclass
            from typing import Optional, List
            
            @dataclass
            class ProtocolData:
                name: str
                slug: str
                category: str
                chains: List[str]
                tvl: float
                description: Optional[str] = None
                website: Optional[str] = None
                twitter: Optional[str] = None
                github: Optional[str] = None
                logo: Optional[str] = None
                audit_links: Optional[List[str]] = None
                token_symbol: Optional[str] = None
                change_24h: Optional[float] = None
                raw_data: Optional[dict] = None
            
            # Comprehensive list of 55+ DeFi protocols
            protocols = [
                # === Lending (10) ===
                ProtocolData(name="Aave", slug="aave", category="Lending", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=10_500_000_000, description="Leading decentralized lending protocol with flash loans", website="https://aave.com", audit_links=["OpenZeppelin", "Trail of Bits", "Certora"], token_symbol="AAVE", change_24h=2.5, raw_data={}),
                ProtocolData(name="Compound", slug="compound", category="Lending", chains=["Ethereum", "Arbitrum", "Base"], tvl=2_800_000_000, description="Algorithmic money market protocol", website="https://compound.finance", audit_links=["OpenZeppelin", "Trail of Bits"], token_symbol="COMP", change_24h=1.1, raw_data={}),
                ProtocolData(name="Morpho", slug="morpho", category="Lending", chains=["Ethereum", "Base"], tvl=1_500_000_000, description="Peer-to-peer lending optimizer", website="https://morpho.org", audit_links=["Spearbit", "ChainSecurity"], token_symbol="MORPHO", change_24h=5.5, raw_data={}),
                ProtocolData(name="Spark", slug="spark", category="Lending", chains=["Ethereum"], tvl=3_200_000_000, description="MakerDAO's lending protocol fork of Aave", website="https://spark.fi", audit_links=["ChainSecurity", "Cantina"], token_symbol="SPK", change_24h=1.8, raw_data={}),
                ProtocolData(name="Radiant", slug="radiant", category="Lending", chains=["Arbitrum", "BSC"], tvl=150_000_000, description="Cross-chain money market", website="https://radiant.capital", audit_links=["Peckshield"], token_symbol="RDNT", change_24h=-3.2, raw_data={}),
                ProtocolData(name="Venus", slug="venus", category="Lending", chains=["BSC"], tvl=800_000_000, description="BSC lending protocol", website="https://venus.io", audit_links=["Certik", "Peckshield"], token_symbol="XVS", change_24h=0.5, raw_data={}),
                ProtocolData(name="Benqi", slug="benqi", category="Lending", chains=["Avalanche"], tvl=200_000_000, description="Avalanche native lending", website="https://benqi.fi", audit_links=["Halborn"], token_symbol="QI", change_24h=-1.1, raw_data={}),
                ProtocolData(name="Silo", slug="silo", category="Lending", chains=["Ethereum", "Arbitrum"], tvl=120_000_000, description="Isolated risk lending markets", website="https://silo.finance", audit_links=["Quantstamp"], token_symbol="SILO", change_24h=2.3, raw_data={}),
                ProtocolData(name="Euler", slug="euler", category="Lending", chains=["Ethereum"], tvl=50_000_000, description="Permissionless lending protocol", website="https://euler.finance", audit_links=["Sherlock", "Omniscia"], token_symbol="EUL", change_24h=-0.8, raw_data={}),
                ProtocolData(name="Notional", slug="notional", category="Lending", chains=["Ethereum", "Arbitrum"], tvl=80_000_000, description="Fixed rate lending protocol", website="https://notional.finance", audit_links=["OpenZeppelin", "Code4rena"], token_symbol="NOTE", change_24h=1.5, raw_data={}),
                
                # === DEX (12) ===
                ProtocolData(name="Uniswap", slug="uniswap", category="DEX", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=5_200_000_000, description="Leading decentralized exchange", website="https://uniswap.org", audit_links=["OpenZeppelin", "Trail of Bits"], token_symbol="UNI", change_24h=-1.2, raw_data={}),
                ProtocolData(name="Curve", slug="curve", category="DEX", chains=["Ethereum", "Arbitrum", "Polygon"], tvl=2_100_000_000, description="Stablecoin and pegged asset exchange", website="https://curve.fi", audit_links=["Trail of Bits"], token_symbol="CRV", change_24h=-0.5, raw_data={}),
                ProtocolData(name="SushiSwap", slug="sushiswap", category="DEX", chains=["Ethereum", "Arbitrum", "Polygon", "Avalanche"], tvl=300_000_000, description="Multi-chain AMM DEX", website="https://sushi.com", audit_links=["Peckshield", "Quantstamp"], token_symbol="SUSHI", change_24h=0.3, raw_data={}),
                ProtocolData(name="Balancer", slug="balancer", category="DEX", chains=["Ethereum", "Arbitrum", "Polygon"], tvl=800_000_000, description="Programmable liquidity protocol", website="https://balancer.fi", audit_links=["Trail of Bits", "OpenZeppelin"], token_symbol="BAL", change_24h=1.8, raw_data={}),
                ProtocolData(name="1inch", slug="1inch", category="DEX", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=50_000_000, description="DEX aggregator", website="https://1inch.io", audit_links=["OpenZeppelin", "Decurity"], token_symbol="1INCH", change_24h=-0.2, raw_data={}),
                ProtocolData(name="PancakeSwap", slug="pancakeswap", category="DEX", chains=["BSC", "Ethereum", "Arbitrum"], tvl=1_500_000_000, description="Multi-chain DEX with farming", website="https://pancakeswap.finance", audit_links=["Certik", "Peckshield"], token_symbol="CAKE", change_24h=2.1, raw_data={}),
                ProtocolData(name="Velodrome", slug="velodrome", category="DEX", chains=["Optimism"], tvl=200_000_000, description="Optimism native ve(3,3) DEX", website="https://velodrome.finance", audit_links=["Spearbit"], token_symbol="VELO", change_24h=3.5, raw_data={}),
                ProtocolData(name="Aerodrome", slug="aerodrome", category="DEX", chains=["Base"], tvl=500_000_000, description="Base native ve(3,3) DEX", website="https://aerodrome.finance", audit_links=["Spearbit"], token_symbol="AERO", change_24h=5.2, raw_data={}),
                ProtocolData(name="Camelot", slug="camelot", category="DEX", chains=["Arbitrum"], tvl=100_000_000, description="Arbitrum native DEX with NFT incentives", website="https://camelot.exchange", audit_links=["Paladin"], token_symbol="GRAIL", change_24h=-1.5, raw_data={}),
                ProtocolData(name="TraderJoe", slug="traderjoe", category="DEX", chains=["Avalanche", "Arbitrum"], tvl=120_000_000, description="Multi-chain DEX with Liquidity Book", website="https://traderjoexyz.com", audit_links=["Omniscia"], token_symbol="JOE", change_24h=0.8, raw_data={}),
                ProtocolData(name="Quickswap", slug="quickswap", category="DEX", chains=["Polygon"], tvl=80_000_000, description="Polygon native DEX", website="https://quickswap.exchange", audit_links=["Certik"], token_symbol="QUICK", change_24h=-0.3, raw_data={}),
                ProtocolData(name="Maverick", slug="maverick", category="DEX", chains=["Ethereum", "Base", "zkSync"], tvl=60_000_000, description="Dynamic distribution AMM", website="https://mav.xyz", audit_links=["Spearbit", "Zellic"], token_symbol="MAV", change_24h=1.2, raw_data={}),
                
                # === Staking/Liquid Staking (8) ===
                ProtocolData(name="Lido", slug="lido", category="Staking", chains=["Ethereum"], tvl=25_000_000_000, description="Largest liquid staking protocol", website="https://lido.fi", audit_links=["Quantstamp", "MixBytes", "Statemind"], token_symbol="LDO", change_24h=0.8, raw_data={}),
                ProtocolData(name="Rocket Pool", slug="rocketpool", category="Staking", chains=["Ethereum"], tvl=3_500_000_000, description="Decentralized staking pool", website="https://rocketpool.net", audit_links=["Sigma Prime", "Trail of Bits"], token_symbol="RPL", change_24h=-0.5, raw_data={}),
                ProtocolData(name="Frax ETH", slug="fraxeth", category="Staking", chains=["Ethereum"], tvl=1_200_000_000, description="Frax liquid staking derivative", website="https://frax.finance", audit_links=["Trail of Bits"], token_symbol="FXS", change_24h=1.2, raw_data={}),
                ProtocolData(name="Swell", slug="swell", category="Staking", chains=["Ethereum"], tvl=800_000_000, description="Liquid restaking protocol", website="https://swellnetwork.io", audit_links=["Sigma Prime"], token_symbol="SWELL", change_24h=2.5, raw_data={}),
                ProtocolData(name="Mantle LSP", slug="mantle-lsp", category="Staking", chains=["Ethereum", "Mantle"], tvl=600_000_000, description="Mantle ecosystem liquid staking", website="https://mantle.xyz", audit_links=["OpenZeppelin"], token_symbol="MNT", change_24h=0.3, raw_data={}),
                ProtocolData(name="Ankr", slug="ankr", category="Staking", chains=["Ethereum", "BSC", "Polygon"], tvl=150_000_000, description="Multi-chain liquid staking", website="https://ankr.com", audit_links=["Beosin"], token_symbol="ANKR", change_24h=-1.8, raw_data={}),
                ProtocolData(name="Stakewise", slug="stakewise", category="Staking", chains=["Ethereum"], tvl=200_000_000, description="Non-custodial ETH staking", website="https://stakewise.io", audit_links=["Quantstamp", "Runtime Verification"], token_symbol="SWISE", change_24h=0.7, raw_data={}),
                ProtocolData(name="Stader", slug="stader", category="Staking", chains=["Ethereum", "Polygon", "BSC"], tvl=300_000_000, description="Multi-chain liquid staking", website="https://staderlabs.com", audit_links=["Halborn", "Peckshield"], token_symbol="SD", change_24h=1.1, raw_data={}),
                
                # === CDP/Stablecoins (5) ===
                ProtocolData(name="MakerDAO", slug="makerdao", category="CDP", chains=["Ethereum"], tvl=7_500_000_000, description="DAI stablecoin issuer", website="https://makerdao.com", audit_links=["Trail of Bits", "PeckShield"], token_symbol="MKR", change_24h=3.2, raw_data={}),
                ProtocolData(name="Liquity", slug="liquity", category="CDP", chains=["Ethereum"], tvl=500_000_000, description="Interest-free borrowing against ETH", website="https://liquity.org", audit_links=["Trail of Bits", "Coinspect"], token_symbol="LQTY", change_24h=-0.8, raw_data={}),
                ProtocolData(name="Frax", slug="frax", category="CDP", chains=["Ethereum"], tvl=700_000_000, description="Fractional algorithmic stablecoin", website="https://frax.finance", audit_links=["Trail of Bits", "Certik"], token_symbol="FXS", change_24h=1.5, raw_data={}),
                ProtocolData(name="Prisma", slug="prisma", category="CDP", chains=["Ethereum"], tvl=200_000_000, description="LST-backed stablecoin", website="https://prismafinance.com", audit_links=["MixBytes"], token_symbol="PRISMA", change_24h=2.1, raw_data={}),
                ProtocolData(name="crvUSD", slug="crvusd", category="CDP", chains=["Ethereum"], tvl=400_000_000, description="Curve's overcollateralized stablecoin", website="https://curve.fi", audit_links=["MixBytes", "ChainSecurity"], token_symbol="CRV", change_24h=0.5, raw_data={}),
                
                # === Derivatives (6) ===
                ProtocolData(name="GMX", slug="gmx", category="Derivatives", chains=["Arbitrum", "Avalanche"], tvl=500_000_000, description="Decentralized perpetual exchange", website="https://gmx.io", audit_links=["ABDK"], token_symbol="GMX", change_24h=-2.1, raw_data={}),
                ProtocolData(name="dYdX", slug="dydx", category="Derivatives", chains=["Ethereum", "dYdX Chain"], tvl=300_000_000, description="Decentralized derivatives exchange", website="https://dydx.exchange", audit_links=["Trail of Bits", "Peckshield"], token_symbol="DYDX", change_24h=1.5, raw_data={}),
                ProtocolData(name="Synthetix", slug="synthetix", category="Derivatives", chains=["Ethereum", "Optimism", "Base"], tvl=400_000_000, description="Synthetic assets protocol", website="https://synthetix.io", audit_links=["Iosiro", "Sigma Prime"], token_symbol="SNX", change_24h=-0.3, raw_data={}),
                ProtocolData(name="Gains Network", slug="gains", category="Derivatives", chains=["Arbitrum", "Polygon"], tvl=100_000_000, description="Leveraged trading platform", website="https://gains.trade", audit_links=["Certik"], token_symbol="GNS", change_24h=2.8, raw_data={}),
                ProtocolData(name="Hyperliquid", slug="hyperliquid", category="Derivatives", chains=["Hyperliquid"], tvl=800_000_000, description="High performance perpetual DEX", website="https://hyperliquid.xyz", audit_links=["Internal"], token_symbol="HYPE", change_24h=5.5, raw_data={}),
                ProtocolData(name="Vertex", slug="vertex", category="Derivatives", chains=["Arbitrum"], tvl=80_000_000, description="Cross-margin DEX", website="https://vertexprotocol.com", audit_links=["Omniscia"], token_symbol="VRTX", change_24h=-1.2, raw_data={}),
                
                # === Yield/Vaults (6) ===
                ProtocolData(name="Pendle", slug="pendle", category="Yield", chains=["Ethereum", "Arbitrum"], tvl=300_000_000, description="Yield trading protocol", website="https://pendle.finance", audit_links=["Ackee", "Dedaub"], token_symbol="PENDLE", change_24h=8.2, raw_data={}),
                ProtocolData(name="Yearn", slug="yearn", category="Yield", chains=["Ethereum", "Arbitrum", "Optimism"], tvl=300_000_000, description="Automated yield strategies", website="https://yearn.fi", audit_links=["Trail of Bits", "MixBytes"], token_symbol="YFI", change_24h=-0.5, raw_data={}),
                ProtocolData(name="Convex", slug="convex", category="Yield", chains=["Ethereum"], tvl=1_500_000_000, description="Curve yield optimizer", website="https://convexfinance.com", audit_links=["MixBytes"], token_symbol="CVX", change_24h=1.2, raw_data={}),
                ProtocolData(name="Beefy", slug="beefy", category="Yield", chains=["BSC", "Polygon", "Arbitrum", "Optimism"], tvl=150_000_000, description="Multi-chain yield optimizer", website="https://beefy.finance", audit_links=["Certik"], token_symbol="BIFI", change_24h=0.8, raw_data={}),
                ProtocolData(name="Sommelier", slug="sommelier", category="Yield", chains=["Ethereum"], tvl=100_000_000, description="Active DeFi strategy vaults", website="https://sommelier.finance", audit_links=["Macro"], token_symbol="SOMM", change_24h=3.2, raw_data={}),
                ProtocolData(name="Origin Dollar", slug="origin-dollar", category="Yield", chains=["Ethereum"], tvl=80_000_000, description="Yield-bearing stablecoin", website="https://ousd.com", audit_links=["OpenZeppelin", "Trail of Bits"], token_symbol="OGN", change_24h=-0.3, raw_data={}),
                
                # === Bridges (5) ===
                ProtocolData(name="Stargate", slug="stargate", category="Bridge", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=400_000_000, description="Cross-chain bridge by LayerZero", website="https://stargate.finance", audit_links=["Quantstamp", "Zellic"], token_symbol="STG", change_24h=0.3, raw_data={}),
                ProtocolData(name="Across", slug="across", category="Bridge", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=150_000_000, description="Fast cross-chain bridge", website="https://across.to", audit_links=["OpenZeppelin"], token_symbol="ACX", change_24h=1.5, raw_data={}),
                ProtocolData(name="Hop Protocol", slug="hop", category="Bridge", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism"], tvl=50_000_000, description="Token bridge for rollups", website="https://hop.exchange", audit_links=["OpenZeppelin"], token_symbol="HOP", change_24h=-0.8, raw_data={}),
                ProtocolData(name="Synapse", slug="synapse", category="Bridge", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Avalanche"], tvl=80_000_000, description="Cross-chain communication", website="https://synapseprotocol.com", audit_links=["Veridise"], token_symbol="SYN", change_24h=0.5, raw_data={}),
                ProtocolData(name="Socket", slug="socket", category="Bridge", chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"], tvl=30_000_000, description="Bridge aggregator", website="https://socket.tech", audit_links=["ChainSecurity"], token_symbol="SOCKET", change_24h=2.1, raw_data={}),
                
                # === Restaking (3) ===
                ProtocolData(name="EigenLayer", slug="eigenlayer", category="Restaking", chains=["Ethereum"], tvl=15_000_000_000, description="Restaking for shared security", website="https://eigenlayer.xyz", audit_links=["Sigma Prime", "ChainSecurity"], token_symbol="EIGEN", change_24h=1.8, raw_data={}),
                ProtocolData(name="Ether.fi", slug="etherfi", category="Restaking", chains=["Ethereum"], tvl=5_000_000_000, description="Liquid restaking protocol", website="https://ether.fi", audit_links=["Certora", "Zellic"], token_symbol="ETHFI", change_24h=3.2, raw_data={}),
                ProtocolData(name="Renzo", slug="renzo", category="Restaking", chains=["Ethereum"], tvl=2_000_000_000, description="Liquid restaking token", website="https://renzoprotocol.com", audit_links=["Halborn"], token_symbol="REZ", change_24h=2.5, raw_data={}),
            ]
            
            if limit:
                return protocols[:limit]
            return protocols
    
    print("\n📊 Populating graph with protocol data...")
    
    # Create repository
    repo = GraphRepositoryAge(session, graph_name="defi_knowledge_graph")
    
    # Create data provider
    data_provider = MockDefiDataProvider()
    
    # Create interactor
    interactor = PopulateGraphInteractor(repo, data_provider)
    
    # Populate
    stats = await interactor.populate_protocols(limit=limit)
    
    print(f"\n📈 Population Results:")
    print(f"   Protocols fetched: {stats.get('protocols_fetched', 0)}")
    print(f"   Protocols created: {stats.get('protocols_created', 0)}")
    print(f"   Chains created: {stats.get('chains_created', 0)}")
    print(f"   Relationships: {stats.get('relationships_created', 0)}")
    print(f"   Errors: {stats.get('errors', 0)}")
    
    return stats


async def validate_graph(session, graph_name: str = "defi_knowledge_graph"):
    """Validate graph structure and data."""
    from sqlalchemy import text
    
    print("\n🔍 Validating graph...")
    
    issues = []
    
    try:
        await session.execute(text("LOAD 'age'"))
        await session.execute(text("SET search_path = ag_catalog, \"$user\", public"))
        
        # Check for orphan nodes (protocols without chain)
        result = await session.execute(text(f"""
            SELECT * FROM cypher('{graph_name}', $$
                MATCH (p:Protocol)
                WHERE NOT (p)-[:DEPLOYED_ON]->(:Chain)
                RETURN count(p) as cnt
            $$) as (cnt agtype)
        """))
        row = result.fetchone()
        orphans = int(str(row[0]).strip('"')) if row else 0
        if orphans > 0:
            issues.append(f"⚠️ {orphans} protocols without chain relationship")
        
        # Check for protocols with properties
        result = await session.execute(text(f"""
            SELECT * FROM cypher('{graph_name}', $$
                MATCH (p:Protocol)
                WHERE p.name IS NOT NULL AND p.tvl IS NOT NULL
                RETURN count(p) as cnt
            $$) as (cnt agtype)
        """))
        row = result.fetchone()
        valid_protocols = int(str(row[0]).strip('"')) if row else 0
        print(f"   ✅ {valid_protocols} protocols with valid properties")
        
        if issues:
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   ✅ Graph structure is valid")
        
    except Exception as e:
        print(f"   ❌ Validation error: {e}")


async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="GraphRAG Setup Script")
    parser.add_argument("--populate", action="store_true", help="Populate graph with protocol data")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of protocols to populate")
    parser.add_argument("--validate", action="store_true", help="Validate graph structure")
    args = parser.parse_args()
    
    print("=" * 70)
    print("GRAPHRAG SETUP SCRIPT")
    print("=" * 70)
    
    # Load configuration
    from app.setup.config.loader import load_full_config, get_current_env
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    config = load_full_config(env=get_current_env())
    pg = config.get("postgres", {})
    
    # Build connection string
    url = f"postgresql+asyncpg://{pg.get('USER', 'postgres')}:{pg.get('PASSWORD', '')}@{pg.get('HOST', 'localhost')}:{pg.get('PORT', 5432)}/{pg.get('DB', 'anvil_db')}"
    
    engine = create_async_engine(url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Step 1: Check AGE extension
        print("\n1️⃣ Checking Apache AGE extension...")
        if not await check_age_extension(session):
            print("\n❌ Setup failed: AGE extension required")
            print("   Run: sudo apt-get install postgresql-16-age")
            print("   Then: CREATE EXTENSION IF NOT EXISTS age;")
            return
        
        # Step 2: Check/create graph
        print("\n2️⃣ Checking knowledge graph...")
        if not await check_graph_exists(session):
            print("   Creating graph...")
            if not await create_graph(session):
                print("\n❌ Setup failed: Could not create graph")
                return
        
        # Step 3: Count current nodes
        print("\n3️⃣ Current graph statistics:")
        stats = await count_nodes(session)
        print(f"   Total nodes: {stats['total']}")
        print(f"   Protocols: {stats['protocols']}")
        print(f"   Chains: {stats['chains']}")
        print(f"   Tokens: {stats['tokens']}")
        
        # Step 4: Populate if requested
        if args.populate:
            print("\n4️⃣ Populating graph...")
            await populate_graph(session, limit=args.limit)
            
            # Recount after population
            print("\n   Updated statistics:")
            stats = await count_nodes(session)
            print(f"   Total nodes: {stats['total']}")
            print(f"   Protocols: {stats['protocols']}")
        
        # Step 5: Validate if requested
        if args.validate:
            print("\n5️⃣ Validating graph...")
            await validate_graph(session)
    
    await engine.dispose()
    
    print("\n" + "=" * 70)
    print("✅ GraphRAG setup complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Generate embeddings: python scripts/generate_embeddings.py")
    print("  2. Test search: curl http://localhost:8080/api/v1/graph/search?q=lending")
    print("  3. View in chat: Ask 'find safe lending protocols'")


if __name__ == "__main__":
    asyncio.run(main())
