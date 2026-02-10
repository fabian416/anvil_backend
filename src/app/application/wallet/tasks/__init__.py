"""Wallet background tasks."""

from app.application.wallet.tasks.generate_wallet_qr import GenerateWalletQRTask

__all__ = [
    "GenerateWalletQRTask",
]
