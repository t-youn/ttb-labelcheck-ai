# Architecture

## Prototype Architecture

TTB LabelCheck AI is a lightweight Streamlit prototype with modular Python components.

```text
Streamlit UI
   |
   |-- Single Label Review
   |      |-- Manual application fields
   |      |-- Image upload
   |      |-- OCR extraction with fallback
   |      |-- Field comparison
   |      |-- Agent review summary
   |
   |-- Batch Review Queue
          |-- CSV upload
          |-- Row-by-row field comparison
          |-- Queue summary
          |-- Detailed results
          |-- CSV export