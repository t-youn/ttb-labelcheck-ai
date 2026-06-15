import os
from PIL import Image
import pytesseract

_HOMEBREW_TESSERACT = "/opt/homebrew/bin/tesseract"

def _configure_tesseract():
    if os.path.isfile(_HOMEBREW_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = _HOMEBREW_TESSERACT

def extract_text_from_image(uploaded_file):
    """
    Attempts OCR extraction from an uploaded image.
    Returns extracted text and an error message.
    If OCR is unavailable, the app can still use pasted label text.
    """
    _configure_tesseract()
    try:
        image = uploaded_file if isinstance(uploaded_file, Image.Image) else Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
        return text.strip(), None
    except pytesseract.TesseractNotFoundError:
        return "", (
            "Tesseract is not installed or not on PATH. "
            "Install it with: brew install tesseract"
        )
    except Exception as exc:
        return "", (
            "OCR could not run in this environment. "
            "You can still paste label text manually. "
            f"Technical detail: {str(exc)}"
        )
