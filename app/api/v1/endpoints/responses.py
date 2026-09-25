import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import response as response_schema
from app.crud import crud_form, crud_response
from app.models import user as user_model
from app.dependencies import get_current_user, get_db # Assuming responses might need auth later
from app.services.response_validation import validate_response

router = APIRouter()

# Note: We are nesting response creation under the form's endpoint for clarity

@router.post("/forms/{form_id}/responses/", response_model=response_schema.Response, status_code=status.HTTP_201_CREATED)
async def create_response_for_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_id: uuid.UUID,
    response_in: response_schema.ResponseCreate,
    # No current_user dependency here = public submission allowed
    # Add Depends(get_current_user) if submissions require login
):
    """
    Submit a new response to a specific form.
    Currently public, but could check form settings later (e.g., require login).
    """
    # 1. Check if form exists
    form = await crud_form.get_form(db=db, form_id=form_id)
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    # Optional: Add validation based on form settings here
    # if form.data.get("settings", {}).get("requireLogin"):
    #    # If requireLogin is true, you'd need a current_user dependency
    #    pass

    # 2. Validate answers against the form definition (required, types, options, lengths)
    errors = validate_response(form.data, response_in.data)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "Some answers are invalid", "errors": errors},
        )

    # 3. Create the response
    response = await crud_response.create_response(
        db=db, response_in=response_in, form_id=form_id
    )
    return response


@router.get("/forms/{form_id}/responses/", response_model=List[response_schema.Response])
async def read_responses_for_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000), # Allow fetching more responses at once
    current_user: user_model.User = Depends(get_current_user), # Only owner can view responses
):
    """
    Retrieve all responses for a specific form. Only allowed by the owner.
    """
    # 1. Check if form exists and if current user owns it
    form = await crud_form.get_form(db=db, form_id=form_id)
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # 2. Fetch responses
    responses = await crud_response.get_responses_by_form(
        db=db, form_id=form_id, skip=skip, limit=limit
    )
    return responses

# Optional: Get a single specific response? Less common use case.
# @router.get("/responses/{response_id}", response_model=schemas.Response)
# async def read_response( ... )
# Requires checking ownership via the response's form_id and then the form's owner_id