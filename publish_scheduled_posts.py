#!/usr/bin/env python3
"""
Background job to publish scheduled posts.
This should be run periodically (e.g., every minute via cron or systemd timer).

Usage: uv run python publish_scheduled_posts.py
"""
import datetime
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import Post, PostStatus


def publish_scheduled_posts():
    """Check for scheduled posts that are due and publish them."""
    with Session(engine) as session:
        # Find all posts with status SCHEDULED and scheduled_at <= now
        now = datetime.datetime.utcnow()
        
        query = select(Post).where(
            Post.status == PostStatus.SCHEDULED,
            Post.scheduled_at <= now,
            Post.scheduled_at.is_not(None)
        )
        
        due_posts = session.exec(query).all()
        
        if not due_posts:
            print(f"[{now.isoformat()}] No scheduled posts due for publication.")
            return
        
        print(f"[{now.isoformat()}] Found {len(due_posts)} scheduled post(s) to publish:")
        
        for post in due_posts:
            print(f"  - Publishing post #{post.id}: '{post.title[:50]}...'")
            post.status = PostStatus.PUBLISHED
            session.add(post)
        
        session.commit()
        print(f"[{now.isoformat()}] Successfully published {len(due_posts)} post(s).")


if __name__ == "__main__":
    try:
        publish_scheduled_posts()
    except Exception as e:
        print(f"Error publishing scheduled posts: {e}")
        raise
