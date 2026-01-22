"""
User Router - User profile, settings
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pathlib import Path
import time

from database import get_db
from models import User
from schemas import UserResponse, UserProfileUpdate
from utils.auth import get_current_user
from config import settings

router = APIRouter()

AVATAR_DIR = Path(settings.MEDIA_ROOT) / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB


def delete_existing_avatar(avatar_url: str) -> None:
    if not avatar_url:
        return
    if not avatar_url.startswith(settings.MEDIA_URL):
        return
    relative_path = avatar_url.replace(settings.MEDIA_URL, "", 1).lstrip("/")
    file_path = Path(settings.MEDIA_ROOT) / relative_path
    if file_path.is_file():
        try:
            file_path.unlink()
        except OSError:
            pass


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return current_user


@router.put("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile fields"""
    if profile_data.email and profile_data.email != current_user.email:
        existing_email = (
            db.query(User)
            .filter(User.email == profile_data.email, User.id != current_user.id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use"
            )
        current_user.email = profile_data.email

    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/profile/avatar",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and set the user's avatar image"""
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Use JPEG, PNG, or WebP."
        )

    contents = await file.read()
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image exceeds maximum size of 2 MB."
        )

    filename = f"user_{current_user.id}_{int(time.time())}{ALLOWED_AVATAR_TYPES[file.content_type]}"
    destination = AVATAR_DIR / filename
    with open(destination, "wb") as buffer:
        buffer.write(contents)

    avatar_url = f"{settings.MEDIA_URL}/avatars/{filename}"
    delete_existing_avatar(current_user.avatar_url or "")
    current_user.avatar_url = avatar_url

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """Get user public profile by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
