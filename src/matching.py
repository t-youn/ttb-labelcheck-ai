import re
from rapidfuzz import fuzz

def normalize_text(value: str) -> str:
    if value is None:
        return ""
    value = value.lower()
    value = value.replace("'", "")
    value = value.replace("’", "")
    value = re.sub(r"[^a-z0-9.% ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()

def extract_abv_values(text: str):
    text = text.lower()
    values = []

    percent_matches = re.findall(r"(\d+(?:\.\d+)?)\s*%|\b(\d+(?:\.\d+)?)\s*abv", text)
    for match in percent_matches:
        for item in match:
            if item:
                values.append(float(item))

    proof_matches = re.findall(r"(\d+(?:\.\d+)?)\s*proof", text)
    for proof in proof_matches:
        values.append(float(proof) / 2)

    return values

def compare_alcohol_content(expected: str, label_text: str):
    expected_values = extract_abv_values(expected)
    label_values = extract_abv_values(label_text)

    for expected_value in expected_values:
        for label_value in label_values:
            if abs(expected_value - label_value) < 0.1:
                return "Exact Match", f"Alcohol content matched at approximately {expected_value}% ABV."

    if expected and normalize_text(expected) in normalize_text(label_text):
        return "Exact Match", "Alcohol content text appears on the label."

    return "Mismatch", "Expected alcohol content was not clearly found on the label."

def compare_government_warning(expected: str, label_text: str):
    if not expected:
        return "Missing / Unreadable", "No expected warning statement was provided."

    if expected in label_text:
        return "Exact Match", "Government warning text appears exactly as expected."

    if "GOVERNMENT WARNING:" not in label_text:
        if "government warning" in label_text.lower():
            return "Mismatch", "Warning heading appears present but not in required all-caps format."
        return "Missing / Unreadable", "Government warning heading was not found."

    expected_norm = normalize_text(expected)
    label_norm = normalize_text(label_text)

    score = fuzz.partial_ratio(expected_norm, label_norm)
    if score >= 92:
        return "Possible Match, Human Review", "Warning appears substantially present, but exact wording should be reviewed."
    return "Mismatch", "Government warning text does not appear to match the expected language."

def compare_generic_field(field_name: str, expected: str, label_text: str):
    if not expected:
        return "Missing / Unreadable", "No expected value was provided."

    expected_norm = normalize_text(expected)
    label_norm = normalize_text(label_text)

    if expected in label_text:
        return "Exact Match", "Expected value appears exactly on the label."

    if expected_norm and expected_norm in label_norm:
        return "Normalized Match", "Expected value appears after normalizing case, punctuation, or spacing."

    score = fuzz.partial_ratio(expected_norm, label_norm)
    if score >= 88:
        return "Possible Match, Human Review", f"Similar text found with fuzzy match score {score}."

    return "Mismatch", "Expected value was not clearly found on the label."

def compare_label_fields(expected_fields: dict, label_text: str):
    results = []

    for field_name, expected_value in expected_fields.items():
        if field_name == "Alcohol Content":
            status, explanation = compare_alcohol_content(expected_value, label_text)
        elif field_name == "Government Warning":
            status, explanation = compare_government_warning(expected_value, label_text)
        else:
            status, explanation = compare_generic_field(field_name, expected_value, label_text)

        results.append({
            "Field": field_name,
            "Application Value": expected_value,
            "Status": status,
            "Explanation": explanation
        })

    return results
