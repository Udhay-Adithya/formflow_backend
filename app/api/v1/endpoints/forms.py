import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_form, crud_response
from app.models import  user
from app.schemas import form as form_schema
from app.dependencies import get_current_user, get_db

router = APIRouter()


@router.post("/", response_model=form_schema.Form, status_code=status.HTTP_201_CREATED)
async def create_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_in: form_schema.FormCreate,
    current_user: user.User = Depends(get_current_user),
):
    """
    Create new form owned by the current user, using a client-provided ID.
    """
    form = await crud_form.create_form(db=db, form_in=form_in, owner_id=current_user.id)
    if form is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Form with ID '{form_in.id}' already exists.",
        )
    # Ensure owner data is loaded for the response schema
    # crud function should handle this with eager loading or refresh
    return form


@router.get("/", response_model=List[form_schema.FormSummary])
async def read_forms(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: user.User = Depends(get_current_user),
):
    """
    Retrieve forms owned by the current user, each with its response count.
    """
    forms = await crud_form.get_forms_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    counts = await crud_response.get_response_counts(db=db, form_ids=[form.id for form in forms])
    for form in forms:
        form.response_count = counts.get(form.id, 0)
    return forms


@router.get("/{form_id}", response_model=form_schema.Form)
async def read_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_id: uuid.UUID,
    # Note: For now, allows any authenticated user to *read* a form definition
    # You might want owner-only access or a public flag later.
    # current_user: models.User = Depends(get_current_user), # Uncomment if read requires login
):
    """
    Get a specific form by ID.
    """
    db_form = await crud_form.get_form(db=db, form_id=form_id)
    if db_form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    # Optional: Add ownership check if reading should be restricted
    # if db_form.owner_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return db_form


@router.put("/{form_id}", response_model=form_schema.Form)
async def update_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_id: uuid.UUID,
    form_in: form_schema.FormUpdate,
    current_user: user.User = Depends(get_current_user),
):
    """
    Update a form. Only allowed by the owner.
    """
    db_form = await crud_form.get_form(db=db, form_id=form_id)
    if db_form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    if db_form.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    updated_form = await crud_form.update_form(db=db, db_form=db_form, form_in=form_in)
    return updated_form


@router.delete("/{form_id}", response_model=form_schema.Form)
async def delete_form(
    *,
    db: AsyncSession = Depends(get_db),
    form_id: uuid.UUID,
    current_user: user.User = Depends(get_current_user),
):
    """
    Delete a form. Only allowed by the owner.
    This will also delete all associated responses due to cascade settings.
    """
    db_form = await crud_form.get_form(db=db, form_id=form_id) # Fetch to check ownership first
    if db_form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    if db_form.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    deleted_form = await crud_form.remove_form(db=db, form_id=form_id)
    # remove_form should return the deleted object or None if deletion failed unexpectedly
    # If using status_code 204 (No Content) on success, return Response(status_code=204) instead
    if deleted_form:
        return deleted_form # Return the data of the deleted form
    else:
        # This case should ideally not happen if the ownership check passed
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found for deletion")