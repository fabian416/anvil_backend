import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.commands.chat.send_message import SendMessage
from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.agent_task_queue import AgentTaskQueue


@pytest.mark.asyncio
async def test_send_message_flow():
    # Arrange
    mock_repo = AsyncMock(spec=LLMConversationRepository)
    mock_tx = MagicMock(spec=TransactionManager)
    mock_queue = AsyncMock(spec=AgentTaskQueue)

    interactor = SendMessage(repo=mock_repo, tx=mock_tx, task_queue=mock_queue)

    conversation_id = uuid4()
    content = "Hello Anvil"

    # Act
    message = await interactor.execute(conversation_id, content)

    # Assert
    assert message.content == content
    assert message.conversation_id == conversation_id

    # Verify async task was enqueued
    mock_queue.enqueue_message_processing.assert_called_once_with(
        conversation_id, message.id
    )
