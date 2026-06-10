# Decision Brief: TTB LabelCheck AI Prototype

## Purpose

TTB LabelCheck AI is a human-in-the-loop prototype designed to reduce repetitive alcohol label verification work while keeping final compliance judgment with trained agents.

The prototype focuses on routine field matching: brand name, class/type, alcohol content, net contents, producer or bottler address, country of origin, and government health warning language.

## What the Prototype Demonstrates

The application demonstrates:

- Single-label review
- Image upload with OCR fallback
- Manual text fallback when OCR is unavailable or unclear
- Field-by-field comparison against submitted application values
- Match categories that support agent judgment
- Review summary with recommended action
- Processing time display
- Batch CSV review queue
- Downloadable review reports

## Why This Matters

The stakeholder notes describe a high-volume compliance environment where 47 agents review approximately 150,000 label applications annually. Much of the routine workload involves verifying whether information on label artwork matches the application.

This prototype targets that repetitive matching work so agents can spend more time on nuanced compliance decisions, exceptions, and applicant communication.

## Human-in-the-Loop Design

The application does not make final regulatory determinations. It supports agent review by identifying likely matches, mismatches, and uncertain cases.

The review categories are:

- Exact Match
- Normalized Match
- Possible Match, Human Review
- Mismatch
- Missing / Unreadable

This design reflects the stakeholder concern that label review requires judgment, especially when wording, formatting, punctuation, or image quality creates ambiguity.

## Security and Compliance Considerations

The prototype avoids persistent storage and does not integrate with COLA or other production systems.

A production version would require:

- Deployment within an approved federal cloud boundary
- FedRAMP-authorized services
- Identity and access management
- Role-based access controls
- Audit logging
- Document retention controls
- Privacy review for any PII or business-sensitive submissions
- Monitoring and incident response procedures
- Model and OCR performance evaluation
- Human override tracking

## Recommended Pilot

A controlled pilot should begin with a small group of 5 to 10 agents across different experience and technical comfort levels.

Suggested pilot metrics:

- Average review time per label
- Percentage of labels routed to human review
- False positive rate
- False negative rate
- Agent override rate
- OCR failure rate
- Agent satisfaction
- Batch processing time savings

The pilot should begin as an assistive pre-screening workflow, not as an automated approval or rejection tool.

## Trade-Offs

This prototype prioritizes a working core application over broad regulatory coverage.

Current limitations:

- Batch mode uses CSV label text rather than multi-image OCR
- OCR depends on local environment configuration
- No direct COLA integration
- No database or persistent case history
- Limited beverage-specific regulatory logic
- No authentication or role-based access control

These trade-offs are intentional for a time-constrained proof of concept.

## Future Enhancements

Future versions could include:

- Azure AI Document Intelligence or approved OCR services
- Batch image OCR
- COLA workflow integration
- Review history and audit trail
- Confidence scoring by field
- Beverage-type-specific validation rules
- Image quality detection
- Role-based access
- Dashboard reporting for supervisors
- Feedback loop for agent overrides
