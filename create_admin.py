#!/usr/bin/env python3
"""
Script to create an admin user for the CJ36 application with email verification.
Usage: uv run python create_admin.py
"""
import sys
import random
import re
from getpass import getpass
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import User, UserType, AdminType, Role
from cj36.core.security import get_password_hash
from cj36.core.email import send_email


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(email: str, otp: str, name: str):
    """Send OTP verification email."""
    subject = "Admin Account Verification - Channel July 36"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #C62828 0%, #D32F2F 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .otp-box {{ background: white; border: 2px dashed #C62828; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
            .otp-code {{ font-size: 32px; font-weight: bold; color: #C62828; letter-spacing: 8px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Account Verification</h1>
                <p>Channel July 36</p>
            </div>
            <div class="content">
                <p>Hello {name},</p>
                <p>You are creating an admin account for Channel July 36. Please use the following OTP to verify your email address:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #666; font-size: 14px;">Your Verification Code</p>
                    <div class="otp-code">{otp}</div>
                </div>
                
                <p><strong>Important:</strong> This OTP is valid for this session only. Do not share it with anyone.</p>
                <p>If you did not request this, please ignore this email.</p>
                
                <div class="footer">
                    <p>© 2024 Channel July 36. All rights reserved.</p>
                    <p>তারুণ্যের কথা বলে</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    send_email(email, subject, html_content)


def create_admin_user():
    """Create an admin user interactively with email verification."""
    print("=" * 60)
    print("Create Admin User for Channel July 36")
    print("=" * 60)
    print()
    
    # Get name
    while True:
        name = input("Enter full name: ").strip()
        if not name:
            print("❌ Name cannot be empty!")
            continue
        if len(name) < 2:
            print("❌ Name must be at least 2 characters!")
            continue
        break
    
    # Get email
    while True:
        email = input("Enter email address: ").strip().lower()
        if not email:
            print("❌ Email cannot be empty!")
            continue
        if not validate_email(email):
            print("❌ Invalid email format!")
            continue
        break
    
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
    
    # Check if user already exists
    try:
        with Session(engine) as session:
            # Check username
            statement = select(User).where(User.username == username)
            existing_user = session.exec(statement).first()
            if existing_user:
                print(f"\n❌ Username '{username}' already exists!")
                sys.exit(1)
            
            # Check email
            statement = select(User).where(User.email == email)
            existing_email = session.exec(statement).first()
            if existing_email:
                print(f"\n❌ Email '{email}' is already registered!")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error checking existing users: {e}")
        sys.exit(1)
    
    # Generate and send OTP
    otp = generate_otp()
    print(f"\n📧 Sending verification code to {email}...")
    
    try:
        send_otp_email(email, otp, name)
        print("✅ Verification code sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("Please check your SMTP settings in the .env file.")
        sys.exit(1)
    
    # Verify OTP
    print("\n" + "=" * 60)
    print("Please check your email for the verification code.")
    print("=" * 60)
    
    max_attempts = 3
    for attempt in range(max_attempts):
        entered_otp = input(f"\nEnter verification code (Attempt {attempt + 1}/{max_attempts}): ").strip()
        
        if entered_otp == otp:
            print("✅ Email verified successfully!")
            break
        else:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"❌ Invalid code! {remaining} attempt(s) remaining.")
            else:
                print("❌ Maximum attempts reached. Please run the script again.")
                sys.exit(1)
    
    # Get password
    print()
    while True:
        password = getpass("Enter password: ")
        if not password:
            print("❌ Password cannot be empty!")
            continue
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            continue
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match!")
            continue
        break
    
    # Create user in database
    try:
        with Session(engine) as session:
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                full_name=name,
                hashed_password=hashed_password,
                user_type=UserType.ADMINISTRATOR,
                admin_type=AdminType.ADMIN,
                role=Role.ADMIN,  # Required by DB constraint (deprecated field)
                is_verified=True,  # Email already verified
                post_review_before_publish=False  # Admins don't need review
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            print()
            print("=" * 60)
            print("✅ Admin user created successfully!")
            print("=" * 60)
            print(f"Name: {new_user.full_name}")
            print(f"Email: {new_user.email}")
            print(f"Username: {new_user.username}")
            print(f"User ID: {new_user.id}")
            print(f"User Type: {new_user.user_type}")
            print(f"Admin Type: {new_user.admin_type}")
            print()
            print("You can now login with your username/email and password.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
