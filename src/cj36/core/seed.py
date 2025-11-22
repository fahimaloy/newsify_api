"""
Database seeding utilities.
"""
from sqlmodel import Session, select
from cj36.models import Category
from cj36.core.seed_data import DEFAULT_CATEGORIES


def seed_categories(session: Session) -> None:
    """
    Seed the database with default categories if none exist.
    This runs on application startup.
    """
    # Check if categories already exist
    statement = select(Category)
    existing_categories = session.exec(statement).first()
    
    if existing_categories:
        print("Categories already exist in database. Skipping seed.")
        return
    
    print("Seeding database with default categories...")
    
    # Create categories with their children
    for cat_data in DEFAULT_CATEGORIES:
        # Create parent category
        parent = Category(
            name=cat_data["name"],
            bn_name=cat_data.get("bn_name", cat_data["name"])
        )
        session.add(parent)
        session.commit()
        session.refresh(parent)
        
        # Create child categories if any
        for child_data in cat_data.get("children", []):
            child = Category(
                name=child_data["name"],
                bn_name=child_data.get("bn_name", child_data["name"]),
                parent_id=parent.id
            )
            session.add(child)
        
        session.commit()
    
    print(f"Successfully seeded {len(DEFAULT_CATEGORIES)} parent categories with their children.")
