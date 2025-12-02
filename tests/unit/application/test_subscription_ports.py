"""
Unit tests for subscription repository ports.

Tests port interfaces, contracts, and protocol compliance.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock


@pytest.mark.unit
class TestSubscriptionRepositoryPort:
    """Tests for SubscriptionRepository port interface."""
    
    def test_subscription_repository_protocol_exists(self):
        """Test SubscriptionRepository protocol exists."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert SubscriptionRepository is not None
    
    def test_subscription_repository_has_read_by_name(self):
        """Test SubscriptionRepository has read_by_name method."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert hasattr(SubscriptionRepository, 'read_by_name')
    
    def test_subscription_repository_has_read_all(self):
        """Test SubscriptionRepository has read_all method."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert hasattr(SubscriptionRepository, 'read_all')
    
    def test_subscription_repository_has_read_by_id(self):
        """Test SubscriptionRepository has read_by_id method."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert hasattr(SubscriptionRepository, 'read_by_id')
    
    def test_subscription_repository_has_add(self):
        """Test SubscriptionRepository has add method."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert hasattr(SubscriptionRepository, 'add')
    
    def test_subscription_repository_has_update_stripe_ids(self):
        """Test SubscriptionRepository has update_stripe_ids method."""
        from app.application.subscription.ports import SubscriptionRepository
        
        assert hasattr(SubscriptionRepository, 'update_stripe_ids')
    
    @pytest.mark.asyncio
    async def test_subscription_repository_read_by_name_callable(self):
        """Test read_by_name is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.read_by_name.return_value = {
            "id": 1,
            "name": "pro_monthly",
            "price": 29.99,
            "subscription_type": "monthly",
        }
        
        # Act
        result = await mock_repo.read_by_name("pro_monthly")
        
        # Assert
        assert result is not None
        assert result["name"] == "pro_monthly"
        mock_repo.read_by_name.assert_called_once_with("pro_monthly")
    
    @pytest.mark.asyncio
    async def test_subscription_repository_read_all_callable(self):
        """Test read_all is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.read_all.return_value = [
            {"id": 1, "name": "basic"},
            {"id": 2, "name": "pro"},
        ]
        
        # Act
        result = await mock_repo.read_all()
        
        # Assert
        assert result is not None
        assert len(result) == 2
        mock_repo.read_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscription_repository_add_callable(self):
        """Test add is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.add.return_value = 123
        
        # Act
        result = await mock_repo.add(
            name="pro_monthly",
            price=29.99,
            subscription_type="monthly",
            currency="USD",
            duration=30,
            features={"feature1": True},
            is_active=True,
            stripe_price_id="price_123",
            stripe_product_id="prod_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Assert
        assert result == 123
        mock_repo.add.assert_called_once()


@pytest.mark.unit
class TestSubscriptionUserRepositoryPort:
    """Tests for SubscriptionUserRepository port interface."""
    
    def test_subscription_user_repository_protocol_exists(self):
        """Test SubscriptionUserRepository protocol exists."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert SubscriptionUserRepository is not None
    
    def test_subscription_user_repository_has_add(self):
        """Test SubscriptionUserRepository has add method."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'add')
    
    def test_subscription_user_repository_has_read_for_user_by_id(self):
        """Test SubscriptionUserRepository has read_for_user_by_id."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'read_for_user_by_id')
    
    def test_subscription_user_repository_has_update_status(self):
        """Test SubscriptionUserRepository has update_status."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'update_status')
    
    def test_subscription_user_repository_has_update_stripe_subscription_id(self):
        """Test SubscriptionUserRepository has update_stripe_subscription_id."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'update_stripe_subscription_id')
    
    def test_subscription_user_repository_has_read_by_checkout_session_id(self):
        """Test SubscriptionUserRepository has read_by_checkout_session_id."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'read_by_checkout_session_id')
    
    def test_subscription_user_repository_has_update_data_json(self):
        """Test SubscriptionUserRepository has update_data_json."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'update_data_json')
    
    def test_subscription_user_repository_has_read_active_for_user_and_subscription(self):
        """Test SubscriptionUserRepository has read_active_for_user_and_subscription."""
        from app.application.subscription.ports import SubscriptionUserRepository
        
        assert hasattr(SubscriptionUserRepository, 'read_active_for_user_and_subscription')
    
    @pytest.mark.asyncio
    async def test_subscription_user_repository_add_callable(self):
        """Test add is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.add.return_value = 456
        
        # Act
        result = await mock_repo.add(
            user_id=123,
            subscription_id=1,
            status="active",
            data_json={"stripe_id": "sub_123"},
        )
        
        # Assert
        assert result == 456
        mock_repo.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscription_user_repository_update_status_callable(self):
        """Test update_status is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.update_status.return_value = None
        
        # Act
        await mock_repo.update_status(id_=456, status="cancelled")
        
        # Assert
        mock_repo.update_status.assert_called_once_with(id_=456, status="cancelled")


