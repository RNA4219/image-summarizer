from app.clients.openai_client import extract_text_with_openai
from app.clients.ollama_client import extract_text_with_ollama
from app.clients.ndlocr_client import extract_text_with_ndlocr
from app.utils.exceptions import TextExtractionFailedError
from app.utils.preprocessing import preprocess_image


async def extract_text_from_image(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    ocr_mode: str = "api",
) -> str:
    """
    Extract text from image with preprocessing.

    Args:
        file_bytes: Image bytes
        content_type: Content type
        filename: File name
        ocr_mode: OCR mode ("api", "local_llm", or "high_accuracy")

    Returns:
        Extracted text

    Raises:
        TextExtractionFailedError: When extraction result is empty
    """
    text = ""

    if ocr_mode == "local_llm":
        # Ollama multimodal OCR - no preprocessing needed for multimodal models
        text = await extract_text_with_ollama(
            file_bytes=file_bytes,
            content_type=content_type,
            filename=filename,
        )
    elif ocr_mode == "high_accuracy":
        # NDLOCR-Lite - no preprocessing, direct image processing
        text = await extract_text_with_ndlocr(
            file_bytes=file_bytes,
            filename=filename,
        )
    else:
        # Default: api mode (OpenAI)
        # Preprocess image for API OCR
        processed_bytes, processed_content_type = preprocess_image(
            file_bytes, content_type
        )
        text = await extract_text_with_openai(
            file_bytes=processed_bytes,
            content_type=processed_content_type,
            filename=filename,
        )

    if not text.strip():
        raise TextExtractionFailedError()

    return text