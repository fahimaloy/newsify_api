"""
Scheduler module for background tasks.
This runs within the FastAPI application and works on both cPanel and VPS.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import Post, PostStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = BackgroundScheduler()


def publish_scheduled_posts():
    """
    Check for scheduled posts that are due and publish them.
    This function runs every minute via the scheduler.
    """
    try:
        with Session(engine) as session:
            now = datetime.datetime.utcnow()
            
            # Find all posts with status SCHEDULED and scheduled_at <= now
            query = select(Post).where(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_at <= now,
                Post.scheduled_at.is_not(None)
            )
            
            due_posts = session.exec(query).all()
            
            if not due_posts:
                logger.debug(f"[{now.isoformat()}] No scheduled posts due for publication.")
                return
            
            logger.info(f"[{now.isoformat()}] Found {len(due_posts)} scheduled post(s) to publish:")
            
            for post in due_posts:
                logger.info(f"  - Publishing post #{post.id}: '{post.title[:50]}...'")
                post.status = PostStatus.PUBLISHED
                session.add(post)
            
            session.commit()
            logger.info(f"[{now.isoformat()}] Successfully published {len(due_posts)} post(s).")
            
    except Exception as e:
        logger.error(f"Error publishing scheduled posts: {e}", exc_info=True)


def start_scheduler():
    """
    Start the background scheduler.
    Called when the FastAPI application starts.
    """
    # Add job to run every minute
    scheduler.add_job(
        func=publish_scheduled_posts,
        trigger=IntervalTrigger(minutes=1),
        id='publish_scheduled_posts',
        name='Publish scheduled posts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Background scheduler started successfully")
    logger.info("📅 Scheduled job: Publish posts every 1 minute")


def shutdown_scheduler():
    """
    Shutdown the background scheduler.
    Called when the FastAPI application shuts down.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background scheduler shut down")
