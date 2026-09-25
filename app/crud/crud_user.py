import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.form import Form
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.services.default_form import build_default_form_data

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        id=uuid.uuid4(), # Set explicitly so the sample form can reference it before flush
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=user_in.is_active # Or set a default
    )
    db.add(db_user)
    # Every new account starts with a sample form. Same transaction:
    # either both the user and the form are saved, or neither is.
    db.add(Form(id=uuid.uuid4(), owner_id=db_user.id, data=build_default_form_data()))
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Add get_user(db: AsyncSession, user_id: uuid.UUID) later