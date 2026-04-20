"""File validation module"""

from fastapi import UploadFile

from app.config import settings
from app.utils.exceptions import (
    UnsupportedFileTypeError,
    EmptyFileError,
    FileTooLargeError,
)


async def validate_upload_file(file: UploadFile) -> bytes:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file

    Returns:
        File bytes

    Raises:
        UnsupportedFileTypeError: Invalid file type
        EmptyFileError: Empty file
        FileTooLargeError: File too large
    """
    # Check content type
    content_type = file.content_type or ""
    if content_type not in settings.allowed_content_types:
        raise UnsupportedFileTypeError()

    # Read file bytes
    file_bytes = await file.read()

    # Check file size
    if len(file_bytes) > settings.max_file_size_bytes:
        raise FileTooLargeError()

    # Check empty file
    if len(file_bytes) == 0:
        raise EmptyFileError()

    return file_bytes