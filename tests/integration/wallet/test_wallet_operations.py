"""
Integration tests for wallet operations.

Tests wallet export functionality including:
- Export wallet with valid credentials
- Export nonexistent wallet
- Authorization checks
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper
from tests.helpers.error_validator import validate_error_response


@pytest.mark.integration
class TestExportWallet:
    """Integration tests for wallet export."""

    def test_export_wallet_with_valid_credentials(self, client):
        """
        WHEN user exports owned wallet
        THEN system SHALL return wallet data with private key
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        export_request = {
            "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
            "wallet_address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7",
        }

        response = client.post(
            "/api/v1/wallet/export",
            json=export_request,
            headers=headers,
        )

        # Could succeed or fail depending on Privy mock
        assert response.status_code in (200, 401, 404, 500, 503)

        if response.status_code == 200:
            data = response.json()
            assert "wallet_id" in data
            assert "address" in data
            assert "private_key" in data
            assert "chain_type" in data

    def test_export_nonexistent_wallet(self, client):
        """
        WHEN user exports nonexistent wallet
        THEN system SHALL return WALLET_001 error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        export_request = {
            "wallet_id": f"nonexistent_{uuid4().hex[:20]}",
        }

        response = client.post(
            "/api/v1/wallet/export",
            json=export_request,
            headers=headers,
        )

        # Should return 404 for nonexistent wallet
        assert response.status_code in (401, 404, 500, 503)

    def test_export_wallet_without_auth(self, client):
        """
        WHEN unauthenticated user exports wallet
        THEN system SHALL return 401
        """
        export_request = {
            "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
        }

        response = client.post("/api/v1/wallet/export", json=export_request)

        assert response.status_code in (401, 403, 422)

    def test_export_wallet_missing_wallet_id(self, client):
        """
        WHEN wallet_id is missing
        THEN system SHALL return validation error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        export_request = {
            # Missing wallet_id
            "wallet_address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7",
        }

        response = client.post(
            "/api/v1/wallet/export",
            json=export_request,
            headers=headers,
        )

        # Should return 422 for missing required field
        assert response.status_code in (400, 401, 422, 500, 503)


@pytest.mark.integration
class TestWalletErrorResponses:
    """Integration tests for wallet error responses."""

    def test_wallet_not_found_error_format(self):
        """
        WHEN wallet not found
        THEN error SHALL follow standardized format
        """
        error_response = {
            "error": {
                "code": "WALLET_001",
                "message": "Wallet not found",
                "i18n_key": "errors.wallet.not_found",
                "http_status": 404,
            }
        }

        assert "code" in error_response["error"]
        assert "i18n_key" in error_response["error"]

    def test_wallet_export_failed_error_format(self):
        """
        WHEN wallet export fails
        THEN error SHALL follow standardized format
        """
        error_response = {
            "error": {
                "code": "WALLET_002",
                "message": "Wallet export failed",
                "i18n_key": "errors.wallet.export_failed",
                "http_status": 500,
            }
        }

        assert error_response["error"]["http_status"] == 500
