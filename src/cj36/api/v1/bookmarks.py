from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from cj36.dependencies import get_db, get_current_user
from cj36.models import Bookmark, BookmarkCreate, BookmarkRead, User, Post

router = APIRouter()


@router.get("/", response_model=List[BookmarkRead])
def get_user_bookmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all bookmarks for the current user"""
    bookmarks = db.exec(
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    ).all()
    return bookmarks


@router.post("/", response_model=BookmarkRead)
def add_bookmark(
    bookmark_in: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a bookmark"""
    # Check if post exists
    post = db.get(Post, bookmark_in.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if already bookmarked
    existing = db.exec(
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .where(Bookmark.post_id == bookmark_in.post_id)
    ).first()
    
    if existing:
        return existing
    
    # Create bookmark
    bookmark = Bookmark(
        post_id=bookmark_in.post_id,
        user_id=current_user.id
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{post_id}")
def remove_bookmark(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a bookmark"""
    bookmark = db.exec(
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .where(Bookmark.post_id == post_id)
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark removed successfully"}


@router.post("/sync")
def sync_bookmarks(
    post_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync local bookmarks to server"""
    synced_count = 0
    
    for post_id in post_ids:
        # Check if post exists
        post = db.get(Post, post_id)
        if not post:
            continue
        
        # Check if already bookmarked
        existing = db.exec(
            select(Bookmark)
            .where(Bookmark.user_id == current_user.id)
            .where(Bookmark.post_id == post_id)
        ).first()
        
        if not existing:
            bookmark = Bookmark(
                post_id=post_id,
                user_id=current_user.id
            )
            db.add(bookmark)
            synced_count += 1
    
    db.commit()
    return {"message": f"Synced {synced_count} bookmarks"}
