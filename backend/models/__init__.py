"""
Database Models - Complete Trading Platform Schema
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, DECIMAL, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

# Import additional models
from .simulator_result import SimulatorResult


# Enums
class OrderType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class OrderBookOrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class P2PTradeStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAYMENT_SENT = "PAYMENT_SENT"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"


class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class SuspiciousEventStatus(str, enum.Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class SuspiciousTransactionType(str, enum.Enum):
    ORDERBOOK_TRADE = "ORDERBOOK_TRADE"
    P2P_TRADE = "P2P_TRADE"
    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRADE = "TRADE"
    P2P_BUY = "P2P_BUY"
    P2P_SELL = "P2P_SELL"
    TRANSFER = "TRANSFER"
    FEE = "FEE"
    ESCROW_LOCK = "ESCROW_LOCK"
    ESCROW_RELEASE = "ESCROW_RELEASE"


# Suspicious Event Model
class SuspiciousEvent(Base):
    __tablename__ = "suspicious_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    counterparty_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    transaction_id = Column(Integer, nullable=False)
    transaction_type = Column(SQLEnum(SuspiciousTransactionType), nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    rules_triggered = Column(Text)  # JSON array of triggered rule names
    features_snapshot = Column(Text)  # JSON snapshot of engineered features
    explanation = Column(Text)
    status = Column(SQLEnum(SuspiciousEventStatus), default=SuspiciousEventStatus.OPEN)
    admin_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    counterparty = relationship("User", foreign_keys=[counterparty_id])

    __table_args__ = (
        Index('idx_susp_user_id', 'user_id'),
        Index('idx_susp_score_status', 'score', 'status'),
        Index('idx_susp_transaction', 'transaction_id', 'transaction_type', unique=True),
    )


# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    face_embedding = Column(Text)  # JSON array of face encoding (128 floats for deepface)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)  # Admin flag for admin dashboard access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("OrderBookOrder", back_populates="user", cascade="all, delete-orphan")
    p2p_ads = relationship("P2PAdvertisement", back_populates="user", cascade="all, delete-orphan")
    buyer_trades = relationship("P2PTrade", foreign_keys="P2PTrade.buyer_id", back_populates="buyer")
    seller_trades = relationship("P2PTrade", foreign_keys="P2PTrade.seller_id", back_populates="seller")
    reputation = relationship("Reputation", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reviews_given = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_received = relationship("Review", foreign_keys="Review.reviewed_user_id", back_populates="reviewed_user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    forum_posts = relationship("ForumPost", back_populates="author", cascade="all, delete-orphan")
    forum_comments = relationship("ForumComment", back_populates="author", cascade="all, delete-orphan")
    forum_votes = relationship("ForumVote", back_populates="user", cascade="all, delete-orphan")
    formation_progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")
    assigned_formations = relationship("FormationAssignment", foreign_keys="FormationAssignment.user_id", back_populates="user", cascade="all, delete-orphan")


# Wallet Model
class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String(10), nullable=False)  # USD, BTC, ETH, USDT
    available_balance = Column(DECIMAL(20, 8), default=0.0, nullable=False)
    locked_balance = Column(DECIMAL(20, 8), default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_currency', 'user_id', 'currency', unique=True),
    )


# Transaction Model
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), default="COMPLETED")
    reference_id = Column(String(100))  # Order ID, Trade ID, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_wallet_type', 'wallet_id', 'type'),
        Index('idx_created_at', 'created_at'),
    )


# Order Book Order Model
class OrderBookOrder(Base):
    __tablename__ = "orderbook_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument = Column(String(20), nullable=False, index=True)  # BTC/USD, ETH/USD, etc.
    order_type = Column(SQLEnum(OrderType), nullable=False)
    order_subtype = Column(SQLEnum(OrderBookOrderType), default=OrderBookOrderType.LIMIT)
    price = Column(DECIMAL(20, 8))  # NULL for market orders
    quantity = Column(DECIMAL(20, 8), nullable=False)
    remaining_quantity = Column(DECIMAL(20, 8), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Take Profit / Stop Loss fields
    parent_order_id = Column(Integer, ForeignKey("orderbook_orders.id"), nullable=True)  # For TP/SL orders linked to parent
    take_profit_price = Column(DECIMAL(20, 8), nullable=True)  # Price to trigger take profit order
    stop_loss_price = Column(DECIMAL(20, 8), nullable=True)  # Price to trigger stop loss order
    entry_price = Column(DECIMAL(20, 8), nullable=True)  # Entry price for TP/SL calculation (for filled orders)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")
    parent_order = relationship("OrderBookOrder", remote_side=[id], backref="conditional_orders")
    
    # Indexes
    __table_args__ = (
        Index('idx_instrument_status', 'instrument', 'status'),
        Index('idx_order_type_price', 'order_type', 'price'),
        Index('idx_created_at_order', 'created_at'),
        Index('idx_parent_order', 'parent_order_id'),
        Index('idx_tp_sl_active', 'instrument', 'status', 'take_profit_price', 'stop_loss_price'),
    )


# Trade Execution Model
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orderbook_orders.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument = Column(String(20), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    total_amount = Column(DECIMAL(20, 8), nullable=False)
    fee = Column(DECIMAL(20, 8), default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("OrderBookOrder", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('idx_buyer_seller', 'buyer_id', 'seller_id'),
        Index('idx_instrument_trade', 'instrument'),
    )


# P2P Advertisement Model
class P2PAdvertisement(Base):
    __tablename__ = "p2p_advertisements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ad_type = Column(SQLEnum(OrderType), nullable=False)  # BUY or SELL
    currency = Column(String(10), nullable=False)  # BTC, ETH, USDT
    fiat_currency = Column(String(10), default="USD")
    price = Column(DECIMAL(20, 8), nullable=False)
    min_limit = Column(DECIMAL(20, 8), nullable=False)
    max_limit = Column(DECIMAL(20, 8), nullable=False)
    available_amount = Column(DECIMAL(20, 8), nullable=False)
    payment_methods = Column(Text)  # JSON string array
    payment_time_limit = Column(Integer, default=30)  # minutes
    terms_conditions = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="p2p_ads")
    trades = relationship("P2PTrade", back_populates="advertisement", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_currency_type', 'currency', 'ad_type'),
        Index('idx_is_active', 'is_active'),
    )


# P2P Trade Model
class P2PTrade(Base):
    __tablename__ = "p2p_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    advertisement_id = Column(Integer, ForeignKey("p2p_advertisements.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    total_fiat = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    fiat_currency = Column(String(10), nullable=False)
    status = Column(SQLEnum(P2PTradeStatus), default=P2PTradeStatus.PENDING)
    payment_method = Column(String(50))
    escrow_id = Column(Integer, ForeignKey("escrow.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    payment_deadline = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    advertisement = relationship("P2PAdvertisement", back_populates="trades")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_trades")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_trades")
    escrow = relationship("Escrow", back_populates="trade", uselist=False)
    dispute = relationship("Dispute", back_populates="trade", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_buyer_status', 'buyer_id', 'status'),
        Index('idx_seller_status', 'seller_id', 'status'),
    )


# Escrow Model
class Escrow(Base):
    __tablename__ = "escrow"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    locked_at = Column(DateTime(timezone=True), server_default=func.now())
    released_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="LOCKED")  # LOCKED, RELEASED, REFUNDED
    
    # Relationships
    trade = relationship("P2PTrade", back_populates="escrow")


# Dispute Model
class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("p2p_trades.id"), nullable=False, unique=True)
    filed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence = Column(Text)  # JSON array of evidence URLs
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.OPEN)
    resolution = Column(Text)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    trade = relationship("P2PTrade", back_populates="dispute")


# Reputation Model
class Reputation(Base):
    __tablename__ = "reputation"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    score = Column(Integer, default=100)
    total_trades = Column(Integer, default=0)
    completed_trades = Column(Integer, default=0)
    disputed_trades = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)  # in minutes
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    badges = Column(Text)  # JSON array of badges
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reputation")


# Review Model
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("p2p_trades.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewed_user = relationship("User", foreign_keys=[reviewed_user_id], back_populates="reviews_received")
    
    # Indexes
    __table_args__ = (
        Index('idx_reviewed_user', 'reviewed_user_id'),
        UniqueConstraint('trade_id', 'reviewer_id', name='uq_trade_reviewer'),
    )


# Notification Model
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # P2P_MATCH, PARTIAL_MATCH, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(Text)  # JSON data about the match/trade
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_unread', 'user_id', 'is_read'),
    )


# Chat Message Model
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user or assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


# ==================== FORUM MODELS ====================

class ForumCategory(Base):
    """Forum categories/salons based on reputation levels"""
    __tablename__ = "forum_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # Emoji or icon name
    min_reputation_required = Column(Integer, default=0)  # 0=Normal, 500=Pro, 1000=Expert
    read_only_for_lower_levels = Column(Boolean, default=False)  # If True, lower levels can only read
    parent_category_id = Column(Integer, ForeignKey("forum_categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parent_category = relationship("ForumCategory", remote_side=[id], backref="subcategories")
    posts = relationship("ForumPost", back_populates="category", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_category_reputation', 'min_reputation_required'),
        Index('idx_category_parent', 'parent_category_id'),
    )


class ForumPost(Base):
    """Forum posts/topics"""
    __tablename__ = "forum_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("forum_categories.id"), nullable=False)
    tags = Column(Text)  # JSON array of tags
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="forum_posts")
    category = relationship("ForumCategory", back_populates="posts")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan", order_by="ForumComment.created_at")
    votes = relationship("ForumVote", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_category', 'category_id', 'created_at'),
        Index('idx_post_author', 'author_id'),
        Index('idx_post_pinned', 'category_id', 'is_pinned', 'created_at'),
        Index('idx_post_activity', 'last_activity_at'),
    )


class ForumComment(Base):
    """Comments/replies to forum posts"""
    __tablename__ = "forum_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    is_solution = Column(Boolean, default=False)  # Mark as accepted solution
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    post = relationship("ForumPost", back_populates="comments")
    author = relationship("User", back_populates="forum_comments")
    parent_comment = relationship("ForumComment", remote_side=[id], backref="replies")
    votes = relationship("ForumVote", back_populates="comment", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_comment_post', 'post_id', 'created_at'),
        Index('idx_comment_author', 'author_id'),
        Index('idx_comment_parent', 'parent_comment_id'),
    )


class ForumVote(Base):
    """Votes (upvote/downvote) on posts and comments"""
    __tablename__ = "forum_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)
    vote_type = Column(String(10), nullable=False)  # UP or DOWN
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="forum_votes")
    post = relationship("ForumPost", back_populates="votes")
    comment = relationship("ForumComment", back_populates="votes")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_user_post_vote'),
        UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_vote'),
        Index('idx_vote_post', 'post_id'),
        Index('idx_vote_comment', 'comment_id'),
    )


# ==================== FORMATION MODELS ====================

class FormationLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class LessonType(str, enum.Enum):
    TEXT = "TEXT"
    VIDEO = "VIDEO"
    QUIZ = "QUIZ"
    CHALLENGE = "CHALLENGE"


class Formation(Base):
    """Formation (Course) Model"""
    __tablename__ = "formations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    level = Column(SQLEnum(FormationLevel), nullable=False, default=FormationLevel.BEGINNER)
    content_json = Column(Text)  # JSON array of lessons
    thumbnail_url = Column(String(255))
    estimated_duration = Column(Integer)  # in minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_progress = relationship("UserProgress", back_populates="formation", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="formation", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="formation", cascade="all, delete-orphan", order_by="Module.module_number")
    exam = relationship("Exam", back_populates="formation", uselist=False, cascade="all, delete-orphan")
    assigned_users = relationship("FormationAssignment", back_populates="formation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_formation_level', 'level'),
        Index('idx_formation_active', 'is_active'),
    )


class FormationAssignment(Base):
    """Formation Assignment - Many-to-Many relationship between Formations and Users"""
    __tablename__ = "formation_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who assigned it
    
    # Relationships
    formation = relationship("Formation", back_populates="assigned_users")
    user = relationship("User", foreign_keys=[user_id], back_populates="assigned_formations")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('formation_id', 'user_id', name='uq_formation_user_assignment'),
        Index('idx_assignment_formation', 'formation_id'),
        Index('idx_assignment_user', 'user_id'),
    )


class UserProgress(Base):
    """User Progress in Formations"""
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    completed_lessons = Column(Text)  # JSON array of lesson IDs
    current_lesson_id = Column(String(50))  # Current lesson being viewed
    status = Column(String(20), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, NOT_STARTED
    progress_percentage = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    formation = relationship("Formation", back_populates="user_progress")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'formation_id', name='uq_user_formation'),
        Index('idx_user_progress', 'user_id', 'formation_id'),
    )


class Certificate(Base):
    """Certificate for completed formations"""
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    certificate_url = Column(String(255))  # URL to generated certificate PDF/image
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    formation = relationship("Formation", back_populates="certificates")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'formation_id', name='uq_user_formation_certificate'),
        Index('idx_certificate_user', 'user_id'),
    )


class Module(Base):
    """Module within a formation (split from PDF)"""
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    module_number = Column(Integer, nullable=False)  # Order of module in formation
    title = Column(String(200), nullable=False)
    content = Column(Text)  # Text content from PDF
    video_url = Column(String(500))  # URL to generated video
    video_duration = Column(Integer)  # Duration in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    formation = relationship("Formation", back_populates="modules")
    quiz = relationship("Quiz", back_populates="module", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_module_formation', 'formation_id', 'module_number'),
    )


class Quiz(Base):
    """Quiz for a module"""
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    questions_json = Column(Text)  # JSON array of questions
    passing_score = Column(Float, default=70.0)  # Minimum score to pass (percentage)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    module = relationship("Module", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_quiz_module', 'module_id'),
    )


class QuizAttempt(Base):
    """User's attempt at a quiz"""
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    answers_json = Column(Text)  # JSON object with question_id -> answer mapping
    score = Column(Float)  # Percentage score
    passed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    quiz = relationship("Quiz", back_populates="attempts")
    
    # Indexes
    __table_args__ = (
        Index('idx_quiz_attempt_user', 'user_id', 'quiz_id'),
    )


class Exam(Base):
    """Final exam for a formation"""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    questions_json = Column(Text)  # JSON array of questions
    passing_score = Column(Float, default=70.0)  # Minimum score to pass (percentage)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    formation = relationship("Formation", back_populates="exam")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_exam_formation', 'formation_id'),
    )


class ExamAttempt(Base):
    """User's attempt at the final exam"""
    __tablename__ = "exam_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    answers_json = Column(Text)  # JSON object with question_id -> answer mapping
    score = Column(Float)  # Percentage score
    passed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    exam = relationship("Exam", back_populates="attempts")
    
    # Indexes
    __table_args__ = (
        Index('idx_exam_attempt_user', 'user_id', 'exam_id'),
    )
