# TTB LabelCheck AI

AI-assisted alcohol label verification prototype for compliance review workflows.

## Summary

TTB LabelCheck AI is a human-in-the-loop prototype that helps compliance agents compare submitted alcohol label application fields against label artwork or extracted label text.

The goal is not to automate final regulatory decisions. The goal is to reduce repetitive field matching, surface likely discrepancies, and help agents prioritize review work.

## Problem

The discovery notes describe a compliance environment where agents review a high volume of label applications and spend significant time manually checking whether label artwork matches submitted application data.

Common checks include:

- Brand name
- Class/type designation
- Alcohol content
- Net contents
- Producer or bottler address
- Country of origin
- Government health warning statement

This prototype focuses on those routine checks while keeping final judgment with the agent.

## Features

### Single Label Review

- Manual application field entry
- Label image upload (PNG, JPG, JPEG)
- Live image preview after upload
- OCR extraction with autofill of editable review fields
- Image quality scoring with status, recommendation, and processing time
- Manual pasted text fallback when OCR fails or image quality is too low
- Agents must review and confirm autofilled fields before running verification
- Field-by-field comparison
- Agent review summary
- Downloadable CSV results

### Batch Review Queue

- CSV upload for multiple applications
- Row-by-row verification
- Review queue summary
- Detailed field-level results
- Downloadable batch reports

### Match Categories

The prototype uses clear review categories:

- Exact Match
- Normalized Match
- Possible Match, Human Review
- Mismatch
- Missing / Unreadable

## Stakeholder-Informed Design

The application design reflects the discovery notes:

- Sarah needed speed, simplicity, and batch support.
- Marcus raised infrastructure, FedRAMP, firewall, and security concerns.
- Dave emphasized agent judgment and review nuance.
- Jenny highlighted strict government warning requirements and image quality issues.

The label upload workflow directly addresses feedback about poor image quality, glare, and unreadable labels in the field. The image quality score and recommendation give agents immediate signal on whether OCR output can be trusted. Processing time is displayed to confirm the workflow stays within the roughly 5-second threshold stakeholders identified as the minimum for practical use.

See docs/stakeholder_traceability.md for the full traceability matrix.

## Architecture

The app is built with:

- Python
- Streamlit
- pandas
- pytesseract
- rapidfuzz
- Pillow

Core files:

text app.py src/ocr.py src/matching.py sample_data/application_batch.csv docs/ 

See docs/architecture.md for more detail.

## Setup

Create and activate a virtual environment:

bash python3 -m venv .venv source .venv/bin/activate 

Install dependencies:

bash pip install -r requirements.txt 

Run the app:

bash streamlit run app.py 

## Suggested Reviewer Demo

Follow these steps in order to exercise all major workflows.

**Step 1 — Image upload (Single Label Review tab)**

1. Open the Single Label Review tab.
2. Upload any PNG or JPG label image using the file uploader.
3. Review the image quality score and recommendation that appear immediately after upload.
4. If OCR runs successfully, confirm the autofilled fields before proceeding.
5. Click **Run Verification** to see field-by-field results.

**Step 2 — Paste fallback using demo cases**

Use the files in `sample_data/demo_cases/` when no image is available or to test specific failure modes. For each file:

1. Open the file and copy the label text block (lines above the `--- Application fields ---` separator).
2. In the app, expand **Paste label text manually** and paste the text.
3. Enter the application field values listed in the file.
4. Click **Run Verification** and compare the output to the expected results described in the file.

| Demo file | Key expected outcome |
|---|---|
| `clean_approved_label.txt` | All fields — Exact Match |
| `abv_mismatch_label.txt` | Alcohol Content — Mismatch (45% vs 40%) |
| `warning_capitalization_issue.txt` | Government Warning — Mismatch (wrong heading case) |
| `missing_warning_label.txt` | Government Warning — Missing / Unreadable |
| `brand_punctuation_case_variation.txt` | Brand Name — Normalized Match (apostrophe/case difference) |

See `sample_data/README.md` for a full explanation of each case.

**Step 3 — Batch mode**

1. Open the **Batch Review Queue** tab.
2. Upload `sample_data/application_batch.csv`.
3. Click **Run Batch Verification**.
4. Review the summary table and download the CSV report.
5. The batch contains one clean row, one warning-capitalization issue, and one ABV mismatch — the summary should reflect two rows with at least one flag each.

## Testing Batch Mode

Use the sample batch file:

text sample_data/application_batch.csv 

Upload it in the Batch Review Queue tab and click Run Batch Verification.

## OCR Notes

The prototype includes OCR support through pytesseract. If local OCR is not configured, the app still works through the manual pasted text fallback.

This fallback is intentional. It prevents the review workflow from failing when OCR is unavailable, blocked, or unreliable.

## Security and Compliance Notes

This prototype:

- Does not store uploaded files permanently
- Does not use a database
- Does not integrate with COLA
- Does not make final compliance determinations
- Keeps the agent in control

A production version would require:

- Approved federal cloud deployment
- FedRAMP-authorized services
- Identity and access management
- Audit logging
- Retention policies
- Privacy review
- Monitoring and incident response
- Human override tracking

## Trade-Offs

This is a time-constrained prototype. It prioritizes a working core workflow over broad regulatory coverage.

Current limitations:

- Batch mode uses CSV label text rather than batch image OCR
- OCR may depend on local environment configuration
- No authentication
- No persistent case history
- Limited beverage-specific compliance logic
- No direct COLA integration

## Future Enhancements

Potential future improvements:

- Batch image OCR
- Azure AI Document Intelligence integration
- Confidence scoring by field
- Beverage-specific validation rules
- Review history and audit trail
- Agent override feedback loop
- COLA workflow integration
- Supervisor dashboard