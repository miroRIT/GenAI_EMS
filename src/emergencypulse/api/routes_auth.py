from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from emergencypulse.core.config import Settings, get_settings
from emergencypulse.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Issue an operator access token",
    description=(
        "Authenticates a dispatcher with form credentials and returns a bearer token for "
        "testing secured dispatch APIs in Swagger UI."
    ),
    responses={
        200: {
            "description": "Bearer token issued.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {"description": "Invalid username or password."},
    },
)
async def issue_token(
    form: OAuth2PasswordRequestForm = Depends(), settings: Settings = Depends(get_settings)
) -> TokenResponse:
    if form.username != settings.admin_username or not verify_password(
        form.password, settings.admin_password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(
            subject=form.username,
            scopes=["dispatch:write", "dispatch:read", "health:read"],
            settings=settings,
        )
    )
