"""
Forum Router - API endpoints for forum functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional
import json
from datetime import datetime

from database import get_db
from models import User, ForumCategory, ForumPost, ForumComment, ForumVote, Reputation
from utils.auth import get_current_user
from schemas import (
    ForumCategoryResponse, ForumCategoryCreate, ForumCategoryUpdate,
    ForumPostResponse, ForumPostCreate, ForumPostUpdate, ForumPostListResponse, ForumPostDetailResponse,
    ForumCommentResponse, ForumCommentCreate, ForumCommentUpdate,
    ForumVoteCreate, ForumVoteResponse,
    AuthorInfo
)
from services.forum_permission_service import (
    can_read_category, can_write_category, can_edit_post, can_delete_post,
    can_pin_post, can_lock_post, can_mark_solution, get_user_reputation_level,
    get_reputation_level_name
)

router = APIRouter(prefix="/forum", tags=["forum"])


# ==================== Categories ====================

@router.get("/categories", response_model=List[ForumCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get all active forum categories"""
    categories = db.query(ForumCategory).filter(ForumCategory.is_active == True).order_by(
        ForumCategory.min_reputation_required, ForumCategory.sort_order, ForumCategory.name
    ).all()
    
    # Add post count for each category
    result = []
    for cat in categories:
        post_count = db.query(func.count(ForumPost.id)).filter(
            ForumPost.category_id == cat.id,
            ForumPost.is_deleted == False
        ).scalar()
        
        cat_dict = {
            **{col.name: getattr(cat, col.name) for col in cat.__table__.columns},
            "post_count": post_count
        }
        result.append(ForumCategoryResponse(**cat_dict))
    
    return result


