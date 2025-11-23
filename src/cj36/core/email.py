import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cj36.core.config import settings

def send_email(to_email: str, subject: str, html_content: str):
    """
    Send an email using SMTP.
    """
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = to_email

        part = MIMEText(html_content, "html")
        message.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAILS_FROM_EMAIL, to_email, message.as_string()
            )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_verification_email(to_email: str, code: str):
    """
    Send verification code email.
    """
    subject = "Verify your Channel July 36 account"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #C62828; text-align: center;">Welcome to Channel July 36!</h2>
                <p>Thank you for registering. Please use the following verification code to verify your account:</p>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style="margin: 0; letter-spacing: 5px; color: #333;">{code}</h1>
                </div>
                <p>If you did not create an account, please ignore this email.</p>
                <br>
                <p style="font-size: 12px; color: #888; text-align: center;">
                    &copy; 2025 Channel July 36. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, html_content)

def send_password_reset_email(to_email: str, code: str):
    """
    Send password reset OTP email.
    """
    subject = "Reset your Channel July 36 password"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #C62828; text-align: center;">Password Reset Request</h2>
                <p>We received a request to reset your password. Use the following OTP to proceed:</p>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style="margin: 0; letter-spacing: 5px; color: #333;">{code}</h1>
                </div>
                <p>If you did not request a password reset, please ignore this email.</p>
                <br>
                <p style="font-size: 12px; color: #888; text-align: center;">
                    &copy; 2025 Channel July 36. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, html_content)
