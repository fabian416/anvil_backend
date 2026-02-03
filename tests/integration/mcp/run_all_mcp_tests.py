#!/usr/bin/env python3
"""
Master test runner for all MCP Server integration tests.

This script runs comprehensive tests for all 11 MCP servers:

Core Data & Market Intelligence (6 servers):
  - 1inch MCP Server (port 8081) - DEX aggregator
  - DeFiLlama MCP Server (port 8082) - TVL and protocol data
  - TheGraph MCP Server (port 8083) - Subgraph queries
  - CoinGecko MCP Server (port 8084) - Token prices and market data
  - Aave MCP Server (port 8085) - Lending protocol
  - Portfolio MCP Server (port 8086) - User portfolio management

Advanced DeFi & Trading (5 servers):
  - Perplexity MCP Server (port 8087) - AI research
  - Morpho MCP Server (port 8088) - Optimized lending
  - Curve MCP Server (port 8089) - Stable swaps
  - Hyperliquid MCP Server (port 8090) - Perpetual futures
  - LayerZero MCP Server (port 8091) - Cross-chain messaging

Usage:
    # Run all MCP tests
    python -m pytest tests/integration/mcp/ -v

    # Run specific server tests
    python -m pytest tests/integration/mcp/test_aave_mcp.py -v

    # Run with coverage
    python -m pytest tests/integration/mcp/ -v --cov=src/app/infrastructure/mcp

    # Run only integration tests
    python -m pytest tests/integration/mcp/ -v -m integration

    # Run this script directly
    python tests/integration/mcp/run_all_mcp_tests.py
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


# MCP Server definitions
MCP_SERVERS = [
    # Core Data & Market Intelligence
    {"name": "1inch", "port": 8081, "test_file": "test_oneinch_server.py", "tools": 4},
    {
        "name": "DeFiLlama",
        "port": 8082,
        "test_file": "test_all_mcp_servers.py",
        "tools": 5,
    },
    {
        "name": "TheGraph",
        "port": 8083,
        "test_file": "test_all_mcp_servers.py",
        "tools": 4,
    },
    {
        "name": "CoinGecko",
        "port": 8084,
        "test_file": "test_all_mcp_servers.py",
        "tools": 6,
    },
    {"name": "Aave", "port": 8085, "test_file": "test_aave_mcp.py", "tools": 9},
    {
        "name": "Portfolio",
        "port": 8086,
        "test_file": "test_portfolio_mcp.py",
        "tools": 3,
    },
    # Advanced DeFi & Trading
    {
        "name": "Perplexity",
        "port": 8087,
        "test_file": "test_perplexity_mcp.py",
        "tools": 2,
    },
    {"name": "Morpho", "port": 8088, "test_file": "test_morpho_mcp.py", "tools": 6},
    {"name": "Curve", "port": 8089, "test_file": "test_curve_mcp.py", "tools": 7},
    {
        "name": "Hyperliquid",
        "port": 8090,
        "test_file": "test_hyperliquid_mcp.py",
        "tools": 9,
    },
    {
        "name": "LayerZero",
        "port": 8091,
        "test_file": "test_layerzero_mcp.py",
        "tools": 6,
    },
]


def print_header():
    """Print test suite header."""
    print("\n" + "=" * 70)
    print("         MCP SERVER INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nTesting all 11 MCP servers:")
    print("\n  Core Data & Market Intelligence:")
    for server in MCP_SERVERS[:6]:
        print(
            f"    ✓ {server['name']:12} (port {server['port']}) - {server['tools']} tools"
        )
    print("\n  Advanced DeFi & Trading:")
    for server in MCP_SERVERS[6:]:
        print(
            f"    ✓ {server['name']:12} (port {server['port']}) - {server['tools']} tools"
        )
    print("\n" + "-" * 70)


def get_test_files() -> List[str]:
    """Get all unique test files."""
    test_dir = Path(__file__).parent
    test_files = set()

    for server in MCP_SERVERS:
        test_file = test_dir / server["test_file"]
        if test_file.exists():
            test_files.add(str(test_file))

    # Add additional test files
    additional_files = [
        "test_base_server.py",
        "test_mcp_exceptions.py",
        "test_mcp_flags.py",
        "test_mcp_server_retry.py",
    ]

    for filename in additional_files:
        filepath = test_dir / filename
        if filepath.exists():
            test_files.add(str(filepath))

    return sorted(test_files)


def run_tests(verbose: bool = True, coverage: bool = False) -> Tuple[int, str]:
    """
    Run all MCP integration tests.

    Args:
        verbose: Enable verbose output
        coverage: Enable coverage reporting

    Returns:
        Tuple of (exit_code, output)
    """
    test_dir = Path(__file__).parent

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-m",
        "integration",
    ]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=src/app/infrastructure/mcp",
            "--cov-report=term-missing",
        ])

    # Add color output
    cmd.append("--color=yes")

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_specific_server_tests(server_name: str) -> int:
    """Run tests for a specific MCP server."""
    server = next(
        (s for s in MCP_SERVERS if s["name"].lower() == server_name.lower()), None
    )

    if not server:
        print(f"Error: Unknown server '{server_name}'")
        print(f"Available servers: {', '.join(s['name'] for s in MCP_SERVERS)}")
        return 1

    test_dir = Path(__file__).parent
    test_file = test_dir / server["test_file"]

    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return 1

    print(f"\nRunning tests for {server['name']} MCP Server...")
    print(f"  Port: {server['port']}")
    print(f"  Tools: {server['tools']}")
    print("-" * 50)

    cmd = [sys.executable, "-m", "pytest", str(test_file), "-v", "--color=yes"]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def print_summary():
    """Print test execution summary."""
    total_tools = sum(s["tools"] for s in MCP_SERVERS)

    print("\n" + "-" * 70)
    print("TEST SUMMARY")
    print("-" * 70)
    print(f"  Total MCP Servers: {len(MCP_SERVERS)}")
    print(f"  Total Tools: {total_tools}")
    print(f"  Test Files: {len(get_test_files())}")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run MCP Server integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all tests
    python run_all_mcp_tests.py
    
    # Run tests for specific server
    python run_all_mcp_tests.py --server aave
    
    # Run with coverage
    python run_all_mcp_tests.py --coverage
    
    # Quick mode (no verbose)
    python run_all_mcp_tests.py --quick
        """,
    )

    parser.add_argument(
        "--server", "-s", type=str, help="Run tests for specific server only"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Enable coverage reporting"
    )
    parser.add_argument(
        "--quick", "-q", action="store_true", help="Quick mode (less verbose)"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all MCP servers and exit"
    )

    args = parser.parse_args()

    if args.list:
        print_header()
        print_summary()
        return 0

    print_header()

    if args.server:
        exit_code = run_specific_server_tests(args.server)
    else:
        exit_code = run_tests(verbose=not args.quick, coverage=args.coverage)

    print_summary()

    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
