"""
Chat Handler - Manages agent chat responses via Groq API.

WHAT IT IS: Handles all agent-user chat interactions.
WHY IT EXISTS: Provides the conversational interface for the compliance agent.
WHAT IT DOES:
    - Builds context from documents and chat history
    - Sends to Groq API with appropriate prompts
    - Returns agent responses
    - Saves messages to database
"""

import json
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session

from config import settings
from models import ChatSession, ChatMessage, Document
from services.agent.context_manager import (
    build_agent_context,
    get_processing_summary,
    format_documents_for_prompt,
    format_chat_history_for_prompt
)
from services.agent.prompt_library import (
    INITIAL_MESSAGE_PROMPT,
    CHAT_RESPONSE_PROMPT
)


async def generate_initial_message(
    session_id: str,
    db: Session
) -> str:
    """
    Generate the first agent message after documents are processed.
    
    Args:
        session_id: The chat session ID
        db: Database session
        
    Returns:
        The initial agent message
    """
    context = build_agent_context(session_id, db)
    documents = context["documents_processed"]
    
    # Build processing summary
    doc_summaries = []
    for doc in documents:
        status = "✓" if doc["validation_status"] == "valid" else "⚠️"
        doc_type = doc["classified_type"] or "Unknown"
        doc_summaries.append(f"{status} {doc['filename']}: {doc_type}")
    
    processing_summary = "\n".join(doc_summaries)
    
    prompt = INITIAL_MESSAGE_PROMPT.format(
        count=len(documents),
        processing_summary=processing_summary
    )
    
    # Call Groq API
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are ClearDesk, a professional document processing assistant for accountants in Ghana. Be helpful, concise, and professional."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
    
    message_content = result["choices"][0]["message"]["content"]
    
    # Save as agent message
    message = ChatMessage(
        id=str(uuid4()),
        session_id=session_id,
        role="agent",
        content=message_content,
        metadata={"type": "initial_message"}
    )
    db.add(message)
    db.commit()
    
    return message_content


async def generate_chat_response(
    session_id: str,
    user_message: str,
    db: Session
) -> str:
    """
    Generate an agent response to a user message.
    
    Args:
        session_id: The chat session ID
        user_message: The user's message
        db: Database session
        
    Returns:
        The agent's response
    """
    context = build_agent_context(session_id, db)
    
    # Format context for prompt
    documents_str = format_documents_for_prompt(context["documents_processed"])
    chat_history_str = format_chat_history_for_prompt(context["chat_history"])
    
    prompt = CHAT_RESPONSE_PROMPT.format(
        document_count=context["document_count"],
        current_focus="document review" if context["document_count"] > 0 else "general assistance",
        documents_context=documents_str,
        chat_history=chat_history_str,
        user_message=user_message
    )
    
    # Call Groq API
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are ClearDesk, a professional document processing assistant for accountants in Ghana. Be helpful, concise, and professional. Focus on the user's documents and compliance needs."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
    
    message_content = result["choices"][0]["message"]["content"]
    
    return message_content


async def save_user_message(
    session_id: str,
    content: str,
    db: Session,
    metadata: Optional[Dict] = None
) -> ChatMessage:
    """
    Save a user message to the database.
    
    Args:
        session_id: The chat session ID
        content: Message content
        db: Database session
        metadata: Optional metadata
        
    Returns:
        The saved ChatMessage object
    """
    message = ChatMessage(
        id=str(uuid4()),
        session_id=session_id,
        role="user",
        content=content,
        metadata=metadata or {}
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def save_agent_message(
    session_id: str,
    content: str,
    db: Session,
    metadata: Optional[Dict] = None
) -> ChatMessage:
    """
    Save an agent message to the database.
    
    Args:
        session_id: The chat session ID
        content: Message content
        db: Database session
        metadata: Optional metadata
        
    Returns:
        The saved ChatMessage object
    """
    message = ChatMessage(
        id=str(uuid4()),
        session_id=session_id,
        role="agent",
        content=content,
        metadata=metadata or {}
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def stream_chat_response(
    session_id: str,
    user_message: str,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    Stream an agent response token by token (for real-time UI).
    
    Args:
        session_id: The chat session ID
        user_message: The user's message
        db: Database session
        
    Yields:
        Response tokens as they arrive
    """
    context = build_agent_context(session_id, db)
    
    documents_str = format_documents_for_prompt(context["documents_processed"])
    chat_history_str = format_chat_history_for_prompt(context["chat_history"])
    
    prompt = CHAT_RESPONSE_PROMPT.format(
        document_count=context["document_count"],
        current_focus="document review",
        documents_context=documents_str,
        chat_history=chat_history_str,
        user_message=user_message
    )
    
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are ClearDesk, a professional document processing assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": True
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk["choices"][0]["delta"].get("content", "")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        continue
