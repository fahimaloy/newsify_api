from sqlmodel import Session, create_engine, select
from cj36.models import Post

sqlite_url = "sqlite:///cj36.db"
engine = create_engine(sqlite_url)

def check_posts():
    with Session(engine) as session:
        posts = session.exec(select(Post)).all()
        print(f"Total posts: {len(posts)}")
        for post in posts:
            print(f"ID: {post.id}, Title: {post.title}, Status: {post.status}")

if __name__ == "__main__":
    check_posts()
