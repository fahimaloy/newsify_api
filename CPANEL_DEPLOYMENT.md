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
3. Create a new database: `username_cj36`
4. Create a database user: `username_cj36user`
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
ssh username@yourserver.com

# Navigate to your home directory
cd ~

# Create application directory
mkdir -p cj36-backend
cd cj36-backend

# Upload files using SCP from your local machine
# (Run this from your local machine, not on server)
scp -r /path/to/cj36/backend/* username@yourserver.com:~/cj36-backend/
```

#### Option B: Using File Manager

1. In cPanel, go to **File Manager**
2. Navigate to your home directory
3. Create folder: `cj36-backend`
4. Upload all files from your local `backend` folder
5. Extract if uploaded as ZIP

### 3. Set Up Python Application in cPanel

#### 3.1 Create Python App

1. In cPanel, go to **Setup Python App**
2. Click **Create Application**
3. Configure:

   - **Python version**: 3.11 or higher
   - **Application root**: `cj36-backend`
   - **Application URL**: Choose your domain/subdomain (e.g., `api.yourdomain.com`)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

4. Click **Create**

#### 3.2 Note the Virtual Environment Path

cPanel will show you the command to activate the virtual environment:

```bash
source /home/username/virtualenv/cj36-backend/3.11/bin/activate
```

### 4. Install Dependencies

#### Via SSH (Recommended)

```bash
# SSH into your server
ssh username@yourserver.com

# Activate virtual environment
source /home/username/virtualenv/cj36-backend/3.11/bin/activate

# Navigate to app directory
cd ~/cj36-backend

# Install dependencies
pip install -r requirements.txt

# Or if using uv (if available)
pip install uv
uv sync
```

#### Via cPanel Terminal

1. In cPanel, go to **Terminal**
2. Run the same commands as above

### 5. Create requirements.txt

If you don't have a `requirements.txt`, create one:

```bash
cd ~/cj36-backend
source /home/username/virtualenv/cj36-backend/3.11/bin/activate

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
EOF

pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create `.env` file in your application root:

```bash
cd ~/cj36-backend
nano .env
```

Add the following (replace with your actual values):

```bash
# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=your-generated-secret-key-here

# Database (use your cPanel database details)
DB_HOST=localhost
DB_USER=username_cj36user
DB_PASSWORD=your-database-password
DB_NAME=username_cj36
DB_PORT=5432

# Email (use your email settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com

# CORS (use your actual domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

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
source /home/username/virtualenv/cj36-backend/3.11/bin/activate

# Navigate to app directory
cd ~/cj36-backend

# Run database initialization
python3 -c "
from sqlmodel import SQLModel, Session
from src.cj36.dependencies import engine
from src.cj36.core.seed import seed_database

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
cd ~/cj36-backend
mkdir -p static/uploads
chmod 755 static
chmod 755 static/uploads
```

### 9. Configure Passenger

The `passenger_wsgi.py` file is already configured. Verify it exists:

```bash
cd ~/cj36-backend
cat passenger_wsgi.py
```

### 10. Set File Permissions

```bash
cd ~/cj36-backend

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
cd ~/cj36-backend
touch tmp/restart.txt
```

### 12. Verify Deployment

Test your API:

```bash
# Test health endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {"status":"healthy","message":"API is running","version":"0.1.0","environment":"production"}
```

## Troubleshooting

### Application Not Starting

1. **Check Error Logs**

```bash
tail -f ~/cj36-backend/tmp/error.log
```

2. **Check Passenger Log**

```bash
tail -f ~/logs/passenger.log
```

3. **Verify Python Version**

```bash
source /home/username/virtualenv/cj36-backend/3.11/bin/activate
python --version
```

### Database Connection Issues

1. **Test Database Connection**

```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='username_cj36',
    user='username_cj36user',
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
cd ~/cj36-backend
python3 -c "import sys; print('\n'.join(sys.path))"
```

2. **Reinstall Dependencies**

```bash
source /home/username/virtualenv/cj36-backend/3.11/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Permission Errors

```bash
cd ~/cj36-backend
chmod -R 755 .
chmod 644 .env
```

## Setting Up Scheduled Tasks (Cron Jobs)

For scheduled post publishing:

1. In cPanel, go to **Cron Jobs**
2. Add a new cron job:

```bash
# Run every minute to publish scheduled posts
* * * * * source /home/username/virtualenv/cj36-backend/3.11/bin/activate && cd /home/username/cj36-backend && python3 publish_scheduled_posts.py >> /home/username/cj36-backend/cron.log 2>&1
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
cd ~/cj36-backend
cat > .passenger << EOF
{
  "app_type": "python",
  "startup_file": "passenger_wsgi.py",
  "python": "/home/username/virtualenv/cj36-backend/3.11/bin/python3",
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
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/health/scheduler
```

### View Logs

```bash
# Application logs
tail -f ~/cj36-backend/tmp/error.log

# Passenger logs
tail -f ~/logs/passenger.log

# Cron logs
tail -f ~/cj36-backend/cron.log
```

## Updating the Application

```bash
# SSH into server
ssh username@yourserver.com

# Activate virtual environment
source /home/username/virtualenv/cj36-backend/3.11/bin/activate

# Navigate to app directory
cd ~/cj36-backend

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
BACKUP_DIR="/home/username/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump username_cj36 | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-db.sh

# Add to cron (daily at 2 AM)
# 0 2 * * * /home/username/backup-db.sh
```

### Application Backup

```bash
# Backup application files
tar -czf ~/backups/cj36-backend-$(date +%Y%m%d).tar.gz ~/cj36-backend
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
