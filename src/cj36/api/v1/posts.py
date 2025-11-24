from typing import List, Optional
import shutil
from pathlib import Path
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, File, UploadFile, Form
from sqlmodel import Session, select
from cj36.dependencies import (
    get_db,
    get_current_user,
    AdminChecker,
    get_optional_current_user,
)
from cj36.models import (
    Post,
    PostCreate,
    PostRead,
    PostUpdate,
    User,
    Category,
    PostStatus,
    Role,
    PostCategoryLink,
    UserType,
    PostCategoryLink,
    UserType,
    AdminType,
    PostSyncResponse,
)
from sqlalchemy import func

router = APIRouter()

# ---------- Create Post ----------
@router.post("/", response_model=PostRead)
def create_post(
    title: str = Form(...),
    description: str = Form(...),
    topic_ids: List[int] = Form(...),
    category_id: Optional[int] = Form(None),
    status: Optional[PostStatus] = Form(None),
    scheduled_at: Optional[datetime.datetime] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    # Writers are ADMINISTRATOR with admin_type WRITER; admins and maintainers can also create
    current_user: User = Depends(AdminChecker(["admin", "maintainer", "writer"])),
):
    topics = db.query(Category).where(Category.id.in_(topic_ids)).all()
    if not topics:
        raise HTTPException(status_code=400, detail="Invalid topic IDs")

    # Determine final category (same logic as before)
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
        file_extension = Path(image.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        save_path = Path("static/images") / unique_filename
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = str(save_path)
    elif image_url:
        image_path = image_url

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
    
    if scheduled_at is not None:
        post_data["scheduled_at"] = scheduled_at
        # If scheduled time is in future, force status to SCHEDULED unless it's draft
        if scheduled_at > datetime.datetime.utcnow() and status != PostStatus.DRAFT:
             post_data["status"] = PostStatus.SCHEDULED

    db_post = Post(**post_data)
    db_post.topics = topics

    # Apply review logic based on user flag
    if current_user.post_review_before_publish:
        db_post.status = PostStatus.PENDING
    elif status is None:
        # Default behavior if no status provided
        if scheduled_at and scheduled_at > datetime.datetime.utcnow():
             db_post.status = PostStatus.SCHEDULED
        else:
             db_post.status = PostStatus.PUBLISHED
    # else keep provided status (validated by enum)

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

# ---------- Sync Posts ----------
@router.get("/sync", response_model=PostSyncResponse)
def sync_posts(
    last_id: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    # 1. Fetch new posts
    query = select(Post).where(Post.id > last_id)
    
    # Filter based on user role
    if current_user is None:
        query = query.where(Post.status == PostStatus.PUBLISHED)
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type == AdminType.WRITER:
        query = query.where(
            (Post.author_id == current_user.id)
            | (Post.status == PostStatus.PUBLISHED)
        )
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type in [AdminType.MAINTAINER, AdminType.ADMIN]:
        pass
    else:
        query = query.where(Post.status == PostStatus.PUBLISHED)
        
    new_posts = db.exec(query.limit(50)).all()
    
    # 2. Fetch category counts (Total published posts per category)
    count_query = select(Post.category_id, func.count(Post.id)).where(Post.status == PostStatus.PUBLISHED).group_by(Post.category_id)
    counts = db.exec(count_query).all()
    category_counts = {cat_id: count for cat_id, count in counts if cat_id is not None}
    
    return PostSyncResponse(posts=new_posts, category_counts=category_counts)

# ---------- Read Posts ----------
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
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type == AdminType.WRITER:
        query = query.where(
            (Post.author_id == current_user.id)
            | (Post.status == PostStatus.PUBLISHED)
        )
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type in [AdminType.MAINTAINER, AdminType.ADMIN]:
        # Maintainers and Admins can see all posts
        pass
    else:
        # Subscribers or others
        # Only show PUBLISHED posts, or SCHEDULED posts that are now due
        # But wait, we should rely on a background job to flip SCHEDULED -> PUBLISHED.
        # If we don't have a background job, we can check here.
        # Simpler: Only show PUBLISHED. The background job (or a check on access) should handle the flip.
        # For now, let's assume we only show PUBLISHED.
        query = query.where(Post.status == PostStatus.PUBLISHED)

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
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type == AdminType.WRITER:
        if db_post.author_id != current_user.id and db_post.status != PostStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this post"
            )
    elif current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type in [AdminType.MAINTAINER, AdminType.ADMIN]:
        pass  # Maintainers and Admins can see all posts
    else:
        # Subscribers
        if db_post.status != PostStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this post"
            )
    return db_post


@router.put("/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    topic_ids: Optional[List[int]] = Form(None),
    category_id: Optional[int] = Form(None),
    status: Optional[PostStatus] = Form(None),
    scheduled_at: Optional[datetime.datetime] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin", "maintainer", "writer"])),
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Writers can only edit their own posts
    if current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type == AdminType.WRITER:
        if db_post.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    # Only Admin/Maintainer can update status
    if status is not None and current_user.admin_type not in [AdminType.ADMIN, AdminType.MAINTAINER]:
        # If writer tries to change status, ignore it or raise error?
        # Let's ignore it for now or keep existing status if they send it.
        # But if they explicitly try to change it, we should probably forbid.
        # However, the form might send the current status.
        if status != db_post.status:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update post status"
            )

    if title is not None:
        db_post.title = title
    if description is not None:
        db_post.description = description
    if category_id is not None:
        db_post.category_id = category_id
    if video_url is not None:
        db_post.video_url = video_url
    if scheduled_at is not None:
        db_post.scheduled_at = scheduled_at
        # If updating schedule and it's in future, update status to SCHEDULED if not draft
        if scheduled_at > datetime.datetime.utcnow() and db_post.status != PostStatus.DRAFT:
             db_post.status = PostStatus.SCHEDULED
    
    # Handle status update if authorized
    if status is not None and current_user.admin_type in [AdminType.ADMIN, AdminType.MAINTAINER]:
        db_post.status = status

    # Handle topics
    if topic_ids is not None:
        topics = db.query(Category).where(Category.id.in_(topic_ids)).all()
        if not topics and topic_ids: # If IDs provided but no topics found
             raise HTTPException(status_code=400, detail="Invalid topic IDs")
        db_post.topics = topics

    # Handle Image
    if image:
        file_extension = Path(image.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        save_path = Path("static/images") / unique_filename
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        db_post.image = str(save_path)
    elif image_url is not None:
        db_post.image = image_url

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.delete("/{post_id}", response_model=PostRead)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin", "maintainer", "writer"])),
):
    db_post = db.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.user_type == UserType.ADMINISTRATOR and current_user.admin_type == AdminType.WRITER:
        if db_post.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

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
    current_user: User = Depends(AdminChecker(["admin", "maintainer"])),
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
