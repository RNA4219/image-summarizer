"""Text normalization module"""


def normalize_extracted_text(text: str) -> tuple[str, list[str]]:
    """
    Normalize extracted text and return warnings.

    Args:
        text: Raw extracted text

    Returns:
        Tuple of (normalized_text, warnings)
    """
    warnings = []

    # Basic normalization
    normalized = text.strip()

    # Check for short text
    if len(normalized) < 50:
        warnings.append("抽出テキストが短い可能性があります。")

    # Remove excessive whitespace
    import re
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r" {2,}", " ", normalized)

    return normalized, warnings