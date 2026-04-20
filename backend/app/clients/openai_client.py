import base64
import logging
from typing import Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from app.config import settings
from app.schemas.summarize import StructuredSummary
from app.utils.exceptions import OpenAIAPIError

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """画像内の日本語テキストを抽出してください。
給与明細や帳票のような表形式文書を想定し、項目名と数値の対応が分かる形で出力してください。
読めない箇所は無理に補完せず、そのまま曖昧なまま残してください。"""


async def get_openai_client() -> AsyncOpenAI:
    """
    Dependency injection for OpenAI client.
    """
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout,
    )


async def extract_text_with_openai(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    client: Optional[AsyncOpenAI] = None,
) -> str:
    """
    OpenAI APIを使用して画像からテキストを抽出する

    Args:
        file_bytes: Image bytes
        content_type: Content type
        filename: File name
        client: OpenAI client (optional, defaults to DI client)
    """
    if client is None:
        client = await get_openai_client()

    try:
        base64_image = base64.b64encode(file_bytes).decode("utf-8")
        image_url = f"data:{content_type};base64,{base64_image}"

        logger.info(f"Extracting text from image: {filename}")
        logger.info(f"Using model: {settings.openai_model}")

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
        )

        text = response.choices[0].message.content or ""
        logger.info(f"Extraction completed for {filename}, length: {len(text)}")
        return text

    except RateLimitError as e:
        logger.error(f"Rate limit error: {e}")
        raise OpenAIAPIError("API rate limit reached.")
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise OpenAIAPIError("Failed to connect to API.")
    except APIError as e:
        logger.error(f"API error: {e}")
        raise OpenAIAPIError()


async def summarize_text_with_openai(
    text: str,
    client: Optional[AsyncOpenAI] = None,
) -> dict:
    """
    OpenAI APIのStructured Outputsを使用してテキストを要約し、構造化データを返す

    Args:
        text: Text to summarize
        client: OpenAI client (optional, defaults to DI client)

    Returns:
        dict: 構造化された要約データ
    """
    if client is None:
        client = await get_openai_client()

    try:
        logger.info("Starting summarization with structured output")

        response = await client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": """あなたは日本語の文書要約アシスタントです。
確認可能な情報のみを用いて、保守的な要約を作成してください。

重要なルール：
1. 小さな文字や表形式の列対応が不鮮明な場合は、詳細項目の断定を避けてください
2. 読み取りが不確実な数値は「約」「程度」等の表現を使用するか、「読み取り困難」と記載
3. 抽出結果をそのまま列挙せず、重要な情報を整理して要約

confidence（確信度）の基準：
- high: 明確に読み取れる
- medium: おそらく正しいが確認が必要
- low: 読み取りが不確実""",
                },
                {
                    "role": "user",
                    "content": f"以下のテキストを要約してください：\n\n{text}",
                },
            ],
            response_format=StructuredSummary,
        )

        # Structured Outputから直接パース
        result = response.choices[0].message.parsed
        logger.info(f"Summarization completed, type: {result.documentType}")

        return result.model_dump()

    except RateLimitError as e:
        logger.error(f"Rate limit error: {e}")
        raise OpenAIAPIError("API rate limit reached.")
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise OpenAIAPIError("Failed to connect to API.")
    except APIError as e:
        logger.error(f"API error: {e}")
        raise OpenAIAPIError()