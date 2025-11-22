#!/usr/bin/env python3
"""
Script to create an admin user for the CJ36 application.
Usage: uv run python create_admin.py
"""
import sys
from getpass import getpass
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import User, Role
from cj36.core.security import get_password_hash


def create_admin_user():
    """Create an admin user interactively."""
    print("=" * 50)
    print("Create Admin User for Channel July 36")
    print("=" * 50)
    print()
    
    # Get username
    while True:
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            continue
        if len(username) < 3:
            print("❌ Username must be at least 3 characters!")
            continue
        break
    
    # Get password
    while True:
        password = getpass("Enter password: ")
        if not password:
            print("❌ Password cannot be empty!")
            continue
        if len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            continue
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match!")
            continue
        break
    
    # Create user in database
    try:
        with Session(engine) as session:
            # Check if username already exists
            statement = select(User).where(User.username == username)
            existing_user = session.exec(statement).first()
            
            if existing_user:
                print(f"\n❌ User '{username}' already exists!")
                sys.exit(1)
            
            # Create new admin user
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                hashed_password=hashed_password,
                role=Role.ADMIN,
                post_review_before_publish=False  # Admins don't need review
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            print()
            print("=" * 50)
            print("✅ Admin user created successfully!")
            print("=" * 50)
            print(f"Username: {new_user.username}")
            print(f"User ID: {new_user.id}")
            print(f"Role: {new_user.role}")
            print()
            print("You can now login with these credentials.")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n❌ Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
