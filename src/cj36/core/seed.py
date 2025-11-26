"""
Database seeding utilities.
"""
from sqlmodel import Session, select
from cj36.models import Category, User, UserType, AdminType, Role
from cj36.core.seed_data import DEFAULT_CATEGORIES
from cj36.core.security import get_password_hash


def seed_database(session: Session) -> None:
    """
    Seed the database.
    Currently empty as seeding is done manually via scripts:
    - create_admin.py
    - seed_categories.py
    """
    pass
