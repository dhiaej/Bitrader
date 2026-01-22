"""
Forum Permission Service - Manages access control based on user reputation
"""
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from models import User, Reputation, ForumCategory

# Reputation thresholds for forum access
REPUTATION_NORMAL = 0
REPUTATION_PRO = 500
REPUTATION_EXPERT = 1000


def get_user_reputation_level(user: User, db: Session) -> str:
    """
    Get user's reputation level: 'normal', 'pro', or 'expert'
    """
    if not user.reputation:
        return "normal"
    
    score = user.reputation.score or 0
    
    if score >= REPUTATION_EXPERT:
        return "expert"
    elif score >= REPUTATION_PRO:
        return "pro"
    else:
        return "normal"


def can_read_category(user: User, category: ForumCategory, db: Session) -> bool:
    """
    Check if user can read a category.
    All users can read all categories (to learn from experts).
    """
    if not user.is_active:
        return False
    
    return True


def can_write_category(user: User, category: ForumCategory, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Check if user can write (create posts/comments) in a category.
    Returns (allowed: bool, reason: Optional[str])
    """
    if not user.is_active:
        return False, "User account is inactive"
    
    if not user.reputation:
        user_reputation_score = 0
    else:
        user_reputation_score = user.reputation.score or 0
    
    # Check if user meets minimum reputation requirement
    if user_reputation_score < category.min_reputation_required:
        level_name = "Normal"
        if category.min_reputation_required >= REPUTATION_EXPERT:
            level_name = "Expert"
        elif category.min_reputation_required >= REPUTATION_PRO:
            level_name = "Pro"
        
        return False, f"This category requires {level_name} level (reputation ≥ {category.min_reputation_required}). Your reputation: {user_reputation_score}"
    
    return True, None


def can_edit_post(user: User, post_author_id: int, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Check if user can edit a post.
    Users can only edit their own posts (or admins can edit any).
    """
    if user.is_admin:
        return True, None
    
    if user.id == post_author_id:
        return True, None
    
    return False, "You can only edit your own posts"


def can_delete_post(user: User, post_author_id: int, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Check if user can delete a post.
    Users can only delete their own posts (or admins can delete any).
    """
    if user.is_admin:
        return True, None
    
    if user.id == post_author_id:
        return True, None
    
    return False, "You can only delete your own posts"


def can_pin_post(user: User, db: Session) -> bool:
    """
    Check if user can pin posts.
    Only admins can pin posts.
    """
    return user.is_admin


def can_lock_post(user: User, db: Session) -> bool:
    """
    Check if user can lock posts.
    Only admins can lock posts.
    """
    return user.is_admin


def can_mark_solution(user: User, post_author_id: int, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Check if user can mark a comment as solution.
    Only the post author can mark comments as solutions.
    """
    if user.id == post_author_id:
        return True, None
    
    return False, "Only the post author can mark comments as solutions"


def get_reputation_level_name(score: int) -> str:
    """
    Get human-readable reputation level name.
    """
    if score >= REPUTATION_EXPERT:
        return "Expert"
    elif score >= REPUTATION_PRO:
        return "Pro"
    else:
        return "Normal"

