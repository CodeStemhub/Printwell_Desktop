"""
Document Routes - Upload, list, and manage documents.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4

# Placeholder dependencies
def get_db():
    pass

def get_current_user():
    return {"user_id": "placeholder-user-id"}

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document for processing.
    
    Accepts: PDF, DOCX, XLSX, JPG, PNG, WEBP
    """
    from services.ingestion.upload_service import ingest_uploaded_file
    
    # Create new session if none provided
    if not session_id:
        session_id = str(uuid4())
    
    try:
        doc_id = await ingest_uploaded_file(
            file=file,
            user_id=current_user["user_id"],
            session_id=session_id,
            db=db
        )
        
        return {
            "document_id": doc_id,
            "session_id": session_id,
            "filename": file.filename,
            "status": "pending",
            "message": "Document uploaded successfully. Processing will begin shortly."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def scan_document(
    image: bytes = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Process a phone camera scan.
    
    Accepts: Raw image bytes from mobile camera
    """
    from services.ingestion.scan_service import process_phone_scan
    
    if not session_id:
        session_id = str(uuid4())
    
    try:
        doc_id = await process_phone_scan(
            raw_image_bytes=image,
            user_id=current_user["user_id"],
            session_id=session_id,
            db=db
        )
        
        return {
            "document_id": doc_id,
            "session_id": session_id,
            "status": "pending",
            "message": "Scan processed successfully. OCR will begin shortly."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(
    session_id: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents for the user, optionally filtered by session.
    """
    # TODO: Implement actual database query
    return {
        "documents": [],
        "message": "Implement database query to list documents"
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific document including extraction results and flags.
    """
    # TODO: Implement actual database query
    return {
        "document": {},
        "message": "Implement database query to get document details"
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document.
    """
    # TODO: Implement actual deletion
    return {
        "message": "Document deleted successfully"
    }
