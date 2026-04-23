"""
Image Utilities - Image processing helpers.

WHAT IT IS: Common image manipulation functions.
WHY IT EXISTS: Shared utilities for document scanning and enhancement.
WHAT IT DOES:
    - Converts between image formats
    - Applies basic enhancements
    - Prepares images for OCR
"""

import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional


def convert_to_grayscale(image_bytes: bytes) -> bytes:
    """
    Convert image to grayscale.
    """
    img = Image.open(io.BytesIO(image_bytes))
    gray = img.convert('L')

    output = io.BytesIO()
    gray.save(output, format='JPEG')
    output.seek(0)

    return output.getvalue()


def enhance_image(
    image_bytes: bytes,
    brightness: float = 1.2,
    contrast: float = 1.3,
    sharpness: float = 1.5
) -> bytes:
    """
    Enhance image quality for better OCR results.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Apply enhancements
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95)
    output.seek(0)

    return output.getvalue()


def resize_image(image_bytes: bytes, max_width: int = 2000, max_height: int = 2000) -> bytes:
    """
    Resize image while maintaining aspect ratio.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Calculate new dimensions
    width, height = img.size
    ratio = min(max_width / width, max_height / height)

    if ratio < 1.0:
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95)
    output.seek(0)

    return output.getvalue()


def deskew_image(image_bytes: bytes) -> bytes:
    """
    Attempt to deskew a scanned document.
    Simple implementation using projection profile.
    """
    import cv2

    # Convert bytes to OpenCV image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    # Invert if necessary (text should be dark on light background)
    if np.mean(img[:50, :50]) < 128:
        img = 255 - img

    # Calculate skew angle using projections
    angles = np.arange(-5, 6, 0.5)
    scores = []

    for angle in angles:
        # Rotate image
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Calculate projection profile
        projection = np.sum(rotated, axis=1)
        score = np.var(projection)
        scores.append(score)

    # Find best angle
    best_angle = angles[np.argmax(scores)]

    # Rotate to correct skew
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -best_angle, 1.0)
    deskewed = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Convert back to bytes
    _, buffer = cv2.imencode('.jpg', deskewed)
    return buffer.tobytes()


def crop_to_content(image_bytes: bytes, margin: int = 10) -> bytes:
    """
    Crop image to remove excessive white borders.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to numpy array
    arr = np.array(img)

    if len(arr.shape) == 3:
        # RGB image - check if all channels are bright
        mask = np.all(arr > 240, axis=2)
    else:
        # Grayscale
        mask = arr > 240

    # Find bounding box of non-white content
    rows = np.any(~mask, axis=1)
    cols = np.any(~mask, axis=0)

    if np.any(rows) and np.any(cols):
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Add small margin
        rmin = max(0, rmin - margin)
        rmax = min(arr.shape[0], rmax + margin)
        cmin = max(0, cmin - margin)
        cmax = min(arr.shape[1], cmax + margin)

        cropped = img.crop((cmin, rmin, cmax + 1, rmax + 1))
    else:
        cropped = img

    output = io.BytesIO()
    cropped.save(output, format='JPEG', quality=95)
    output.seek(0)

    return output.getvalue()


def prepare_for_ocr(image_bytes: bytes) -> bytes:
    """
    Full preprocessing pipeline for OCR optimization.
    """
    # Step 1: Resize if too large
    processed = resize_image(image_bytes, max_width=2000, max_height=2000)

    # Step 2: Enhance contrast and sharpness
    processed = enhance_image(processed, brightness=1.1, contrast=1.4, sharpness=1.6)

    # Step 3: Deskew
    try:
        processed = deskew_image(processed)
    except Exception:
        pass  # Continue without deskewing if it fails

    # Step 4: Crop excess borders
    processed = crop_to_content(processed, margin=5)

    return processed


def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    """
    Get image width and height.
    """
    img = Image.open(io.BytesIO(image_bytes))
    return img.size


def calculate_dpi(image_bytes: bytes, physical_width_inches: float = 8.5) -> float:
    """
    Estimate DPI from image dimensions and assumed physical size.
    """
    img = Image.open(io.BytesIO(image_bytes))
    width_px = img.size[0]

    if physical_width_inches <= 0:
        return 72.0  # Default screen DPI

    dpi = width_px / physical_width_inches
    return dpi
