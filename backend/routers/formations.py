"""
Formations Router
Endpoints for course/formation management with AI integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import logging

from database import get_db
from models import (
    User, Formation, UserProgress, Certificate, FormationLevel, LessonType,
    Module, Quiz, Exam, QuizAttempt, ExamAttempt, FormationAssignment
)
from utils.auth import get_current_user, get_current_admin, get_optional_user
from services.gemini_service import gemini_service
from services.market_data_service import market_data_service
from services.binance_service import binance_service
from services.pdf_service import pdf_service
from services.module_splitter_service import module_splitter_service
from services.video_generation_service import video_generation_service
from services.quiz_generation_service import quiz_generation_service
from services.certificate_service import certificate_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== REQUEST/RESPONSE MODELS ====================

class LessonData(BaseModel):
    """Lesson data structure"""
    id: str
    title: str
    type: str  # TEXT, VIDEO, QUIZ, CHALLENGE
    data: str
    duration: Optional[int] = None


class FormationCreate(BaseModel):
    """Request model for creating a formation"""
    title: str
    description: Optional[str] = None
    level: str  # BEGINNER, INTERMEDIATE, ADVANCED
    content_json: Optional[List[LessonData]] = []
    thumbnail_url: Optional[str] = None
    estimated_duration: Optional[int] = None


class FormationUpdate(BaseModel):
    """Request model for updating a formation"""
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    content_json: Optional[List[LessonData]] = None
    thumbnail_url: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_active: Optional[bool] = None


class FormationResponse(BaseModel):
    """Response model for formation"""
    id: int
    title: str
    description: Optional[str]
    level: str
    content_json: List[dict]
    thumbnail_url: Optional[str]
    estimated_duration: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProgressResponse(BaseModel):
    """Response model for user progress"""
    id: int
    user_id: int
    formation_id: int
    completed_lessons: List[str]
    current_lesson_id: Optional[str]
    status: str
    progress_percentage: float
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request model for chat with Gemini"""
    question: str
    userId: int
    context: Optional[str] = None


class CompleteLessonRequest(BaseModel):
    """Request model for completing a lesson"""
    lesson_id: str


# ==================== FORMATION ENDPOINTS ====================

@router.get("", response_model=List[FormationResponse])
async def get_formations(
    level: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Get formations assigned to the current user (or all if admin)
    
    Args:
        level: Filter by level (BEGINNER, INTERMEDIATE, ADVANCED)
        current_user: Authenticated user (optional)
        db: Database session
        
    Returns:
        List of formations
    """
    query = db.query(Formation).filter(Formation.is_active == True)
    
    # If user is logged in, filter by assignments (unless admin)
    if current_user:
        if not current_user.is_admin:
            # For regular users, only show assigned formations
            # Query assignments for this user
            assignments = db.query(FormationAssignment).filter(
                FormationAssignment.user_id == current_user.id
            ).all()
            logger.info(f"User {current_user.id} (non-admin) has {len(assignments)} assignments")
            
            if assignments:
                formation_ids = [assignment.formation_id for assignment in assignments]
                logger.info(f"User {current_user.id} assigned formation IDs: {formation_ids}")
                query = query.filter(Formation.id.in_(formation_ids))
            else:
                # No assignments, return empty list
                logger.info(f"User {current_user.id} has no assignments, returning empty list")
                return []
        else:
            logger.info(f"User {current_user.id} is admin, showing all formations")
        # Admins see all formations
    
    if level:
        try:
            level_enum = FormationLevel(level.upper())
            query = query.filter(Formation.level == level_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid level. Must be one of: BEGINNER, INTERMEDIATE, ADVANCED"
            )
    
    formations = query.order_by(Formation.created_at.desc()).all()
    
    result = []
    for formation in formations:
        content_json = json.loads(formation.content_json) if formation.content_json else []
        result.append(FormationResponse(
            id=formation.id,
            title=formation.title,
            description=formation.description,
            level=formation.level.value,
            content_json=content_json,
            thumbnail_url=formation.thumbnail_url,
            estimated_duration=formation.estimated_duration,
            is_active=formation.is_active,
            created_at=formation.created_at,
            updated_at=formation.updated_at
        ))
    
    return result


@router.get("/{formation_id}")
async def get_formation(
    formation_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific formation by ID with optional user-specific data
    
    Args:
        formation_id: Formation ID
        current_user: Optional authenticated user (for progress/certificate info)
        db: Database session
        
    Returns:
        Formation details with optional progress and certificate info
    """
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    content_json = json.loads(formation.content_json) if formation.content_json else []
    
    # Get modules if this is a PDF-based course
    modules = db.query(Module).filter(
        Module.formation_id == formation_id
    ).order_by(Module.module_number).all()
    
    # Get exam if exists
    exam = db.query(Exam).filter(Exam.formation_id == formation_id).first()
    
    # Base response
    response = {
        "id": formation.id,
        "title": formation.title,
        "description": formation.description,
        "level": formation.level.value,
        "content_json": content_json,
        "thumbnail_url": formation.thumbnail_url,
        "estimated_duration": formation.estimated_duration,
        "is_active": formation.is_active,
        "created_at": formation.created_at,
        "updated_at": formation.updated_at,
        "has_modules": len(modules) > 0,
        "modules_count": len(modules),
        "has_exam": exam is not None
    }
    
    # Add user-specific data if authenticated
    if current_user:
        # Get progress
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.formation_id == formation_id
        ).first()
        
        if progress:
            response["user_progress"] = {
                "status": progress.status,
                "progress_percentage": progress.progress_percentage,
                "started_at": progress.started_at,
                "completed_at": progress.completed_at
            }
        
        # Get certificate if exists
        certificate = db.query(Certificate).filter(
            Certificate.user_id == current_user.id,
            Certificate.formation_id == formation_id
        ).first()
        
        if certificate:
            response["certificate"] = {
                "certificate_url": certificate.certificate_url,
                "issued_at": certificate.issued_at
            }
    
    return response


