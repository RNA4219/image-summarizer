"""Tests for preprocessing, normalization, file validation, and pipeline"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image

from app.utils.exceptions import (
    UnsupportedFileTypeError,
    EmptyFileError,
    FileTooLargeError,
    AppError,
)


class TestPreprocessing:
    """Tests for image preprocessing"""

    def test_preprocess_image_jpeg(self):
        """Test preprocessing JPEG image"""
        from app.utils.preprocessing import preprocess_image

        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="white")
        output = BytesIO()
        img.save(output, format="JPEG")
        output.seek(0)
        file_bytes = output.read()

        processed_bytes, processed_type = preprocess_image(file_bytes, "image/jpeg")

        assert processed_type == "image/jpeg"
        assert len(processed_bytes) > 0

    def test_preprocess_image_png_rgba(self):
        """Test preprocessing PNG with RGBA"""
        from app.utils.preprocessing import preprocess_image

        # Create PNG with RGBA
        img = Image.new("RGBA", (100, 100), color=(255, 255, 255, 255))
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        file_bytes = output.read()

        processed_bytes, processed_type = preprocess_image(file_bytes, "image/png")

        assert processed_type == "image/jpeg"
        assert len(processed_bytes) > 0

    def test_preprocess_image_png_palette(self):
        """Test preprocessing PNG with palette mode"""
        from app.utils.preprocessing import preprocess_image

        # Create PNG with palette
        img = Image.new("P", (100, 100), color=0)
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        file_bytes = output.read()

        processed_bytes, processed_type = preprocess_image(file_bytes, "image/png")

        assert processed_type == "image/jpeg"
        assert len(processed_bytes) > 0

    def test_preprocess_image_scaling(self):
        """Test that image is scaled 2x"""
        from app.utils.preprocessing import preprocess_image

        # Create small image
        img = Image.new("RGB", (50, 50), color="white")
        output = BytesIO()
        img.save(output, format="JPEG")
        output.seek(0)
        file_bytes = output.read()

        processed_bytes, _ = preprocess_image(file_bytes, "image/jpeg")

        # Verify processed image is 100x100
        processed_img = Image.open(BytesIO(processed_bytes))
        assert processed_img.size == (100, 100)


class TestNormalization:
    """Tests for text normalization"""

    def test_normalize_basic_text(self):
        """Test basic text normalization"""
        from app.services.normalization import normalize_extracted_text

        text = "  Hello World  \n\n\n\n"
        normalized, warnings = normalize_extracted_text(text)

        assert normalized == "Hello World"
        assert len(warnings) == 0 or "短い" in warnings[0]

    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        from app.services.normalization import normalize_extracted_text

        text = "Line 1\n\n\n\n\nLine 2    word"
        normalized, warnings = normalize_extracted_text(text)

        assert "\n\n\n" not in normalized
        assert "    " not in normalized

    def test_normalize_short_text_warning(self):
        """Test warning for short text"""
        from app.services.normalization import normalize_extracted_text

        text = "Short"
        normalized, warnings = normalize_extracted_text(text)

        assert len(warnings) > 0
        assert "短い" in warnings[0]


class TestFileValidation:
    """Tests for file validation"""

    @pytest.mark.asyncio
    async def test_validate_valid_jpeg(self):
        """Test valid JPEG file"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        result = await validate_upload_file(mock_file)

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_validate_valid_png(self):
        """Test valid PNG file"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = "image/png"
        mock_file.read = AsyncMock(return_value=b"\x89PNG" + b"\x00" * 100)

        result = await validate_upload_file(mock_file)

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_validate_invalid_content_type(self):
        """Test invalid content type"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"data")

        with pytest.raises(UnsupportedFileTypeError):
            await validate_upload_file(mock_file)

    @pytest.mark.asyncio
    async def test_validate_empty_file(self):
        """Test empty file"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"")

        with pytest.raises(EmptyFileError):
            await validate_upload_file(mock_file)

    @pytest.mark.asyncio
    async def test_validate_large_file(self):
        """Test file too large"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        # 11MB (over 10MB limit)
        mock_file.read = AsyncMock(return_value=b"\x00" * (11 * 1024 * 1024))

        with pytest.raises(FileTooLargeError):
            await validate_upload_file(mock_file)

    @pytest.mark.asyncio
    async def test_validate_no_content_type(self):
        """Test file without content type"""
        from app.utils.file_validation import validate_upload_file

        mock_file = MagicMock()
        mock_file.content_type = None
        mock_file.read = AsyncMock(return_value=b"data")

        with pytest.raises(UnsupportedFileTypeError):
            await validate_upload_file(mock_file)


