"""
SQLAlchemy implementation of PortfolioRepository.

Provides persistence operations for portfolio snapshots and token holdings.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.domain.entities.portfolio_snapshot import (
    PortfolioSnapshot,
    PortfolioSnapshotId,
    TokenHolding,
    TokenHoldingId,
)
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.ports.portfolio.portfolio_repository import PortfolioRepository
from app.domain.value_objects.created_at import CreatedAt
from app.infrastructure.adapters.types import MainAsyncSession

logger = logging.getLogger(__name__)


class SqlaPortfolioRepository(PortfolioRepository):
    """SQLAlchemy implementation of PortfolioRepository."""

    def __init__(self, session: MainAsyncSession) -> None:
        """Initialize with SQLAlchemy session."""
        self._session = session

    async def get_by_id(
        self, snapshot_id: PortfolioSnapshotId
    ) -> PortfolioSnapshot | None:
        """Get portfolio snapshot by ID."""
        query = text("""
            SELECT id, wallet_id, chain, total_usd, native_balance,
                   native_usd_value, captured_at, created_at
            FROM portfolio_snapshots
            WHERE id = :snapshot_id
        """)

        result = await self._session.execute(query, {"snapshot_id": snapshot_id.value})
        row = result.mappings().first()

        if not row:
            return None

        snapshot = self._row_to_snapshot(row)

        # Load holdings
        holdings = await self._load_holdings(snapshot_id)
        for holding in holdings:
            snapshot.holdings.append(holding)

        return snapshot

    async def get_latest_by_wallet(
        self,
        wallet_id: WalletId,
        chain: ChainType | None = None,
    ) -> PortfolioSnapshot | None:
        """Get the most recent portfolio snapshot for a wallet."""
        query_str = """
            SELECT id, wallet_id, chain, total_usd, native_balance,
                   native_usd_value, captured_at, created_at
            FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
        """

        params: dict[str, Any] = {"wallet_id": wallet_id.value}

        if chain:
            query_str += " AND chain = :chain"
            params["chain"] = chain.value

        query_str += " ORDER BY captured_at DESC LIMIT 1"

        result = await self._session.execute(text(query_str), params)
        row = result.mappings().first()

        if not row:
            return None

        snapshot = self._row_to_snapshot(row)

        # Load holdings
        holdings = await self._load_holdings(snapshot.id_)
        for holding in holdings:
            snapshot.holdings.append(holding)

        return snapshot

    async def get_by_wallet(
        self,
        wallet_id: WalletId,
        *,
        chain: ChainType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PortfolioSnapshot]:
        """Get portfolio snapshots for a wallet."""
        query_str = """
            SELECT id, wallet_id, chain, total_usd, native_balance,
                   native_usd_value, captured_at, created_at
            FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
        """

        params: dict[str, Any] = {"wallet_id": wallet_id.value}

        if chain:
            query_str += " AND chain = :chain"
            params["chain"] = chain.value

        query_str += " ORDER BY captured_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = await self._session.execute(text(query_str), params)
        rows = result.mappings().all()

        snapshots = []
        for row in rows:
            snapshot = self._row_to_snapshot(row)
            # Load holdings for each snapshot
            holdings = await self._load_holdings(snapshot.id_)
            for holding in holdings:
                snapshot.holdings.append(holding)
            snapshots.append(snapshot)

        return snapshots

    async def get_history(
        self,
        wallet_id: WalletId,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
    ) -> list[PortfolioSnapshot]:
        """Get portfolio snapshot history for a date range."""
        query_str = """
            SELECT id, wallet_id, chain, total_usd, native_balance,
                   native_usd_value, captured_at, created_at
            FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
              AND captured_at >= :start_date
              AND captured_at <= :end_date
        """

        params: dict[str, Any] = {
            "wallet_id": wallet_id.value,
            "start_date": start_date,
            "end_date": end_date,
        }

        if chain:
            query_str += " AND chain = :chain"
            params["chain"] = chain.value

        query_str += " ORDER BY captured_at ASC"

        result = await self._session.execute(text(query_str), params)
        rows = result.mappings().all()

        snapshots = []
        for row in rows:
            snapshot = self._row_to_snapshot(row)
            holdings = await self._load_holdings(snapshot.id_)
            for holding in holdings:
                snapshot.holdings.append(holding)
            snapshots.append(snapshot)

        return snapshots

    async def save(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshot:
        """Save a new portfolio snapshot with its holdings."""
        # Insert snapshot
        insert_query = text("""
            INSERT INTO portfolio_snapshots
                (wallet_id, chain, total_usd, native_balance, native_usd_value, captured_at)
            VALUES
                (:wallet_id, :chain, :total_usd, :native_balance, :native_usd_value, :captured_at)
            RETURNING id
        """)

        result = await self._session.execute(
            insert_query,
            {
                "wallet_id": snapshot.wallet_id.value,
                "chain": snapshot.chain.value,
                "total_usd": snapshot.total_usd,
                "native_balance": snapshot.native_balance,
                "native_usd_value": snapshot.native_usd_value,
                "captured_at": snapshot.captured_at,
            },
        )

        row = result.mappings().first()
        snapshot_id = row["id"]

        # Update snapshot with new ID
        snapshot = PortfolioSnapshot(
            id_=PortfolioSnapshotId(snapshot_id),
            wallet_id=snapshot.wallet_id,
            chain=snapshot.chain,
            total_usd=snapshot.total_usd,
            native_balance=snapshot.native_balance,
            native_usd_value=snapshot.native_usd_value,
            captured_at=snapshot.captured_at,
            created_at=snapshot.created_at,
            holdings=[],
        )

        # Insert holdings
        for holding in snapshot.holdings:
            await self._insert_holding(PortfolioSnapshotId(snapshot_id), holding)

        await self._session.flush()

        return snapshot

    async def save_holding(self, holding: TokenHolding) -> TokenHolding:
        """Save a token holding to an existing snapshot."""
        return await self._insert_holding(holding.snapshot_id, holding)

    async def _insert_holding(
        self,
        snapshot_id: PortfolioSnapshotId,
        holding: TokenHolding,
    ) -> TokenHolding:
        """Insert a single token holding."""
        insert_query = text("""
            INSERT INTO token_holdings
                (snapshot_id, token_address, symbol, name, decimals, amount, usd_value, usd_price, percentage)
            VALUES
                (:snapshot_id, :token_address, :symbol, :name, :decimals, :amount, :usd_value, :usd_price, :percentage)
            RETURNING id
        """)

        result = await self._session.execute(
            insert_query,
            {
                "snapshot_id": snapshot_id.value,
                "token_address": holding.token_address,
                "symbol": holding.symbol,
                "name": holding.name,
                "decimals": holding.decimals,
                "amount": holding.amount,
                "usd_value": holding.usd_value,
                "usd_price": holding.usd_price,
                "percentage": Decimal(str(holding.percentage)),
            },
        )

        row = result.mappings().first()
        holding_id = row["id"]

        return TokenHolding(
            id_=TokenHoldingId(holding_id),
            snapshot_id=snapshot_id,
            token_address=holding.token_address,
            symbol=holding.symbol,
            name=holding.name,
            decimals=holding.decimals,
            amount=holding.amount,
            usd_value=holding.usd_value,
            usd_price=holding.usd_price,
            percentage=holding.percentage,
        )

    async def delete(self, snapshot_id: PortfolioSnapshotId) -> bool:
        """Delete a portfolio snapshot and its holdings."""
        # Holdings are deleted via CASCADE
        delete_query = text("""
            DELETE FROM portfolio_snapshots WHERE id = :snapshot_id
        """)

        result = await self._session.execute(
            delete_query, {"snapshot_id": snapshot_id.value}
        )
        await self._session.flush()

        return result.rowcount > 0

    async def delete_old_snapshots(
        self,
        wallet_id: WalletId,
        *,
        keep_count: int = 100,
    ) -> int:
        """Delete old snapshots for a wallet, keeping the most recent ones."""
        # Get IDs to keep
        keep_query = text("""
            SELECT id FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
            ORDER BY captured_at DESC
            LIMIT :keep_count
        """)

        keep_result = await self._session.execute(
            keep_query,
            {"wallet_id": wallet_id.value, "keep_count": keep_count},
        )
        keep_ids = [row["id"] for row in keep_result.mappings().all()]

        if not keep_ids:
            return 0

        # Delete all except the ones to keep
        # Convert list to tuple for IN clause
        delete_query = text("""
            DELETE FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
              AND id NOT IN :keep_ids
        """)

        result = await self._session.execute(
            delete_query,
            {"wallet_id": wallet_id.value, "keep_ids": tuple(keep_ids)},
        )
        await self._session.flush()

        return result.rowcount

    async def count_snapshots(self, wallet_id: WalletId | None = None) -> int:
        """Count total portfolio snapshots."""
        if wallet_id:
            query = text("""
                SELECT COUNT(*) as count FROM portfolio_snapshots WHERE wallet_id = :wallet_id
            """)
            result = await self._session.execute(query, {"wallet_id": wallet_id.value})
        else:
            query = text("SELECT COUNT(*) as count FROM portfolio_snapshots")
            result = await self._session.execute(query)

        row = result.mappings().first()
        return row["count"] if row else 0

    async def get_portfolio_value_history(
        self,
        wallet_id: WalletId,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, float]]:
        """Get portfolio total USD value history for charts."""
        query = text("""
            SELECT captured_at, total_usd
            FROM portfolio_snapshots
            WHERE wallet_id = :wallet_id
              AND captured_at >= :start_date
              AND captured_at <= :end_date
            ORDER BY captured_at ASC
        """)

        result = await self._session.execute(
            query,
            {
                "wallet_id": wallet_id.value,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        return [
            (row["captured_at"], float(row["total_usd"]))
            for row in result.mappings().all()
        ]

    async def _load_holdings(
        self, snapshot_id: PortfolioSnapshotId
    ) -> list[TokenHolding]:
        """Load all holdings for a snapshot."""
        query = text("""
            SELECT id, snapshot_id, token_address, symbol, name, decimals,
                   amount, usd_value, usd_price, percentage
            FROM token_holdings
            WHERE snapshot_id = :snapshot_id
            ORDER BY usd_value DESC NULLS LAST
        """)

        result = await self._session.execute(query, {"snapshot_id": snapshot_id.value})

        return [self._row_to_holding(row) for row in result.mappings().all()]

    def _row_to_snapshot(self, row: Any) -> PortfolioSnapshot:
        """Convert database row to PortfolioSnapshot entity."""
        return PortfolioSnapshot(
            id_=PortfolioSnapshotId(row["id"]),
            wallet_id=WalletId(row["wallet_id"]),
            chain=ChainType(row["chain"]),
            total_usd=Decimal(str(row["total_usd"]))
            if row["total_usd"]
            else Decimal("0"),
            native_balance=Decimal(str(row["native_balance"]))
            if row["native_balance"]
            else Decimal("0"),
            native_usd_value=Decimal(str(row["native_usd_value"]))
            if row["native_usd_value"]
            else None,
            captured_at=row["captured_at"],
            created_at=CreatedAt(row["created_at"]),
            holdings=[],
        )

    def _row_to_holding(self, row: Any) -> TokenHolding:
        """Convert database row to TokenHolding entity."""
        return TokenHolding(
            id_=TokenHoldingId(row["id"]),
            snapshot_id=PortfolioSnapshotId(row["snapshot_id"]),
            token_address=row["token_address"],
            symbol=row["symbol"],
            name=row["name"],
            decimals=row["decimals"],
            amount=Decimal(str(row["amount"])) if row["amount"] else Decimal("0"),
            usd_value=Decimal(str(row["usd_value"])) if row["usd_value"] else None,
            usd_price=Decimal(str(row["usd_price"])) if row["usd_price"] else None,
            percentage=float(row["percentage"]) if row["percentage"] else 0.0,
        )
