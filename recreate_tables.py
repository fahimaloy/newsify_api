#!/usr/bin/env python3
"""
Script to recreate database tables with the new schema.
Usage: uv run python recreate_tables.py
"""
from sqlmodel import SQLModel
from cj36.dependencies import engine

def recreate_tables():
    """Drop all tables and recreate them with the current schema."""
    print("=" * 60)
    print("Recreating Database Tables")
    print("=" * 60)
    print()
    
    response = input("⚠️  This will DELETE all existing data. Continue? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Operation cancelled.")
        return
    
    print("\n🗑️  Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("✅ Tables dropped successfully!")
    
    print("\n🔨 Creating tables with new schema...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created successfully!")
    
    print()
    print("=" * 60)
    print("✅ Database schema updated!")
    print("=" * 60)
    print("\nYou can now run 'uv run python create_admin.py' to create an admin user.")
    print("=" * 60)

if __name__ == "__main__":
    recreate_tables()
