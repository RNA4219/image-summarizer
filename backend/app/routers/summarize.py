import logging
from typing import List

from fastapi import APIRouter, File, UploadFile, Form

from app.schemas.summarize import SummarizeResponse, MultiSummarizeResponse
from app.schemas.error import ErrorResponse
from app.services.pipeline import process_single_image, process_single_image_safe
from app.utils.exceptions import InvalidOcrModeError, InvalidSummaryModeError

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_OCR_MODES = ["api", "local_llm", "high_accuracy"]
VALID_SUMMARY_MODES = ["api", "local_llm"]


def validate_ocr_mode(ocr_mode: str) -> None:
    """Validate OCR mode."""
    if ocr_mode not in VALID_OCR_MODES:
        raise InvalidOcrModeError()


def validate_summary_mode(summary_mode: str) -> None:
    """Validate summary mode."""
    if summary_mode not in VALID_SUMMARY_MODES:
        raise InvalidSummaryModeError()


@router.post(
    "/api/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        413: {"model": ErrorResponse, "description": "Payload Too Large"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        502: {"model": ErrorResponse, "description": "Bad Gateway"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"},
    },
)
async def summarize(
    file: UploadFile = File(...),
    ocr_mode: str = Form("api"),
    summary_mode: str = Form("api"),
) -> SummarizeResponse:
    """
    Upload single image and get structured summary

    Args:
        file: Image file to process
        ocr_mode: OCR mode ("api", "local_llm", or "high_accuracy")
        summary_mode: Summary mode ("api" or "local_llm")
    """
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    logger.info(f"ocr_mode: {ocr_mode}, summary_mode: {summary_mode}")

    # Validate modes
    validate_ocr_mode(ocr_mode)
    validate_summary_mode(summary_mode)

    result = await process_single_image(file, ocr_mode=ocr_mode, summary_mode=summary_mode)

    logger.info(f"Summarization completed for {file.filename}")

    return SummarizeResponse(
        filename=result.filename,
        ocrMode=result.ocrMode,
        summaryMode=result.summaryMode,
        summary=result.summary,
        structuredData=result.structuredData,
        extractedText=result.extractedText,
        warnings=result.warnings,
    )


@router.post(
    "/api/summarize-multiple",
    response_model=MultiSummarizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        413: {"model": ErrorResponse, "description": "Payload Too Large"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def summarize_multiple(
    files: List[UploadFile] = File(...),
    ocr_mode: str = Form("api"),
    summary_mode: str = Form("api"),
) -> MultiSummarizeResponse:
    """
    Upload multiple images and get structured summaries

    Args:
        files: List of image files to process
        ocr_mode: OCR mode ("api", "local_llm", or "high_accuracy")
        summary_mode: Summary mode ("api" or "local_llm")
    """
    logger.info(f"Received {len(files)} files")
    logger.info(f"ocr_mode: {ocr_mode}, summary_mode: {summary_mode}")

    # Validate modes
    validate_ocr_mode(ocr_mode)
    validate_summary_mode(summary_mode)

    results = []
    success_count = 0
    error_count = 0

    for file in files:
        result = await process_single_image_safe(file, ocr_mode=ocr_mode, summary_mode=summary_mode)
        results.append(result)

        if result.error:
            error_count += 1
            logger.error(f"Error processing {file.filename}: {result.error}")
        else:
            success_count += 1
            logger.info(f"Processed: {file.filename}")

    return MultiSummarizeResponse(
        totalFiles=len(files),
        successCount=success_count,
        errorCount=error_count,
        results=results,
    )