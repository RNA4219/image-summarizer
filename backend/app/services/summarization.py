from app.clients.openai_client import summarize_text_with_openai
from app.clients.ollama_client import summarize_text_with_ollama
from app.utils.exceptions import SummaryGenerationFailedError


async def summarize_text(normalized_text: str, summary_mode: str = "api") -> dict:
    """
    テキストを要約し、構造化データを返す

    Args:
        normalized_text: 正規化されたテキスト
        summary_mode: 要約モード ("api" or "local_llm")

    Returns:
        構造化された要約データ

    Raises:
        SummaryGenerationFailedError: 要約結果が空
    """
    if summary_mode == "local_llm":
        result = await summarize_text_with_ollama(normalized_text)
    else:
        # Default: api mode
        result = await summarize_text_with_openai(normalized_text)

    if not result.get("summary"):
        raise SummaryGenerationFailedError()

    return result