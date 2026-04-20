"""
Image processing pipeline module
"""

from fastapi import UploadFile

from app.schemas.summarize import StructuredSummary, SingleFileResult, SummarizeResponse
from app.services.extraction import extract_text_from_image
from app.services.normalization import normalize_extracted_text
from app.services.summarization import summarize_text
from app.utils.file_validation import validate_upload_file
from app.utils.exceptions import AppError


async def process_single_image(
    file: UploadFile,
    ocr_mode: str = "api",
    summary_mode: str = "api",
) -> SingleFileResult:
    """
    Process a single image file through the full pipeline.

    Args:
        file: Uploaded image file
        ocr_mode: OCR mode ("api", "local_llm", or "high_accuracy")
        summary_mode: Summary mode ("api" or "local_llm")

    Returns:
        SingleFileResult with structured summary data
    """
    # File validation
    file_bytes = await validate_upload_file(file)

    # Text extraction
    raw_text = await extract_text_from_image(
        file_bytes=file_bytes,
        content_type=file.content_type or "image/jpeg",
        filename=file.filename or "unknown",
        ocr_mode=ocr_mode,
    )

    # Text normalization
    normalized_text, warnings = normalize_extracted_text(raw_text)

    # Summary generation
    summary_data = await summarize_text(normalized_text, summary_mode=summary_mode)
    structured = StructuredSummary(**summary_data)

    return SingleFileResult(
        filename=file.filename or "unknown",
        ocrMode=ocr_mode,
        summaryMode=summary_mode,
        summary=structured.summary,
        structuredData=structured,
        extractedText=normalized_text,
        warnings=warnings,
    )


async def process_single_image_safe(
    file: UploadFile,
    ocr_mode: str = "api",
    summary_mode: str = "api",
) -> SingleFileResult:
    """
    Process a single image with error handling for batch operations.

    Args:
        file: Uploaded image file
        ocr_mode: OCR mode ("api", "local_llm", or "high_accuracy")
        summary_mode: Summary mode ("api" or "local_llm")

    Returns:
        SingleFileResult (success or error)
    """
    try:
        return await process_single_image(file, ocr_mode=ocr_mode, summary_mode=summary_mode)
    except AppError as e:
        return SingleFileResult(
            filename=file.filename or "unknown",
            ocrMode=ocr_mode,
            summaryMode=summary_mode,
            summary="",
            structuredData=StructuredSummary(),
            extractedText="",
            warnings=[],
            error=e.message,
        )
    except Exception:
        return SingleFileResult(
            filename=file.filename or "unknown",
            ocrMode=ocr_mode,
            summaryMode=summary_mode,
            summary="",
            structuredData=StructuredSummary(),
            extractedText="",
            warnings=[],
            error="予期しないエラーが発生しました。",
        )