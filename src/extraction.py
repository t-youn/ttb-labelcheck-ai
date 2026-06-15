import re


def extract_fields_from_text(text: str) -> dict:
    """
    Parse structured label fields from raw OCR text.
    Returns best-effort values — agents must review all fields before running validation.
    """
    fields = {
        "brand_name": "",
        "class_type": "",
        "alcohol_content": "",
        "net_contents": "",
        "government_warning": "",
        "bottler_name": "",
        "bottler_location": "",
        "country_of_origin": "",
    }

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # --- Alcohol content: handles "45% Alc./Vol.", "ALC/VOL: 5%", and "5% ALC/VOL"
    abv = re.search(
        r"(?:ALC/?VOL\s*:\s*\d+\.?\d*\s*%"
        r"|\d+\.?\d*\s*%\s*(?:[Aa]lc\.?(?:\s*/\s*[Vv]ol\.?)?|ALC/?VOL))",
        text, re.IGNORECASE
    )
    if abv:
        fields["alcohol_content"] = abv.group(0).strip()
    else:
        proof = re.search(r"\d+\.?\d*\s*[Pp]roof", text)
        if proof:
            fields["alcohol_content"] = proof.group(0).strip()

    # --- Net contents: volume units including gallons
    vol = re.search(
        r"\d+\.?\d*\s*(?:mL|ML|ml|fl\.?\s*oz\.?|L\b|GAL|gal|[Gg]allon[s]?)",
        text
    )
    if vol:
        fields["net_contents"] = vol.group(0).strip()

    # --- Government warning: capture full block after the heading
    warn = re.search(
        r"(GOVERNMENT WARNING\s*:.*?)(?:\n\n|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if warn:
        fields["government_warning"] = " ".join(warn.group(1).split())

    # --- Country of origin: explicit label or common standalone values
    country = re.search(
        r"(?:Product of|Made in|Distilled in|Produced in|Country of Origin\s*:?)\s*([A-Za-z ]+)",
        text, re.IGNORECASE
    )
    if country:
        fields["country_of_origin"] = country.group(1).strip()
    elif re.search(r"\bU\.?S\.?A\.?\b", text):
        fields["country_of_origin"] = "USA"
    elif re.search(r"\bUnited States\b", text, re.IGNORECASE):
        fields["country_of_origin"] = "United States"

    # --- Spirit/beverage class / type (longest/most-specific first to avoid partial matches)
    ttb_types = [
        # Whiskey
        "Kentucky Straight Bourbon Whiskey", "Straight Bourbon Whiskey", "Bourbon Whiskey",
        "Tennessee Whiskey", "Blended Whiskey", "Scotch Whisky", "Irish Whiskey",
        "Single Malt Whisky", "Straight Rye Whiskey", "Rye Whiskey",
        # Spirits
        "Vodka", "Gin", "Rum", "Tequila", "Brandy", "Cognac", "Mezcal",
        # Wine
        "Red Wine", "White Wine", "Rosé Wine", "Sparkling Wine",
        # Beer — multi-word styles before single-word fallbacks
        "Malt Beverage", "Cream Ale", "Pale Ale", "India Pale Ale", "Imperial Stout",
        "Brown Ale", "Amber Ale", "Red Ale", "Wheat Beer", "Hefeweizen",
        "Farmhouse Ale", "Sour Ale", "Witbier", "Pilsner", "Pilsener",
        "Stout", "Porter", "Lager", "Saison", "IPA",
    ]
    for spirit in ttb_types:
        if re.search(r"\b" + re.escape(spirit) + r"\b", text, re.IGNORECASE):
            fields["class_type"] = spirit
            break

    # Fallback: dynamic beer/ale pattern for descriptors like "Ale with Elderberries"
    if not fields["class_type"]:
        beer_match = re.search(
            r"\bAle(?:\s+with\s+[A-Za-z]+)?\b|\bBeer\b|\bLager\b|\bStout\b|\bPorter\b",
            text, re.IGNORECASE
        )
        if beer_match:
            fields["class_type"] = beer_match.group(0).strip()

    # --- Bottler address: handles "Louisville, KY", "Arlington, Virginia", "ARLINGTON, VIRGINIA"
    # State must start with uppercase (rules out mid-sentence words like "women")
    addr_re = re.compile(
        r"[A-Za-z][A-Za-z]+(?: [A-Za-z][A-Za-z]+)*,\s*(?:[A-Z]{2}\b|[A-Z][A-Za-z]{3,19})(?:\s+\d{5})?"
    )

    # Remove lines that contain already-captured field content to avoid false matches
    known_values = [v for v in [
        fields["alcohol_content"], fields["net_contents"], fields["class_type"]
    ] if v]
    remaining = []
    for ln in lines:
        # Require an exact line match for short values; substring match only for longer ones
        if any(
            k.lower() == ln.lower() or (len(k) >= 8 and k.lower() in ln.lower())
            for k in known_values
        ):
            continue
        if "government warning" in ln.lower():
            continue
        if fields["country_of_origin"] and ln.strip() == fields["country_of_origin"]:
            continue
        remaining.append(ln)

    for i, line in enumerate(remaining):
        if addr_re.search(line) and not fields["bottler_location"]:
            fields["bottler_location"] = line
            if i > 0 and not fields["bottler_name"]:
                fields["bottler_name"] = remaining[i - 1]
            break

    # --- Brand name: first non-address remaining line.
    # Join the next line if it looks like a name continuation (e.g. "Example" + "Brewing Company").
    brand_candidate = None
    brand_idx = None
    for i, line in enumerate(remaining):
        if line != fields["bottler_location"] and len(line) > 2:
            brand_candidate = line
            brand_idx = i
            break

    if brand_candidate is not None and brand_idx + 1 < len(remaining):
        next_line = remaining[brand_idx + 1]
        is_continuation = (
            next_line != fields["bottler_location"]
            and not addr_re.search(next_line)
            and "%" not in next_line
            and not re.search(r"\d+\s*(?:mL|ML|GAL|gal|fl)", next_line, re.IGNORECASE)
            and "government warning" not in next_line.lower()
            and not re.search(r"\d", next_line)
            and len(next_line) > 2
        )
        if is_continuation:
            brand_candidate = brand_candidate + " " + next_line

    if brand_candidate:
        fields["brand_name"] = brand_candidate

    return fields
