"""Tests for preprocessing, normalization, file validation, and pipeline"""

import pytest
import subprocess
from pathlib import Path
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


class TestRouterEndpoints:
    """Tests for router endpoints"""

    def test_summarize_endpoint_success(self):
        """Test successful summarize endpoint"""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        fake_image = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        with patch("app.routers.summarize.process_single_image") as mock_process:
            from app.schemas.summarize import SingleFileResult, StructuredSummary
            mock_result = SingleFileResult(
                filename="test.jpg",
                ocrMode="api",
                summaryMode="api",
                summary="Test summary",
                structuredData=StructuredSummary(summary="Test summary"),
                extractedText="Test text",
                warnings=[],
            )
            mock_process.return_value = mock_result

            response = client.post(
                "/api/summarize",
                files={"file": ("test.jpg", fake_image, "image/jpeg")},
                data={"ocr_mode": "api", "summary_mode": "api"},
            )

            assert response.status_code == 200
            assert response.json()["filename"] == "test.jpg"
            assert response.json()["ocrMode"] == "api"

    def test_summarize_multiple_endpoint(self):
        """Test summarize multiple endpoint"""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        fake_image1 = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")
        fake_image2 = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        with patch("app.routers.summarize.process_single_image_safe") as mock_process:
            from app.schemas.summarize import SingleFileResult, StructuredSummary
            mock_result1 = SingleFileResult(
                filename="test1.jpg",
                ocrMode="api",
                summaryMode="api",
                summary="Summary 1",
                structuredData=StructuredSummary(summary="Summary 1"),
                extractedText="Text 1",
                warnings=[],
            )
            mock_result2 = SingleFileResult(
                filename="test2.jpg",
                ocrMode="api",
                summaryMode="api",
                summary="",
                structuredData=StructuredSummary(),
                extractedText="",
                warnings=[],
                error="Error processing file",
            )
            mock_process.side_effect = [mock_result1, mock_result2]

            response = client.post(
                "/api/summarize-multiple",
                files=[
                    ("files", ("test1.jpg", fake_image1, "image/jpeg")),
                    ("files", ("test2.jpg", fake_image2, "image/jpeg")),
                ],
                data={"ocr_mode": "api", "summary_mode": "api"},
            )

            assert response.status_code == 200
            assert response.json()["totalFiles"] == 2
            assert response.json()["successCount"] == 1
            assert response.json()["errorCount"] == 1

    def test_summarize_multiple_invalid_ocr_mode(self):
        """Test summarize multiple with invalid OCR mode"""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        fake_image = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        response = client.post(
            "/api/summarize-multiple",
            files=[("files", ("test.jpg", fake_image, "image/jpeg"))],
            data={"ocr_mode": "invalid", "summary_mode": "api"},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_OCR_MODE"

    def test_summarize_multiple_invalid_summary_mode(self):
        """Test summarize multiple with invalid summary mode"""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        fake_image = BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        response = client.post(
            "/api/summarize-multiple",
            files=[("files", ("test.jpg", fake_image, "image/jpeg"))],
            data={"ocr_mode": "api", "summary_mode": "invalid"},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_SUMMARY_MODE"


class TestOllamaClientCoverage:
    """Tests for Ollama client additional coverage"""

    @pytest.mark.asyncio
    async def test_summarize_connection_error(self):
        """Test connection error during summarization"""
        from app.clients.ollama_client import summarize_text_with_ollama
        from app.utils.exceptions import LocalLLMUnavailableError

        with patch("app.clients.ollama_client.check_ollama_settings", return_value="model"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post.side_effect = Exception("Connection failed")
                mock_client.return_value.__aenter__.return_value = mock_instance

                with pytest.raises(LocalLLMUnavailableError):
                    await summarize_text_with_ollama("test")

    def test_parse_summary_response_empty(self):
        """Test parsing empty response"""
        from app.clients.ollama_client import parse_ollama_summary_response

        result = parse_ollama_summary_response("")

        assert result["documentType"] == "不明"
        assert result["summary"] == ""

    def test_parse_summary_response_full(self):
        """Test parsing full response"""
        from app.clients.ollama_client import parse_ollama_summary_response

        response = """文書種別: 給与明細
対象期間: 2024年10月
要約: 給与明細の要約です。
詳細項目:
支給額: 300,000円
控除額: 50,000円
不確実な項目:
読み取り不確実な行"""

        result = parse_ollama_summary_response(response)

        assert result["documentType"] == "給与明細"
        assert result["targetPeriod"] == "2024年10月"
        assert result["summary"] == "給与明細の要約です。"
        assert len(result["details"]) >= 1
        assert len(result["uncertainItems"]) >= 1


class TestNDLOCRClientCoverage:
    """Tests for NDLOCR client coverage"""

    @pytest.mark.asyncio
    async def test_extract_text_ndlocr_unavailable(self):
        """Test NDLOCR unavailable"""
        from app.clients.ndlocr_client import extract_text_with_ndlocr
        from app.utils.exceptions import NDLOCRUnavailableError

        with patch("app.clients.ndlocr_client.check_ndlocr_settings", side_effect=NDLOCRUnavailableError()):
            with pytest.raises(NDLOCRUnavailableError):
                await extract_text_with_ndlocr(b"image", "test.jpg")

    @pytest.mark.asyncio
    async def test_run_ndlocr_lite_nonzero_exit(self):
        """Test ndlocr-lite nonzero exit"""
        from app.clients.ndlocr_client import run_ndlocr_lite
        from app.utils.exceptions import NDLOCRExecutionFailedError

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_timeout_seconds = 60.0

            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error"

            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(NDLOCRExecutionFailedError):
                    await run_ndlocr_lite(
                        ndlocr_path=MagicMock(),
                        input_path="test.jpg",
                        output_dir="output",
                    )

    @pytest.mark.asyncio
    async def test_run_ndlocr_lite_timeout(self):
        """Test ndlocr-lite timeout"""
        from app.clients.ndlocr_client import run_ndlocr_lite
        from app.utils.exceptions import NDLOCRTimeoutError

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_timeout_seconds = 60.0

            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)):
                with pytest.raises(NDLOCRTimeoutError):
                    await run_ndlocr_lite(
                        ndlocr_path=MagicMock(),
                        input_path="test.jpg",
                        output_dir="output",
                    )

    @pytest.mark.asyncio
    async def test_run_ndlocr_fallback_success(self):
        """Test fallback success"""
        from app.clients.ndlocr_client import run_ndlocr_fallback

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=True)))

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_timeout_seconds = 60.0

            with patch("subprocess.run", return_value=mock_result):
                result = await run_ndlocr_fallback(
                    ndlocr_path=MagicMock(),
                    input_path="test.jpg",
                    output_dir="output",
                )

                assert result.returncode == 0

    @pytest.mark.asyncio
    async def test_run_ndlocr_fallback_timeout(self):
        """Test fallback timeout"""
        from app.clients.ndlocr_client import run_ndlocr_fallback
        from app.utils.exceptions import NDLOCRTimeoutError

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_timeout_seconds = 60.0

            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)):
                with pytest.raises(NDLOCRTimeoutError):
                    await run_ndlocr_fallback(
                        ndlocr_path=MagicMock(),
                        input_path="test.jpg",
                        output_dir="output",
                    )

    def test_cleanup_temp_dir_error(self):
        """Test cleanup error handling"""
        from app.clients.ndlocr_client import cleanup_temp_dir

        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        mock_dir.iterdir.side_effect = PermissionError("Access denied")

        # Should not raise, just log warning
        cleanup_temp_dir(mock_dir)


