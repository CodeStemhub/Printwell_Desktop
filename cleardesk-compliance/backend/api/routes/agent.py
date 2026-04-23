"""
Agent Chat Routes - Real-time chat with the compliance agent.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional
import json

# Placeholder dependencies
def get_db():
    pass

def get_current_user():
    return {"user_id": "placeholder-user-id"}

router = APIRouter()


@router.post("/message")
async def send_message(
    session_id: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message to the agent and receive a response.
    """
    from services.agent.chat_handler import (
        save_user_message,
        generate_chat_response,
        save_agent_message
    )
    
    try:
        # Save user message
        await save_user_message(
            session_id=session_id,
            content=message,
            db=db
        )
        
        # Generate agent response
        response = await generate_chat_response(
            session_id=session_id,
            user_message=message,
            db=db
        )
        
        # Save agent response
        await save_agent_message(
            session_id=session_id,
            content=response,
            db=db
        )
        
        return {
            "session_id": session_id,
            "user_message": message,
            "agent_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initial-message")
async def get_initial_message(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate the initial agent message after document processing.
    """
    from services.agent.chat_handler import generate_initial_message
    
    try:
        message = await generate_initial_message(
            session_id=session_id,
            db=db
        )
        
        return {
            "session_id": session_id,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat streaming.
    """
    from services.agent.chat_handler import (
        save_user_message,
        save_agent_message,
        stream_chat_response
    )
    
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("content", "")
            
            # Save user message
            await save_user_message(
                session_id=session_id,
                content=user_message,
                db=db
            )
            
            # Stream agent response
            full_response = ""
            async for token in stream_chat_response(
                session_id=session_id,
                user_message=user_message,
                db=db
            ):
                full_response += token
                await websocket.send_json({
                    "type": "token",
                    "content": token
                })
            
            # Save complete agent response
            await save_agent_message(
                session_id=session_id,
                content=full_response,
                db=db
            )
            
            # Signal completion
            await websocket.send_json({
                "type": "complete",
                "content": full_response
            })
            
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
