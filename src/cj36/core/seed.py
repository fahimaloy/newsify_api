"""
Database seeding utilities.
"""
from sqlmodel import Session, select
from cj36.models import Category, User, UserType, AdminType, Role
from cj36.core.seed_data import DEFAULT_CATEGORIES
from cj36.core.security import get_password_hash


def seed_database(session: Session) -> None:
    """
    Seed the database with default categories and an admin user if they don't exist.
    This runs on application startup.
    """
    # Seed Categories
    statement = select(Category)
    existing_categories = session.exec(statement).first()
    
    if not existing_categories:
        print("Seeding categories...")
        for cat_data in DEFAULT_CATEGORIES:
            # Create parent category
            parent = Category(
                name=cat_data["name"],
                bn_name=cat_data["bn_name"]
            )
            session.add(parent)
            session.commit()
            session.refresh(parent)
            
            # Create children
            for child_data in cat_data["children"]:
                child = Category(
                    name=child_data["name"],
                    bn_name=child_data["bn_name"],
                    parent_id=parent.id
                )
                session.add(child)
        session.commit()
        print("Categories seeded successfully.")
    else:
        print("Categories already exist in database. Skipping category seed.")

    # Seed Admin User
    statement = select(User).where(User.username == "admin")
    existing_admin = session.exec(statement).first()
    
    if not existing_admin:
        print("Seeding admin user...")
        admin_user = User(
            username="admin",
            email="admin@cj36.com",
            hashed_password=get_password_hash("admin123"),
            user_type=UserType.ADMINISTRATOR,
            admin_type=AdminType.ADMIN,
            role=Role.ADMIN,  # Required by DB constraint (deprecated field)
            post_review_before_publish=False,
            newsletter_subscribed=False
        )
        session.add(admin_user)
        session.commit()
        print("Admin user seeded successfully.")
    else:
        print("Admin user already exists in database. Skipping admin user seed.")
