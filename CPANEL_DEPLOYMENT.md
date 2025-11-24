# cPanel Deployment Guide for Channel July 36 Backend

## Overview

This guide covers deploying the FastAPI backend to cPanel hosting with integrated background job scheduling. The scheduler runs automatically within the FastAPI application - no separate cron jobs needed!

---

## Prerequisites

### cPanel Requirements

- Python 3.11+ support
- SSH access (recommended but not required)
- File Manager or FTP access
- MySQL/PostgreSQL database (or use SQLite)

### Local Setup

Ensure you have:

```bash
uv sync  # Install all dependencies including apscheduler
```

---

## Step 1: Prepare Your Application

### 1.1 Update Dependencies

The `apscheduler` package has been added to `pyproject.toml`. Verify:

```bash
cd backend
uv sync
```

### 1.2 Configure Environment Variables

Create a `.env` file in your backend directory:

```env
# Database (use cPanel MySQL or SQLite)
DATABASE_URL=sqlite:///./cj36.db
# Or for MySQL:
# DATABASE_URL=mysql://username:password@localhost/database_name

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (update with your actual domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Step 2: Package Your Application

### 2.1 Create Deployment Package

```bash
cd backend

# Create a clean directory for deployment
mkdir -p deploy
cp -r src deploy/
cp pyproject.toml deploy/
cp uv.lock deploy/
cp .env deploy/
cp -r static deploy/  # If you have static files

