import subprocess
import os
import sys

# Delete test.db if exists
if os.path.exists("test.db"):
    os.remove("test.db")

# Set environment variable for SQLite
env = os.environ.copy()
env["DATABASE_URL"] = "sqlite:///./test.db"

# Print routes
code = """
from cj36.main import app
for route in app.routes:
    try:
        print(f"{route.methods} {route.path}")
    except AttributeError:
        print(f"Mount: {route.path}")
"""

with open("debug_output.txt", "w") as f:
    f.write(f"CWD: {os.getcwd()}\n")
    try:
        # Print routes
        f.write("Routes:\n")
        routes_output = subprocess.check_output(["uv", "run", "python", "-c", code], text=True, stderr=subprocess.STDOUT, env=env)
        f.write(routes_output)
        f.write("\nRunning Tests:\n")
        
        # Run pytest
        output = subprocess.check_output(["uv", "run", "python", "-m", "pytest", "-vv"], text=True, stderr=subprocess.STDOUT, env=env)
        f.write(output)
    except subprocess.CalledProcessError as e:
        f.write(f"Error: {e.output}")
    except Exception as e:
        f.write(f"Error: {e}")
