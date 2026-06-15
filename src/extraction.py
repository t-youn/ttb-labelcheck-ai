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

    # --- Alcohol content: % Alc./Vol. or proof
    abv = re.search(r"\d+\.?\d*\s*%\s*[Aa]lc\.?(?:\s*/\s*[Vv]ol\.?)?", text)
    if abv:
        fields["alcohol_content"] = abv.group(0).strip()
    else:
        proof = re.search(r"\d+\.?\d*\s*[Pp]roof", text)
        if proof:
            fields["alcohol_content"] = proof.group(0).strip()

    # --- Net contents: volume units
    vol = re.search(r"\d+\.?\d*\s*(?:mL|ML|ml|fl\.?\s*oz\.?|L(?:\b))", text)
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

    # --- Spirit class / type: match against common TTB-recognized designations
    ttb_types = [
        "Kentucky Straight Bourbon Whiskey", "Straight Bourbon Whiskey", "Bourbon Whiskey",
        "Tennessee Whiskey", "Blended Whiskey", "Scotch Whisky", "Irish Whiskey",
        "Single Malt Whisky", "Straight Rye Whiskey", "Rye Whiskey",
        "Vodka", "Gin", "Rum", "Tequila", "Brandy", "Cognac", "Mezcal",
        "Red Wine", "White Wine", "Rosé Wine", "Sparkling Wine", "Malt Beverage",
    ]
    for spirit in ttb_types:
        if spirit.lower() in text.lower():
            fields["class_type"] = spirit
            break

    # --- Bottler address: City, ST patterns (e.g. "Louisville, KY")
    addr_re = re.compile(r"[A-Z][a-z]+(?: [A-Z][a-z]+)*,\s*[A-Z]{2}(?:\s+\d{5})?")

    # Remove lines that contain already-captured field content to avoid false matches
    known_values = [v for v in [
        fields["alcohol_content"], fields["net_contents"], fields["class_type"]
    ] if v]
    remaining = []
    for ln in lines:
        if any(k.lower() in ln.lower() for k in known_values):
            continue
        if "government warning" in ln.lower():
            continue
        if fields["country_of_origin"] and ln.strip() == fields["country_of_origin"]:
            continue
        remaining.append(ln)

    for i, line in enumerate(remaining):
        if addr_re.search(line) and not fields["bottler_location"]:
            fields["bottler_location"] = line
            # The line immediately before an address is typically the bottler name
            if i > 0 and not fields["bottler_name"]:
                fields["bottler_name"] = remaining[i - 1]
            break

    # --- Brand name: first non-address remaining line.
    # On many labels the brand and producer share the same name — that's expected.
    for line in remaining:
        if line != fields["bottler_location"] and len(line) > 2:
            fields["brand_name"] = line
            break

    return fields
