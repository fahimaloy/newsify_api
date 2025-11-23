"""
Add comments and bookmarks tables to the database
"""
from sqlmodel import SQLModel, create_engine
from cj36.models import Comment, Bookmark
from cj36.database import engine

def add_tables():
    print("Creating comments and bookmarks tables...")
    SQLModel.metadata.create_all(engine, tables=[Comment.__table__, Bookmark.__table__])
    print("Tables created successfully!")

if __name__ == "__main__":
    add_tables()
