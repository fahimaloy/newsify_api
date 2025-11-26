#!/usr/bin/env python3
"""
Script to seed categories into the database.
Usage: python seed_categories.py
"""
import sys
import os

# Add the src directory to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import Category
from cj36.core.seed_data import DEFAULT_CATEGORIES

def seed_categories():
    """Seed categories from DEFAULT_CATEGORIES"""
    try:
        with Session(engine) as session:
            print("Checking existing categories...")
            statement = select(Category)
            existing_categories = session.exec(statement).first()
            
            if existing_categories:
                print("Categories already exist in database.")
                response = input("Do you want to add missing categories? (y/n): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return

            print("Seeding categories...")
            count = 0
            for cat_data in DEFAULT_CATEGORIES:
                # Check if parent exists
                parent = session.exec(select(Category).where(Category.name == cat_data["name"])).first()
                
                if not parent:
                    # Create parent category
                    parent = Category(
                        name=cat_data["name"],
                        bn_name=cat_data["bn_name"]
                    )
                    session.add(parent)
                    session.commit()
                    session.refresh(parent)
                    print(f"Created parent category: {parent.name}")
                    count += 1
                
                # Create children
                for child_data in cat_data["children"]:
                    child = session.exec(select(Category).where(
                        Category.name == child_data["name"],
                        Category.parent_id == parent.id
                    )).first()
                    
                    if not child:
                        child = Category(
                            name=child_data["name"],
                            bn_name=child_data["bn_name"],
                            parent_id=parent.id
                        )
                        session.add(child)
                        print(f"  - Created subcategory: {child.name}")
                        count += 1
            
            session.commit()
            print(f"\nSuccessfully seeded/updated {count} categories.")
            
    except Exception as e:
        print(f"Error seeding categories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("CJ36 Category Seeder")
    print("=" * 60)
    seed_categories()
