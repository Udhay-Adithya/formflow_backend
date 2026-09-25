"""
Server-side validation of form submissions against the stored form definition.

The client validates too, but anyone can call the API directly, so the server
is the source of truth for what a valid answer looks like.
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional, Set

# Field types that only display content and never collect an answer
DISPLAY_ONLY_TYPES = {
    "description", "image", "link", "form_heading", "section_heading",
    "sub_heading", "divider", "spacer", "submit", "page_break",
}
TEXT_TYPES = {"text", "paragraph", "text_editor", "phone", "signature"}
SINGLE_CHOICE_TYPES = {"multiple_choice", "dropdown"}

# Same rule the frontend uses, so both sides agree on what a valid email is
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_response(form_data: Dict[str, Any], answers: Dict[str, Any]) -> Dict[str, str]:
    """
    Check submitted answers against the form's fields.
    Returns a mapping of field id -> error message; an empty dict means the submission is valid.
    """
    fields = {
        field["id"]: field
        for field in form_data.get("fields", [])
        if field.get("type") not in DISPLAY_ONLY_TYPES
    }
    errors: Dict[str, str] = {}

    for field_id in answers:
        if field_id not in fields:
            errors[field_id] = "Unknown field"

    for field_id, field in fields.items():
        value = answers.get(field_id)
        if _is_empty(value):
            if field.get("required"):
                errors[field_id] = "This field is required"
            continue
        error = _check_value(field, value)
        if error:
            errors[field_id] = error

    return errors


def _is_empty(value: Any) -> bool:
    # `is False` (not `== False`) so that the number 0 still counts as an answer
    return (
        value is None
        or value is False
        or (isinstance(value, str) and not value.strip())
        or (isinstance(value, list) and len(value) == 0)
    )


def _check_value(field: Dict[str, Any], value: Any) -> Optional[str]:
    field_type = field.get("type")
    rules = field.get("validation") or {}
    config = field.get("config") or {}

    if field_type in TEXT_TYPES or field_type == "email":
        if not isinstance(value, str):
            return "Must be text"
        if field_type == "email" and not EMAIL_RE.match(value):
            return "Please enter a valid email address"
        min_length = rules.get("minLength", field.get("minLength"))
        max_length = rules.get("maxLength", field.get("maxLength"))
        if min_length is not None and len(value) < min_length:
            return f"Must be at least {min_length} characters"
        if max_length is not None and len(value) > max_length:
            return f"Must be at most {max_length} characters"
        return None

    if field_type == "number":
        # bool is a subclass of int in Python, so exclude it explicitly
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "Must be a number"
        if rules.get("min") is not None and value < rules["min"]:
            return f"Value must be at least {rules['min']}"
        if rules.get("max") is not None and value > rules["max"]:
            return f"Value must be at most {rules['max']}"
        return None

    if field_type == "date_time":
        if not isinstance(value, str):
            return "Must be a date"
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "Must be a valid date"
        return None

    if field_type == "checkbox":
        return None if isinstance(value, bool) else "Must be true or false"

    allowed = _allowed_values(field)
    is_multi_select = field_type == "checkboxes" or (field_type == "choice" and config.get("multiple"))

    if is_multi_select:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return "Must be a list of options"
        if allowed and any(item not in allowed for item in value):
            return "Contains an invalid option"
        return None

    if field_type in SINGLE_CHOICE_TYPES or field_type == "choice":
        if not isinstance(value, str):
            return "Must be a single option"
        if allowed and value not in allowed:
            return "Invalid option"
        return None

    # Unknown field types are accepted as-is so new components don't break submissions
    return None


def _allowed_values(field: Dict[str, Any]) -> Set[str]:
    """Collect valid option values from both config.options and legacy top-level options."""
    config = field.get("config") or {}
    options = (config.get("options") or []) + (field.get("options") or [])
    allowed = {str(option.get("value")) for option in options if isinstance(option, dict)}
    if allowed and (config.get("allowOther") or field.get("otherOption")):
        allowed.add("other")
    return allowed