class TestOpenAIClient:
    """Tests for OpenAI client"""

    @pytest.mark.asyncio
    async def test_extract_text_success(self):
        """Test successful OpenAI OCR"""
        from app.clients.openai_client import extract_text_with_openai

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Extracted text"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            result = await extract_text_with_openai(
                file_bytes=b"test",
                content_type="image/jpeg",
                filename="test.jpg",
            )

            assert result == "Extracted text"

    @pytest.mark.asyncio
    async def test_summarize_text_success(self):
        """Test successful OpenAI summarization"""
        from app.clients.openai_client import summarize_text_with_openai
        from app.schemas.summarize import StructuredSummary

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_parsed = StructuredSummary(
            documentType="文書",
            targetPeriod="2024年10月",
            summary="要約テキスト",
            details=[],
            uncertainItems=[],
        )
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = mock_parsed
        mock_client.chat.completions.parse = AsyncMock(return_value=mock_response)

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            result = await summarize_text_with_openai("test text")

            assert result["summary"] == "要約テキスト"

    @pytest.mark.asyncio
    async def test_extract_text_rate_limit(self):
        """Test rate limit error"""
        from app.clients.openai_client import extract_text_with_openai
        from openai import RateLimitError
        from app.utils.exceptions import OpenAIAPIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit", response=MagicMock(), body=None)
        )

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            with pytest.raises(OpenAIAPIError):
                await extract_text_with_openai(
                    file_bytes=b"test",
                    content_type="image/jpeg",
                    filename="test.jpg",
                )

    @pytest.mark.asyncio
    async def test_extract_text_connection_error(self):
        """Test connection error"""
        from app.clients.openai_client import extract_text_with_openai
        from openai import APIConnectionError
        from app.utils.exceptions import OpenAIAPIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            with pytest.raises(OpenAIAPIError):
                await extract_text_with_openai(
                    file_bytes=b"test",
                    content_type="image/jpeg",
                    filename="test.jpg",
                )


class TestPipeline:
    """Tests for pipeline module"""

    @pytest.mark.asyncio
    async def test_process_single_image_success(self):
        """Test successful image processing"""
        from app.services.pipeline import process_single_image

        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        with patch("app.services.pipeline.validate_upload_file", AsyncMock(return_value=b"image_data")):
            with patch("app.services.pipeline.extract_text_from_image", AsyncMock(return_value="extracted text")):
                with patch("app.services.pipeline.normalize_extracted_text", return_value=("normalized", [])):
                    with patch("app.services.pipeline.summarize_text", AsyncMock(return_value={"summary": "summary text"})):
                        result = await process_single_image(mock_file)

                        assert result.filename == "test.jpg"
                        assert result.summary == "summary text"

    @pytest.mark.asyncio
    async def test_process_single_image_safe_error(self):
        """Test safe processing with error"""
        from app.services.pipeline import process_single_image_safe

        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        with patch("app.services.pipeline.process_single_image", AsyncMock(side_effect=AppError("test error"))):
            result = await process_single_image_safe(mock_file)

            assert result.error == "test error"
            assert result.summary == ""

    @pytest.mark.asyncio
    async def test_process_single_image_safe_unexpected_error(self):
        """Test safe processing with unexpected error"""
        from app.services.pipeline import process_single_image_safe

        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        with patch("app.services.pipeline.process_single_image", AsyncMock(side_effect=Exception("unexpected"))):
            result = await process_single_image_safe(mock_file)

            assert result.error == "予期しないエラーが発生しました。"

    @pytest.mark.asyncio
    async def test_process_single_image_with_modes(self):
        """Test processing with mode parameters"""
        from app.services.pipeline import process_single_image

        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"

        with patch("app.services.pipeline.validate_upload_file", AsyncMock(return_value=b"image_data")):
            with patch("app.services.pipeline.extract_text_from_image", AsyncMock(return_value="text")) as mock_extract:
                with patch("app.services.pipeline.normalize_extracted_text", return_value=("normalized", [])):
                    with patch("app.services.pipeline.summarize_text", AsyncMock(return_value={"summary": "s"})):
                        result = await process_single_image(
                            mock_file,
                            ocr_mode="local_llm",
                            summary_mode="local_llm",
                        )

                        # Verify mode was passed
                        mock_extract.assert_called_once()
                        call_kwargs = mock_extract.call_args.kwargs
                        assert call_kwargs.get("ocr_mode") == "local_llm"
                        assert result.ocrMode == "local_llm"
                        assert result.summaryMode == "local_llm"


class TestMainApp:
    """Tests for FastAPI main module"""

    def test_create_app(self):
        """Test app creation"""
        from app.main import create_app

        app = create_app()

        assert app.title == "Image Summarizer API"

    def test_health_check_endpoint(self):
        """Test health endpoint"""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_app_error_handler(self):
        """Test AppError exception handler"""
        from app.main import app
        from app.utils.exceptions import InvalidOcrModeError
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Trigger error by sending invalid mode
        fake_image = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")
        response = client.post(
            "/api/summarize",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
            data={"ocr_mode": "invalid", "summary_mode": "api"},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_OCR_MODE"