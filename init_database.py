#!/usr/bin/env python3
"""
Initialize database for cPanel deployment
Run this script after uploading to cPanel to set up the database
"""
import sys
import os

# Add the src directory to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def init_database():
    """Initialize database tables and seed initial data"""
    try:
        from sqlmodel import SQLModel, Session
        from cj36.dependencies import engine
        from cj36.core.seed import seed_database
        
        print("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        print("✓ Tables created successfully")
        
        print("\nSeeding initial data...")
        with Session(engine) as session:
            seed_database(session)
        print("✓ Initial data seeded successfully")
        
        print("\n✓ Database initialization complete!")
        print("\nNext steps:")
        print("1. Create an admin user using create_admin.py")
        print("2. Restart your application")
        print("3. Test the /health endpoint")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct database credentials")
        print("2. Verify PostgreSQL is running")
        print("3. Ensure database exists and user has permissions")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CJ36 Database Initialization")
    print("=" * 60)
    print()
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("✗ Error: .env file not found!")
        print("Please create .env file with your database credentials")
        print("See .env.example for reference")
        sys.exit(1)
    
    success = init_database()
    sys.exit(0 if success else 1)
