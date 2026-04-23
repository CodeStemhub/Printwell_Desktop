"""
File Utilities - Common file handling functions.

WHAT IT IS: Shared utilities for file operations.
WHY IT EXISTS: DRY principle - avoid duplicating file handling code.
WHAT IT DOES:
    - Validates file types
    - Generates safe filenames
    - Handles file size checks
"""

import os
import re
import uuid
from typing import Optional
from pathlib import Path


ACCEPTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}


def get_file_extension(filename: str) -> Optional[str]:
    """
    Get lowercase file extension.
    """
    return Path(filename).suffix.lower()


def is_accepted_file(filename: str, content_type: Optional[str] = None) -> bool:
    """
    Check if file type is accepted.
    """
    ext = get_file_extension(filename)
    if ext not in ACCEPTED_EXTENSIONS:
        return False

    # If content_type provided, verify it matches
    if content_type:
        expected_type = ACCEPTED_EXTENSIONS[ext]
        return content_type == expected_type

    return True


def generate_safe_filename(original_filename: str, doc_id: str) -> str:
    """
    Generate a safe, unique filename.

    Removes special characters, adds document ID for uniqueness.
    """
    # Extract extension
    ext = get_file_extension(original_filename)

    # Sanitize base name
    base_name = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
    base_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
    base_name = base_name[:50]  # Limit length

    # Create unique filename
    safe_filename = f"{doc_id}_{base_name}{ext}"

    return safe_filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def validate_file_size(file_size_bytes: int, max_size_mb: int = 50) -> bool:
    """
    Validate file size is within limits.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_size_bytes


async def download_file_from_storage(storage_url: str, local_path: str) -> str:
    """
    Download file from Supabase storage to local path.

    For production use - downloads file for processing.
    For development - may use local path directly.
    """
    from supabase import create_client
    from config import settings

    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        # Download file
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).download(storage_url)

        # Save locally
        with open(local_path, 'wb') as f:
            f.write(response)

        return local_path
    except Exception as e:
        raise Exception(f"Failed to download file: {str(e)}")


def cleanup_temp_files(paths: list):
    """
    Remove temporary files after processing.
    """
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Warning: Failed to clean up {path}: {e}")
