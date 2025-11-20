from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from cj36.dependencies import (
    get_db,
    get_current_user,
    RoleChecker,
    get_optional_current_user,
)
from cj36.models import Post, PostCreate, PostRead, User, Category, PostStatus, Role

router = APIRouter()


@router.post("/", response_model=PostRead)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "writer"])),
):
    topics = db.query(Category).where(Category.id.in_(post.topic_ids)).all()
    if not topics:
        raise HTTPException(status_code=400, detail="Invalid topic IDs")

    parent_categories = set()
    for topic in topics:
        if topic.parent_id:
            parent_categories.add(topic.parent_id)
        else:
            parent_categories.add(topic.id)

    category_id = None
    if len(parent_categories) == 1:
        category_id = parent_categories.pop()
    else:
        if post.category_id not in parent_categories:
            raise HTTPException(
                status_code=400,
                detail="Category must be one of the parent categories of the topics",
            )
        category_id = post.category_id

    db_post = Post.from_orm(post)
    db_post.author_id = current_user.id
    db_post.category_id = category_id
    db_post.topics = topics

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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    query = select(Post)
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
    post_in: PostCreate,
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

    db.delete(db_post)
    db.commit()
    return db_post


@router.patch("/status/{post_id}", response_model=PostRead)
def update_post_status(
    post_id: int,
    new_status: PostStatus,
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
