"""
Compliance Routes - Document processing pipeline endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Placeholder dependencies
def get_db():
    pass

def get_current_user():
    return {"user_id": "placeholder-user-id"}

router = APIRouter()


@router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger the full processing pipeline for a document:
    1. OCR (if image/scan)
    2. Classification
    3. Data extraction
    4. Validation and flagging
    """
    from models import Document
    from services.ingestion.ocr_service import extract_text
    from services.intelligence.classifier import classify_document
    from services.intelligence.extractor import extract_document_data
    from services.intelligence.validator import validate_document
    
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Update status
        document.status = "processing"
        db.commit()
        
        # Step 1: Extract text (OCR if needed)
        ocr_result = await extract_text(document)
        document.extracted_text = ocr_result["text"]
        document.ocr_method = ocr_result["method"]
        document.ocr_confidence = ocr_result["confidence"]
        db.commit()
        
        # Step 2: Classify document
        classification = await classify_document(
            document_text=ocr_result["text"],
            document_id=document_id,
            db=db
        )
        
        # Step 3: Extract data
        extracted_data = await extract_document_data(
            document_text=ocr_result["text"],
            document_type=document.classified_type,
            document_id=document_id,
            db=db
        )
        
        # Step 4: Validate and flag
        flags = validate_document(
            extracted_data=extracted_data,
            document_type=document.classified_type,
            document_id=document_id,
            db=db
        )
        
        # Mark as complete
        document.status = "complete"
        db.commit()
        
        return {
            "document_id": document_id,
            "status": "complete",
            "classification": classification,
            "extracted_data": extracted_data,
            "flags": flags,
            "message": f"Document processed successfully. Found {len(flags)} issue(s)."
        }
        
    except Exception as e:
        document.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/session/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of all documents in a session.
    """
    from models import Document, ChatSession
    from services.agent.context_manager import get_processing_summary
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    documents = session.documents
    summary = get_processing_summary(documents)
    
    return {
        "session_id": session_id,
        "document_count": len(documents),
        "summary": summary,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "type": doc.classified_type,
                "status": doc.status,
                "validation_status": doc.validation_status,
                "flags_count": len(doc.flags) if doc.flags else 0
            }
            for doc in documents
        ]
    }


@router.post("/session/{session_id}/trigger-agent")
async def trigger_agent_message(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger the agent to send an initial message after document processing.
    """
    from services.agent.chat_handler import generate_initial_message
    
    message = await generate_initial_message(session_id=session_id, db=db)
    
    return {
        "session_id": session_id,
        "agent_message": message
    }