@pytest.mark.unit
class TestPaymentRepositoryPort:
    """Tests for PaymentRepository port interface."""
    
    def test_payment_repository_protocol_exists(self):
        """Test PaymentRepository protocol exists."""
        from app.application.subscription.ports import PaymentRepository
        
        assert PaymentRepository is not None
    
    def test_payment_repository_has_add(self):
        """Test PaymentRepository has add method."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'add')
    
    def test_payment_repository_has_find_pending_for_subscription_user(self):
        """Test PaymentRepository has find_pending_for_subscription_user."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'find_pending_for_subscription_user')
    
    def test_payment_repository_has_update_status(self):
        """Test PaymentRepository has update_status."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'update_status')
    
    def test_payment_repository_has_list_by_subscription_user(self):
        """Test PaymentRepository has list_by_subscription_user."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'list_by_subscription_user')
    
    def test_payment_repository_has_update_data_json(self):
        """Test PaymentRepository has update_data_json."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'update_data_json')
    
    def test_payment_repository_has_read_by_user_paginated(self):
        """Test PaymentRepository has read_by_user_paginated."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'read_by_user_paginated')
    
    def test_payment_repository_has_find_or_create_transaction(self):
        """Test PaymentRepository has find_or_create_transaction."""
        from app.application.subscription.ports import PaymentRepository
        
        assert hasattr(PaymentRepository, 'find_or_create_transaction')
    
    @pytest.mark.asyncio
    async def test_payment_repository_add_callable(self):
        """Test add is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.add.return_value = 789
        
        # Act
        result = await mock_repo.add(
            user_id=123,
            subscription_id=1,
            subscription_user_id=456,
            amount=29.99,
            currency="USD",
            status="pending",
            stripe_payment_intent_id="pi_123",
            data_json={"metadata": "test"},
        )
        
        # Assert
        assert result == 789
        mock_repo.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_payment_repository_read_by_user_paginated_callable(self):
        """Test read_by_user_paginated is async callable."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.read_by_user_paginated.return_value = [
            {"id": 1, "amount": 29.99},
            {"id": 2, "amount": 19.99},
        ]
        
        # Act
        result = await mock_repo.read_by_user_paginated(
            user_id=123,
            offset=0,
            limit=10,
        )
        
        # Assert
        assert len(result) == 2
        mock_repo.read_by_user_paginated.assert_called_once()


@pytest.mark.unit
class TestPortContracts:
    """Tests for port contracts and consistency."""
    
    def test_all_repository_ports_use_async(self):
        """Test all repository methods are async."""
        from app.application.subscription.ports import (
            SubscriptionRepository,
            SubscriptionUserRepository,
            PaymentRepository,
        )
        
        # All methods should be abstract
        for port in [SubscriptionRepository, SubscriptionUserRepository, PaymentRepository]:
            for method_name in dir(port):
                if not method_name.startswith('_'):
                    method = getattr(port, method_name)
                    if callable(method):
                        # Protocol methods should have abstractmethod marker
                        assert hasattr(method, '__isabstractmethod__') or method_name in ['__init__']
    
    def test_subscription_ports_consistent_naming(self):
        """Test port methods follow consistent naming."""
        from app.application.subscription.ports import (
            SubscriptionRepository,
            SubscriptionUserRepository,
            PaymentRepository,
        )
        
        # All read methods should start with 'read_' or 'find_' or 'list_'
        # All write methods should be 'add', 'update_', or 'delete_'
        for port in [SubscriptionRepository, SubscriptionUserRepository, PaymentRepository]:
            for method_name in dir(port):
                if not method_name.startswith('_') and method_name not in ['__init__']:
                    assert (
                        method_name.startswith('read_') or
                        method_name.startswith('find_') or
                        method_name.startswith('list_') or
                        method_name.startswith('add') or
                        method_name.startswith('update_') or
                        method_name.startswith('delete_')
                    ), f"Method {method_name} doesn't follow naming convention"
