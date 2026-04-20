import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.exceptions import (
    NDLOCRUnavailableError,
    NDLOCRExecutionFailedError,
    NDLOCRTimeoutError,
    TextExtractionFailedError,
)

logger = logging.getLogger(__name__)

# Internal marker for "need fallback" case
class _NeedFallback(Exception):
    """Internal marker to trigger fallback execution"""
    pass


def check_ndlocr_settings() -> Path:
    """
    Check NDLOCR-Lite settings and return path.

    Returns:
        Path to NDLOCR-Lite directory

    Raises:
        NDLOCRUnavailableError: When path is not configured or invalid
    """
    if not settings.ndlocr_lite_path:
        raise NDLOCRUnavailableError()

    ndlocr_path = Path(settings.ndlocr_lite_path)
    if not ndlocr_path.exists():
        raise NDLOCRUnavailableError()

    return ndlocr_path


def get_temp_dir() -> Path:
    """
    Get temporary directory for NDLOCR output.

    Returns:
        Path to temporary directory
    """
    if settings.ndlocr_temp_dir:
        return Path(settings.ndlocr_temp_dir)
    else:
        # Use OS default temp
        return Path(tempfile.gettempdir())


async def extract_text_with_ndlocr(
    file_bytes: bytes,
    filename: str,
) -> str:
    """
    NDLOCR-Liteを実行してテキストを抽出

    Args:
        file_bytes: Image bytes
        filename: File name

    Returns:
        Extracted text

    Raises:
        NDLOCRUnavailableError: NDLOCR-Lite利用不可
        NDLOCRExecutionFailedError: 実行失敗
        NDLOCRTimeoutError: タイムアウト
        TextExtractionFailedError: 結果が空
    """
    ndlocr_path = check_ndlocr_settings()
    temp_dir = get_temp_dir()

    # Create unique output directory
    output_dir = temp_dir / f"ndlocr_{os.urandom(8).hex()}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save input image
    input_path = output_dir / filename
    with open(input_path, "wb") as f:
        f.write(file_bytes)

    stem = Path(filename).stem
    txt_path = output_dir / f"{stem}.txt"

    logger.info(f"Running NDLOCR-Lite for {filename}")

    try:
        # Try primary execution: ndlocr-lite command
        try:
            await run_ndlocr_lite(
                ndlocr_path=ndlocr_path,
                input_path=str(input_path),
                output_dir=str(output_dir),
            )
        except _NeedFallback:
            # ndlocr-lite not found, try fallback
            logger.info("ndlocr-lite not available, trying fallback ocr.py")
            await run_ndlocr_fallback(
                ndlocr_path=ndlocr_path,
                input_path=str(input_path),
                output_dir=str(output_dir),
            )

        # Check for .txt output
        if not txt_path.exists():
            # Try fallback if primary didn't produce output
            logger.info("Primary execution didn't produce output, trying fallback")
            await run_ndlocr_fallback(
                ndlocr_path=ndlocr_path,
                input_path=str(input_path),
                output_dir=str(output_dir),
            )

        # Read the result
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8").strip()
        else:
            text = ""

        # Cleanup
        cleanup_temp_dir(output_dir)

        if not text:
            logger.error(f"NDLOCR result empty for {filename}")
            raise TextExtractionFailedError()

        logger.info(f"NDLOCR extraction completed for {filename}, length: {len(text)}")
        return text

    except NDLOCRUnavailableError:
        cleanup_temp_dir(output_dir)
        raise
    except NDLOCRExecutionFailedError:
        cleanup_temp_dir(output_dir)
        raise
    except NDLOCRTimeoutError:
        cleanup_temp_dir(output_dir)
        raise
    except Exception as e:
        cleanup_temp_dir(output_dir)
        logger.error(f"NDLOCR unexpected error: {e}")
        raise NDLOCRExecutionFailedError()


async def run_ndlocr_lite(
    ndlocr_path: Path,
    input_path: str,
    output_dir: str,
) -> Optional[subprocess.CompletedProcess]:
    """
    Execute ndlocr-lite command.

    Args:
        ndlocr_path: Path to NDLOCR-Lite directory
        input_path: Input image path
        output_dir: Output directory

    Returns:
        subprocess result or None if command not found

    Raises:
        _NeedFallback: ndlocr-lite command not found (trigger fallback)
        NDLOCRExecutionFailedError: Execution failed
        NDLOCRTimeoutError: Timeout
    """
    try:
        result = subprocess.run(
            ["ndlocr-lite", "--sourceimg", input_path, "--output", output_dir],
            cwd=str(ndlocr_path),
            capture_output=True,
            text=True,
            timeout=settings.ndlocr_timeout_seconds,
        )

        if result.returncode != 0:
            logger.error(f"NDLOCR-lite failed: {result.stderr}")
            raise NDLOCRExecutionFailedError()

        return result

    except subprocess.TimeoutExpired:
        logger.error("NDLOCR-lite timeout")
        raise NDLOCRTimeoutError()
    except FileNotFoundError:
        logger.warning("ndlocr-lite command not found, will try fallback")
        raise _NeedFallback()


async def run_ndlocr_fallback(
    ndlocr_path: Path,
    input_path: str,
    output_dir: str,
) -> subprocess.CompletedProcess:
    """
    Execute fallback python ocr.py.

    Args:
        ndlocr_path: Path to NDLOCR-Lite directory
        input_path: Input image path
        output_dir: Output directory

    Returns:
        subprocess result

    Raises:
        NDLOCRExecutionFailedError: Execution failed
        NDLOCRTimeoutError: Timeout
    """
    ocr_py_path = ndlocr_path / "src" / "ocr.py"

    if not ocr_py_path.exists():
        logger.error(f"ocr.py not found at {ocr_py_path}")
        raise NDLOCRExecutionFailedError("ocr.py not found")

    try:
        result = subprocess.run(
            ["python", str(ocr_py_path), "--sourceimg", input_path, "--output", output_dir],
            cwd=str(ndlocr_path),
            capture_output=True,
            text=True,
            timeout=settings.ndlocr_timeout_seconds,
        )

        if result.returncode != 0:
            logger.error(f"ocr.py failed: {result.stderr}")
            raise NDLOCRExecutionFailedError()

        return result

    except subprocess.TimeoutExpired:
        logger.error("ocr.py timeout")
        raise NDLOCRTimeoutError()
    except FileNotFoundError:
        logger.error("python command not found")
        raise NDLOCRExecutionFailedError("python command not found")


def cleanup_temp_dir(output_dir: Path) -> None:
    """
    Cleanup temporary directory.

    Args:
        output_dir: Directory to cleanup
    """
    try:
        if output_dir.exists():
            for file in output_dir.iterdir():
                file.unlink()
            output_dir.rmdir()
    except Exception as e:
        logger.warning(f"Failed to cleanup temp dir: {e}")