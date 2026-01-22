"""
AI Assistant Router
Endpoints for AI-powered trading assistant chatbot
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import User, Wallet, ChatMessage
from utils.auth import get_current_user
from services.ai_assistant_service import ai_assistant_service

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    content: str


class ChatMessageOut(BaseModel):
    """Chat message output"""
    role: str
    content: str
    timestamp: datetime


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    message: ChatMessageOut


class ChatMessageResponse(BaseModel):
    """Model for individual chat messages"""
    id: int
    role: str
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI assistant and get a response
    
    Args:
        request: Chat request with user message
        current_user: Authenticated user
        db: Database session
        
    Returns:
        AI assistant's response
    """
    try:
        # Get user's wallet data for context
        wallets = db.query(Wallet).filter(Wallet.user_id == current_user.id).all()
        wallet_data = [
            {
                "currency": w.currency,
                "available_balance": str(w.available_balance),
                "locked_balance": str(w.locked_balance)
            }
            for w in wallets
        ]
        
        # Get conversation history
        history_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(history_messages)
        ]
        
        # Prepare user data
        user_data = {
            "username": current_user.username,
            "wallets": wallet_data
        }
        
        # Get AI response
        ai_response = await ai_assistant_service.get_response(
            user_message=request.content,
            conversation_history=conversation_history,
            user_data=user_data
        )
        
        # Save user message to database
        user_message = ChatMessage(
            user_id=current_user.id,
            role="user",
            content=request.content
        )
        db.add(user_message)
        
        # Save AI response to database
        assistant_message = ChatMessage(
            user_id=current_user.id,
            role="assistant",
            content=ai_response
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatResponse(
            message=ChatMessageOut(
                role="assistant",
                content=ai_response,
                timestamp=assistant_message.timestamp
            )
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")


@router.get("/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for the current user
    
    Args:
        limit: Maximum number of messages to return
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of chat messages
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()
    
    return messages


@router.delete("/chat/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear chat history for the current user
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).delete()
        db.commit()
        
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")


@router.get("/suggestions/{suggestion_type}")
async def get_quick_suggestion(
    suggestion_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quick AI suggestions
    
    Args:
        suggestion_type: Type of suggestion (market_analysis, trading_tip, risk_assessment)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        AI suggestion
    """
    if suggestion_type not in ["market_analysis", "trading_tip", "risk_assessment"]:
        raise HTTPException(status_code=400, detail="Invalid suggestion type")
    
    try:
        # Get user's wallet data
        wallets = db.query(Wallet).filter(Wallet.user_id == current_user.id).all()
        wallet_data = [
            {
                "currency": w.currency,
                "available_balance": str(w.available_balance),
                "locked_balance": str(w.locked_balance)
            }
            for w in wallets
        ]
        
        user_data = {
            "username": current_user.username,
            "wallets": wallet_data
        }
        
        suggestion = await ai_assistant_service.get_quick_suggestion(suggestion_type, user_data)
        
        return {"suggestion": suggestion}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")