# Create requirements.txt for cPanel
uv pip compile pyproject.toml -o deploy/requirements.txt
```

### 2.2 Upload to cPanel

Use one of these methods:

**Option A: File Manager**

1. Login to cPanel
2. Go to File Manager
3. Navigate to your app directory (e.g., `/home/username/cj36-backend`)
4. Upload the `deploy` folder contents

**Option B: FTP**

1. Use FileZilla or similar FTP client
2. Upload to `/home/username/cj36-backend`

**Option C: SSH (Recommended)**

```bash
# From your local machine
scp -r deploy/* username@yourserver.com:/home/username/cj36-backend/
```

---

## Step 3: Setup Python App in cPanel

### 3.1 Create Python Application

1. Login to cPanel
2. Go to **"Setup Python App"** (under Software section)
3. Click **"Create Application"**

Configure:

- **Python Version**: 3.11 or higher
- **Application Root**: `/home/username/cj36-backend`
- **Application URL**: Choose your subdomain (e.g., `api.yourdomain.com`)
- **Application Startup File**: `src/cj36/main.py`
- **Application Entry Point**: `app`

### 3.2 Install Dependencies

In the Python App interface:

1. Click "Enter to the virtual environment"
2. Or use the command shown (e.g., `source /home/username/virtualenv/cj36-backend/3.11/bin/activate`)
3. Run:

```bash
pip install -r requirements.txt
```

### 3.3 Configure Passenger WSGI

cPanel uses Passenger to run Python apps. Create `passenger_wsgi.py` in your app root:

```python
import sys
import os

# Add your application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import your FastAPI app
from src.cj36.main import app as application

# Passenger expects 'application' variable
```

Upload this file to `/home/username/cj36-backend/passenger_wsgi.py`

---

## Step 4: Verify Scheduler is Running

### 4.1 Check Application Logs

In cPanel Python App interface, check the logs. You should see:

```
✅ Background scheduler started successfully
📅 Scheduled job: Publish posts every 1 minute
```

### 4.2 Test Scheduled Publishing

1. Create a post scheduled 2 minutes in the future
2. Wait 2-3 minutes
3. Check if the post status changed to "Published"
4. Check logs for: `Successfully published X post(s)`

---

## Step 5: Database Setup

### 5.1 Using SQLite (Simplest)

Already configured! The database file `cj36.db` will be created automatically.

### 5.2 Using cPanel MySQL (Recommended for Production)

1. In cPanel, go to **MySQL Databases**
2. Create a new database: `username_cj36`
3. Create a user and grant all privileges
4. Update `.env`:

```env
DATABASE_URL=mysql+pymysql://username_dbuser:password@localhost/username_cj36
```

5. Install MySQL driver:

```bash
pip install pymysql
```

---

## Step 6: Static Files Configuration

### 6.1 Serve Static Files

FastAPI serves static files from `/static` directory. Ensure:

```bash
mkdir -p /home/username/cj36-backend/static/images
chmod 755 /home/username/cj36-backend/static
```

### 6.2 Configure Passenger for Static Files

In `.htaccess` (created automatically by cPanel):

```apache
# Serve static files directly
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{REQUEST_URI} ^/static/
    RewriteRule ^(.*)$ - [L]
</IfModule>
```

---

## Step 7: Domain Configuration

### 7.1 Setup Subdomain

1. In cPanel, go to **Subdomains**
2. Create subdomain: `api.yourdomain.com`
3. Point it to `/home/username/cj36-backend`

### 7.2 SSL Certificate

1. Go to **SSL/TLS Status**
2. Enable AutoSSL for `api.yourdomain.com`
3. Or use Let's Encrypt

---

## Troubleshooting

### Scheduler Not Running

**Symptom**: Scheduled posts not auto-publishing

**Solution**:

1. Check application logs in cPanel
2. Verify scheduler started: Look for "Background scheduler started"
3. Restart the Python app in cPanel
4. Check for errors in error logs

### Application Won't Start

**Symptom**: 500 Internal Server Error

**Solution**:

1. Check `passenger_wsgi.py` exists
2. Verify Python version matches (3.11+)
3. Check error logs: `/home/username/logs/`
4. Ensure all dependencies installed: `pip list`

### Database Connection Errors

**Symptom**: "Could not connect to database"

**Solution**:

1. Verify `DATABASE_URL` in `.env`
2. Check database credentials
3. For MySQL: Ensure user has privileges
4. Test connection: `python -c "from sqlmodel import create_engine; engine = create_engine('your-url'); print('OK')"`

### Static Files Not Loading

**Symptom**: Images/uploads not displaying

**Solution**:

1. Check directory permissions: `chmod 755 static`
2. Verify path in code matches actual path
3. Check `.htaccess` configuration
4. Test direct URL: `https://api.yourdomain.com/static/images/test.jpg`

---

## Monitoring & Maintenance

### Check Scheduler Health

Create a health check endpoint (already in your app):

```python
# Add to main.py
@app.get("/health/scheduler")
async def scheduler_health():
    from cj36.scheduler import scheduler
    return {
        "running": scheduler.running,
        "jobs": [job.id for job in scheduler.get_jobs()]
    }
```

Access: `https://api.yourdomain.com/health/scheduler`

### View Logs

- Application logs: cPanel Python App interface
- Error logs: `/home/username/logs/`
- Scheduler logs: Check application stdout

### Restart Application

In cPanel Python App interface:

1. Click "Stop App"
2. Wait 5 seconds
3. Click "Start App"

Or via SSH:

```bash
touch /home/username/cj36-backend/tmp/restart.txt
```

---

## Migration to VPS (Future)

When you move to VPS, the scheduler will work **exactly the same** because it's integrated into the FastAPI app. No changes needed!

### VPS Deployment (Quick Guide)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn src.cj36.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with Uvicorn
uvicorn src.cj36.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The scheduler starts automatically when the app starts - no additional setup required!

---

## Security Checklist

Before going live:

- [ ] Change `SECRET_KEY` in `.env` to a strong random value
- [ ] Update `ALLOWED_ORIGINS` to your actual domain
- [ ] Enable SSL/HTTPS
- [ ] Set proper file permissions (644 for files, 755 for directories)
- [ ] Disable debug mode in production
- [ ] Setup database backups
- [ ] Configure firewall rules (VPS only)

---

## Support

If you encounter issues:

1. Check cPanel error logs
2. Review application logs
3. Test scheduler manually: `python -c "from src.cj36.scheduler import publish_scheduled_posts; publish_scheduled_posts()"`
4. Contact cPanel support for hosting-specific issues

---

## Summary

✅ **Scheduler runs automatically** - No cron jobs needed!
✅ **Works on cPanel** - Integrated with Passenger
✅ **Works on VPS** - No changes required when migrating
✅ **Production-ready** - Proper error handling and logging
✅ **Easy monitoring** - Health check endpoint included

Your scheduled posts will auto-publish every minute as long as the FastAPI application is running!
