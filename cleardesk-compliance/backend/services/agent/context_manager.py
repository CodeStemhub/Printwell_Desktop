"""
Context Manager - Builds and maintains agent context.

WHAT IT IS: Manages the full context the agent needs for every conversation.
WHY IT EXISTS: The agent must always know what documents are in the session,
              their status, and the chat history to give relevant responses.
WHAT IT DOES:
    - Gathers all documents in a session
    - Includes chat history
    - Formats context for LLM consumption
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session, joinedload

from models import Document, ChatSession, ChatMessage


def build_agent_context(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Build complete context for the agent.
    
    Args:
        session_id: The chat session ID
        db: Database session
        
    Returns:
        Dictionary containing all context needed for agent responses
    """
    # Get the session with all relationships loaded
    session = db.query(ChatSession).options(
        joinedload(ChatSession.documents),
        joinedload(ChatSession.messages)
    ).filter(ChatSession.id == session_id).first()
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Build document contexts
    documents_context = []
    for doc in session.documents:
        doc_context = {
            "id": doc.id,
            "filename": doc.filename,
            "input_method": doc.input_method,
            "status": doc.status,
            "classified_type": doc.classified_type,
            "classification_confidence": doc.classification_confidence,
            "issuing_organization": doc.issuing_organization,
            "document_period": doc.document_period,
            "extracted_data": doc.extracted_data or {},
            "flags": doc.flags or [],
            "validation_status": doc.validation_status,
            "ocr_confidence": doc.ocr_confidence
        }
        documents_context.append(doc_context)
    
    # Build chat history (last 20 messages for context window efficiency)
    chat_history = []
    for msg in session.messages[-20:]:
        chat_history.append({
            "role": msg.role,
            "content": msg.content,
            "metadata": msg.message_metadata or {}
        })
    
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "module": session.module,
        "documents_processed": documents_context,
        "document_count": len(documents_context),
        "chat_history": chat_history,
        "created_at": session.created_at.isoformat()
    }


def get_processing_summary(documents: List[Document]) -> str:
    """
    Generate a summary of processed documents for the initial agent message.
    
    Args:
        documents: List of Document objects
        
    Returns:
        Formatted summary string
    """
    if not documents:
        return "No documents processed yet."
    
    summary_parts = []
    
    # Group by type
    by_type = {}
    for doc in documents:
        doc_type = doc.classified_type or "Unknown"
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(doc)
    
    for doc_type, docs in by_type.items():
        count = len(docs)
        flagged = sum(1 for d in docs if d.validation_status != "valid")
        
        summary_parts.append(f"- {count}x {doc_type.replace('_', ' ').title()}" + 
                           (f" ({flagged} with issues)" if flagged > 0 else ""))
    
    # Add critical flags
    critical_flags = []
    for doc in documents:
        if doc.flags:
            for flag in doc.flags:
                if flag.get("severity") in ["critical", "high"]:
                    critical_flags.append(f"- [{doc.filename}] {flag.get('message')}")
    
    if critical_flags:
        summary_parts.append("\n⚠️ Issues requiring attention:")
        summary_parts.extend(critical_flags)
    
    return "\n".join(summary_parts)


def format_documents_for_prompt(documents_context: List[Dict]) -> str:
    """
    Format document context into a prompt-friendly string.
    
    Args:
        documents_context: List of document context dictionaries
        
    Returns:
        Formatted string for inclusion in prompts
    """
    if not documents_context:
        return "No documents in session."
    
    formatted = []
    for doc in documents_context:
        doc_str = f"""
Document: {doc['filename']}
Type: {doc['classified_type'] or 'Not classified'}
Status: {doc['status']}
"""
        if doc['extracted_data']:
            doc_str += f"Key data: {doc['extracted_data']}\n"
        
        if doc['flags']:
            doc_str += f"Issues: {[f['message'] for f in doc['flags']]}\n"
        
        formatted.append(doc_str)
    
    return "\n---\n".join(formatted)


def format_chat_history_for_prompt(chat_history: List[Dict]) -> str:
    """
    Format chat history for inclusion in prompts.
    
    Args:
        chat_history: List of chat message dictionaries
        
    Returns:
        Formatted string
    """
    if not chat_history:
        return "No previous messages."
    
    formatted = []
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Agent"
        formatted.append(f"{role}: {msg['content']}")
    
    return "\n".join(formatted)
