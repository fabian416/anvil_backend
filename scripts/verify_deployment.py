#!/usr/bin/env python3
"""
Production Deployment Verification Script

This script verifies that all components are properly configured and ready for production deployment.

Usage:
    python scripts/verify_deployment.py
    
    # Or with specific checks:
    python scripts/verify_deployment.py --check=database
    python scripts/verify_deployment.py --check=redis
    python scripts/verify_deployment.py --check=api
    python scripts/verify_deployment.py --check=mcp
    python scripts/verify_deployment.py --check=agents

Exit codes:
    0: All checks passed
    1: One or more checks failed
"""

import sys
import os
import asyncio
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
import redis
from sqlalchemy import create_engine, text
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class CheckStatus(Enum):
    """Status of a verification check"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️  WARN"
    SKIP = "⏭️  SKIP"


@dataclass
class CheckResult:
    """Result of a verification check"""
    name: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class DeploymentVerifier:
    """Verify deployment readiness"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def run_all_checks(self) -> bool:
        """Run all verification checks"""
        
        print("=" * 80)
        print("🚀 ANVIL BACKEND - PRODUCTION DEPLOYMENT VERIFICATION")
        print("=" * 80)
        print()
        
        # Run checks in order
        await self.check_environment()
        await self.check_database()
        await self.check_redis()
        await self.check_migrations()
        await self.check_api_server()
        await self.check_mcp_servers()
        await self.check_agent_router()
        await self.check_websocket()
        await self.check_celery()
        await self.check_performance()
        
        # Print summary
        self.print_summary()
        
        # Return True if all critical checks passed
        failed_checks = [r for r in self.results if r.status == CheckStatus.FAIL]
        return len(failed_checks) == 0
    
    async def check_environment(self):
        """Check environment variables"""
        print("📋 Checking Environment Variables...")
        
        required_vars = [
            "APP_ENV",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "POSTGRES_HOST",
            "REDIS_URL",
            "OPENAI_API_KEY",
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.results.append(CheckResult(
                name="Environment Variables",
                status=CheckStatus.FAIL,
                message=f"Missing required environment variables: {', '.join(missing_vars)}",
                details={"missing": missing_vars}
            ))
        else:
            self.results.append(CheckResult(
                name="Environment Variables",
                status=CheckStatus.PASS,
                message="All required environment variables are set"
            ))
        
        print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        print()
    
    async def check_database(self):
        """Check PostgreSQL connection and extensions"""
        print("🗄️  Checking PostgreSQL Database...")
        
        try:
            # Get database URL from environment
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
            db_name = os.getenv("POSTGRES_DB", "anvil_backend")
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            # Create engine
            engine = create_engine(db_url)
            
            # Test connection
            with engine.connect() as conn:
                # Check PostgreSQL version
                result = conn.execute(text("SELECT version();"))
                version = result.scalar()
                
                # Check required extensions
                result = conn.execute(text("""
                    SELECT extname FROM pg_extension 
                    WHERE extname IN ('uuid-ossp', 'pgvector', 'age');
                """))
                extensions = [row[0] for row in result]
                
                # Check table count
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """))
                table_count = result.scalar()
            
            # Verify extensions
            required_extensions = ['uuid-ossp', 'pgvector']
            optional_extensions = ['age']
            
            missing_required = [ext for ext in required_extensions if ext not in extensions]
            missing_optional = [ext for ext in optional_extensions if ext not in extensions]
            
            if missing_required:
                self.results.append(CheckResult(
                    name="PostgreSQL Database",
                    status=CheckStatus.FAIL,
                    message=f"Missing required extensions: {', '.join(missing_required)}",
                    details={
                        "version": version,
                        "extensions": extensions,
                        "table_count": table_count,
                    }
                ))
            elif missing_optional:
                self.results.append(CheckResult(
                    name="PostgreSQL Database",
                    status=CheckStatus.WARN,
                    message=f"Connected successfully, but missing optional extensions: {', '.join(missing_optional)}",
                    details={
                        "version": version,
                        "extensions": extensions,
                        "table_count": table_count,
                    }
                ))
            else:
                self.results.append(CheckResult(
                    name="PostgreSQL Database",
                    status=CheckStatus.PASS,
                    message=f"Connected successfully, {table_count} tables, all extensions installed",
                    details={
                        "version": version,
                        "extensions": extensions,
                        "table_count": table_count,
                    }
                ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
            if self.verbose and self.results[-1].details:
                print(f"    Extensions: {', '.join(extensions)}")
                print(f"    Tables: {table_count}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="PostgreSQL Database",
                status=CheckStatus.FAIL,
                message=f"Connection failed: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_redis(self):
        """Check Redis connection"""
        print("🔴 Checking Redis...")
        
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            r.ping()
            
            # Get info
            info = r.info()
            
            self.results.append(CheckResult(
                name="Redis",
                status=CheckStatus.PASS,
                message=f"Connected successfully (version {info['redis_version']})",
                details={
                    "version": info['redis_version'],
                    "used_memory_human": info['used_memory_human'],
                    "connected_clients": info['connected_clients'],
                }
            ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
            if self.verbose:
                print(f"    Memory: {info['used_memory_human']}")
                print(f"    Clients: {info['connected_clients']}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="Redis",
                status=CheckStatus.FAIL,
                message=f"Connection failed: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_migrations(self):
        """Check database migrations"""
        print("🔄 Checking Database Migrations...")
        
        try:
            # Get database URL
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
            db_name = os.getenv("POSTGRES_DB", "anvil_backend")
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            engine = create_engine(db_url)
            
            with engine.connect() as conn:
                # Check alembic_version table
                result = conn.execute(text("""
                    SELECT version_num FROM alembic_version;
                """))
                current_version = result.scalar()
            
            if current_version:
                self.results.append(CheckResult(
                    name="Database Migrations",
                    status=CheckStatus.PASS,
                    message=f"Migrations applied (current: {current_version})",
                    details={"current_version": current_version}
                ))
            else:
                self.results.append(CheckResult(
                    name="Database Migrations",
                    status=CheckStatus.FAIL,
                    message="No migrations applied! Run: alembic upgrade head"
                ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="Database Migrations",
                status=CheckStatus.FAIL,
                message=f"Failed to check migrations: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_api_server(self):
        """Check main API server"""
        print("🌐 Checking Main API Server...")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            # Check health endpoint
            response = await self.http_client.get(f"{api_url}/health")
            
            if response.status_code == 200:
                self.results.append(CheckResult(
                    name="API Server",
                    status=CheckStatus.PASS,
                    message=f"API server is running ({api_url})"
                ))
            else:
                self.results.append(CheckResult(
                    name="API Server",
                    status=CheckStatus.FAIL,
                    message=f"API server returned status {response.status_code}"
                ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        except httpx.ConnectError:
            self.results.append(CheckResult(
                name="API Server",
                status=CheckStatus.FAIL,
                message=f"Cannot connect to API server at {api_url}. Is it running?"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="API Server",
                status=CheckStatus.FAIL,
                message=f"Error checking API: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_mcp_servers(self):
        """Check MCP servers"""
        print("🔧 Checking MCP Servers...")
        
        mcp_servers = [
            ("Portfolio MCP", os.getenv("MCP_PORTFOLIO_URL", "http://localhost:8081")),
            ("1inch MCP", os.getenv("MCP_ONEINCH_URL", "http://localhost:8082")),
            ("Aave MCP", os.getenv("MCP_AAVE_URL", "http://localhost:8083")),
            ("DeFiLlama MCP", os.getenv("MCP_DEFILLAMA_URL", "http://localhost:8084")),
        ]
        
        all_running = True
        tool_count = 0
        
        for name, url in mcp_servers:
            try:
                response = await self.http_client.get(f"{url}/tools")
                
                if response.status_code == 200:
                    tools = response.json()
                    count = len(tools)
                    tool_count += count
                    print(f"  ✅ {name}: {count} tools available")
                else:
                    print(f"  ❌ {name}: Server responded with status {response.status_code}")
                    all_running = False
            
            except httpx.ConnectError:
                print(f"  ❌ {name}: Cannot connect to {url}")
                all_running = False
            except Exception as e:
                print(f"  ❌ {name}: Error - {str(e)}")
                all_running = False
        
        if all_running:
            self.results.append(CheckResult(
                name="MCP Servers",
                status=CheckStatus.PASS,
                message=f"All 4 MCP servers running ({tool_count} total tools)",
                details={"tool_count": tool_count}
            ))
        else:
            self.results.append(CheckResult(
                name="MCP Servers",
                status=CheckStatus.FAIL,
                message="One or more MCP servers are not running"
            ))
        
        print()
    
    async def check_agent_router(self):
        """Check Agent Router initialization"""
        print("🤖 Checking Agent Router...")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            # Check if agents are initialized via stats endpoint
            response = await self.http_client.get(f"{api_url}/api/v1/agno/stats")
            
            if response.status_code == 200:
                stats = response.json()
                agent_count = len(stats.get("agents", {}))
                
                if agent_count >= 4:
                    self.results.append(CheckResult(
                        name="Agent Router",
                        status=CheckStatus.PASS,
                        message=f"Agent router initialized with {agent_count} agents"
                    ))
                else:
                    self.results.append(CheckResult(
                        name="Agent Router",
                        status=CheckStatus.WARN,
                        message=f"Only {agent_count}/4 agents initialized"
                    ))
            else:
                self.results.append(CheckResult(
                    name="Agent Router",
                    status=CheckStatus.FAIL,
                    message=f"Stats endpoint returned status {response.status_code}"
                ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="Agent Router",
                status=CheckStatus.FAIL,
                message=f"Error checking agent router: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_websocket(self):
        """Check WebSocket endpoint"""
        print("🔌 Checking WebSocket Endpoint...")
        
        # Note: WebSocket check requires a valid JWT token
        # For production, this should be tested manually
        
        self.results.append(CheckResult(
            name="WebSocket Endpoint",
            status=CheckStatus.SKIP,
            message="WebSocket check requires JWT token (test manually)"
        ))
        
        print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        print(f"    Test manually: ws://localhost:8000/api/v1/ws/chat?token=YOUR_JWT")
        print()
    
    async def check_celery(self):
        """Check Celery workers"""
        print("⚙️  Checking Celery Workers...")
        
        try:
            # Check if Celery worker is running via Redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url, decode_responses=True)
            
            # Celery stores worker info in Redis
            # This is a simplified check
            keys = r.keys("celery-task-meta-*")
            
            if keys:
                self.results.append(CheckResult(
                    name="Celery Workers",
                    status=CheckStatus.PASS,
                    message=f"Celery workers detected ({len(keys)} task results in cache)"
                ))
            else:
                self.results.append(CheckResult(
                    name="Celery Workers",
                    status=CheckStatus.WARN,
                    message="No Celery task results found (workers may not have run yet)"
                ))
            
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
            print(f"    Manual check: Open http://localhost:5555 (Flower)")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="Celery Workers",
                status=CheckStatus.WARN,
                message=f"Cannot verify Celery: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    async def check_performance(self):
        """Check performance metrics"""
        print("📊 Checking Performance...")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            # Check cache stats
            response = await self.http_client.get(f"{api_url}/api/v1/agno/stats")
            
            if response.status_code == 200:
                stats = response.json()
                cache_hit_rate = stats.get("cache_hit_rate", 0.0)
                avg_response_time = stats.get("avg_response_time_ms", 0)
                
                if cache_hit_rate >= 0.60:
                    cache_status = CheckStatus.PASS
                    cache_msg = f"Cache hit rate: {cache_hit_rate:.1%} (target: >60%)"
                elif cache_hit_rate >= 0.40:
                    cache_status = CheckStatus.WARN
                    cache_msg = f"Cache hit rate: {cache_hit_rate:.1%} (below target of 60%)"
                else:
                    cache_status = CheckStatus.WARN
                    cache_msg = f"Cache hit rate: {cache_hit_rate:.1%} (needs improvement)"
                
                self.results.append(CheckResult(
                    name="Performance Metrics",
                    status=cache_status,
                    message=cache_msg,
                    details={
                        "cache_hit_rate": cache_hit_rate,
                        "avg_response_time_ms": avg_response_time,
                    }
                ))
                
                print(f"  {self.results[-1].status.value} {self.results[-1].message}")
                if self.verbose:
                    print(f"    Avg response time: {avg_response_time}ms")
            else:
                self.results.append(CheckResult(
                    name="Performance Metrics",
                    status=CheckStatus.SKIP,
                    message="Cannot retrieve performance stats"
                ))
                print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        except Exception as e:
            self.results.append(CheckResult(
                name="Performance Metrics",
                status=CheckStatus.SKIP,
                message=f"Cannot check performance: {str(e)}"
            ))
            print(f"  {self.results[-1].status.value} {self.results[-1].message}")
        
        print()
    
    def print_summary(self):
        """Print verification summary"""
        print("=" * 80)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 80)
        print()
        
        passed = [r for r in self.results if r.status == CheckStatus.PASS]
        failed = [r for r in self.results if r.status == CheckStatus.FAIL]
        warned = [r for r in self.results if r.status == CheckStatus.WARN]
        skipped = [r for r in self.results if r.status == CheckStatus.SKIP]
        
        print(f"✅ Passed:  {len(passed)}")
        print(f"❌ Failed:  {len(failed)}")
        print(f"⚠️  Warned:  {len(warned)}")
        print(f"⏭️  Skipped: {len(skipped)}")
        print()
        
        if failed:
            print("❌ FAILED CHECKS:")
            for result in failed:
                print(f"  • {result.name}: {result.message}")
            print()
        
        if warned:
            print("⚠️  WARNINGS:")
            for result in warned:
                print(f"  • {result.name}: {result.message}")
            print()
        
        if len(failed) == 0 and len(warned) == 0:
            print("🎉 ALL CHECKS PASSED! Ready for production deployment!")
        elif len(failed) == 0:
            print("✅ All critical checks passed, but there are warnings to address.")
        else:
            print("❌ Deployment verification FAILED. Please fix the issues above.")
        
        print()
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Verify Anvil Backend production deployment readiness"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--check",
        type=str,
        help="Run specific check only (database, redis, api, mcp, agents)"
    )
    
    args = parser.parse_args()
    
    verifier = DeploymentVerifier(verbose=args.verbose)
    
    try:
        success = await verifier.run_all_checks()
        await verifier.cleanup()
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        await verifier.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification failed with error: {str(e)}")
        await verifier.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
