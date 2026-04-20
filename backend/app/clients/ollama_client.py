import base64
import logging
from typing import Optional

import httpx

from app.config import settings
from app.utils.exceptions import (
    LocalLLMUnavailableError,
    LocalLLMModelMissingError,
    LocalLLMTimeoutError,
)

logger = logging.getLogger(__name__)

OCR_PROMPT = """この画像内の日本語テキストを抽出してください。
給与明細や帳票のような表形式文書を想定し、項目名と数値の対応が分かる形で出力してください。
読めない箇所は無理に補完せず、そのまま曖昧なまま残してください。"""

SUMMARY_PROMPT = """以下のテキストを日本語で要約してください。
文書種別、対象期間、主要な項目と値を整理してください。
出力形式:
- 文書種別: [種別名]
- 対象期間: [期間]
- 要約: [自然文要約]
- 詳細項目: [項目名: 値 のリスト]
- 不確実な項目: [読み取りが不確実な項目リスト]"""


def check_ollama_settings(model_type: str) -> str:
    """
    Check Ollama settings and return model name.

    Args:
        model_type: "ocr" or "summary"

    Returns:
        Model name

    Raises:
        LocalLLMModelMissingError: When model is not configured
        LocalLLMUnavailableError: When base URL is not configured
    """
    if not settings.ollama_base_url:
        raise LocalLLMUnavailableError()

    model_name = ""
    if model_type == "ocr":
        model_name = settings.ollama_ocr_model
    elif model_type == "summary":
        model_name = settings.ollama_summary_model

    if not model_name:
        raise LocalLLMModelMissingError()

    return model_name


async def extract_text_with_ollama(
    file_bytes: bytes,
    content_type: str,
    filename: str,
) -> str:
    """
    OllamaマルチモーダルOCRを実行

    Args:
        file_bytes: Image bytes
        content_type: Content type
        filename: File name

    Returns:
        Extracted text

    Raises:
        LocalLLMUnavailableError: Ollama接続不可
        LocalLLMModelMissingError: モデル未設定
        LocalLLMTimeoutError: タイムアウト
    """
    model_name = check_ollama_settings("ocr")

    base64_image = base64.b64encode(file_bytes).decode("utf-8")
    image_url = f"data:{content_type};base64,{base64_image}"

    payload = {
        "model": model_name,
        "prompt": OCR_PROMPT,
        "images": [base64_image],
        "stream": False,
    }

    logger.info(f"Extracting text with Ollama: {filename}, model: {model_name}")

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )

            if response.status_code != 200:
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", str(error_json))
                except:
                    error_detail = response.text[:500]
                logger.error(f"Ollama response error: {response.status_code}, detail: {error_detail}")
                raise LocalLLMUnavailableError(f"Ollama error: {error_detail}")

            result = response.json()
            text = result.get("response", "")

            logger.info(f"Ollama OCR completed for {filename}, length: {len(text)}")
            return text

    except httpx.TimeoutException:
        logger.error(f"Ollama timeout for {filename}")
        raise LocalLLMTimeoutError()
    except httpx.ConnectError:
        logger.error(f"Ollama connection failed for {filename}")
        raise LocalLLMUnavailableError()
    except Exception as e:
        logger.error(f"Ollama unexpected error: {e}")
        raise LocalLLMUnavailableError()


async def summarize_text_with_ollama(text: str) -> dict:
    """
    Ollamaでテキストを要約

    Args:
        text: Text to summarize

    Returns:
        dict: 構造化された要約データ

    Raises:
        LocalLLMUnavailableError: Ollama接続不可
        LocalLLMModelMissingError: モデル未設定
        LocalLLMTimeoutError: タイムアウト
    """
    model_name = check_ollama_settings("summary")

    full_prompt = f"{SUMMARY_PROMPT}\n\nテキスト:\n{text}"

    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
    }

    logger.info(f"Summarizing with Ollama, model: {model_name}")

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"Ollama response error: {response.status_code}")
                raise LocalLLMUnavailableError(f"Ollama returned status {response.status_code}")

            result = response.json()
            response_text = result.get("response", "")

            # Parse structured output from Ollama response
            structured = parse_ollama_summary_response(response_text)

            logger.info(f"Ollama summarization completed, type: {structured.get('documentType', '不明')}")
            return structured

    except httpx.TimeoutException:
        logger.error("Ollama timeout during summarization")
        raise LocalLLMTimeoutError()
    except httpx.ConnectError:
        logger.error("Ollama connection failed during summarization")
        raise LocalLLMUnavailableError()
    except Exception as e:
        logger.error(f"Ollama unexpected error: {e}")
        raise LocalLLMUnavailableError()


def parse_ollama_summary_response(response_text: str) -> dict:
    """
    Ollama応答から構造化データを解析

    Args:
        response_text: Raw response from Ollama

    Returns:
        dict: Structured summary data
    """
    lines = response_text.strip().split("\n")

    result = {
        "documentType": "不明",
        "targetPeriod": None,
        "recordCount": None,
        "summary": "",
        "details": [],
        "uncertainItems": [],
    }

    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse sections
        if line.startswith("文書種別:"):
            result["documentType"] = line.split(":", 1)[1].strip()
        elif line.startswith("対象期間:"):
            result["targetPeriod"] = line.split(":", 1)[1].strip()
        elif line.startswith("要約:"):
            result["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("詳細項目:"):
            current_section = "details"
        elif line.startswith("不確実な項目:"):
            current_section = "uncertain"
        elif current_section == "details":
            # Parse detail items
            if ":" in line or ":" in line:
                parts = line.replace(":", ":").split(":")
                if len(parts) >= 2:
                    result["details"].append({
                        "label": parts[0].strip(),
                        "value": parts[1].strip(),
                        "confidence": "medium",
                    })
        elif current_section == "uncertain":
            result["uncertainItems"].append(line)

    # Use full text as summary if parsing failed
    if not result["summary"]:
        result["summary"] = response_text.strip()

    return result