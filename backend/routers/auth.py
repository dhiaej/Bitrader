"""
Authentication Router - User registration, login, token management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models import User, Wallet, Reputation
from schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    FaceRegisterResponse, FaceLoginResponse
)
from utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from config import settings

# Try to import face recognition service (optional dependency)
try:
    from services.face_recognition_service import (
        extract_face_embedding,
        verify_face,
        embedding_to_json,
        DEEPFACE_AVAILABLE
    )
except ImportError:
    DEEPFACE_AVAILABLE = False
    extract_face_embedding = None
    verify_face = None
    embedding_to_json = None

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user with initial fake money"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.flush()
    
    # Create initial wallets with fake money
    wallets_config = [
        ("USD", settings.INITIAL_USD_BALANCE),
        ("BTC", settings.INITIAL_BTC_BALANCE),
        ("ETH", settings.INITIAL_ETH_BALANCE),
        ("USDT", settings.INITIAL_USDT_BALANCE),
    ]
    
    for currency, initial_balance in wallets_config:
        wallet = Wallet(
            user_id=new_user.id,
            currency=currency,
            available_balance=initial_balance,
            locked_balance=0.0
        )
        db.add(wallet)
    
    # Create reputation record
    reputation = Reputation(
        user_id=new_user.id,
        score=settings.INITIAL_REPUTATION_SCORE
    )
    db.add(reputation)
    
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login - returns access token"""
    
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current logged in user information"""
    # Refresh user from database to get latest reputation
    db.refresh(current_user)
    
    # Include reputation score if available
    reputation_score = None
    if current_user.reputation:
        reputation_score = current_user.reputation.score
    
    # Create response with reputation score
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        reputation_score=reputation_score
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should delete token)"""
    return {"message": "Successfully logged out"}


@router.post("/face-register", response_model=FaceRegisterResponse, status_code=status.HTTP_200_OK)
async def register_face(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register user's face for face login.
    Requires authentication (user must be logged in).
    
    The user must provide a clear image of their face.
    """
    # Read image data first
    try:
        image_data = await file.read()
        if len(image_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading image file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read image file: {str(e)}"
        )
    
    # Validate image type (content_type can be None, so we check magic numbers as backup)
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        # Validate by checking image magic numbers
        is_image = (
            image_data.startswith(b'\xff\xd8\xff') or  # JPEG
            image_data.startswith(b'\x89PNG\r\n\x1a\n') or  # PNG
            image_data.startswith(b'GIF87a') or  # GIF87a
            image_data.startswith(b'GIF89a') or  # GIF89a
            image_data.startswith(b'RIFF')  # WebP
        )
        
        if not is_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Only JPEG, PNG, GIF, or WebP images are allowed."
            )
    
    # Limit image size (5 MB)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Maximum size is {MAX_IMAGE_SIZE / 1024 / 1024} MB"
        )
    
    # Process image in try block
    try:
        
        # Check if DeepFace is available
        if not DEEPFACE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Face recognition service is not available. Please install DeepFace library."
            )
        
        # Extract face embedding
        try:
            embedding = extract_face_embedding(image_data)
            if embedding is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not detect a face in the image. Please ensure your face is clearly visible, lighting is good, and you're looking directly at the camera."
                )
        except ValueError as e:
            # Handle face detection errors - propagate the detailed error message
            error_msg = str(e)
            logger.warning(f"Face registration failed (ValueError): {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        except ImportError as e:
            logger.error(f"Face registration ImportError: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Face recognition service is not available. DeepFace library not installed."
            )
        except (AttributeError, TypeError) as e:
            # Handle attribute/type errors with detailed logging
            error_msg = str(e)
            logger.error(f"Face registration processing error ({type(e).__name__}): {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image processing error: {error_msg}. Please try with a different image or ensure the image contains a clearly visible face."
            )
        except Exception as e:
            # Catch any other errors
            error_msg = str(e)
            logger.error(f"Face registration unexpected error: {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process image: {error_msg}. Please ensure the image is valid and contains a clearly visible face."
            )
        
        # Store embedding as JSON string
        try:
            embedding_json = embedding_to_json(embedding)
            current_user.face_embedding = embedding_json
        except Exception as e:
            logger.error(f"Error storing face embedding: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save face data: {str(e)}"
            )
        
        db.commit()
        db.refresh(current_user)
        
        return FaceRegisterResponse(
            message="Face registered successfully. You can now use face login.",
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in face registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.post("/face-login", response_model=FaceLoginResponse, status_code=status.HTTP_200_OK)
async def login_with_face(
    username: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Login using face recognition.
    User provides username and face image.
    """
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Check if user has registered face
    if not user.face_embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Face not registered. Please register your face first or use password login."
        )
    
    # Read image data and process
    try:
        # Read image data first
        image_data = await file.read()
        if len(image_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )
        
        # Validate image type (content_type can be None, so we check magic numbers as backup)
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            # Validate by checking image magic numbers
            is_image = (
                image_data.startswith(b'\xff\xd8\xff') or  # JPEG
                image_data.startswith(b'\x89PNG\r\n\x1a\n') or  # PNG
                image_data.startswith(b'GIF87a') or  # GIF87a
                image_data.startswith(b'GIF89a') or  # GIF89a
                image_data.startswith(b'RIFF')  # WebP
            )
            
            if not is_image:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image file. Only JPEG, PNG, GIF, or WebP images are allowed."
                )
        
        # Check if DeepFace is available
        if not DEEPFACE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Face recognition service is not available. Please install DeepFace library."
            )
        
        # Verify face
        try:
            is_match, distance = verify_face(user.face_embedding, image_data)
        except ValueError as e:
            # Handle face detection errors (e.g., no face detected)
            error_msg = str(e)
            logger.warning(f"Face verification failed (ValueError): {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        except ImportError as e:
            logger.error(f"Face verification ImportError: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Face recognition service is not available. DeepFace library not installed."
            )
        except Exception as e:
            logger.error(f"Face verification error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Face verification failed: {str(e)}"
            )
        
        if not is_match:
            from services.face_recognition_service import FACE_VERIFICATION_THRESHOLD
            logger.warning(f"Face verification failed for user {username}. Distance: {distance:.3f}, Threshold: {FACE_VERIFICATION_THRESHOLD}")
            
            # Provide more helpful error message based on distance
            if distance == float('inf'):
                error_detail = (
                    "Could not detect a face in the image. Please ensure:\n"
                    "- Your face is clearly visible and centered\n"
                    "- Lighting is good (not too dark or too bright)\n"
                    "- You're looking directly at the camera\n"
                    "- There's only one person in the frame\n"
                    "- You're at a good distance (50cm-1m from camera)\n"
                    "- Remove masks, sunglasses, or anything covering your face"
                )
            elif distance >= 1.0:
                error_detail = (
                    f"Face detected but verification failed (distance: {distance:.3f}, threshold: {FACE_VERIFICATION_THRESHOLD}). "
                    "This might not be the same person as registered. Please:\n"
                    "- Use the same face you registered\n"
                    "- Ensure similar lighting conditions\n"
                    "- Look directly at the camera with the same angle"
                )
            else:
                error_detail = (
                    f"Face verification failed. Distance: {distance:.3f} (threshold: {FACE_VERIFICATION_THRESHOLD}). "
                    "Please try again with better lighting or ensure you're looking directly at the camera."
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_detail,
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        
        return FaceLoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in face login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process login: {str(e)}"
        )
