"""
Upload Service - Handles file uploads from computer.

WHAT IT IS: Receives files dragged/dropped or selected from user's computer.
WHY IT EXISTS: Need to store raw files safely before processing.
WHAT IT DOES:
    1. Validates file type is acceptable
    2. Generates unique document ID
    3. Uploads file to Supabase Storage
    4. Creates database record with status 'pending'
    5. Triggers processing pipeline
"""

import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from config import settings
from models import Document


ACCEPTED_TYPES = [
    "application/pdf",
    "image/jpeg", "image/png", "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]


async def ingest_uploaded_file(
    file: UploadFile,
    user_id: str,
    session_id: str,
    db: Session
) -> str:
    """
    Process an uploaded file and store it for processing.
    
    Args:
        file: The uploaded file from FastAPI
        user_id: ID of the uploading user
        session_id: ID of the chat session
        db: Database session
        
    Returns:
        document_id: The ID of the created document record
    """
    # Validate file type
    if file.content_type not in ACCEPTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. "
                   f"Accepted types: {', '.join(ACCEPTED_TYPES)}"
        )
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    
    # Read file bytes
    file_bytes = await file.read()
    
    # Upload to Supabase Storage
    storage_path = f"documents/{user_id}/{session_id}/{doc_id}_{file.filename}"
    
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to storage: {str(e)}"
        )
    
    # Create database record
    document = Document(
        id=doc_id,
        user_id=user_id,
        session_id=session_id,
        filename=file.filename,
        storage_url=storage_path,
        content_type=file.content_type,
        input_method="upload",
        status="pending"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Trigger async processing (to be implemented with Celery/Redis)
    # await trigger_processing_pipeline.delay(doc_id)
    
    return doc_id
