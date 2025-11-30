# cPanel Deployment Guide for CJ36 Backend

## Prerequisites

- cPanel account with Python App support (Passenger)
- PostgreSQL database access
- SSH access (recommended)
- Python 3.11 or higher

## Step-by-Step Deployment

### 1. Prepare Your cPanel Account

#### 1.1 Create PostgreSQL Database

1. Log into cPanel
2. Go to **MySQL Databases** or **PostgreSQL Databases**
3. Create a new database: `priteqvf_cj36_db`
4. Create a database user: `priteqvf_cj36_user`
5. Set a strong password
6. Add user to database with ALL PRIVILEGES
7. Note down:
   - Database name
   - Database user
   - Database password
   - Database host (usually `localhost`)

#### 1.2 Enable SSH Access (Recommended)

1. In cPanel, go to **SSH Access**
2. Generate SSH key or use password
3. Note your SSH details

### 2. Upload Application Files

#### Option A: Using SSH (Recommended)

```bash
# Connect to your server
ssh priteqvf@api.cj36.prithibistudio.com

# Navigate to your home directory
cd ~

# Create application directory
mkdir -p api.cj36.prithibistudio.com
cd api.cj36.prithibistudio.com

# Upload files using SCP from your local machine
# (Run this from your local machine, not on server)
scp -r /path/to/cj36/backend/* priteqvf@api.cj36.prithibistudio.com:~/api.cj36.prithibistudio.com/
```

#### Option B: Using File Manager

1. In cPanel, go to **File Manager**
2. Navigate to your home directory
3. Create folder: `api.cj36.prithibistudio.com`
4. Upload all files from your local `backend` folder
5. Extract if uploaded as ZIP

### 3. Set Up Python Application in cPanel

#### 3.1 Create Python App

1. In cPanel, go to **Setup Python App**
2. Click **Create Application**
3. Configure:

   - **Python version**: 3.11 or 3.12 (Recommended - 3.14 may cause build issues)
   - **Application root**: `api.cj36.prithibistudio.com`
   - **Application URL**: Choose your domain/subdomain (e.g., `api.cj36.prithibistudio.com`)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

4. Click **Create**

#### 3.2 Note the Virtual Environment Path

cPanel will show you the command to activate the virtual environment:

```bash
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate
```

### 4. Install Dependencies

#### Via SSH (Recommended)

```bash
# SSH into your server
ssh priteqvf@api.cj36.prithibistudio.com

# Activate virtual environment
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate

# Navigate to app directory
cd ~/api.cj36.prithibistudio.com

# Install dependencies
pip install -r requirements.txt

```

#### Via cPanel Terminal

1. In cPanel, go to **Terminal**
2. Run the same commands as above

### 5. Create requirements.txt

If you don't have a `requirements.txt`, create one:

```bash
cd ~/api.cj36.prithibistudio.com
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate

# Generate from pyproject.toml
pip install pip-tools
pip-compile pyproject.toml -o requirements.txt

# Or manually create requirements.txt with:
cat > requirements.txt << EOF
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic-settings>=2.5.0
python-dotenv>=1.0.0
asyncpg>=0.29.0
sqlmodel>=0.0.19
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.9
psycopg2-binary>=2.9.9
psutil>=6.0.0
bcrypt<4.0.0
apscheduler>=3.11.1
a2wsgi>=1.10.0
EOF

pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create `.env` file in your application root:

```bash
cd ~/api.cj36.prithibistudio.com
nano .env
```

Add the following (replace with your actual values):

```bash
# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=your-generated-secret-key-here

# Database (use your cPanel database details)
DB_HOST=127.0.0.1
DB_USER=priteqvf_cj36user
DB_PASSWORD=your-database-password
DB_NAME=priteqvf_cj36
DB_PORT=5432

# Email (use your email settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@cj36.prithibistudio.com

# CORS (use your actual domain)
CORS_ORIGINS=*

# API
API_V1_STR=/api/v1
```

**Important**: Generate a secure SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 7. Set Up Database

```bash
# Activate virtual environment
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate

# Navigate to app directory
cd ~/api.cj36.prithibistudio.com

# Run database initialization
python3 -c "
import sys
import os
sys.path.insert(0, 'src')
from sqlmodel import SQLModel, Session
from cj36.dependencies import engine
from cj36.core.seed import seed_database

# Create tables
SQLModel.metadata.create_all(engine)

# Seed initial data
with Session(engine) as session:
    seed_database(session)

print('Database initialized successfully!')
"
```

### 8. Create Static Files Directory

```bash
cd ~/api.cj36.prithibistudio.com
mkdir -p static/uploads
chmod 755 static
chmod 755 static/uploads
```

### 9. Configure Passenger

The default `passenger_wsgi.py` created by cPanel is incorrect. Replace it with:

```python
cat > passenger_wsgi.py << 'EOF'
import sys
import os

# Get the current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the src directory to Python path so we can import cj36
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(CURRENT_DIR, '.env'))

# Import the FastAPI application
from cj36.main import app as asgi_app

# Convert ASGI to WSGI for Passenger
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(asgi_app)
EOF
```

### 10. Set File Permissions

```bash
cd ~/api.cj36.prithibistudio.com

