"""
Pydantic Schemas - Request/Response Models
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============= User Schemas =============
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    reputation_score: Optional[int] = None  # Added for forum reputation display
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class FaceRegisterRequest(BaseModel):
    """Request model for face registration (image sent as base64 or multipart)"""
    pass  # Image will be sent as multipart/form-data UploadFile


class FaceRegisterResponse(BaseModel):
    """Response model for face registration"""
    message: str
    success: bool


class FaceLoginRequest(BaseModel):
    """Request model for face login - username + image"""
    username: str = Field(..., min_length=3, max_length=50)


class FaceLoginResponse(BaseModel):
    """Response model for face login - returns token if successful"""
    access_token: str
    token_type: str
    user_id: int
    username: str
    success: bool


class SuspiciousEventResponse(BaseModel):
    id: int
    transaction_id: int
    transaction_type: str
    user_id: int
    counterparty_id: Optional[int]
    score: float
    rules_triggered: Optional[List[str]] = None
    features_snapshot: Optional[Dict[str, Any]] = None
    explanation: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SuspiciousEventListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    events: List[SuspiciousEventResponse]


class SuspiciousEventUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None


# ============= Wallet Schemas =============
class WalletResponse(BaseModel):
    id: int
    user_id: int
    currency: str
    available_balance: Decimal
    locked_balance: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: int
    wallet_id: int
    type: str
    amount: Decimal
    currency: str
    status: str
    reference_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    recipient_username: str
    currency: str
    amount: float = Field(..., gt=0)


class WalletBalanceUpdate(BaseModel):
    currency: str
    amount: float


class DepositRequest(BaseModel):
    currency: str
    amount: float = Field(..., gt=0)


class WithdrawRequest(BaseModel):
    currency: str
    amount: float = Field(..., gt=0)
    address: Optional[str] = None  # Optional withdrawal address for virtual game


# ============= Order Book Schemas =============
class OrderCreate(BaseModel):
    instrument: str  # BTC/USD, ETH/USD
    order_type: str  # BUY or SELL
    order_subtype: str = "LIMIT"  # MARKET or LIMIT
    price: Optional[float] = None
    quantity: float = Field(..., gt=0)
    take_profit_price: Optional[float] = None  # Price to trigger take profit (optional)
    stop_loss_price: Optional[float] = None  # Price to trigger stop loss (optional)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    instrument: str
    order_type: str
    order_subtype: str
    price: Optional[Decimal]
    quantity: Decimal
    remaining_quantity: Decimal
    status: str
    created_at: datetime
    take_profit_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    entry_price: Optional[Decimal] = None
    parent_order_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class OrderBookSnapshot(BaseModel):
    instrument: str
    bids: List[dict]  # [{price, quantity, count}]
    asks: List[dict]  # [{price, quantity, count}]
    last_price: Optional[Decimal] = None
    timestamp: datetime


class TradeResponse(BaseModel):
    id: int
    order_id: int
    buyer_id: int
    seller_id: int
    instrument: str
    price: Decimal
    quantity: Decimal
    total_amount: Decimal
    fee: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= P2P Schemas =============
class P2PAdCreate(BaseModel):
    ad_type: str  # BUY or SELL
    currency: str  # BTC, ETH, USDT
    fiat_currency: str = "USD"
    price: float = Field(..., gt=0)
    min_limit: float = Field(..., gt=0)
    max_limit: float = Field(..., gt=0)
    available_amount: float = Field(..., gt=0)
    payment_methods: List[str]
    payment_time_limit: int = 30
    terms_conditions: Optional[str] = None
    
    @validator('max_limit')
    def validate_limits(cls, v, values):
        if 'min_limit' in values and v < values['min_limit']:
            raise ValueError('max_limit must be greater than min_limit')
        return v


class P2PAdResponse(BaseModel):
    id: int
    user_id: int
    ad_type: str
    currency: str
    fiat_currency: str
    price: Decimal
    min_limit: Decimal
    max_limit: Decimal
    available_amount: Decimal
    payment_methods: str
    payment_time_limit: int
    terms_conditions: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class P2PTradeCreate(BaseModel):
    advertisement_id: int
    amount: float = Field(..., gt=0, description="Amount in fiat currency (USD, EUR, etc.)")
    payment_method: str


class P2PTradeResponse(BaseModel):
    id: int
    advertisement_id: int
    buyer_id: int
    seller_id: int
    amount: Decimal
    price: Decimal
    total_fiat: Decimal
    currency: str
    fiat_currency: str
    status: str
    payment_method: Optional[str]
    created_at: datetime
    payment_deadline: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= Dispute Schemas =============
class DisputeCreate(BaseModel):
    trade_id: int
    reason: str
    evidence: Optional[List[str]] = None  # List of evidence URLs/descriptions


class DisputeResponse(BaseModel):
    id: int
    trade_id: int
    filed_by: int
    filed_by_username: Optional[str] = None
    reason: str
    evidence: Optional[str]
    status: str
    resolution: Optional[str]
    resolved_by: Optional[int]
    resolved_by_username: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime]
    # Trade details
    trade_amount: Optional[float] = None
    trade_currency: Optional[str] = None
    buyer_id: Optional[int] = None
    buyer_username: Optional[str] = None
    seller_id: Optional[int] = None
    seller_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class DisputeListResponse(BaseModel):
    total: int
    disputes: List[DisputeResponse]


class DisputeAddEvidence(BaseModel):
    evidence: str  # Evidence content/description


class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None


class DisputeResolve(BaseModel):
    resolution: str  # Admin's resolution explanation
    refund_to_buyer: bool = False
    release_to_seller: bool = False


# ============= Reputation Schemas =============
class ReputationResponse(BaseModel):
    id: int
    user_id: int
    score: int
    total_trades: int
    completed_trades: int
    disputed_trades: int
    completion_rate: float
    average_response_time: float
    average_rating: float
    review_count: int
    badges: List[str] = []
    
    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    trade_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    trade_id: int
    reviewer_id: int
    reviewed_user_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PublicUserProfile(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]


class ReputationProfileResponse(BaseModel):
    user: PublicUserProfile
    reputation: ReputationResponse
    recent_reviews: List[ReviewResponse]


class ReviewedTradesResponse(BaseModel):
    trade_ids: List[int]


# ============= WebSocket Messages =============
class WSMessage(BaseModel):
    type: str  # order_update, balance_update, trade_executed, etc.
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============= Trading Schemas =============
class OHLCVData(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class TradingHistoryResponse(BaseModel):
    symbol: str
    timeframe: str
    data: List[OHLCVData]


# ============= Simulator Schemas =============
class SimulatorResultCreate(BaseModel):
    pair: str
    start_date: datetime
    end_date: datetime
    entry_price: float
    stop_loss: float
    take_profit: float


class SimulatorResultResponse(BaseModel):
    id: int
    user_id: int
    username: str
    pair: str
    start_date: datetime
    end_date: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    exit_price: float
    pnl_percent: float
    is_win: bool
    hit_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SimulatorCalculation(BaseModel):
    """Response for simulation calculation before saving"""
    exit_price: float
    pnl_percent: float
    is_win: bool
    hit_type: str  # "TP", "SL", or "END"
    message: str


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    pair: str
    pnl_percent: float
    is_win: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_count: int


# ============= Forum Schemas =============

class VoteType(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


# Category Schemas
class ForumCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    min_reputation_required: int = Field(default=0, ge=0)
    read_only_for_lower_levels: bool = False
    parent_category_id: Optional[int] = None
    sort_order: int = 0


class ForumCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    min_reputation_required: Optional[int] = Field(None, ge=0)
    read_only_for_lower_levels: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ForumCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    min_reputation_required: int
    read_only_for_lower_levels: bool
    parent_category_id: Optional[int]
    sort_order: int
    is_active: bool
    post_count: Optional[int] = None  # Number of posts in this category
    created_at: datetime
    
    class Config:
        from_attributes = True


# Post Schemas
class ForumPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category_id: int
    tags: Optional[List[str]] = None


class ForumPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None


class AuthorInfo(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str]
    reputation_score: Optional[int] = None
    reputation_level: Optional[str] = None  # "normal", "pro", "expert"
    
    class Config:
        from_attributes = True


class ForumPostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: AuthorInfo
    category_id: int
    category_name: Optional[str] = None
    tags: Optional[List[str]] = None
    upvotes: int
    downvotes: int
    view_count: int
    comment_count: int
    is_pinned: bool
    is_locked: bool
    user_vote: Optional[str] = None  # "UP", "DOWN", or None
    last_activity_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ForumPostListResponse(BaseModel):
    posts: List[ForumPostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Comment Schemas
class ForumCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[int] = None


class ForumCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


class ForumCommentResponse(BaseModel):
    id: int
    post_id: int
    author: AuthorInfo
    content: str
    parent_comment_id: Optional[int]
    upvotes: int
    downvotes: int
    is_solution: bool
    user_vote: Optional[str] = None  # "UP", "DOWN", or None
    reply_count: Optional[int] = 0
    replies: Optional[List["ForumCommentResponse"]] = []
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Fix forward reference
ForumCommentResponse.model_rebuild()


# Vote Schema
class ForumVoteCreate(BaseModel):
    vote_type: VoteType


class ForumVoteResponse(BaseModel):
    id: int
    user_id: int
    post_id: Optional[int]
    comment_id: Optional[int]
    vote_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Post with Comments
class ForumPostDetailResponse(ForumPostResponse):
    comments: List[ForumCommentResponse] = []