class TestExtractionService:
    """Tests for extraction service"""

    @pytest.mark.asyncio
    async def test_extract_text_empty_result(self):
        """Test empty extraction result"""
        from app.services.extraction import extract_text_from_image
        from app.utils.exceptions import TextExtractionFailedError

        with patch("app.services.extraction.extract_text_with_openai", AsyncMock(return_value="")):
            with patch("app.services.extraction.preprocess_image", return_value=(b"data", "image/jpeg")):
                with pytest.raises(TextExtractionFailedError):
                    await extract_text_from_image(
                        file_bytes=b"test",
                        content_type="image/jpeg",
                        filename="test.jpg",
                        ocr_mode="api",
                    )

    @pytest.mark.asyncio
    async def test_extract_text_whitespace_only(self):
        """Test whitespace only result"""
        from app.services.extraction import extract_text_from_image
        from app.utils.exceptions import TextExtractionFailedError

        with patch("app.services.extraction.extract_text_with_openai", AsyncMock(return_value="   \n\n  ")):
            with patch("app.services.extraction.preprocess_image", return_value=(b"data", "image/jpeg")):
                with pytest.raises(TextExtractionFailedError):
                    await extract_text_from_image(
                        file_bytes=b"test",
                        content_type="image/jpeg",
                        filename="test.jpg",
                        ocr_mode="api",
                    )


