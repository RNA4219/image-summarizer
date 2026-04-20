"""
Image preprocessing module for OCR optimization
"""

import io
from PIL import Image
from typing import Tuple


def preprocess_image(file_bytes: bytes, content_type: str) -> Tuple[bytes, str]:
    """
    Preprocess image for better OCR results.

    - 2x scaling
    - Light binarization

    Args:
        file_bytes: Original image bytes
        content_type: Original content type

    Returns:
        Tuple of (processed image bytes, content type)
    """
    # Load image
    image = Image.open(io.BytesIO(file_bytes))

    # Convert to RGB if necessary (for PNG with transparency)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # 2x scaling
    width, height = image.size
    new_size = (width * 2, height * 2)
    image = image.resize(new_size, Image.LANCZOS)

    # Convert to grayscale
    gray = image.convert("L")

    # Light binarization using point() for efficiency
    threshold = 180
    gray = gray.point(lambda x: 255 if x > threshold else 0)

    # Convert back to RGB for consistency with API
    processed = gray.convert("RGB")

    # Save to bytes
    output = io.BytesIO()
    processed.save(output, format="JPEG", quality=95)
    output.seek(0)

    return output.read(), "image/jpeg"