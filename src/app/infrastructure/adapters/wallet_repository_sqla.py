"""
SQLAlchemy implementation of WalletRepository.

Handles CRUD operations for wallets stored locally in the database.
Includes support for Privy wallet configuration fields.
Includes analytics methods for admin metrics.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, and_, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.wallet import AdditionalSigner, Wallet, WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_id import UserId
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaWalletRepository(WalletRepository):
    """SQLAlchemy implementation of WalletRepository."""

    def __init__(self, session: MainAsyncSession):
        map_wallet_tables()
        self._session = session

    def _get_table(self):
        """Get the wallets table from registry."""
        return mapping_registry.metadata.tables["wallets"]

    def _row_to_wallet(self, row: dict[str, Any]) -> Wallet:
        """Convert a database row to a Wallet entity."""
        # Parse chain type, defaulting to ETHEREUM if unknown
        chain_str = row.get("default_chain")
        try:
            default_chain = ChainType(chain_str) if chain_str else ChainType.ETHEREUM
        except ValueError:
            default_chain = ChainType.ETHEREUM

        # Parse provider
        provider_str = row.get("provider")
        try:
            provider = (
                WalletProvider(provider_str) if provider_str else WalletProvider.PRIVY
            )
        except ValueError:
            provider = WalletProvider.PRIVY

        # Parse status
        status_val = row.get("status", WalletStatus.ACTIVE.value)
        try:
            status = WalletStatus(status_val)
        except ValueError:
            status = WalletStatus.ACTIVE

        # Parse timestamps
        created_at_val = row.get("created_at")
        updated_at_val = row.get("updated_at")

        if created_at_val:
            created_at = CreatedAt(created_at_val)
        else:
            created_at = CreatedAt(datetime.now(UTC))
        updated_at = (
            UpdatedAt(updated_at_val)
            if updated_at_val
            else UpdatedAt(datetime.now(UTC))
        )

        # Parse policy_ids (JSON array)
        policy_ids_raw = row.get("policy_ids")
        policy_ids: list[str] = (
            policy_ids_raw if isinstance(policy_ids_raw, list) else []
        )

        # Parse additional_signers (JSON array of objects)
        additional_signers_raw = row.get("additional_signers")
        additional_signers: list[AdditionalSigner] = []
        if isinstance(additional_signers_raw, list):
            for signer_data in additional_signers_raw:
                if isinstance(signer_data, dict):
                    additional_signers.append(AdditionalSigner.from_dict(signer_data))

        return Wallet(
            id_=WalletId(row["id"]),
            user_id=UserId(row["user_id"]),
            privy_wallet_id=row.get("privy_wallet_id"),
            address=row["address"],
            provider=provider,
            default_chain=default_chain,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            # Privy configuration fields
            policy_ids=policy_ids,
            owner_type=row.get("owner_type"),
            owner_id=row.get("owner_id"),
            additional_signers=additional_signers,
            exported_at=row.get("exported_at"),
            imported_at=row.get("imported_at"),
            last_privy_sync_at=row.get("last_privy_sync_at"),
        )

    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None:
        """Get wallet by ID."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(table.c.id == wallet_id.value)
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_wallet(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_address(self, address: str) -> Wallet | None:
        """Get wallet by blockchain address."""
        try:
            table = self._get_table()
            # Case-insensitive address comparison
            stmt: Select = select(table).where(table.c.address == address.lower())
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_wallet(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_privy_wallet_id(self, privy_wallet_id: str) -> Wallet | None:
        """Get wallet by Privy wallet ID."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(
                table.c.privy_wallet_id == privy_wallet_id
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_wallet(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]:
        """Get all wallets for a specific user."""
        try:
            # Check if transaction is in failed state and rollback if needed
            try:
                from sqlalchemy import text
                await self._session.execute(text("SELECT 1"))
            except Exception:
                # Transaction is in failed state, rollback first
                await self._session.rollback()
            
            table = self._get_table()
            stmt: Select = (
                select(table)
                .where(table.c.user_id == user_id.value)
                .order_by(table.c.created_at.desc())
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_wallet(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            # Rollback on error to prevent InFailedSqlTransaction
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_user_and_address(
        self,
        user_id: UserId,
        address: str,
    ) -> Wallet | None:
        """Get wallet by user ID and address combination."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(
                and_(
                    table.c.user_id == user_id.value,
                    table.c.address == address.lower(),
                )
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_wallet(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_user_and_provider(
        self,
        user_id: UserId,
        provider: WalletProvider,
    ) -> list[Wallet]:
        """Get all wallets for a user with a specific provider."""
        try:
            table = self._get_table()
            stmt: Select = (
                select(table)
                .where(
                    and_(
                        table.c.user_id == user_id.value,
                        table.c.provider == provider.value,
                    )
                )
                .order_by(table.c.created_at.desc())
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_wallet(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def save(self, wallet: Wallet) -> Wallet:
        """Save a new wallet to the database."""
        try:
            table = self._get_table()

            # Serialize additional_signers to JSON-compatible format
            additional_signers_json = (
                [signer.to_dict() for signer in wallet.additional_signers]
                if wallet.additional_signers
                else None
            )

            result = await self._session.execute(
                table.insert()
                .values(
                    user_id=wallet.user_id.value,
                    privy_wallet_id=wallet.privy_wallet_id,
                    address=wallet.address.lower(),
                    provider=wallet.provider.value,
                    default_chain=wallet.default_chain.value,
                    status=wallet.status.value,
                    created_at=wallet.created_at.value,
                    updated_at=wallet.updated_at.value,
                    # Privy configuration fields
                    policy_ids=wallet.policy_ids if wallet.policy_ids else None,
                    owner_type=wallet.owner_type,
                    owner_id=wallet.owner_id,
                    additional_signers=additional_signers_json,
                    exported_at=wallet.exported_at,
                    imported_at=wallet.imported_at,
                    last_privy_sync_at=wallet.last_privy_sync_at,
                )
                .returning(table.c.id)
            )
            new_id = result.scalar_one()
            await self._session.commit()

            # Return wallet with generated ID
            return Wallet(
                id_=WalletId(new_id),
                user_id=wallet.user_id,
                privy_wallet_id=wallet.privy_wallet_id,
                address=wallet.address.lower(),
                provider=wallet.provider,
                default_chain=wallet.default_chain,
                status=wallet.status,
                created_at=wallet.created_at,
                updated_at=wallet.updated_at,
                # Privy configuration fields
                policy_ids=wallet.policy_ids,
                owner_type=wallet.owner_type,
                owner_id=wallet.owner_id,
                additional_signers=wallet.additional_signers,
                exported_at=wallet.exported_at,
                imported_at=wallet.imported_at,
                last_privy_sync_at=wallet.last_privy_sync_at,
            )
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update(self, wallet: Wallet) -> Wallet:
        """Update an existing wallet."""
        try:
            table = self._get_table()

            # Serialize additional_signers to JSON-compatible format
            additional_signers_json = (
                [signer.to_dict() for signer in wallet.additional_signers]
                if wallet.additional_signers
                else None
            )

            await self._session.execute(
                update(table)
                .where(table.c.id == wallet.id_.value)
                .values(
                    privy_wallet_id=wallet.privy_wallet_id,
                    address=wallet.address.lower(),
                    provider=wallet.provider.value,
                    default_chain=wallet.default_chain.value,
                    status=wallet.status.value,
                    updated_at=datetime.now(UTC),
                    # Privy configuration fields
                    policy_ids=wallet.policy_ids if wallet.policy_ids else None,
                    owner_type=wallet.owner_type,
                    owner_id=wallet.owner_id,
                    additional_signers=additional_signers_json,
                    exported_at=wallet.exported_at,
                    imported_at=wallet.imported_at,
                    last_privy_sync_at=wallet.last_privy_sync_at,
                )
            )
            await self._session.commit()
            return wallet
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def upsert(
        self,
        user_id: UserId,
        address: str,
        provider: WalletProvider,
        privy_wallet_id: str | None = None,
        chain_type: str | None = None,
    ) -> Wallet:
        """
        Insert or update a wallet by user_id + address.

        Uses PostgreSQL's ON CONFLICT to perform upsert.
        """
        try:
            # Check if transaction is in failed state and rollback if needed
            try:
                from sqlalchemy import text
                await self._session.execute(text("SELECT 1"))
            except Exception:
                # Transaction is in failed state, rollback first
                await self._session.rollback()
            
            table = self._get_table()
            now = datetime.now(UTC)

            # Normalize address
            normalized_address = address.lower()

            # Generate synthetic ID for imported wallets if not provided
            wallet_id = privy_wallet_id
            if wallet_id is None and provider == WalletProvider.IMPORTED:
                wallet_id = f"imported:{normalized_address}"

            # Parse chain type - handle Privy's bitcoin-segwit/bitcoin-taproot formats
            default_chain = ChainType.ETHEREUM
            if chain_type:
                chain_lower = chain_type.lower()
                if chain_lower in ("bitcoin", "bitcoin-segwit", "bitcoin-taproot"):
                    default_chain = ChainType.BITCOIN
                elif chain_lower == "bitcoin_testnet":
                    default_chain = ChainType.BITCOIN_TESTNET
                else:
                    try:
                        default_chain = ChainType(chain_type)
                    except ValueError:
                        default_chain = ChainType.ETHEREUM

            # PostgreSQL upsert
            stmt = pg_insert(table).values(
                user_id=user_id.value,
                privy_wallet_id=wallet_id,
                address=normalized_address,
                provider=provider.value,
                default_chain=default_chain.value,
                status=WalletStatus.ACTIVE.value,
                created_at=now,
                updated_at=now,
            )

            # On conflict update existing row
            stmt = stmt.on_conflict_do_update(
                constraint="unique_user_wallet_address",
                set_={
                    "privy_wallet_id": wallet_id,
                    "provider": provider.value,
                    "default_chain": default_chain.value,
                    "updated_at": now,
                },
            ).returning(table)

            result = await self._session.execute(stmt)
            row = result.mappings().first()
            await self._session.commit()

            if row:
                return self._row_to_wallet(dict(row))

            # Fallback: fetch the wallet if returning didn't work
            return await self.get_by_user_and_address(user_id, normalized_address)  # type: ignore

        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def delete(self, wallet_id: WalletId) -> bool:
        """Delete a wallet by ID."""
        try:
            table = self._get_table()
            result = await self._session.execute(
                delete(table).where(table.c.id == wallet_id.value)
            )
            await self._session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def delete_by_user_and_address(
        self,
        user_id: UserId,
        address: str,
    ) -> bool:
        """Delete a wallet by user ID and address."""
        try:
            table = self._get_table()
            result = await self._session.execute(
                delete(table).where(
                    and_(
                        table.c.user_id == user_id.value,
                        table.c.address == address.lower(),
                    )
                )
            )
            await self._session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def mark_exported(self, privy_wallet_id: str) -> bool:
        """
        Mark a wallet as exported by setting exported_at timestamp.

        Args:
            privy_wallet_id: The Privy wallet ID.

        Returns:
            True if updated, False if wallet not found in local DB.
        """
        try:
            table = self._get_table()
            now = datetime.now(UTC)

            result = await self._session.execute(
                update(table)
                .where(table.c.privy_wallet_id == privy_wallet_id)
                .values(exported_at=now, updated_at=now)
            )
            await self._session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    # ============================================================
    # Analytics Methods (for Admin Metrics)
    # ============================================================

    async def count_all(self) -> int:
        """Count total number of wallets in the system."""
        try:
            table = self._get_table()
            stmt = select(func.count()).select_from(table)
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_by_provider(self, provider: WalletProvider) -> int:
        """Count wallets by provider type."""
        try:
            table = self._get_table()
            stmt = (
                select(func.count())
                .select_from(table)
                .where(table.c.provider == provider.value)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_active_wallets(self) -> int:
        """Count wallets with ACTIVE status."""
        try:
            table = self._get_table()
            stmt = (
                select(func.count())
                .select_from(table)
                .where(table.c.status == WalletStatus.ACTIVE.value)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_wallet_counts_by_provider(self) -> dict[str, int]:
        """Get wallet counts grouped by provider."""
        try:
            table = self._get_table()
            stmt = (
                select(table.c.provider, func.count().label("count"))
                .group_by(table.c.provider)
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return {row.provider: row.count for row in rows}
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_wallets_created_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Wallet]:
        """Get wallets created within a date range."""
        try:
            table = self._get_table()
            stmt: Select = (
                select(table)
                .where(
                    and_(
                        table.c.created_at >= start_date,
                        table.c.created_at <= end_date,
                    )
                )
                .order_by(table.c.created_at.desc())
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_wallet(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_wallets_created_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count wallets created within a date range."""
        try:
            table = self._get_table()
            stmt = (
                select(func.count())
                .select_from(table)
                .where(
                    and_(
                        table.c.created_at >= start_date,
                        table.c.created_at <= end_date,
                    )
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_daily_wallet_counts(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, int]]:
        """Get daily wallet creation counts for a date range."""
        try:
            table = self._get_table()
            # Use PostgreSQL date_trunc for daily grouping
            stmt = (
                select(
                    func.date_trunc("day", table.c.created_at).label("date"),
                    func.count().label("count"),
                )
                .where(
                    and_(
                        table.c.created_at >= start_date,
                        table.c.created_at <= end_date,
                    )
                )
                .group_by(func.date_trunc("day", table.c.created_at))
                .order_by(func.date_trunc("day", table.c.created_at))
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return [(row.date, row.count) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error
