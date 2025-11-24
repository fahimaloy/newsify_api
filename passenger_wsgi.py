"""
Passenger WSGI file for cPanel deployment.
This file is required by cPanel's Passenger to run the FastAPI application.
"""
import sys
import os

# Add your application directory to the Python path
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'cj36-backend', '3.11', 'bin', 'python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add the application directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI application
from src.cj36.main import app as application

# Passenger expects an 'application' callable
# FastAPI's app object is already ASGI-compatible and works with Passenger
