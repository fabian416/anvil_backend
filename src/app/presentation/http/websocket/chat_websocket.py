"""Chat WebSocket Endpoint.

Real-time chat with streaming agent responses.

Features:
    - Real-time message streaming
    - Agent response streaming (token-by-token)
    - Progress events during agent execution
    - Connection lifecycle management
    - Authentication via JWT token

Message Types:
    Client → Server:
        - message: Send chat message
        - ping: Heartbeat
    
    Server → Client:
        - message: Complete message
        - stream: Streaming token
        - progress: Agent progress update
        - error: Error message
        - pong: Heartbeat response
"""
from typing import Optional, Dict, Any
from uuid import UUID
import logging
import json
from datetime import datetime, UTC

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.websocket.connection_manager import connection_manager
from app.infrastructure.agno import AgentRouter
from app.setup.config.agno import AgnoConfig
from app.domain.exceptions.auth import InvalidAuthorizationHeaderError


router = APIRouter()
logger = logging.getLogger(__name__)

# Alias for backward compatibility
manager = connection_manager


# TODO: Replace with actual JWT authentication
async def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user from JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        User info or None
    """
    # PLACEHOLDER: Implement actual JWT validation
    # For now, return mock user for development
    if not token or token == "null":
        return None
    
    return {
        "user_id": "user_123",  # Should be extracted from JWT
        "email": "user@example.com",
    }


@router.websocket("/ws/chat")
@inject
async def chat_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    session_id: Optional[str] = Query(None, description="Chat session ID"),
    agent_router: FromDishka[AgentRouter] = None,
):
    """
    WebSocket endpoint for real-time chat with agent streaming.
    
    Connection:
        ws://localhost:8000/api/v1/ws/chat?token=<jwt>&session_id=<optional>
    
    Client Message Format:
        {
            "type": "message",
            "content": "Your message here",
            "conversation_id": "optional-uuid"
        }
    
    Server Message Formats:
        # Stream token
        {
            "type": "stream",
            "content": "token",
            "message_id": "uuid"
        }
        
        # Progress event
        {
            "type": "progress",
            "status": "thinking|tool_call|processing",
            "message": "Checking swap prices...",
            "tool": "get_swap_quote",
            "data": {}
        }
        
        # Complete message
        {
            "type": "message",
            "content": "Complete response",
            "message_id": "uuid",
            "metadata": {}
        }
        
        # Error
        {
            "type": "error",
            "error": "Error message",
            "code": "error_code"
        }
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token
        session_id: Optional session ID
        agent_router: Agno agent router (injected)
    """
    # Authenticate user
    user = await get_current_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    user_id = user["user_id"]
    
    # Connect to manager
    await connection_manager.connect(
        websocket,
        user_id=user_id,
        session_id=session_id,
        metadata={
            "email": user.get("email"),
            "connected_at": datetime.now(UTC).isoformat(),
        },
    )
    
    # Send welcome message
    await websocket.send_json({
        "type": "system",
        "message": "Connected to Anvil AI Chat",
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
    })
    
    try:
        # Initialize agent router if not already initialized
        if agent_router and not agent_router._initialized:
            logger.info(f"[WS] Initializing agent router for user {user_id}")
            await agent_router.initialize()
            logger.info(f"[WS] Agent router ready with {len(agent_router.agents)} agents")
        
        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            # Handle ping
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            
            # Handle message
            if message_type == "message":
                content = data.get("content", "").strip()
                conversation_id = data.get("conversation_id")
                
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message content is required",
                        "code": "empty_message",
                    })
                    continue
                
                logger.info(f"[WS] User {user_id}: {content[:100]}...")
                
                try:
                    # Send "thinking" progress
                    await websocket.send_json({
                        "type": "progress",
                        "status": "thinking",
                        "message": "Processing your request...",
                    })
                    
                    # Route to appropriate agent and stream response
                    if agent_router:
                        # Classify intent for progress feedback
                        agent_type, confidence = agent_router.classify_intent(content)
                        
                        await websocket.send_json({
                            "type": "progress",
                            "status": "routing",
                            "message": f"Routing to {agent_type.value} agent (confidence: {confidence:.0%})",
                            "agent": agent_type.value,
                        })
                        
                        # Execute with streaming
                        message_id = None
                        full_response = ""
                        
                        async for event in agent_router.agents[agent_type].run_stream(
                            content,
                            user_id=user_id,
                            session_id=session_id,
                        ):
                            # Handle different event types
                            if hasattr(event, 'content') and event.content:
                                # Stream content token
                                await websocket.send_json({
                                    "type": "stream",
                                    "content": event.content,
                                    "message_id": message_id,
                                })
                                full_response += event.content
                            
                            elif hasattr(event, 'event'):
                                # Progress event (tool calls, etc.)
                                event_type = event.event
                                
                                if event_type == "tool_call_started":
                                    tool_name = getattr(event, 'tool_name', 'unknown')
                                    await websocket.send_json({
                                        "type": "progress",
                                        "status": "tool_call",
                                        "message": f"Using tool: {tool_name}",
                                        "tool": tool_name,
                                    })
                                
                                elif event_type == "tool_call_completed":
                                    tool_name = getattr(event, 'tool_name', 'unknown')
                                    await websocket.send_json({
                                        "type": "progress",
                                        "status": "tool_completed",
                                        "message": f"Completed: {tool_name}",
                                        "tool": tool_name,
                                    })
                        
                        # Send complete message marker
                        await websocket.send_json({
                            "type": "message_complete",
                            "message_id": message_id,
                            "content": full_response,
                            "metadata": {
                                "agent": agent_type.value,
                                "confidence": confidence,
                            },
                        })
                    
                    else:
                        # Fallback if no agent router
                        await websocket.send_json({
                            "type": "message",
                            "content": "Agent router not available. Please check server configuration.",
                            "metadata": {"error": True},
                        })
                
                except Exception as e:
                    logger.error(f"[WS] Error processing message: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "code": "processing_error",
                    })
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "code": "unknown_type",
                })
    
    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: user={user_id}, session={session_id}")
    
    except Exception as e:
        logger.error(f"[WS] WebSocket error: {e}", exc_info=True)
    
    finally:
        # Disconnect from manager
        await connection_manager.disconnect(websocket, user_id, session_id)


@router.get("/user/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Connection statistics
    """
    return connection_manager.get_statistics()
