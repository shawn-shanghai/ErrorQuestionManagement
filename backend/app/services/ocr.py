"""
OCR service wrapping PaddleOCR.
Loaded once at module level so the model is warm on first request.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        logger.info("PaddleOCR model loaded")
    return _ocr


def extract_text(image_path: str) -> str:
    """Run OCR on a local image file and return concatenated text."""
    ocr = get_ocr()
    result = ocr.ocr(image_path, cls=True)
    lines = []
    if result:
        for page in result:
            if page:
                for line in page:
                    text = line[1][0]
                    lines.append(text)
    return "\n".join(lines)
