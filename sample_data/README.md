# Sample Data

## demo_images/

Sample label images for testing the image upload workflow in the Single Label Review tab. Reviewers can select these directly from the app without uploading a file — use the "Or choose a sample label image" dropdown.

| File | Description |
|---|---|
| `approved_beer_label_01.png` | Sample beer label for testing OCR extraction and autofill |
| `approved_beer_label_02.png` | Second sample beer label for comparison |

Both images go through the full upload workflow: image preview, OCR extraction, image quality score, processing time display, and sidebar autofill. If OCR does not produce text, the manual paste fallback remains available.

## application_batch.csv

Batch input file for the Batch Review Queue tab. Contains three pre-built rows covering a clean label, a warning capitalization issue, and an ABV mismatch. Upload this file in the app and click **Run Batch Verification** to see all three cases processed at once.

## demo_cases/

Five individual text files for testing the Single Label Review tab via the paste-text fallback. Each file contains:

- **Label text** — the raw text to paste into the "Paste label text" box
- **Application fields** — the exact values to enter in the left-hand fields
- **Expected result** — what the verification output should show

### clean_approved_label.txt

All application fields exactly match the label text. Every field should return **Exact Match**. Use this first to confirm the baseline workflow is working.

### abv_mismatch_label.txt

The application declares 45% Alc./Vol. but the label shows 40% (80 Proof). The **Alcohol Content** field should return **Mismatch**. All other fields match. Demonstrates the ABV numeric extraction logic that catches proof/percentage discrepancies.

### warning_capitalization_issue.txt

The label uses title-case "Government Warning:" instead of the required all-caps heading "GOVERNMENT WARNING:". The **Government Warning** field should return **Mismatch** with an explanation that the required capitalization format is absent. All other fields match.

### missing_warning_label.txt

The label text contains no warning statement of any kind. The **Government Warning** field should return **Missing / Unreadable**. All other fields match. Demonstrates that the app surfaces complete omissions, not just formatting errors.

### brand_punctuation_case_variation.txt

The application brand is "O'MALLEY'S BREWING CO." (all-caps, straight apostrophe, trailing period). The label shows "O'Malley's Brewing Co." (mixed-case, curly apostrophe). After normalization, both resolve to "omalleys brewing co" — the **Brand Name** field should return **Normalized Match**. Net Contents also returns **Normalized Match** because the label includes a unit qualifier ("12 fl oz") not in the application field. Demonstrates how the normalizer handles punctuation and encoding differences without treating them as mismatches.
