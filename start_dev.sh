#!/bin/bash
# Quick start script for local development
# This demonstrates that the scheduler works automatically

echo "🚀 Starting Channel July 36 Backend with Integrated Scheduler"
echo "=============================================================="
echo ""
echo "The background scheduler will start automatically!"
echo "It will check for scheduled posts every minute."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"

# Start the FastAPI server
uv run uvicorn src.cj36.main:app --reload --host 0.0.0.0 --port 8000