# Set correct permissions
chmod 755 passenger_wsgi.py
chmod 644 .env
chmod -R 755 src
chmod -R 755 static
```

### 11. Restart Application

#### Via cPanel

1. Go to **Setup Python App**
2. Find your application
3. Click **Restart** button

#### Via SSH

```bash
cd ~/api.cj36.prithibistudio.com
touch tmp/restart.txt
```

### 12. Verify Deployment

Test your API:

```bash
# Test health endpoint
curl https://api.cj36.prithibistudio.com/health

# Expected response:
# {"status":"healthy","message":"API is running","version":"0.1.0","environment":"production"}
```

## Troubleshooting

### Application Not Starting

1. **Check Error Logs**

```bash
tail -f ~/api.cj36.prithibistudio.com/stderr.log
```

2. **Check Passenger Log**

```bash
tail -f ~/api.cj36.prithibistudio.com/startup.log
```

3. **Verify Python Version**

```bash
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate
python --version
```

### Database Connection Issues

1. **Test Database Connection**

```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='priteqvf_cj36',
    user='priteqvf_cj36user',
    password='your-password'
)
print('Database connection successful!')
conn.close()
"
```

2. **Check PostgreSQL is Running**

```bash
ps aux | grep postgres
```

### Import Errors

1. **Verify Python Path**

```bash
cd ~/api.cj36.prithibistudio.com
python3 -c "import sys; print('\n'.join(sys.path))"
```

2. **Reinstall Dependencies**

```bash
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Permission Errors

```bash
cd ~/api.cj36.prithibistudio.com
chmod -R 755 .
chmod 644 .env
```

## Setting Up Scheduled Tasks (Cron Jobs)

For scheduled post publishing:

1. In cPanel, go to **Cron Jobs**
2. Add a new cron job:

```bash
# Run every minute to publish scheduled posts
* * * * * source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate && cd /home/priteqvf/api.cj36.prithibistudio.com && python3 publish_scheduled_posts.py >> /home/priteqvf/api.cj36.prithibistudio.com/cron.log 2>&1
```

## SSL/HTTPS Setup

1. In cPanel, go to **SSL/TLS Status**
2. Enable AutoSSL for your domain
3. Or install Let's Encrypt certificate
4. Verify HTTPS is working

## Performance Optimization

### 1. Enable OPcache (if available)

In cPanel PHP settings, enable OPcache

### 2. Configure Passenger

Create `.passenger` file in app root:

```bash
cd ~/api.cj36.prithibistudio.com
cat > .passenger << EOF
{
  "app_type": "python",
  "startup_file": "passenger_wsgi.py",
  "python": "/home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/python3",
  "environment": "production",
  "max_pool_size": 6,
  "min_instances": 2,
  "max_instances": 6
}
EOF
```

### 3. Enable Compression

Already enabled in the application (GZip middleware)

## Monitoring

### Check Application Status

```bash
# Via cPanel: Setup Python App > View application status

# Via SSH:
curl https://api.cj36.prithibistudio.com/health
curl https://api.cj36.prithibistudio.com/health/scheduler
```

### View Logs

```bash
# Application logs
tail -f ~/api.cj36.prithibistudio.com/stderr.log

# Passenger logs
tail -f ~/api.cj36.prithibistudio.com/startup.log

# Cron logs
tail -f ~/api.cj36.prithibistudio.com/cron.log
```

## Updating the Application

```bash
# SSH into server
ssh priteqvf@api.cj36.prithibistudio.com

# Activate virtual environment
source /home/priteqvf/virtualenv/api.cj36.prithibistudio.com/3.11/bin/activate

# Navigate to app directory
cd ~/api.cj36.prithibistudio.com

# Pull latest changes (if using git)
git pull origin main

# Or upload new files via SCP/File Manager

# Install any new dependencies
pip install -r requirements.txt

# Restart application
touch tmp/restart.txt
```

## Backup Strategy

### Database Backup

```bash
# Create backup script
cat > ~/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/priteqvf/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump priteqvf_cj36 | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-db.sh

# Add to cron (daily at 2 AM)
# 0 2 * * * /home/priteqvf/backup-db.sh
```

### Application Backup

```bash
# Backup application files
tar -czf ~/backups/api.cj36.prithibistudio.com-$(date +%Y%m%d).tar.gz ~/api.cj36.prithibistudio.com
```

## Security Checklist

- [x] `.env` file has correct permissions (644)
- [x] SECRET_KEY is strong and unique
- [x] Database password is strong
- [x] CORS_ORIGINS is set to your domain only
- [x] ENVIRONMENT is set to "production"
- [x] HTTPS is enabled
- [x] API docs are disabled in production
- [x] File permissions are correct
- [x] Regular backups are configured

## Common cPanel-Specific Issues

### Issue: Module Not Found

**Solution**: Ensure virtual environment is activated and dependencies are installed

### Issue: Database Connection Refused

**Solution**: Check if PostgreSQL is running and credentials are correct

### Issue: Static Files Not Serving

**Solution**: Verify static directory exists and has correct permissions

### Issue: Application Keeps Restarting

**Solution**: Check error logs for Python errors, fix and restart

## Support

If you encounter issues:

1. Check error logs first
2. Verify all environment variables are set
3. Test database connection
4. Contact your hosting provider's support
5. Check cPanel documentation for Python apps

## Additional Resources

- [cPanel Python App Documentation](https://docs.cpanel.net/cpanel/software/python-selector/)
- [Passenger Documentation](https://www.phusionpassenger.com/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
