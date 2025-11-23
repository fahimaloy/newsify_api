from typing import List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
import datetime
import enum


class UserType(str, enum.Enum):
    SUBSCRIBER = "subscriber"
    ADMINISTRATOR = "administrator"


class AdminType(str, enum.Enum):
    ADMIN = "admin"
    WRITER = "writer"
    MAINTAINER = "maintainer"


class Role(str, enum.Enum):
    """Deprecated - kept for backward compatibility"""
    WRITER = "writer"
    MAINTAINER = "maintainer"
    ADMIN = "admin"


class PostStatus(str, enum.Enum):
    PENDING = "pending"
    DRAFT = "draft"
    PUBLISHED = "published"
    REJECTED = "rejected"


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    user_type: UserType = Field(default=UserType.SUBSCRIBER)
    admin_type: Optional[AdminType] = Field(default=None)
    post_review_before_publish: bool = Field(default=False)
    newsletter_subscribed: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    is_blocked: bool = Field(default=False)
    verification_code: Optional[str] = Field(default=None)
    
    # Deprecated field - kept for backward compatibility
    role: Optional[Role] = Field(default=None)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    posts: List["Post"] = Relationship(back_populates="author")


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    user_type: Optional[UserType] = None
    admin_type: Optional[AdminType] = None
    post_review_before_publish: Optional[bool] = None
    newsletter_subscribed: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserRead(UserBase):
    id: int


class UserSignup(SQLModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    newsletter_subscribed: bool = Field(default=False)


class PostCategoryLink(SQLModel, table=True):
    post_id: Optional[int] = Field(
        default=None, foreign_key="post.id", primary_key=True
    )
    category_id: Optional[int] = Field(
        default=None, foreign_key="category.id", primary_key=True
    )


class CategoryBase(SQLModel):
    name: str = Field(index=True)
    bn_name: Optional[str] = Field(default=None, index=True)


class Category(CategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="category.id")

    parent: Optional["Category"] = Relationship(
        back_populates="subcategories",
        sa_relationship_kwargs=dict(remote_side="Category.id"),
    )
    subcategories: List["Category"] = Relationship(back_populates="parent")
    posts: List["Post"] = Relationship(back_populates="category")
    
    # Many-to-many relationship for topics
    topic_posts: List["Post"] = Relationship(back_populates="topics", link_model=PostCategoryLink)


class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None


class CategoryRead(CategoryBase):
    id: int
    parent_id: Optional[int] = None


class PostBase(SQLModel):
    title: str
    description: str
    image: Optional[str] = None
    video_url: Optional[str] = None
    status: PostStatus = Field(default=PostStatus.DRAFT)


class Post(PostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    last_modified: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship(back_populates="posts")

    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="posts")

    topics: List[Category] = Relationship(back_populates="topic_posts", link_model=PostCategoryLink)


class PostCreate(PostBase):
    topic_ids: List[int]
    category_id: Optional[int] = None
    status: Optional[PostStatus] = None


class PostUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic_ids: Optional[List[int]] = None
    category_id: Optional[int] = None
    status: Optional[PostStatus] = None
    image: Optional[str] = None
    video_url: Optional[str] = None





class PostRead(PostBase):
    id: int
    created_at: datetime.datetime
    last_modified: datetime.datetime
    author: UserRead
    category: Optional[CategoryRead] = None
    topics: List[CategoryRead] = []
    status: Optional[PostStatus] = None


class PostSyncResponse(SQLModel):
    posts: List[PostRead]
    category_counts: Dict[int, int]


# Comment Models
class CommentBase(SQLModel):
    content: str


class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    
    post_id: int = Field(foreign_key="post.id")
    author_id: int = Field(foreign_key="user.id")


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    created_at: datetime.datetime
    author: UserRead
    post_id: int


# Bookmark Models
class Bookmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    
    post_id: int = Field(foreign_key="post.id")
    user_id: int = Field(foreign_key="user.id")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class BookmarkCreate(SQLModel):
    post_id: int


class BookmarkRead(SQLModel):
    id: int
    created_at: datetime.datetime
    post: PostRead

