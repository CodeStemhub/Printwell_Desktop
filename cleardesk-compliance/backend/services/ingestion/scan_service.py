"""
Scan Service - Processes phone camera scans.

WHAT IT IS: Handles photos taken from phone cameras.
WHY IT EXISTS: Physical documents on desks need digitising without external scanners.
WHAT IT DOES:
    1. Converts raw bytes to OpenCV image
    2. Detects document edges automatically
    3. Applies perspective correction (straightens document)
    4. Enhances contrast for better OCR accuracy
    5. Saves cleaned image and feeds into ingestion pipeline
"""

import uuid
import numpy as np
import cv2
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from config import settings
from models import Document
from services.ingestion.upload_service import ACCEPTED_TYPES


def get_largest_rectangle(contours) -> Optional[np.ndarray]:
    """
    Find the largest rectangular contour (assumed to be the document).
    """
    if not contours:
        return None
    
    # Sort by area, largest first
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    for contour in contours:
        # Approximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # If the approximated polygon has 4 points, it's likely a rectangle
        if len(approx) == 4:
            return approx
    
    return None


def four_point_transform(image, pts) -> np.ndarray:
    """
    Apply perspective transformation to straighten the document.
    """
    # Order points: top-left, top-right, bottom-right, bottom-left
    rect = order_points(pts.reshape(4, 2))
    (tl, tr, br, bl) = rect
    
    # Calculate width and height of new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = int(max(widthA, widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = int(max(heightA, heightB))
    
    # Destination points for straightened document
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")
    
    # Compute perspective transform matrix
    M = cv2.getPerspectiveTransform(rect.astype("float32"), dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order points in top-left, top-right, bottom-right, bottom-left order.
    """
    rect = np.zeros((4, 2), dtype="float32")
    
    # Top-left has smallest sum, bottom-right has largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right has smallest difference, bottom-left has largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Improve image quality for text recognition.
    Handles uneven phone lighting with adaptive thresholding.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding for better text contrast
    enhanced = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )
    
    return enhanced


async def process_phone_scan(
    raw_image_bytes: bytes,
    user_id: str,
    session_id: str,
    db: Session
) -> str:
    """
    Process a phone scan: detect, straighten, enhance, and store.
    
    Args:
        raw_image_bytes: Raw image data from phone camera
        user_id: ID of the uploading user
        session_id: ID of the chat session
        db: Database session
        
    Returns:
        document_id: The ID of the created document record
    """
    # Convert bytes to OpenCV image
    nparr = np.frombuffer(raw_image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Failed to decode image")
    
    # Convert to grayscale for edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 75, 200)
    
    # Find contours
    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Get largest rectangle (the document)
    doc_contour = get_largest_rectangle(contours)
    
    # Apply perspective correction if document found
    if doc_contour is not None:
        straightened = four_point_transform(img, doc_contour)
    else:
        # Use original image if no clear document boundary
        straightened = img
    
    # Enhance for OCR
    enhanced = enhance_for_ocr(straightened)
    
    # Encode back to JPEG
    _, buffer = cv2.imencode('.jpg', enhanced)
    cleaned_bytes = buffer.tobytes()
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    storage_path = f"documents/{user_id}/{session_id}/{doc_id}_scan.jpg"
    
    # Upload to Supabase Storage
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=storage_path,
            file=cleaned_bytes,
            file_options={"content-type": "image/jpeg"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload scanned image: {str(e)}"
        )
    
    # Create database record
    document = Document(
        id=doc_id,
        user_id=user_id,
        session_id=session_id,
        filename="phone_scan.jpg",
        storage_url=storage_path,
        content_type="image/jpeg",
        input_method="scan",
        status="pending"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return doc_id
