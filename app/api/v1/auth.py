# register/login/refresh
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserRead
from app.schemas.token import Token
from app.crud.user import get_user_by_email, create_user
from app.db.session import get_async_session
from app.auth.password import verify_password
from app.auth.jwt import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_async_session)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = await create_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user = await get_user_by_email(
        db, form_data.username
    )  # username will contain email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    return Token(access_token=access_token, expires_in=access_token_expires.seconds)


# @router.post("/login", response_model=Token)
# async def login(
#     email: str = Form(...),
#     password: str = Form(...),
#     db: AsyncSession = Depends(get_async_session),
# ):
#     user = await get_user_by_email(db, email)
#     if not user:
#         return HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
#         )
#     if not verify_password(password, user.hashed_password):
#         return HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
#         )

#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         subject=str(user.id), expires_delta=access_token_expires
#     )

#     return Token(access_token=access_token, expires_in=access_token_expires.seconds)
