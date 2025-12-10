"""
Test data builders and factories.

Provides fluent interfaces for creating test data.
"""

from tests.builders.user_builder import (
    UserBuilder,
    a_user,
    an_admin,
    a_super_admin,
)
from tests.builders.conversation_builder import (
    ConversationBuilder,
    a_conversation,
)
from tests.builders.message_builder import (
    MessageBuilder,
    a_message,
    a_user_message,
    an_agent_message,
)

__all__ = [
    # User builders
    "UserBuilder",
    "a_user",
    "an_admin",
    "a_super_admin",
    # Conversation builders
    "ConversationBuilder",
    "a_conversation",
    # Message builders
    "MessageBuilder",
    "a_message",
    "a_user_message",
    "an_agent_message",
]

from tests.builders.subscription_builder import (
    SubscriptionBuilder,
    a_subscription,
    a_free_subscription,
    a_basic_subscription,
    a_premium_subscription,
    an_enterprise_subscription,
    a_cancelled_subscription,
    a_failed_payment_subscription,
)

__all__.extend([
    "SubscriptionBuilder",
    "a_subscription",
    "a_free_subscription",
    "a_basic_subscription",
    "a_premium_subscription",
    "an_enterprise_subscription",
    "a_cancelled_subscription",
    "a_failed_payment_subscription",
])