@router.post("", response_model=FormationResponse, status_code=status.HTTP_201_CREATED)
async def create_formation(
    formation: FormationCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new formation (Admin only)
    
    Args:
        formation: Formation data
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Created formation
    """
    try:
        level_enum = FormationLevel(formation.level.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {formation.level}")
    
    try:
        content_json = json.dumps([lesson.dict() for lesson in formation.content_json])
        
        new_formation = Formation(
            title=formation.title,
            description=formation.description,
            level=level_enum,
            content_json=content_json,
            thumbnail_url=formation.thumbnail_url,
            estimated_duration=formation.estimated_duration
        )
        
        db.add(new_formation)
        db.commit()
        db.refresh(new_formation)
        
        content_json_parsed = json.loads(new_formation.content_json) if new_formation.content_json else []
        
        return FormationResponse(
            id=new_formation.id,
            title=new_formation.title,
            description=new_formation.description,
            level=new_formation.level.value,
            content_json=content_json_parsed,
            thumbnail_url=new_formation.thumbnail_url,
            estimated_duration=new_formation.estimated_duration,
            is_active=new_formation.is_active,
            created_at=new_formation.created_at,
            updated_at=new_formation.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid level: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create formation: {str(e)}")


@router.put("/{formation_id}", response_model=FormationResponse)
async def update_formation(
    formation_id: int,
    formation: FormationUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a formation (Admin only)
    
    Args:
        formation_id: Formation ID
        formation: Updated formation data
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Updated formation
    """
    db_formation = db.query(Formation).filter(Formation.id == formation_id).first()
    
    if not db_formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    try:
        if formation.title is not None:
            db_formation.title = formation.title
        if formation.description is not None:
            db_formation.description = formation.description
        if formation.level is not None:
            db_formation.level = FormationLevel(formation.level.upper())
        if formation.content_json is not None:
            db_formation.content_json = json.dumps([lesson.dict() for lesson in formation.content_json])
        if formation.thumbnail_url is not None:
            db_formation.thumbnail_url = formation.thumbnail_url
        if formation.estimated_duration is not None:
            db_formation.estimated_duration = formation.estimated_duration
        if formation.is_active is not None:
            db_formation.is_active = formation.is_active
        
        db.commit()
        db.refresh(db_formation)
        
        content_json_parsed = json.loads(db_formation.content_json) if db_formation.content_json else []
        
        return FormationResponse(
            id=db_formation.id,
            title=db_formation.title,
            description=db_formation.description,
            level=db_formation.level.value,
            content_json=content_json_parsed,
            thumbnail_url=db_formation.thumbnail_url,
            estimated_duration=db_formation.estimated_duration,
            is_active=db_formation.is_active,
            created_at=db_formation.created_at,
            updated_at=db_formation.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid level: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update formation: {str(e)}")


@router.delete("/{formation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_formation(
    formation_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a formation (Admin only)
    
    Args:
        formation_id: Formation ID
        current_user: Authenticated admin user
        db: Database session
    """
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    try:
        db.delete(formation)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete formation: {str(e)}")


# ==================== PROGRESS ENDPOINTS ====================

@router.get("/{formation_id}/progress/{user_id}", response_model=UserProgressResponse)
async def get_user_progress(
    formation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user progress for a formation
    
    Args:
        formation_id: Formation ID
        user_id: User ID (must match current user or be admin)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        User progress
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this progress")
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.formation_id == formation_id
    ).first()
    
    if not progress:
        # Return default progress if not found
        return UserProgressResponse(
            id=0,
            user_id=user_id,
            formation_id=formation_id,
            completed_lessons=[],
            current_lesson_id=None,
            status="NOT_STARTED",
            progress_percentage=0.0,
            started_at=datetime.now(),
            completed_at=None
        )
    
    completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
    
    return UserProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        formation_id=progress.formation_id,
        completed_lessons=completed_lessons,
        current_lesson_id=progress.current_lesson_id,
        status=progress.status,
        progress_percentage=progress.progress_percentage,
        started_at=progress.started_at,
        completed_at=progress.completed_at
    )


@router.post("/{formation_id}/progress/{user_id}/complete-lesson")
async def complete_lesson(
    formation_id: int,
    user_id: int,
    request: CompleteLessonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a lesson as completed
    
    Args:
        formation_id: Formation ID
        user_id: User ID
        request: Lesson completion request
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated progress
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get or create progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.formation_id == formation_id
    ).first()
    
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    content_json = json.loads(formation.content_json) if formation.content_json else []
    total_lessons = len(content_json)
    
    if not progress:
        progress = UserProgress(
            user_id=user_id,
            formation_id=formation_id,
            completed_lessons=json.dumps([request.lesson_id]),
            current_lesson_id=request.lesson_id,
            status="IN_PROGRESS",
            progress_percentage=1.0 / total_lessons * 100 if total_lessons > 0 else 0.0
        )
        db.add(progress)
    else:
        completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
        if request.lesson_id not in completed_lessons:
            completed_lessons.append(request.lesson_id)
            progress.completed_lessons = json.dumps(completed_lessons)
            progress.current_lesson_id = request.lesson_id
            progress.progress_percentage = len(completed_lessons) / total_lessons * 100 if total_lessons > 0 else 0.0
            
            # Check if all lessons completed
            if len(completed_lessons) >= total_lessons:
                progress.status = "COMPLETED"
                progress.completed_at = datetime.now()
            else:
                progress.status = "IN_PROGRESS"
    
    db.commit()
    db.refresh(progress)
    
    completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
    
    return UserProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        formation_id=progress.formation_id,
        completed_lessons=completed_lessons,
        current_lesson_id=progress.current_lesson_id,
        status=progress.status,
        progress_percentage=progress.progress_percentage,
        started_at=progress.started_at,
        completed_at=progress.completed_at
    )


@router.post("/{formation_id}/modules/{module_id}/complete")
async def complete_module(
    formation_id: int,
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a module as watched/completed (for video viewing)"""
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.formation_id == formation_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get or create progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.formation_id == formation_id
    ).first()
    
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    total_modules = db.query(Module).filter(Module.formation_id == formation_id).count()
    module_lesson_id = f"module_{module_id}"
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            formation_id=formation_id,
            completed_lessons=json.dumps([module_lesson_id]),
            current_lesson_id=module_lesson_id,
            status="IN_PROGRESS",
            progress_percentage=(1.0 / total_modules * 100) if total_modules > 0 else 0.0
        )
        db.add(progress)
    else:
        completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
        if module_lesson_id not in completed_lessons:
            completed_lessons.append(module_lesson_id)
            progress.completed_lessons = json.dumps(completed_lessons)
            progress.current_lesson_id = module_lesson_id
            progress.progress_percentage = (len(completed_lessons) / total_modules * 100) if total_modules > 0 else 0.0
            progress.status = "IN_PROGRESS"
    
    db.commit()
    db.refresh(progress)
    
    completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
    
    return {
        "module_id": module_id,
        "completed": True,
        "progress_percentage": progress.progress_percentage,
        "total_modules": total_modules,
        "completed_modules": len(completed_lessons)
    }


@router.post("/{formation_id}/certificate/{user_id}")
async def generate_certificate(
    formation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a certificate for completed formation
    
    Args:
        formation_id: Formation ID
        user_id: User ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Certificate URL
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if formation is completed
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.formation_id == formation_id
    ).first()
    
    if not progress or progress.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Formation must be completed to generate certificate")
    
    # Check if certificate already exists
    existing_cert = db.query(Certificate).filter(
        Certificate.user_id == user_id,
        Certificate.formation_id == formation_id
    ).first()
    
    if existing_cert:
        return {"certificate_url": existing_cert.certificate_url}
    
    # Generate certificate (simplified - in production, generate PDF/image)
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    certificate_url = f"/certificates/{user_id}/{formation_id}.pdf"
    
    certificate = Certificate(
        user_id=user_id,
        formation_id=formation_id,
        certificate_url=certificate_url
    )
    
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    return {"certificate_url": certificate_url}


# ==================== GEMINI CHAT ENDPOINT ====================

@router.post("/gemini/ask")
async def ask_gemini(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question to Gemini AI with context
    
    Args:
        request: Chat request with question and context
        current_user: Authenticated user
        db: Database session
        
    Returns:
        AI response
    """
    if current_user.id != request.userId and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Build context from user's current formation progress
        context_parts = []
        
        if request.context:
            context_parts.append(request.context)
        
        # Get user's active formations and progress
        user_progress = db.query(UserProgress).filter(
            UserProgress.user_id == request.userId,
            UserProgress.status == "IN_PROGRESS"
        ).all()
        
        if user_progress:
            context_parts.append("\nFORMATIONS EN COURS:")
            for progress in user_progress:
                formation = db.query(Formation).filter(Formation.id == progress.formation_id).first()
                if formation:
                    completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
                    context_parts.append(
                        f"- {formation.title} ({formation.level.value}): "
                        f"{len(completed_lessons)} leçons complétées, "
                        f"Progression: {progress.progress_percentage:.1f}%"
                    )
        
        full_context = "\n".join(context_parts) if context_parts else "Aucun contexte spécifique."
        
        # Get AI response from Gemini service
        response = await gemini_service.generate_chat_response(
            prompt=request.question,
            context=full_context
        )
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")


# ==================== COURSE GENERATION ENDPOINT ====================

@router.post("/generate-course/{symbol}")
async def generate_course_from_market_data(
    symbol: str,
    level: Optional[str] = "INTERMEDIATE",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a course based on real market data for a symbol
    
    Args:
        symbol: Trading symbol (e.g., BTC, ETH, BTC-USD)
        level: Course level (BEGINNER, INTERMEDIATE, ADVANCED)
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Generated course data
    """
    try:
        # Normalize symbol - Binance uses symbols like BTCUSDT, ETHUSDT
        original_symbol = symbol.strip()
        clean_symbol = symbol.upper().strip()
        
        # Normalize to Binance format (BTC -> BTCUSDT, etc.)
        binance_symbol = binance_service.normalize_symbol(original_symbol)
        logger.info(f"Normalized '{original_symbol}' to Binance symbol: {binance_symbol}")
        
        # Fetch 24hr ticker data from Binance (includes price, volume, change, etc.)
        ticker_data = None
        coin_name = None
        coin_symbol = clean_symbol
        
        try:
            ticker_data = binance_service.get_24hr_ticker(binance_symbol)
            if ticker_data:
                logger.info(f"✅ Successfully fetched 24hr ticker for {binance_symbol}")
                # Extract base symbol (remove USDT, BUSD, etc.)
                base_symbol = binance_symbol.replace("USDT", "").replace("BUSD", "").replace("BTC", "")
                coin_symbol = base_symbol
                coin_name = base_symbol  # Will be improved with proper name mapping
        except Exception as e:
            logger.error(f"Error fetching 24hr ticker for {binance_symbol}: {e}")
        
        if not ticker_data:
            # Try to search for similar symbols
            logger.info(f"Direct lookup failed for {binance_symbol}, searching alternatives...")
            try:
                search_results = binance_service.search_symbols(clean_symbol, limit=5)
                if search_results:
                    logger.info(f"Found {len(search_results)} search results")
                    # Use first result (most relevant)
                    found_symbol = search_results[0]
                    binance_symbol = found_symbol["symbol"]
                    coin_symbol = found_symbol["base"]
                    coin_name = found_symbol["base"]
                    logger.info(f"Trying alternative symbol: {binance_symbol}")
                    ticker_data = binance_service.get_24hr_ticker(binance_symbol)
                    if ticker_data:
                        logger.info(f"✅ Successfully fetched data with alternative symbol: {binance_symbol}")
            except Exception as e:
                logger.error(f"Error during symbol search: {e}")
        
        if not ticker_data:
            logger.error(f"❌ Failed to fetch data for '{original_symbol}' (tried: {binance_symbol})")
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{original_symbol}' not found on Binance. Please try a valid symbol (e.g., 'BTC', 'ETH', 'BTCUSDT', 'ETHUSDT'). Common examples: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, DOT."
            )
        
        # Get coin name using the service's name mapping
        if not coin_name:
            coin_name = binance_service.get_coin_name(coin_symbol)
        
        # Prepare market data for Gemini with comprehensive information
        formatted_market_data = {
            "symbol": coin_symbol,
            "binance_symbol": binance_symbol,
            "name": coin_name,
            "current_price_usd": ticker_data.get("price", 0),
            "open_price_usd": ticker_data.get("open_price", 0),
            "prev_close_price_usd": ticker_data.get("prev_close_price", 0),
            "high_price_24h": ticker_data.get("high_price", 0),
            "low_price_24h": ticker_data.get("low_price", 0),
            "volume_24h": ticker_data.get("volume", 0),  # Base currency volume
            "quote_volume_24h": ticker_data.get("quote_volume", 0),  # Volume in USDT
            "price_change_24h": ticker_data.get("price_change", 0),
            "change_24h_percent": ticker_data.get("price_change_percent", 0),
            "bid_price": ticker_data.get("bid_price", 0),  # Best bid price
            "ask_price": ticker_data.get("ask_price", 0),  # Best ask price
            "spread": ticker_data.get("ask_price", 0) - ticker_data.get("bid_price", 0),  # Bid-ask spread
            "trade_count_24h": ticker_data.get("count", 0),
            "source": "Binance API",
            "data_url": f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}",
            "exchange": "Binance"
        }
        
        # Generate course using Gemini (with Groq fallback)
        try:
            course_data = await gemini_service.generate_course_content(
                symbol=coin_symbol,
                market_data=formatted_market_data
            )
        except ValueError as e:
            # If it's a configuration error, provide helpful message
            error_msg = str(e)
            if "not configured" in error_msg.lower() or "not available" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"{error_msg}. Veuillez configurer GEMINI_API_KEY ou GROQ_API_KEY dans le fichier .env"
                )
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate course_data before processing
        if course_data is None:
            raise HTTPException(
                status_code=500,
                detail="Course data is None - AI did not return valid course structure"
            )
        if not isinstance(course_data, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid course data type: expected dict, got {type(course_data).__name__}"
            )
        
        # Convert course data to formation format
        lessons = []
        content = course_data.get("content", {})
        if not isinstance(content, dict):
            content = {}
        sections = content.get("sections", [])
        if not isinstance(sections, list):
            sections = []
        
        for idx, section in enumerate(sections, 1):
            lessons.append({
                "id": f"L{idx}",
                "title": section.get("title", f"Section {idx}"),
                "type": section.get("type", "TEXT"),
                "data": section.get("data", ""),
                "duration": section.get("duration", 10)
            })
        
        # Calculate estimated duration
        estimated_duration = sum(lesson.get("duration", 10) for lesson in lessons)
        
        # Create formation object (don't save yet, return data for preview)
        formation_data = {
            "title": course_data.get("title", f"Cours de Trading - {coin_symbol} ({coin_name})"),
            "description": course_data.get("description", ""),
            "level": level.upper(),
            "content_json": lessons,
            "estimated_duration": estimated_duration,
            "quiz": course_data.get("quiz", {})
        }
        
        return {
            "formation": formation_data,
            "preview": True,
            "message": "Course generated successfully. Review and save to create the formation."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate course: {str(e)}")


@router.post("/generate-course/{symbol}/save")
async def save_generated_course(
    symbol: str,
    level: Optional[str] = "INTERMEDIATE",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and save a course as a formation
    
    Args:
        symbol: Trading symbol
        level: Course level
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Created formation
    """
    try:
        # Generate course first
        course_result = await generate_course_from_market_data(symbol, level, current_user, db)
        formation_data = course_result["formation"]
        
        # Validate level
        try:
            level_enum = FormationLevel(level.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
        
        # Create formation
        new_formation = Formation(
            title=formation_data["title"],
            description=formation_data["description"],
            level=level_enum,
            content_json=json.dumps(formation_data["content_json"]),
            estimated_duration=formation_data.get("estimated_duration"),
            is_active=True
        )
        
        db.add(new_formation)
        db.commit()
        db.refresh(new_formation)
        
        # Automatically assign the formation to the user who created it
        # (so they can see it in their formations list, even if they're not an admin)
        assignment = FormationAssignment(
            formation_id=new_formation.id,
            user_id=current_user.id,
            assigned_by=current_user.id
        )
        db.add(assignment)
        db.commit()
        
        content_json_parsed = json.loads(new_formation.content_json) if new_formation.content_json else []
        
        return FormationResponse(
            id=new_formation.id,
            title=new_formation.title,
            description=new_formation.description,
            level=new_formation.level.value,
            content_json=content_json_parsed,
            thumbnail_url=new_formation.thumbnail_url,
            estimated_duration=new_formation.estimated_duration,
            is_active=new_formation.is_active,
            created_at=new_formation.created_at,
            updated_at=new_formation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving generated course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save course: {str(e)}")


# ==================== YOUTUBE VIDEO FORMATION CREATION ====================

class YouTubeFormationCreate(BaseModel):
    """Request model for creating a formation with YouTube videos"""
    title: str
    description: Optional[str] = None
    level: str = "INTERMEDIATE"
    video_urls: List[str]  # List of YouTube video URLs
    video_titles: Optional[List[str]] = None  # Optional titles for each video
    user_ids: Optional[List[int]] = None  # Optional list of user IDs to assign the formation to


class FormationAssignmentRequest(BaseModel):
    """Request model for assigning a formation to users"""
    user_ids: List[int]  # List of user IDs to assign the formation to


@router.post("/create-youtube-formation", status_code=status.HTTP_201_CREATED)
async def create_youtube_formation(
    formation_data: YouTubeFormationCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a formation with YouTube videos (Admin only)
    
    Args:
        formation_data: Formation data with YouTube URLs
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Created formation
    """
    try:
        # Debug: print to see what we're receiving
        print(f"[DEBUG] Creating YouTube formation: title={formation_data.title}, user_ids={formation_data.user_ids}")
        logger.info(f"Creating YouTube formation: title={formation_data.title}, user_ids={formation_data.user_ids}")
        # Validate level
        try:
            level_enum = FormationLevel(formation_data.level.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid level: {formation_data.level}")
        
        # Validate video URLs
        if not formation_data.video_urls or len(formation_data.video_urls) == 0:
            raise HTTPException(status_code=400, detail="At least one YouTube video URL is required")
        
        # Extract YouTube video IDs from URLs
        import re
        youtube_video_ids = []
        for url in formation_data.video_urls:
            # Extract video ID from various YouTube URL formats
            video_id = None
            patterns = [
                r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
            
            if not video_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid YouTube URL: {url}. Please provide a valid YouTube video URL."
                )
            youtube_video_ids.append(video_id)
        
        # Create lessons from YouTube videos
        lessons = []
        video_titles = formation_data.video_titles or []
        
        for idx, video_id in enumerate(youtube_video_ids):
            video_title = video_titles[idx] if idx < len(video_titles) else f"Video {idx + 1}"
            youtube_embed_url = f"https://www.youtube.com/embed/{video_id}"
            
            lessons.append({
                "id": f"video_{idx + 1}",
                "title": video_title,
                "type": "VIDEO",
                "data": youtube_embed_url,  # YouTube embed URL
                "youtube_id": video_id,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": 0  # Will be estimated or fetched if needed
            })
        
        # Calculate estimated duration (default 10 min per video)
        estimated_duration = len(lessons) * 10
        
        # Create formation
        new_formation = Formation(
            title=formation_data.title,
            description=formation_data.description or f"Formation avec {len(lessons)} vidéos YouTube",
            level=level_enum,
            content_json=json.dumps(lessons),
            estimated_duration=estimated_duration,
            is_active=True
        )
        
        db.add(new_formation)
        db.commit()
        db.refresh(new_formation)
        
        # Assign formation to users if provided
        assigned_count = 0
        print(f"[DEBUG] user_ids check: user_ids={formation_data.user_ids}, type={type(formation_data.user_ids)}, len={len(formation_data.user_ids) if formation_data.user_ids else 0}")
        if formation_data.user_ids and len(formation_data.user_ids) > 0:
            print(f"[DEBUG] Assigning formation {new_formation.id} to {len(formation_data.user_ids)} user(s): {formation_data.user_ids}")
            logger.info(f"Assigning formation {new_formation.id} to {len(formation_data.user_ids)} user(s)")
            for user_id in formation_data.user_ids:
                # Check if user exists
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # Check if assignment already exists
                    existing = db.query(FormationAssignment).filter(
                        FormationAssignment.formation_id == new_formation.id,
                        FormationAssignment.user_id == user_id
                    ).first()
                    if not existing:
                        assignment = FormationAssignment(
                            formation_id=new_formation.id,
                            user_id=user_id,
                            assigned_by=current_user.id
                        )
                        db.add(assignment)
                        assigned_count += 1
                        logger.info(f"Assigned formation {new_formation.id} to user {user_id}")
                    else:
                        logger.warning(f"Assignment already exists for formation {new_formation.id} and user {user_id}")
                else:
                    logger.warning(f"User {user_id} not found when assigning formation {new_formation.id}")
            db.commit()
            print(f"[DEBUG] Successfully assigned formation {new_formation.id} to {assigned_count} user(s)")
            logger.info(f"Successfully assigned formation {new_formation.id} to {assigned_count} user(s)")
        else:
            print(f"[DEBUG] No user_ids provided for formation {new_formation.id}, skipping assignment")
            logger.info(f"No user_ids provided for formation {new_formation.id}, skipping assignment")
        
        content_json_parsed = json.loads(new_formation.content_json) if new_formation.content_json else []
        
        logger.info(f"Successfully created YouTube formation {new_formation.id} with {len(lessons)} videos")
        
        return {
            "formation": FormationResponse(
                id=new_formation.id,
                title=new_formation.title,
                description=new_formation.description,
                level=new_formation.level.value,
                content_json=content_json_parsed,
                thumbnail_url=new_formation.thumbnail_url,
                estimated_duration=new_formation.estimated_duration,
                is_active=new_formation.is_active,
                created_at=new_formation.created_at,
                updated_at=new_formation.updated_at
            ),
            "videos_count": len(lessons),
            "message": f"Formation créée avec succès avec {len(lessons)} vidéos YouTube"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating YouTube formation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create formation: {str(e)}")


# ==================== FORMATION ASSIGNMENT ENDPOINTS ====================

@router.post("/{formation_id}/assign", status_code=status.HTTP_200_OK)
async def assign_formation_to_users(
    formation_id: int,
    assignment_data: FormationAssignmentRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Assign a formation to specific users (Admin only)
    
    Args:
        formation_id: ID of the formation to assign
        assignment_data: List of user IDs to assign the formation to
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Success message with assigned user count
    """
    # Check if formation exists
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    assigned_count = 0
    for user_id in assignment_data.user_ids:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue
        
        # Check if assignment already exists
        existing = db.query(FormationAssignment).filter(
            FormationAssignment.formation_id == formation_id,
            FormationAssignment.user_id == user_id
        ).first()
        
        if not existing:
            assignment = FormationAssignment(
                formation_id=formation_id,
                user_id=user_id,
                assigned_by=current_user.id
            )
            db.add(assignment)
            assigned_count += 1
    
    db.commit()
    
    return {
        "message": f"Formation assigned to {assigned_count} user(s)",
        "assigned_count": assigned_count,
        "formation_id": formation_id
    }


@router.delete("/{formation_id}/assign/{user_id}", status_code=status.HTTP_200_OK)
async def unassign_formation_from_user(
    formation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Unassign a formation from a specific user (Admin only)
    
    Args:
        formation_id: ID of the formation
        user_id: ID of the user to unassign
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Success message
    """
    assignment = db.query(FormationAssignment).filter(
        FormationAssignment.formation_id == formation_id,
        FormationAssignment.user_id == user_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Formation unassigned successfully"}


@router.get("/{formation_id}/assigned-users")
async def get_assigned_users(
    formation_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of users assigned to a formation (Admin only)
    
    Args:
        formation_id: ID of the formation
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        List of assigned users
    """
    # Check if formation exists
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    assignments = db.query(FormationAssignment).filter(
        FormationAssignment.formation_id == formation_id
    ).all()
    
    users = []
    for assignment in assignments:
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if user:
            users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "assigned_at": assignment.assigned_at
            })
    
    return {
        "formation_id": formation_id,
        "formation_title": formation.title,
        "users": users,
        "count": len(users)
    }


# ==================== PDF UPLOAD AND PROCESSING (DEPRECATED) ====================

@router.post("/upload-pdf", status_code=status.HTTP_201_CREATED)
async def upload_pdf_formation(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    level: Optional[str] = "INTERMEDIATE",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF training file and automatically:
    1. Extract text from PDF
    2. Split into logical modules
    3. Generate videos for each module
    4. Create quizzes for each module
    5. Generate final exam
    6. Create formation with all content
    
    Args:
        file: PDF file upload
        title: Optional title (will extract from PDF if not provided)
        description: Optional description
        level: Course level (BEGINNER, INTERMEDIATE, ADVANCED)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created formation with modules, quizzes, and exam
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read PDF file
        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        
        # Step 1: Extract text from PDF
        logger.info("Extracting text from PDF...")
        pdf_text = pdf_service.extract_text_from_pdf(pdf_bytes)
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Could not extract meaningful text from PDF")
        
        # Get PDF metadata
        metadata = pdf_service.get_pdf_metadata(pdf_bytes)
        if not title:
            title = metadata.get("title") or file.filename.replace('.pdf', '')
        
        # Step 2: Split into modules
        logger.info("Splitting PDF into modules...")
        modules_data = await module_splitter_service.split_into_modules(
            pdf_text=pdf_text,
            title=title,
            target_modules=5
        )
        
        # Step 3: Create formation
        try:
            level_enum = FormationLevel(level.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
        
        new_formation = Formation(
            title=title,
            description=description or f"Formation générée automatiquement à partir du PDF: {file.filename}",
            level=level_enum,
            content_json=json.dumps([]),  # Will be populated with lessons
            estimated_duration=len(modules_data) * 15,  # Estimate 15 min per module
            is_active=True
        )
        
        db.add(new_formation)
        db.flush()  # Get formation ID
        
        # Step 4: Create modules and generate videos
        logger.info(f"Creating {len(modules_data)} modules and generating videos...")
        created_modules = []
        
        for module_data in modules_data:
            # Create module
            module = Module(
                formation_id=new_formation.id,
                module_number=module_data["module_number"],
                title=module_data["title"],
                content=module_data["content"]
            )
            db.add(module)
            db.flush()  # Get module ID
            
            # Generate video (async, may take time)
            try:
                video_result = await video_generation_service.generate_video_from_text(
                    text=module_data["content"],
                    title=module_data["title"],
                    formation_id=new_formation.id,
                    module_id=module.id,
                    language="fr"
                )
                
                if video_result.get("video_url"):
                    module.video_url = video_result["video_url"]
                    module.video_duration = video_result.get("duration", 0)
            except Exception as e:
                logger.warning(f"Video generation failed for module {module.id}: {e}")
                # Continue without video
            
            created_modules.append(module)
        
        # Step 5: Generate quizzes for each module
        logger.info("Generating quizzes for modules...")
        for module in created_modules:
            try:
                quiz_data = await quiz_generation_service.generate_quiz_for_module(
                    module_content=module.content,
                    module_title=module.title,
                    num_questions=5
                )
                
                quiz = Quiz(
                    module_id=module.id,
                    questions_json=json.dumps(quiz_data["questions"]),
                    passing_score=quiz_data["passing_score"]
                )
                db.add(quiz)
            except Exception as e:
                logger.warning(f"Quiz generation failed for module {module.id}: {e}")
        
        # Step 6: Generate final exam
        logger.info("Generating final exam...")
        try:
            all_modules_content = [
                {"title": m.title, "content": m.content}
                for m in created_modules
            ]
            
            exam_data = await quiz_generation_service.generate_final_exam(
                all_modules_content=all_modules_content,
                formation_title=title,
                num_questions=20
            )
            
            exam = Exam(
                formation_id=new_formation.id,
                questions_json=json.dumps(exam_data["questions"]),
                passing_score=exam_data["passing_score"]
            )
            db.add(exam)
        except Exception as e:
            logger.warning(f"Exam generation failed: {e}")
        
        # Update formation content_json with module lessons
        lessons = []
        for module in created_modules:
            lessons.append({
                "id": f"module_{module.id}",
                "title": module.title,
                "type": "VIDEO" if module.video_url else "TEXT",
                "data": module.video_url or module.content[:500],  # Use video URL or content preview
                "duration": module.video_duration or 900  # Default 15 min
            })
        
        new_formation.content_json = json.dumps(lessons)
        
        # Commit all changes
        db.commit()
        db.refresh(new_formation)
        
        logger.info(f"Successfully created formation {new_formation.id} with {len(created_modules)} modules")
        
        # Return formation with modules
        content_json_parsed = json.loads(new_formation.content_json) if new_formation.content_json else []
        
        return {
            "formation": FormationResponse(
                id=new_formation.id,
                title=new_formation.title,
                description=new_formation.description,
                level=new_formation.level.value,
                content_json=content_json_parsed,
                thumbnail_url=new_formation.thumbnail_url,
                estimated_duration=new_formation.estimated_duration,
                is_active=new_formation.is_active,
                created_at=new_formation.created_at,
                updated_at=new_formation.updated_at
            ),
            "modules_count": len(created_modules),
            "message": f"Formation created successfully with {len(created_modules)} modules, quizzes, and final exam"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


# ==================== QUIZ ENDPOINTS ====================

@router.get("/{formation_id}/modules/{module_id}/quiz")
async def get_module_quiz(
    formation_id: int,
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz for a module"""
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.formation_id == formation_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    quiz = db.query(Quiz).filter(Quiz.module_id == module_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")
    
    questions = json.loads(quiz.questions_json) if quiz.questions_json else []
    
    return {
        "quiz_id": quiz.id,
        "module_id": module_id,
        "questions": questions,
        "passing_score": quiz.passing_score
    }


@router.post("/{formation_id}/modules/{module_id}/quiz/submit")
async def submit_quiz(
    formation_id: int,
    module_id: int,
    answers: dict,  # {question_id: answer}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get score"""
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.formation_id == formation_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    quiz = db.query(Quiz).filter(Quiz.module_id == module_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = json.loads(quiz.questions_json) if quiz.questions_json else []
    
    # Calculate score
    correct = 0
    total = len(questions)
    
    for question in questions:
        q_id = question.get("id")
        user_answer = answers.get(q_id)
        correct_answer = question.get("correct_answer")
        
        if user_answer == correct_answer:
            correct += 1
    
    score = (correct / total * 100) if total > 0 else 0
    passed = score >= quiz.passing_score
    
    # Save attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        answers_json=json.dumps(answers),
        score=score,
        passed=passed
    )
    db.add(attempt)
    
    # Update progress if quiz passed
    if passed:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.formation_id == formation_id
        ).first()
        
        if not progress:
            # Create new progress entry
            progress = UserProgress(
                user_id=current_user.id,
                formation_id=formation_id,
                completed_lessons=json.dumps([]),
                status="IN_PROGRESS",
                progress_percentage=0.0
            )
            db.add(progress)
        
        # Mark module as completed in progress
        completed_lessons = json.loads(progress.completed_lessons) if progress.completed_lessons else []
        module_lesson_id = f"module_{module_id}"
        if module_lesson_id not in completed_lessons:
            completed_lessons.append(module_lesson_id)
            progress.completed_lessons = json.dumps(completed_lessons)
            
            # Calculate progress percentage
            formation = db.query(Formation).filter(Formation.id == formation_id).first()
            if formation:
                total_modules = db.query(Module).filter(Module.formation_id == formation_id).count()
                if total_modules > 0:
                    progress.progress_percentage = (len(completed_lessons) / total_modules) * 100
                    progress.current_lesson_id = module_lesson_id
    
    db.commit()
    
    return {
        "score": score,
        "passed": passed,
        "correct": correct,
        "total": total,
        "passing_score": quiz.passing_score,
        "attempt_id": attempt.id,
        "progress_updated": passed
    }


# ==================== EXAM ENDPOINTS ====================

@router.get("/{formation_id}/exam")
async def get_final_exam(
    formation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get final exam for a formation"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    exam = db.query(Exam).filter(Exam.formation_id == formation_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found for this formation")
    
    questions = json.loads(exam.questions_json) if exam.questions_json else []
    
    return {
        "exam_id": exam.id,
        "formation_id": formation_id,
        "questions": questions,
        "passing_score": exam.passing_score
    }


@router.post("/{formation_id}/exam/submit")
async def submit_exam(
    formation_id: int,
    answers: dict,  # {question_id: answer}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit exam answers and get score"""
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    exam = db.query(Exam).filter(Exam.formation_id == formation_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    questions = json.loads(exam.questions_json) if exam.questions_json else []
    
    # Calculate score
    correct = 0
    total = len(questions)
    
    for question in questions:
        q_id = question.get("id")
        user_answer = answers.get(q_id)
        correct_answer = question.get("correct_answer")
        
        if user_answer == correct_answer:
            correct += 1
    
    score = (correct / total * 100) if total > 0 else 0
    passed = score >= exam.passing_score
    
    # Save attempt
    attempt = ExamAttempt(
        user_id=current_user.id,
        exam_id=exam.id,
        answers_json=json.dumps(answers),
        score=score,
        passed=passed
    )
    db.add(attempt)
    
    # If passed, update progress and generate certificate
    if passed:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.formation_id == formation_id
        ).first()
        
        if progress:
            progress.status = "COMPLETED"
            progress.completed_at = datetime.now()
            progress.progress_percentage = 100.0
        
        # Generate certificate
        try:
            cert_result = certificate_service.generate_certificate(
                user_name=current_user.full_name or current_user.username,
                formation_title=formation.title,
                completion_date=datetime.now(),
                user_id=current_user.id,
                formation_id=formation_id,
                score=score
            )
            
            # Save certificate
            certificate = Certificate(
                user_id=current_user.id,
                formation_id=formation_id,
                certificate_url=cert_result["certificate_url"]
            )
            db.add(certificate)
        except Exception as e:
            logger.warning(f"Certificate generation failed: {e}")
    
    db.commit()
    
    return {
        "score": score,
        "passed": passed,
        "correct": correct,
        "total": total,
        "passing_score": exam.passing_score,
        "attempt_id": attempt.id,
        "certificate_generated": passed
    }


# ==================== CERTIFICATE ENDPOINTS ====================

@router.get("/{formation_id}/certificate/{user_id}")
async def get_certificate(
    formation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get certificate for a completed formation"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    certificate = db.query(Certificate).filter(
        Certificate.user_id == user_id,
        Certificate.formation_id == formation_id
    ).first()
    
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {
        "certificate_url": certificate.certificate_url,
        "issued_at": certificate.issued_at
    }


@router.get("/certificates/{user_id}")
async def get_user_certificates(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for a user"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    certificates = db.query(Certificate).filter(
        Certificate.user_id == user_id
    ).order_by(Certificate.issued_at.desc()).all()
    
    result = []
    for cert in certificates:
        formation = db.query(Formation).filter(Formation.id == cert.formation_id).first()
        result.append({
            "id": cert.id,
            "formation_id": cert.formation_id,
            "formation_title": formation.title if formation else "Unknown",
            "certificate_url": cert.certificate_url,
            "issued_at": cert.issued_at
        })
    
    return {"certificates": result}


@router.get("/{formation_id}/modules/{module_id}")
async def get_module_details(
    formation_id: int,
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed module information including video and quiz"""
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.formation_id == formation_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get quiz if exists
    quiz = db.query(Quiz).filter(Quiz.module_id == module_id).first()
    quiz_data = None
    if quiz:
        questions = json.loads(quiz.questions_json) if quiz.questions_json else []
        # Check if user has attempted this quiz
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz.id
        ).order_by(QuizAttempt.completed_at.desc()).first()
        
        quiz_data = {
            "quiz_id": quiz.id,
            "questions_count": len(questions),
            "passing_score": quiz.passing_score,
            "has_attempted": attempt is not None,
            "best_score": attempt.score if attempt else None,
            "passed": attempt.passed if attempt else False
        }
    
    return {
        "id": module.id,
        "formation_id": formation_id,
        "module_number": module.module_number,
        "title": module.title,
        "content": module.content,
        "video_url": module.video_url,
        "video_duration": module.video_duration,
        "quiz": quiz_data,
        "created_at": module.created_at
    }


@router.get("/{formation_id}/progress/{user_id}/detailed")
async def get_detailed_progress(
    formation_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed progress with module and quiz completion status"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise HTTPException(status_code=404, detail="Formation not found")
    
    # Get progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.formation_id == formation_id
    ).first()
    
    # Get all modules
    modules = db.query(Module).filter(
        Module.formation_id == formation_id
    ).order_by(Module.module_number).all()
    
    # Get all quizzes
    module_ids = [m.id for m in modules]
    quizzes = db.query(Quiz).filter(Quiz.module_id.in_(module_ids)).all() if module_ids else []
    quiz_map = {q.module_id: q for q in quizzes}
    
    # Get user's quiz attempts
    quiz_attempts = {}
    if module_ids:
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.quiz_id.in_([q.id for q in quizzes])
        ).all()
        for attempt in attempts:
            quiz_attempts[attempt.quiz_id] = attempt
    
    # Build module details
    completed_lessons = json.loads(progress.completed_lessons) if progress and progress.completed_lessons else []
    modules_detail = []
    
    for module in modules:
        module_lesson_id = f"module_{module.id}"
        is_completed = module_lesson_id in completed_lessons
        
        quiz_info = None
        if module.id in quiz_map:
            quiz = quiz_map[module.id]
            attempt = quiz_attempts.get(quiz.id)
            quiz_info = {
                "quiz_id": quiz.id,
                "has_quiz": True,
                "has_attempted": attempt is not None,
                "passed": attempt.passed if attempt else False,
                "score": attempt.score if attempt else None,
                "passing_score": quiz.passing_score
            }
        else:
            quiz_info = {"has_quiz": False}
        
        modules_detail.append({
            "id": module.id,
            "module_number": module.module_number,
            "title": module.title,
            "video_url": module.video_url,
            "video_duration": module.video_duration,
            "is_completed": is_completed,
            "quiz": quiz_info
        })
    
    # Check if exam exists and user's attempt
    exam = db.query(Exam).filter(Exam.formation_id == formation_id).first()
    exam_info = None
    if exam:
        exam_attempt = db.query(ExamAttempt).filter(
            ExamAttempt.user_id == user_id,
            ExamAttempt.exam_id == exam.id
        ).order_by(ExamAttempt.completed_at.desc()).first()
        
        exam_info = {
            "exam_id": exam.id,
            "has_attempted": exam_attempt is not None,
            "passed": exam_attempt.passed if exam_attempt else False,
            "score": exam_attempt.score if exam_attempt else None,
            "passing_score": exam.passing_score
        }
    
    # Check certificate
    certificate = db.query(Certificate).filter(
        Certificate.user_id == user_id,
        Certificate.formation_id == formation_id
    ).first()
    
    return {
        "formation_id": formation_id,
        "formation_title": formation.title,
        "user_id": user_id,
        "status": progress.status if progress else "NOT_STARTED",
        "progress_percentage": progress.progress_percentage if progress else 0.0,
        "started_at": progress.started_at if progress else None,
        "completed_at": progress.completed_at if progress else None,
        "modules": modules_detail,
        "total_modules": len(modules),
        "completed_modules": len([m for m in modules_detail if m["is_completed"]]),
        "exam": exam_info,
        "has_certificate": certificate is not None,
        "certificate_url": certificate.certificate_url if certificate else None
    }

