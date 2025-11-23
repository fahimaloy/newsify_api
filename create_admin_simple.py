#!/usr/bin/env python3
"""
Script to create an admin user for the CJ36 application without email verification.
Usage: uv run python create_admin_simple.py
"""
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import User, UserType, AdminType, Role
from cj36.core.security import get_password_hash

def create_admin_user():
    print("=" * 60)
    print("Create Admin User (Simple)")
    print("=" * 60)
    
    username = "admin"
    email = "admin@example.com"
    password = "password123"
    name = "System Admin"
    
    try:
        with Session(engine) as session:
            # Check if user already exists
            statement = select(User).where(User.username == username)
            existing_user = session.exec(statement).first()
            if existing_user:
                print(f"User {username} already exists.")
                return

            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                full_name=name,
                hashed_password=hashed_password,
                user_type=UserType.ADMINISTRATOR,
                admin_type=AdminType.ADMIN,
                role=Role.ADMIN,
                is_verified=True,
                post_review_before_publish=False
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            print(f"Admin user created: {username} / {password}")
            
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    create_admin_user()
