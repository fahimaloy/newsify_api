"""
Passenger WSGI file for cPanel deployment.
This file is required by cPanel's Passenger to run the FastAPI application.
"""
import sys
import os

# Get the current directory (where this file is located)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the src directory to Python path
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src'))
sys.path.insert(0, CURRENT_DIR)

# Set up virtual environment (cPanel creates this automatically)
# The path will be something like: /home/username/virtualenv/app_name/3.x/bin/python
VENV_PATH = os.path.join(os.environ.get('HOME', ''), 'virtualenv', 'cj36-backend', '3.11', 'bin', 'python3')

# If running in cPanel's virtual environment, use it
if os.path.exists(VENV_PATH) and sys.executable != VENV_PATH:
    os.execl(VENV_PATH, VENV_PATH, *sys.argv)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(CURRENT_DIR, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Import the FastAPI application
try:
    from cj36.main import app as application
except ImportError:
    # Fallback import path
    from src.cj36.main import app as application

# Passenger expects an 'application' callable
# FastAPI's app object is ASGI-compatible and works with Passenger 6+
