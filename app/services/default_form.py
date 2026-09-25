"""
Sample form every new user starts with, so the dashboard is never empty on first login.
"""
import uuid
from typing import Any, Dict

from app.schemas.form import FormData


def _options(*labels: str) -> Dict[str, Any]:
    return {"options": [{"label": label, "value": label.lower().replace(" ", "_")} for label in labels]}


def build_default_form_data() -> Dict[str, Any]:
    """Build the sample form definition with fresh field ids."""
    fields = [
        {"type": "text", "label": "Full name", "required": True, "placeholder": "Enter your name"},
        {"type": "email", "label": "Email address", "required": True, "placeholder": "you@example.com"},
        {
            "type": "multiple_choice",
            "label": "How would you rate our service?",
            "required": True,
            "config": _options("Excellent", "Good", "Average", "Poor"),
        },
        {
            "type": "dropdown",
            "label": "How did you hear about us?",
            "config": _options("Social media", "Friend", "Search engine", "Other"),
        },
        {
            "type": "checkboxes",
            "label": "Which features did you use?",
            "config": _options("Drag and drop builder", "AI generation", "Share links", "Response analytics"),
        },
        {
            "type": "number",
            "label": "How likely are you to recommend us? (0-10)",
            "placeholder": "0-10",
            "validation": {"min": 0, "max": 10},
        },
        {"type": "paragraph", "label": "Any other feedback?", "placeholder": "Tell us more"},
    ]

    data = {
        "title": "Customer Feedback Survey (Sample)",
        "description": "A sample form to explore FormFlow. Edit it, share it, or delete it.",
        "settings": {
            "requiresLogin": False,
            "confirmationMessage": "Thank you for your feedback!",
            "allowMultipleSubmissions": True,
        },
        "fields": [
            {"id": str(uuid.uuid4()), "order": index, **field} for index, field in enumerate(fields)
        ],
    }
    # Round-trip through the schema so the sample always matches what the API accepts
    return FormData(**data).model_dump()
