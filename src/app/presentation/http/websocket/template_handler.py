"""Template Execution WebSocket Handler.

Real-time template execution progress streaming.

Features:
    - Step-by-step progress updates
    - Real-time step results
    - Pause/resume controls
    - Completion notifications
    - Error handling and recovery

Message Types:
    Client → Server:
        - pause: Pause execution
        - resume: Resume paused execution
        - cancel: Cancel execution
        - ping: Heartbeat

    Server → Client:
        - step_started: Step execution started
        - step_progress: Progress within a step
        - step_completed: Step execution completed
        - step_failed: Step execution failed
        - execution_paused: Execution paused
        - execution_resumed: Execution resumed
        - execution_completed: Full execution completed
        - execution_failed: Full execution failed
        - error: Error message
        - pong: Heartbeat response
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, status
from dishka.integrations.fastapi import FromDishka

from app.presentation.http.websocket.connection_manager import ConnectionManager
from app.domain.ports.template_execution_repository import TemplateExecutionRepository
from app.domain.entities.chat.template_execution import (
    TemplateExecution,
    StepResult,
)
from app.presentation.http.auth.access_token_processor_jwt import JwtAccessTokenProcessor


logger = logging.getLogger(__name__)


class TemplateExecutionWebSocketHandler:
    """
    WebSocket handler for real-time template execution streaming.

    Manages connections and broadcasts execution progress, step results,
    and status updates to clients. Supports pause/resume controls.

    Usage:
        handler = TemplateExecutionWebSocketHandler(execution_repo, jwt_processor)
        await handler.handle_connection(websocket, execution_id, token)
    """

    def __init__(
        self,
        execution_repository: TemplateExecutionRepository,
        jwt_processor: JwtAccessTokenProcessor,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        """
        Initialize template execution WebSocket handler.

        Args:
            execution_repository: Repository for execution data
            jwt_processor: JWT token processor for authentication
            connection_manager: Optional connection manager
        """
        self.execution_repo = execution_repository
        self.jwt_processor = jwt_processor
        self.connection_manager = connection_manager or ConnectionManager()

        # Track execution subscriptions: {execution_id: set of user_ids}
        self.execution_subscriptions: Dict[str, set[str]] = {}

    async def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user from JWT token.

        Args:
            token: JWT token from query parameter

        Returns:
            User info dict or None if invalid
        """
        try:
            auth_session_id = self.jwt_processor.decode_auth_session_id(token)
            if not auth_session_id:
                logger.warning("Invalid or expired token")
                return None

            return {
                "user_id": auth_session_id,
                "session_id": auth_session_id,
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return None

    async def handle_connection(
        self,
        websocket: WebSocket,
        execution_id: str,
        token: str,
    ) -> None:
        """
        Handle WebSocket connection lifecycle.

        Args:
            websocket: WebSocket connection
            execution_id: Template execution identifier
            token: JWT token from query parameter
        """
        # Authenticate user
        user = await self.authenticate_user(token)
        if not user:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token",
            )
            return

        user_id = user["user_id"]

        # Verify execution exists and user has access
        try:
            execution_uuid = UUID(execution_id)
            execution = await self.execution_repo.get_by_id(execution_uuid)

            if not execution:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Execution not found",
                )
                return

            # Verify user owns this execution
            if str(execution.user_id) != user_id:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Access denied",
                )
                return

        except ValueError:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid execution ID",
            )
            return

        except Exception as e:
            logger.error(f"Error verifying execution access: {e}", exc_info=True)
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Internal server error",
            )
            return

        # Connect to manager
        session_id = f"template_{execution_id}_{user_id}"
        await self.connection_manager.connect(
            websocket,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "type": "template_execution",
                "execution_id": execution_id,
                "connected_at": datetime.utcnow().isoformat(),
            },
        )

        # Track subscription
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()
        self.execution_subscriptions[execution_id].add(user_id)

        # Send welcome message with current execution state
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to template execution stream",
            "execution_id": execution_id,
            "execution_state": execution.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info(
            f"Template execution WebSocket connected: "
            f"execution={execution_id}, user={user_id}"
        )

        try:
            # Message loop
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type")

                # Handle ping
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Handle pause
                if message_type == "pause":
                    await self._handle_pause(
                        websocket,
                        execution_uuid,
                        user_id,
                    )
                    continue

                # Handle resume
                if message_type == "resume":
                    await self._handle_resume(
                        websocket,
                        execution_uuid,
                        user_id,
                    )
                    continue

                # Handle cancel
                if message_type == "cancel":
                    await self._handle_cancel(
                        websocket,
                        execution_uuid,
                        user_id,
                    )
                    continue

                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "code": "unknown_type",
                })

        except WebSocketDisconnect:
            logger.info(
                f"Template execution WebSocket disconnected: "
                f"execution={execution_id}, user={user_id}"
            )

        except Exception as e:
            logger.error(f"Template execution WebSocket error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "code": "internal_error",
                })
            except Exception:
                pass  # Connection already closed

        finally:
            # Clean up subscription
            if execution_id in self.execution_subscriptions:
                self.execution_subscriptions[execution_id].discard(user_id)
                if not self.execution_subscriptions[execution_id]:
                    del self.execution_subscriptions[execution_id]

            # Disconnect from manager
            await self.connection_manager.disconnect(websocket, user_id, session_id)

    async def _handle_pause(
        self,
        websocket: WebSocket,
        execution_id: UUID,
        user_id: str,
    ) -> None:
        """
        Handle pause request.

        Args:
            websocket: WebSocket connection
            execution_id: Execution identifier
            user_id: User identifier
        """
        try:
            execution = await self.execution_repo.get_by_id(execution_id)

            if not execution:
                await websocket.send_json({
                    "type": "error",
                    "error": "Execution not found",
                    "code": "not_found",
                })
                return

            if not execution.is_in_progress():
                await websocket.send_json({
                    "type": "error",
                    "error": f"Cannot pause execution in status: {execution.status}",
                    "code": "invalid_state",
                })
                return

            # Pause execution
            execution.pause()
            await self.execution_repo.save(execution)

            # Broadcast to all subscribers
            await self._broadcast_to_execution(
                str(execution_id),
                {
                    "type": "execution_paused",
                    "message": "Execution paused by user",
                    "execution_state": execution.to_dict(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Execution {execution_id} paused by user {user_id}")

        except Exception as e:
            logger.error(f"Error pausing execution: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": "Failed to pause execution",
                "code": "pause_error",
            })

    async def _handle_resume(
        self,
        websocket: WebSocket,
        execution_id: UUID,
        user_id: str,
    ) -> None:
        """
        Handle resume request.

        Args:
            websocket: WebSocket connection
            execution_id: Execution identifier
            user_id: User identifier
        """
        try:
            execution = await self.execution_repo.get_by_id(execution_id)

            if not execution:
                await websocket.send_json({
                    "type": "error",
                    "error": "Execution not found",
                    "code": "not_found",
                })
                return

            if not execution.is_paused():
                await websocket.send_json({
                    "type": "error",
                    "error": f"Cannot resume execution in status: {execution.status}",
                    "code": "invalid_state",
                })
                return

            # Resume execution
            execution.resume()
            await self.execution_repo.save(execution)

            # Broadcast to all subscribers
            await self._broadcast_to_execution(
                str(execution_id),
                {
                    "type": "execution_resumed",
                    "message": "Execution resumed by user",
                    "execution_state": execution.to_dict(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Execution {execution_id} resumed by user {user_id}")

        except Exception as e:
            logger.error(f"Error resuming execution: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": "Failed to resume execution",
                "code": "resume_error",
            })

    async def _handle_cancel(
        self,
        websocket: WebSocket,
        execution_id: UUID,
        user_id: str,
    ) -> None:
        """
        Handle cancel request.

        Args:
            websocket: WebSocket connection
            execution_id: Execution identifier
            user_id: User identifier
        """
        try:
            execution = await self.execution_repo.get_by_id(execution_id)

            if not execution:
                await websocket.send_json({
                    "type": "error",
                    "error": "Execution not found",
                    "code": "not_found",
                })
                return

            if execution.is_completed() or execution.is_failed():
                await websocket.send_json({
                    "type": "error",
                    "error": f"Cannot cancel execution in status: {execution.status}",
                    "code": "invalid_state",
                })
                return

            # Mark as failed (cancelled)
            execution.fail("Cancelled by user")
            await self.execution_repo.save(execution)

            # Broadcast to all subscribers
            await self._broadcast_to_execution(
                str(execution_id),
                {
                    "type": "execution_cancelled",
                    "message": "Execution cancelled by user",
                    "execution_state": execution.to_dict(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Execution {execution_id} cancelled by user {user_id}")

        except Exception as e:
            logger.error(f"Error cancelling execution: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": "Failed to cancel execution",
                "code": "cancel_error",
            })

    async def broadcast_step_started(
        self,
        execution_id: UUID,
        step_index: int,
        agent_name: str,
        step_description: Optional[str] = None,
    ) -> None:
        """
        Broadcast step started event.

        Args:
            execution_id: Execution identifier
            step_index: Index of the step
            agent_name: Name of the agent executing the step
            step_description: Optional step description
        """
        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "step_started",
                "step_index": step_index,
                "agent_name": agent_name,
                "description": step_description,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_step_progress(
        self,
        execution_id: UUID,
        step_index: int,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """
        Broadcast step progress update.

        Args:
            execution_id: Execution identifier
            step_index: Index of the step
            progress: Progress percentage (0.0 to 1.0)
            message: Optional progress message
        """
        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "step_progress",
                "step_index": step_index,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_step_completed(
        self,
        execution_id: UUID,
        step_result: StepResult,
    ) -> None:
        """
        Broadcast step completed event.

        Args:
            execution_id: Execution identifier
            step_result: Result of the completed step
        """
        # Get updated execution state
        execution = await self.execution_repo.get_by_id(execution_id)

        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "step_completed",
                "step_result": step_result.to_dict(),
                "execution_state": execution.to_dict() if execution else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_step_failed(
        self,
        execution_id: UUID,
        step_index: int,
        agent_name: str,
        error_message: str,
    ) -> None:
        """
        Broadcast step failed event.

        Args:
            execution_id: Execution identifier
            step_index: Index of the failed step
            agent_name: Name of the agent that failed
            error_message: Error description
        """
        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "step_failed",
                "step_index": step_index,
                "agent_name": agent_name,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_execution_completed(
        self,
        execution_id: UUID,
    ) -> None:
        """
        Broadcast execution completed event.

        Args:
            execution_id: Execution identifier
        """
        # Get final execution state
        execution = await self.execution_repo.get_by_id(execution_id)

        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "execution_completed",
                "message": "Template execution completed successfully",
                "execution_state": execution.to_dict() if execution else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_execution_failed(
        self,
        execution_id: UUID,
        error_message: str,
    ) -> None:
        """
        Broadcast execution failed event.

        Args:
            execution_id: Execution identifier
            error_message: Error description
        """
        # Get final execution state
        execution = await self.execution_repo.get_by_id(execution_id)

        await self._broadcast_to_execution(
            str(execution_id),
            {
                "type": "execution_failed",
                "message": "Template execution failed",
                "error_message": error_message,
                "execution_state": execution.to_dict() if execution else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _broadcast_to_execution(
        self,
        execution_id: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Broadcast message to all subscribers of an execution.

        Args:
            execution_id: Execution identifier
            message: Message to broadcast
        """
        if execution_id not in self.execution_subscriptions:
            return

        # Send to all users subscribed to this execution
        for user_id in self.execution_subscriptions[execution_id]:
            await self.connection_manager.send_to_user(
                user_id=user_id,
                message=message,
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get handler statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "active_connections": self.connection_manager.get_active_count(),
            "active_executions": len(self.execution_subscriptions),
            "total_subscribers": sum(
                len(subs) for subs in self.execution_subscriptions.values()
            ),
            "connection_manager_stats": self.connection_manager.get_statistics(),
        }