class TestSummarizationService:
    """Tests for summarization service"""

    @pytest.mark.asyncio
    async def test_summarize_empty_result(self):
        """Test empty summarization result"""
        from app.services.summarization import summarize_text
        from app.utils.exceptions import SummaryGenerationFailedError

        with patch("app.services.summarization.summarize_text_with_openai", AsyncMock(return_value={"summary": ""})):
            with pytest.raises(SummaryGenerationFailedError):
                await summarize_text("test text", summary_mode="api")

    @pytest.mark.asyncio
    async def test_summarize_none_result(self):
        """Test None summarization result"""
        from app.services.summarization import summarize_text
        from app.utils.exceptions import SummaryGenerationFailedError

        with patch("app.services.summarization.summarize_text_with_openai", AsyncMock(return_value={})):
            with pytest.raises(SummaryGenerationFailedError):
                await summarize_text("test text", summary_mode="api")


class TestOpenAIClientSummary:
    """Tests for OpenAI client summarization"""

    @pytest.mark.asyncio
    async def test_summarize_rate_limit(self):
        """Test rate limit during summarization"""
        from app.clients.openai_client import summarize_text_with_openai
        from openai import RateLimitError
        from app.utils.exceptions import OpenAIAPIError

        mock_client = AsyncMock()
        mock_client.chat.completions.parse = AsyncMock(
            side_effect=RateLimitError("Rate limit", response=MagicMock(), body=None)
        )

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            with pytest.raises(OpenAIAPIError):
                await summarize_text_with_openai("test text")

    @pytest.mark.asyncio
    async def test_summarize_api_error(self):
        """Test API error during summarization"""
        from app.clients.openai_client import summarize_text_with_openai
        from openai import APIError
        from app.utils.exceptions import OpenAIAPIError

        mock_client = AsyncMock()
        mock_client.chat.completions.parse = AsyncMock(
            side_effect=APIError("API error", body=None, request=MagicMock())
        )

        with patch("app.clients.openai_client.get_openai_client", AsyncMock(return_value=mock_client)):
            with pytest.raises(OpenAIAPIError):
                await summarize_text_with_openai("test text")


class TestNDLOCRClientMore:
    """More tests for NDLOCR client"""

    def test_check_ndlocr_settings_success(self):
        """Test successful settings check"""
        from app.clients.ndlocr_client import check_ndlocr_settings

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_lite_path = "/valid/path"

            with patch("pathlib.Path.exists", return_value=True):
                result = check_ndlocr_settings()

                assert result is not None

    def test_get_temp_dir_with_settings(self):
        """Test temp dir with custom settings"""
        from app.clients.ndlocr_client import get_temp_dir
        from pathlib import Path

        with patch("app.clients.ndlocr_client.settings") as mock_settings:
            mock_settings.ndlocr_temp_dir = "/custom/temp"

            result = get_temp_dir()

            # Convert to Path for comparison (handles Windows paths)
            expected = Path("/custom/temp")
            assert str(result).replace("\\", "/") == str(expected).replace("\\", "/")

    def test_need_fallback_exception(self):
        """Test _NeedFallback exception"""
        from app.clients.ndlocr_client import _NeedFallback

        exc = _NeedFallback()
        assert isinstance(exc, Exception)

    @pytest.mark.asyncio
    async def test_run_ndlocr_fallback_not_found(self):
        """Test fallback ocr.py not found"""
        from app.clients.ndlocr_client import run_ndlocr_fallback
        from app.utils.exceptions import NDLOCRExecutionFailedError

        # Create mock path that chains: path / "src" / "ocr.py" -> exists = False
        mock_path = MagicMock()
        mock_src = MagicMock()
        mock_ocr_py = MagicMock()
        mock_ocr_py.exists.return_value = False
        # Chain: path / "src" -> mock_src, then mock_src / "ocr.py" -> mock_ocr_py
        mock_src.__truediv__ = MagicMock(return_value=mock_ocr_py)
        mock_path.__truediv__ = MagicMock(return_value=mock_src)

        # Should raise NDLOCRExecutionFailedError before subprocess.run is called
        with pytest.raises(NDLOCRExecutionFailedError):
            await run_ndlocr_fallback(
                ndlocr_path=mock_path,
                input_path="test.jpg",
                output_dir="output",
            )