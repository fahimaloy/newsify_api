from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
import datetime
import enum


class Role(str, enum.Enum):
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
    role: Role = Field(default=Role.WRITER)
    post_review_before_publish: bool = Field(default=False)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    posts: List["Post"] = Relationship(back_populates="author")


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


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


class PostRead(PostBase):
    id: int
    created_at: datetime.datetime
    last_modified: datetime.datetime
    author: UserRead
    category: Optional[CategoryRead] = None
    topics: List[CategoryRead] = []
    status: Optional[PostStatus] = None
