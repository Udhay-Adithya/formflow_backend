import uuid
from pydantic import BaseModel, Field
from typing import List, Any, Optional, Dict
from datetime import datetime

from .user import User # Import User schema for relationship

# Define the structure for a single field within the form definition
class FormFieldOption(BaseModel):
    id: str
    value: str
    label: str

class FormField(BaseModel):
    id: str = Field(..., examples=["fld_abc123"])
    type: str = Field(..., examples=["text", "email", "multiple_choice", "checkbox", "dropdown", "textarea", "description"])
    order: int
    label: Optional[str] = None # Label might not exist for 'description' type
    description: Optional[str] = None # Helper text shown under the label
    required: Optional[bool] = False
    placeholder: Optional[str] = None
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    options: Optional[List[FormFieldOption]] = None
    otherOption: Optional[bool] = None # For multiple_choice
    text: Optional[str] = None # For 'description' type
    # Add other potential validation/config fields here as needed
    validation: Optional[Dict[str, Any]] = {}
    config: Optional[Dict[str, Any]] = {}


# Define the overall structure of the form 'data' field (now more specific)
class FormData(BaseModel):
    title: str = Field(..., examples=["Customer Feedback Survey"])
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {} # For future settings like requireLogin
    fields: List[FormField]


# Properties to receive via API on creation
class FormCreate(BaseModel):
    # Instead of raw 'data', expect structured input
    # data: Dict[str, Any] # Old way - less type safe
    id: uuid.UUID # Client provides the ID
    data: FormData # New way - more specific

# Properties to receive via API on update
class FormUpdate(BaseModel):
    # data: Optional[Dict[str, Any]] = None # Old way
    data: Optional[FormData] = None # New way


# Properties shared by models stored in DB
class FormInDBBase(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    # data: Dict[str, Any] # Old way
    data: FormData # New way
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Pydantic V2+ (replaces orm_mode)


# Properties to return to client
class Form(FormInDBBase):
    owner: User # Include owner information


# Properties stored in DB
class FormInDB(FormInDBBase):
    pass