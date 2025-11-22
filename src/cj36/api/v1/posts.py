from typing import List, Optional
import shutil
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, File, UploadFile, Form
from sqlmodel import Session, select
from cj36.dependencies import (
    get_db,
    get_current_user,
    RoleChecker,
    get_optional_current_user,
)
from cj36.models import Post, PostCreate, PostRead, PostUpdate, User, Category, PostStatus, Role, PostCategoryLink

router = APIRouter()


@router.post("/", response_model=PostRead)
def create_post(
    title: str = Form(...),
    description: str = Form(...),
    topic_ids: List[int] = Form(...),
    category_id: Optional[int] = Form(None),
    status: Optional[PostStatus] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "writer"])),
):
    topics = db.query(Category).where(Category.id.in_(topic_ids)).all()
    if not topics:
        raise HTTPException(status_code=400, detail="Invalid topic IDs")

    parent_categories = set()
    for topic in topics:
        if topic.parent_id:
            parent_categories.add(topic.parent_id)
        else:
            parent_categories.add(topic.id)

    final_category_id = None
    if len(parent_categories) == 1:
        final_category_id = parent_categories.pop()
    else:
        if category_id not in parent_categories:
            raise HTTPException(
                status_code=400,
                detail="Category must be one of the parent categories of the topics",
            )
        final_category_id = category_id
    
    image_path = None
    if image:
        # Generate unique filename
        file_extension = Path(image.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        save_path = Path("static/images") / unique_filename
        
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        image_path = str(save_path)

    post_data = {
        "title": title,
        "description": description,
        "topic_ids": topic_ids,
        "category_id": final_category_id,
        "author_id": current_user.id,
        "image": image_path,
    }
    
    if status is not None:
        post_data["status"] = status
    
    db_post = Post(**post_data)
    db_post.topics = topics

    if current_user.post_review_before_publish:
        db_post.status = PostStatus.PENDING
    elif status is None: # If status not provided and no review needed, default to PUBLISHED
         db_post.status = PostStatus.PUBLISHED
    # Else use provided status (if valid for role, but here we trust the input or model default)
    # Actually model default is DRAFT.
    # Logic in previous code:
    # if current_user.post_review_before_publish:
    #     db_post.status = PostStatus.PENDING
    # else:
    #     db_post.status = PostStatus.PUBLISHED
    
    # Let's keep the previous logic for status if not explicitly provided
    if status is None:
        if current_user.post_review_before_publish:
            db_post.status = PostStatus.PENDING
        else:
            db_post.status = PostStatus.PUBLISHED

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.get("/", response_model=List[PostRead])
def read_posts(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    topic_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    query = select(Post)
    
    if category_id:
        query = query.where(Post.category_id == category_id)
        
    if topic_ids:
        query = query.join(PostCategoryLink).where(PostCategoryLink.category_id.in_(topic_ids)).distinct()

    if current_user is None:
        query = query.where(Post.status == PostStatus.PUBLISHED)
    elif current_user.role == Role.WRITER:
        query = query.where(
            (Post.author_id == current_user.id)
            | (Post.status == PostStatus.PUBLISHED)
        )
    elif current_user.role in [Role.MAINTAINER, Role.ADMIN]:
        # Maintainers and Admins can see all posts
        pass

    posts = db.exec(query.offset(skip).limit(limit)).all()
    return posts


@router.get("/{post_id}", response_model=PostRead)
def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user is None:
        if db_post.status != PostStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this post"
            )
    elif current_user.role == Role.WRITER:
        if db_post.author_id != current_user.id and db_post.status != PostStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this post"
            )
    elif current_user.role in [Role.MAINTAINER, Role.ADMIN]:
        pass  # Maintainers and Admins can see all posts
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this post"
        )
    return db_post


@router.patch("/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "writer"])),  # Writers can update their own posts
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role == Role.WRITER and db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post"
        )
    
    # Only Admin/Maintainer can update status
    if post_in.status is not None and current_user.role not in [Role.ADMIN, Role.MAINTAINER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update post status"
        )

    # Similar logic for category and topics as in create_post
    post_data = post_in.dict(exclude_unset=True)
    for key, value in post_data.items():
        setattr(db_post, key, value)

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.delete("/{post_id}", response_model=PostRead)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "writer"])),  # Writers can delete their own posts
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.role == Role.WRITER and db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post"
        )

    # Eager load relationships before deletion for response
    # Or simpler: just return the ID or basic info?
    # The response model is PostRead, which includes category/topics.
    # We must load them.
    # Actually, if we delete it, we can't refresh it.
    # We should convert to PostRead before deleting.
    post_read = PostRead.from_orm(db_post)
    
    db.delete(db_post)
    db.commit()
    return post_read


@router.patch("/status/{post_id}", response_model=PostRead)
def update_post_status(
    post_id: int,
    new_status: PostStatus = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "maintainer"])),
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if db_post.status == PostStatus.PENDING and new_status in [PostStatus.PUBLISHED, PostStatus.REJECTED]:
        db_post.status = new_status
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status transition"
        )