@router.get("/categories/{category_id}", response_model=ForumCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category"""
    category = db.query(ForumCategory).filter(ForumCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    post_count = db.query(func.count(ForumPost.id)).filter(
        ForumPost.category_id == category_id,
        ForumPost.is_deleted == False
    ).scalar()
    
    cat_dict = {
        **{col.name: getattr(category, col.name) for col in category.__table__.columns},
        "post_count": post_count
    }
    return ForumCategoryResponse(**cat_dict)


# ==================== Posts ====================

@router.get("/categories/{category_id}/posts", response_model=ForumPostListResponse)
def get_posts(
    category_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("activity", regex="^(activity|newest|votes|oldest)$"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get posts in a category with pagination"""
    # Check category exists
    category = db.query(ForumCategory).filter(ForumCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check read permission
    if current_user:
        if not can_read_category(current_user, category, db):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Build query
    query = db.query(ForumPost).filter(
        ForumPost.category_id == category_id,
        ForumPost.is_deleted == False
    )
    
    # Sorting
    if sort == "newest":
        query = query.order_by(desc(ForumPost.created_at))
    elif sort == "oldest":
        query = query.order_by(ForumPost.created_at)
    elif sort == "votes":
        query = query.order_by(desc(ForumPost.upvotes - ForumPost.downvotes))
    else:  # activity (default)
        query = query.order_by(
            desc(ForumPost.is_pinned),
            desc(ForumPost.last_activity_at)
        )
    
    # Get total count
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    # Pagination
    posts = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response with author info and user votes
    posts_response = []
    for post in posts:
        # Get author info with reputation
        author_reputation = post.author.reputation.score if post.author.reputation else 0
        author_level = get_user_reputation_level(post.author, db)
        
        author_info = AuthorInfo(
            id=post.author.id,
            username=post.author.username,
            avatar_url=post.author.avatar_url,
            reputation_score=author_reputation,
            reputation_level=author_level
        )
        
        # Get user vote if logged in
        user_vote = None
        if current_user:
            vote = db.query(ForumVote).filter(
                ForumVote.user_id == current_user.id,
                ForumVote.post_id == post.id
            ).first()
            if vote:
                user_vote = vote.vote_type
        
        # Parse tags
        tags = None
        if post.tags:
            try:
                tags = json.loads(post.tags)
            except:
                tags = []
        
        post_dict = {
            **{col.name: getattr(post, col.name) for col in post.__table__.columns},
            "author": author_info,
            "category_name": category.name,
            "tags": tags,
            "user_vote": user_vote
        }
        posts_response.append(ForumPostResponse(**post_dict))
    
    return ForumPostListResponse(
        posts=posts_response,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/posts/{post_id}", response_model=ForumPostDetailResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific post with comments"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check read permission
    category = post.category
    if current_user:
        if not can_read_category(current_user, category, db):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Increment view count
    post.view_count += 1
    db.commit()
    db.refresh(post)
    
    # Get author info
    author_reputation = post.author.reputation.score if post.author.reputation else 0
    author_level = get_user_reputation_level(post.author, db)
    author_info = AuthorInfo(
        id=post.author.id,
        username=post.author.username,
        avatar_url=post.author.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    # Get user vote
    user_vote = None
    if current_user:
        vote = db.query(ForumVote).filter(
            ForumVote.user_id == current_user.id,
            ForumVote.post_id == post.id
        ).first()
        if vote:
            user_vote = vote.vote_type
    
    # Parse tags
    tags = None
    if post.tags:
        try:
            tags = json.loads(post.tags)
        except:
            tags = []
    
    # Get comments (only top-level, replies will be nested)
    comments = db.query(ForumComment).filter(
        ForumComment.post_id == post_id,
        ForumComment.is_deleted == False,
        ForumComment.parent_comment_id == None  # Top-level only
    ).order_by(ForumComment.created_at).all()
    
    # Build nested comments structure
    comments_response = []
    for comment in comments:
        comments_response.append(_build_comment_response(comment, db, current_user))
    
    post_dict = {
        **{col.name: getattr(post, col.name) for col in post.__table__.columns},
        "author": author_info,
        "category_name": category.name,
        "tags": tags,
        "user_vote": user_vote,
        "comments": comments_response
    }
    
    return ForumPostDetailResponse(**post_dict)


def _build_comment_response(comment: ForumComment, db: Session, current_user: Optional[User]) -> ForumCommentResponse:
    """Recursively build comment response with replies"""
    author_reputation = comment.author.reputation.score if comment.author.reputation else 0
    author_level = get_user_reputation_level(comment.author, db)
    
    author_info = AuthorInfo(
        id=comment.author.id,
        username=comment.author.username,
        avatar_url=comment.author.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    user_vote = None
    if current_user:
        vote = db.query(ForumVote).filter(
            ForumVote.user_id == current_user.id,
            ForumVote.comment_id == comment.id
        ).first()
        if vote:
            user_vote = vote.vote_type
    
    # Get replies
    replies = db.query(ForumComment).filter(
        ForumComment.parent_comment_id == comment.id,
        ForumComment.is_deleted == False
    ).order_by(ForumComment.created_at).all()
    
    replies_response = [_build_comment_response(reply, db, current_user) for reply in replies]
    
    comment_dict = {
        **{col.name: getattr(comment, col.name) for col in comment.__table__.columns},
        "author": author_info,
        "user_vote": user_vote,
        "reply_count": len(replies),
        "replies": replies_response
    }
    
    return ForumCommentResponse(**comment_dict)


@router.post("/posts", response_model=ForumPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new forum post"""
    # Check category exists
    category = db.query(ForumCategory).filter(ForumCategory.id == post_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check write permission
    can_write, reason = can_write_category(current_user, category, db)
    if not can_write:
        raise HTTPException(status_code=403, detail=reason)
    
    # Create post
    tags_json = json.dumps(post_data.tags) if post_data.tags else None
    
    post = ForumPost(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id,
        category_id=post_data.category_id,
        tags=tags_json,
        upvotes=0,
        downvotes=0,
        view_count=0,
        comment_count=0,
        is_pinned=False,
        is_locked=False,
        is_deleted=False,
        last_activity_at=datetime.utcnow()
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Build response
    author_reputation = current_user.reputation.score if current_user.reputation else 0
    author_level = get_user_reputation_level(current_user, db)
    author_info = AuthorInfo(
        id=current_user.id,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    tags_list = post_data.tags if post_data.tags else []
    
    post_dict = {
        **{col.name: getattr(post, col.name) for col in post.__table__.columns},
        "author": author_info,
        "category_name": category.name,
        "tags": tags_list,
        "user_vote": None
    }
    
    return ForumPostResponse(**post_dict)


@router.put("/posts/{post_id}", response_model=ForumPostResponse)
def update_post(
    post_id: int,
    post_data: ForumPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a forum post"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check edit permission
    can_edit, reason = can_edit_post(current_user, post.author_id, db)
    if not can_edit:
        raise HTTPException(status_code=403, detail=reason)
    
    # Update fields
    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content
    if post_data.tags is not None:
        post.tags = json.dumps(post_data.tags)
    if post_data.category_id is not None:
        # Check permission for new category
        new_category = db.query(ForumCategory).filter(ForumCategory.id == post_data.category_id).first()
        if not new_category:
            raise HTTPException(status_code=404, detail="Category not found")
        can_write, reason = can_write_category(current_user, new_category, db)
        if not can_write:
            raise HTTPException(status_code=403, detail=reason)
        post.category_id = post_data.category_id
    if post_data.is_pinned is not None and can_pin_post(current_user, db):
        post.is_pinned = post_data.is_pinned
    if post_data.is_locked is not None and can_lock_post(current_user, db):
        post.is_locked = post_data.is_locked
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    # Build response (similar to create)
    category = post.category
    author_reputation = post.author.reputation.score if post.author.reputation else 0
    author_level = get_user_reputation_level(post.author, db)
    author_info = AuthorInfo(
        id=post.author.id,
        username=post.author.username,
        avatar_url=post.author.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    tags_list = []
    if post.tags:
        try:
            tags_list = json.loads(post.tags)
        except:
            pass
    
    user_vote = None
    vote = db.query(ForumVote).filter(
        ForumVote.user_id == current_user.id,
        ForumVote.post_id == post.id
    ).first()
    if vote:
        user_vote = vote.vote_type
    
    post_dict = {
        **{col.name: getattr(post, col.name) for col in post.__table__.columns},
        "author": author_info,
        "category_name": category.name,
        "tags": tags_list,
        "user_vote": user_vote
    }
    
    return ForumPostResponse(**post_dict)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (soft delete) a forum post"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check delete permission
    can_delete, reason = can_delete_post(current_user, post.author_id, db)
    if not can_delete:
        raise HTTPException(status_code=403, detail=reason)
    
    post.is_deleted = True
    db.commit()
    
    return None


# ==================== Comments ====================

@router.post("/posts/{post_id}/comments", response_model=ForumCommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    comment_data: ForumCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a post"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.is_locked:
        raise HTTPException(status_code=403, detail="Post is locked")
    
    # Check write permission
    category = post.category
    can_write, reason = can_write_category(current_user, category, db)
    if not can_write:
        raise HTTPException(status_code=403, detail=reason)
    
    # Check parent comment exists if provided
    if comment_data.parent_comment_id:
        parent = db.query(ForumComment).filter(ForumComment.id == comment_data.parent_comment_id).first()
        if not parent or parent.is_deleted or parent.post_id != post_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    comment = ForumComment(
        post_id=post_id,
        author_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
        upvotes=0,
        downvotes=0,
        is_solution=False,
        is_deleted=False
    )
    
    db.add(comment)
    
    # Update post comment count and last activity
    post.comment_count += 1
    post.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    # Build response
    author_reputation = current_user.reputation.score if current_user.reputation else 0
    author_level = get_user_reputation_level(current_user, db)
    author_info = AuthorInfo(
        id=current_user.id,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    comment_dict = {
        **{col.name: getattr(comment, col.name) for col in comment.__table__.columns},
        "author": author_info,
        "user_vote": None,
        "reply_count": 0,
        "replies": []
    }
    
    return ForumCommentResponse(**comment_dict)


@router.put("/comments/{comment_id}", response_model=ForumCommentResponse)
def update_comment(
    comment_id: int,
    comment_data: ForumCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment"""
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check edit permission
    if current_user.id != comment.author_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    if comment_data.content is not None:
        comment.content = comment_data.content
    
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    
    # Build response (similar to create)
    author_reputation = comment.author.reputation.score if comment.author.reputation else 0
    author_level = get_user_reputation_level(comment.author, db)
    author_info = AuthorInfo(
        id=comment.author.id,
        username=comment.author.username,
        avatar_url=comment.author.avatar_url,
        reputation_score=author_reputation,
        reputation_level=author_level
    )
    
    user_vote = None
    vote = db.query(ForumVote).filter(
        ForumVote.user_id == current_user.id,
        ForumVote.comment_id == comment.id
    ).first()
    if vote:
        user_vote = vote.vote_type
    
    # Get replies count
    reply_count = db.query(func.count(ForumComment.id)).filter(
        ForumComment.parent_comment_id == comment.id,
        ForumComment.is_deleted == False
    ).scalar()
    
    comment_dict = {
        **{col.name: getattr(comment, col.name) for col in comment.__table__.columns},
        "author": author_info,
        "user_vote": user_vote,
        "reply_count": reply_count,
        "replies": []
    }
    
    return ForumCommentResponse(**comment_dict)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (soft delete) a comment"""
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if current_user.id != comment.author_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    comment.is_deleted = True
    
    # Update post comment count
    post = comment.post
    post.comment_count = max(0, post.comment_count - 1)
    
    db.commit()
    
    return None


@router.post("/comments/{comment_id}/solution", response_model=ForumCommentResponse)
def mark_solution(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a comment as the solution to the post"""
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    post = comment.post
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permission
    can_mark, reason = can_mark_solution(current_user, post.author_id, db)
    if not can_mark:
        raise HTTPException(status_code=403, detail=reason)
    
    # Unmark previous solution if any
    previous_solution = db.query(ForumComment).filter(
        ForumComment.post_id == post.id,
        ForumComment.is_solution == True,
        ForumComment.id != comment_id
    ).first()
    
    if previous_solution:
        previous_solution.is_solution = False
    
    # Mark as solution
    comment.is_solution = True
    db.commit()
    db.refresh(comment)
    
    # Build response (reuse function)
    return _build_comment_response(comment, db, current_user)


# ==================== Votes ====================

@router.post("/posts/{post_id}/vote", response_model=ForumVoteResponse)
def vote_post(
    post_id: int,
    vote_data: ForumVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on a post (upvote or downvote)"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user already voted
    existing_vote = db.query(ForumVote).filter(
        ForumVote.user_id == current_user.id,
        ForumVote.post_id == post_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_data.vote_type:
            # Same vote, remove it
            db.delete(existing_vote)
            if vote_data.vote_type == "UP":
                post.upvotes = max(0, post.upvotes - 1)
            else:
                post.downvotes = max(0, post.downvotes - 1)
        else:
            # Change vote
            if existing_vote.vote_type == "UP":
                post.upvotes = max(0, post.upvotes - 1)
                post.downvotes += 1
            else:
                post.downvotes = max(0, post.downvotes - 1)
                post.upvotes += 1
            
            existing_vote.vote_type = vote_data.vote_type
    else:
        # New vote
        vote = ForumVote(
            user_id=current_user.id,
            post_id=post_id,
            vote_type=vote_data.vote_type
        )
        db.add(vote)
        
        if vote_data.vote_type == "UP":
            post.upvotes += 1
        else:
            post.downvotes += 1
    
    db.commit()
    
    if existing_vote:
        db.refresh(existing_vote)
        vote_dict = {
            **{col.name: getattr(existing_vote, col.name) for col in existing_vote.__table__.columns}
        }
        return ForumVoteResponse(**vote_dict)
    else:
        db.refresh(vote)
        vote_dict = {
            **{col.name: getattr(vote, col.name) for col in vote.__table__.columns}
        }
        return ForumVoteResponse(**vote_dict)


@router.post("/comments/{comment_id}/vote", response_model=ForumVoteResponse)
def vote_comment(
    comment_id: int,
    vote_data: ForumVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on a comment (upvote or downvote)"""
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user already voted
    existing_vote = db.query(ForumVote).filter(
        ForumVote.user_id == current_user.id,
        ForumVote.comment_id == comment_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_data.vote_type:
            # Remove vote
            db.delete(existing_vote)
            if vote_data.vote_type == "UP":
                comment.upvotes = max(0, comment.upvotes - 1)
            else:
                comment.downvotes = max(0, comment.downvotes - 1)
        else:
            # Change vote
            if existing_vote.vote_type == "UP":
                comment.upvotes = max(0, comment.upvotes - 1)
                comment.downvotes += 1
            else:
                comment.downvotes = max(0, comment.downvotes - 1)
                comment.upvotes += 1
            
            existing_vote.vote_type = vote_data.vote_type
    else:
        # New vote
        vote = ForumVote(
            user_id=current_user.id,
            comment_id=comment_id,
            vote_type=vote_data.vote_type
        )
        db.add(vote)
        
        if vote_data.vote_type == "UP":
            comment.upvotes += 1
        else:
            comment.downvotes += 1
    
    db.commit()
    
    if existing_vote:
        db.refresh(existing_vote)
        vote_dict = {
            **{col.name: getattr(existing_vote, col.name) for col in existing_vote.__table__.columns}
        }
        return ForumVoteResponse(**vote_dict)
    else:
        db.refresh(vote)
        vote_dict = {
            **{col.name: getattr(vote, col.name) for col in vote.__table__.columns}
        }
        return ForumVoteResponse(**vote_dict)

