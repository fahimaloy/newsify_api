from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from cj36.dependencies import get_db, get_current_user, get_optional_current_user
from cj36.models import Comment, CommentCreate, CommentRead, User, Post, UserType, AdminType

router = APIRouter()


@router.get("/{post_id}/comments", response_model=List[CommentRead])
def get_post_comments(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get all comments for a post"""
    comments = db.exec(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.desc())
    ).all()
    return comments


@router.post("/{post_id}/comments", response_model=CommentRead)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new comment (requires authentication)"""
    # Verify post exists
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment
    comment = Comment(
        content=comment_in.content,
        post_id=post_id,
        author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a comment (author or admin only)"""
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is author or admin
    is_admin = (
        current_user.user_type == UserType.ADMINISTRATOR and
        current_user.admin_type in [AdminType.ADMIN, AdminType.MAINTAINER]
    )
    
    if comment.author_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
