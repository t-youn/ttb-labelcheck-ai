import numpy as np
from PIL import Image, ImageStat


def assess_image_quality(image: Image.Image, ocr_text: str = "") -> dict:
    """
    Score a label image 0-100 across five dimensions.
    Designed to help agents decide how much to trust autofilled fields before verifying.
    """
    scores = {}

    # Resolution proxy: pixel count (no DPI metadata required)
    px = image.width * image.height
    scores["resolution"] = (
        25 if px >= 2_000_000 else
        20 if px >= 500_000 else
        12 if px >= 150_000 else
        5
    )

    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    mean_brightness = stat.mean[0]
    stddev = stat.stddev[0]

    # Brightness: 0–255 scale; 80–180 is ideal for readable text on labels
    scores["brightness"] = (
        25 if 80 <= mean_brightness <= 180 else
        18 if 60 <= mean_brightness <= 200 else
        10 if 40 <= mean_brightness <= 220 else
        3
    )

    # Contrast: higher standard deviation = more tonal range
    scores["contrast"] = (
        20 if stddev >= 60 else
        15 if stddev >= 40 else
        8 if stddev >= 20 else
        2
    )

    # Sharpness via Laplacian variance (blurry images have low variance)
    arr = np.array(gray, dtype=float)
    laplacian = (
        arr[:-2, 1:-1] + arr[2:, 1:-1] +
        arr[1:-1, :-2] + arr[1:-1, 2:] -
        4 * arr[1:-1, 1:-1]
    )
    lap_var = float(np.var(laplacian))
    scores["sharpness"] = (
        20 if lap_var >= 500 else
        14 if lap_var >= 100 else
        7 if lap_var >= 30 else
        2
    )

    # OCR text yield: more extracted text suggests a readable label
    text_len = len(ocr_text.strip())
    scores["ocr_yield"] = (
        10 if text_len >= 200 else
        7 if text_len >= 80 else
        4 if text_len >= 20 else
        0
    )

    total = sum(scores.values())

    if total >= 80:
        status = "Excellent"
        recommendation = "Proceed with automated review"
    elif total >= 60:
        status = "Good"
        recommendation = "Proceed with automated review"
    elif total >= 40:
        status = "Fair"
        recommendation = "Review autofilled fields carefully"
    else:
        status = "Poor"
        recommendation = "Request a clearer label image or use manual entry"

    return {"score": total, "status": status, "recommendation": recommendation}
