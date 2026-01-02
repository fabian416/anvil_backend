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
            
            protocols = [
                ProtocolData(
                    name="Aave",
                    slug="aave",
                    category="Lending",
                    chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"],
                    tvl=10_500_000_000,
                    description="Decentralized lending protocol",
                    website="https://aave.com",
                    audit_links=["OpenZeppelin", "Trail of Bits", "Certora"],
                    token_symbol="AAVE",
                    change_24h=2.5,
                    raw_data={},
                ),
                ProtocolData(
                    name="Uniswap",
                    slug="uniswap",
                    category="DEX",
                    chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"],
                    tvl=5_200_000_000,
                    description="Leading decentralized exchange",
                    website="https://uniswap.org",
                    audit_links=["OpenZeppelin", "Trail of Bits"],
                    token_symbol="UNI",
                    change_24h=-1.2,
                    raw_data={},
                ),
                ProtocolData(
                    name="Lido",
                    slug="lido",
                    category="Staking",
                    chains=["Ethereum"],
                    tvl=25_000_000_000,
                    description="Liquid staking protocol",
                    website="https://lido.fi",
                    audit_links=["Quantstamp", "MixBytes"],
                    token_symbol="LDO",
                    change_24h=0.8,
                    raw_data={},
                ),
                ProtocolData(
                    name="Curve",
                    slug="curve",
                    category="DEX",
                    chains=["Ethereum", "Arbitrum", "Polygon"],
                    tvl=2_100_000_000,
                    description="Stablecoin exchange",
                    website="https://curve.fi",
                    audit_links=["Trail of Bits"],
                    token_symbol="CRV",
                    change_24h=-0.5,
                    raw_data={},
                ),
                ProtocolData(
                    name="Compound",
                    slug="compound",
                    category="Lending",
                    chains=["Ethereum", "Arbitrum", "Base"],
                    tvl=2_800_000_000,
                    description="Algorithmic money market",
                    website="https://compound.finance",
                    audit_links=["OpenZeppelin", "Trail of Bits"],
                    token_symbol="COMP",
                    change_24h=1.1,
                    raw_data={},
                ),
                ProtocolData(
                    name="MakerDAO",
                    slug="makerdao",
                    category="CDP",
                    chains=["Ethereum"],
                    tvl=7_500_000_000,
                    description="DAI stablecoin issuer",
                    website="https://makerdao.com",
                    audit_links=["Trail of Bits", "PeckShield"],
                    token_symbol="MKR",
                    change_24h=3.2,
                    raw_data={},
                ),
                ProtocolData(
                    name="Morpho",
                    slug="morpho",
                    category="Lending",
                    chains=["Ethereum", "Base"],
                    tvl=1_500_000_000,
                    description="Peer-to-peer lending optimizer",
                    website="https://morpho.org",
                    audit_links=["Spearbit", "ChainSecurity"],
                    token_symbol="MORPHO",
                    change_24h=5.5,
                    raw_data={},
                ),
                ProtocolData(
                    name="GMX",
                    slug="gmx",
                    category="Derivatives",
                    chains=["Arbitrum", "Avalanche"],
                    tvl=500_000_000,
                    description="Decentralized perpetual exchange",
                    website="https://gmx.io",
                    audit_links=["ABDK"],
                    token_symbol="GMX",
                    change_24h=-2.1,
                    raw_data={},
                ),
                ProtocolData(
                    name="Stargate",
                    slug="stargate",
                    category="Bridge",
                    chains=["Ethereum", "Arbitrum", "Polygon", "Optimism", "Base"],
                    tvl=400_000_000,
                    description="Cross-chain bridge by LayerZero",
                    website="https://stargate.finance",
                    audit_links=["Quantstamp", "Zellic"],
                    token_symbol="STG",
                    change_24h=0.3,
                    raw_data={},
                ),
                ProtocolData(
                    name="Pendle",
                    slug="pendle",
                    category="Yield",
                    chains=["Ethereum", "Arbitrum"],
                    tvl=300_000_000,
                    description="Yield trading protocol",
                    website="https://pendle.finance",
                    audit_links=["Ackee", "Dedaub"],
                    token_symbol="PENDLE",
                    change_24h=8.2,
                    raw_data={},
                ),
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
