# Stakeholder Traceability

This prototype was designed from the discovery notes, not just the technical requirements. The goal is to show how stakeholder feedback translated into product, workflow, and technical decisions.

| Stakeholder Input | Design Response |
|---|---|
| Sarah Chen said agents spend much of their time manually matching label fields against application data. | Built a field-by-field verification workflow comparing submitted application values against extracted or pasted label text. |
| Sarah said prior scanning tools failed because they took 30 to 40 seconds per label and agents could review faster by eye. | Added processing time to the review summary and kept the prototype lightweight. The matching logic is deterministic and fast for core fields. |
| Sarah and Janet noted that importers may submit 200 to 300 label applications at once. | Added a Batch Review Queue using CSV upload, queue summary, detailed results, and downloadable reports. |
| Sarah emphasized agents have mixed technical comfort levels. | Designed a simple Streamlit interface with obvious tabs, clear fields, one primary verification button, and plain-language review recommendations. |
| Marcus Williams said production integration with COLA is not in scope for the prototype. | Kept the prototype standalone with no direct COLA integration. The design can inform future procurement or integration planning. |
| Marcus raised Azure, FedRAMP, firewall, PII, retention, and federal deployment concerns. | Avoided persistent file storage in the prototype and documented that production deployment would require approved cloud boundaries, audit logging, IAM, retention controls, and FedRAMP-authorized services. |
| Dave Morrison warned that label review requires judgment, not rigid pattern matching. | Added match categories including Exact Match, Normalized Match, Possible Match, Human Review, Mismatch, and Missing / Unreadable. |
| Dave gave the example of case and punctuation differences such as “STONE'S THROW” versus “Stone's Throw.” | Added normalization for case, punctuation, apostrophes, and spacing so obvious variations are not automatically treated as failures. |
| Jenny Park said the government warning must be exact and that applicants often change capitalization or wording. | Added stricter validation for the government warning heading and wording, including a mismatch when “Government Warning” appears without the required all-caps heading. |
| Jenny mentioned poor image quality, glare, and awkward label photos. | Added OCR fallback and manual text entry so agents can continue review even when OCR fails or the image is unreadable. |
