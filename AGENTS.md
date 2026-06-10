# Project: TTB LabelCheck AI

Build a working Streamlit prototype for AI-assisted alcohol label verification.

Primary goal:
Create a simple, usable, human-in-the-loop compliance assistant that compares submitted application fields against alcohol label artwork.

Do not overbuild.
Working core functionality is more important than a complex architecture.

User audience:
Federal compliance agents with mixed technical comfort levels. The UI must be clean, obvious, and fast.

Core workflow:
1. User enters expected application fields.
2. User uploads a label image.
3. App extracts readable text using OCR.
4. App compares extracted text against expected fields.
5. App shows a field-by-field review summary with status and explanation.
6. App supports basic batch CSV review if time allows.

Required fields:
- Brand name
- Class/type
- Alcohol content
- Net contents
- Government health warning
- Name/address
- Country of origin, if import

Matching categories:
- Exact Match
- Normalized Match
- Possible Match, Human Review
- Mismatch
- Missing / Unreadable

Design principles:
- Human-in-the-loop, not automated final decisioning
- Clear explanations
- No persistent storage
- Processing time displayed
- Simple UI
- Deterministic checks where possible
- AI/cloud services optional, not required for core functionality

Security/compliance notes:
Prototype should avoid storing uploaded files. Production deployment would require FedRAMP-authorized services, audit logging, retention controls, approved identity/access management, and agency cloud boundary review.

Code style:
- Keep code readable and modular.
- Use plain Python.
- Avoid unnecessary frameworks.
- Add comments where logic affects compliance review.
