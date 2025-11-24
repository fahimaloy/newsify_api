# Background Job Setup - Complete Solution

## ✅ What Was Implemented

### Integrated Scheduler (APScheduler)

The background job system is now **built into your FastAPI application**. This means:

- ✅ **No separate cron jobs needed**
- ✅ **Works on cPanel hosting** (Passenger compatible)
- ✅ **Works on VPS hosting** (no changes required)
- ✅ **Automatic startup/shutdown** with the app
- ✅ **Production-ready** with proper logging

---

## 📁 Files Created/Modified

### New Files:

1. **`src/cj36/scheduler.py`** - Background scheduler module
2. **`passenger_wsgi.py`** - cPanel Passenger configuration
3. **`CPANEL_DEPLOYMENT.md`** - Complete deployment guide
4. **`start_dev.sh`** - Local development script

### Modified Files:

1. **`src/cj36/main.py`** - Added scheduler lifecycle management
2. **`pyproject.toml`** - Added `apscheduler` dependency

---

## 🚀 How It Works

### Architecture

```
FastAPI App Starts
    ↓
Lifespan Event (Startup)
    ↓
Scheduler Starts Automatically
    ↓
Job Runs Every 1 Minute
    ↓
Checks for Scheduled Posts
    ↓
Publishes Due Posts
    ↓
Logs Results
```

### The Scheduler Function

```python
def publish_scheduled_posts():
    """Runs every minute automatically"""
    # Find posts with status=SCHEDULED and scheduled_at <= now
    # Change status to PUBLISHED
    # Log results
```

---

## 🖥️ Local Testing

### Start the Server

```bash
cd backend
./start_dev.sh
```

Or manually:

```bash
uv run uvicorn src.cj36.main:app --reload
```

### Check Scheduler Status

Visit: `http://localhost:8000/health/scheduler`

Expected response:

```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "publish_scheduled_posts",
      "name": "Publish scheduled posts",
      "next_run": "2025-11-24T12:35:00"
    }
  ],
  "status": "healthy"
}
```

### Test Scheduled Publishing

1. Create a post scheduled 2 minutes in the future
2. Watch the console logs
3. After 2 minutes, you'll see:
   ```
   INFO: Publishing post #123: 'Your Post Title...'
   INFO: Successfully published 1 post(s).
   ```

---

## 🌐 cPanel Deployment

### Quick Steps:

1. **Upload files** to cPanel via File Manager/FTP
2. **Create Python App** in cPanel (Setup Python App)
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Start the app** - Scheduler starts automatically!

### Verify It's Working:

Visit: `https://api.yourdomain.com/health/scheduler`

### Full Guide:

See `CPANEL_DEPLOYMENT.md` for complete step-by-step instructions.

---

## 🔧 VPS Deployment (Future)

When you migrate to VPS, **nothing changes**! The scheduler is part of the app.

### Example with Gunicorn:

```bash
gunicorn src.cj36.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

The scheduler starts automatically when any worker starts.

---

## 📊 Monitoring

### Health Check Endpoints:

- **Basic**: `GET /health` - Check if API is running
- **Scheduler**: `GET /health/scheduler` - Check scheduler status

### Logs:

The scheduler logs important events:

```
✅ Background scheduler started successfully
📅 Scheduled job: Publish posts every 1 minute
INFO: Found 2 scheduled post(s) to publish:
INFO:   - Publishing post #45: 'Breaking News Story...'
INFO: Successfully published 2 post(s).
```

### In cPanel:

- View logs in the Python App interface
- Check error logs in `/home/username/logs/`

---

## 🛠️ Troubleshooting

### Scheduler Not Running?

**Check**: Visit `/health/scheduler` endpoint
**Expected**: `"scheduler_running": true`
**If false**: Restart the application

### Posts Not Publishing?

**Check logs** for errors:

```bash
# cPanel: View in Python App interface
# VPS: Check application logs
tail -f /path/to/logs/app.log
```

**Common issues**:

- Database connection error
- Timezone mismatch (scheduler uses UTC)
- Post scheduled_at is NULL

### Restart the Scheduler:

**cPanel**: Restart the Python app in cPanel interface
**VPS**: Restart the application server

```bash
# Gunicorn
systemctl restart your-app

# Or touch restart file
touch tmp/restart.txt
```

---

## ⚙️ Configuration

### Change Schedule Interval:

Edit `src/cj36/scheduler.py`:

```python
scheduler.add_job(
    func=publish_scheduled_posts,
    trigger=IntervalTrigger(minutes=1),  # Change this
    # ...
)
```

Options:

- `minutes=1` - Every minute (default)
- `minutes=5` - Every 5 minutes
- `hours=1` - Every hour

### Add More Background Jobs:

```python
# In scheduler.py
def another_background_task():
    # Your task logic
    pass

# In start_scheduler()
scheduler.add_job(
    func=another_background_task,
    trigger=IntervalTrigger(hours=1),
    id='another_task',
    name='Another background task'
)
```

---

## 🎯 Advantages of This Approach

### vs. Separate Cron Jobs:

✅ **No cPanel cron configuration** needed
✅ **Portable** - Works on any hosting
✅ **Integrated logging** - Same logs as your app
✅ **Easy monitoring** - Health check endpoint
✅ **Automatic** - Starts with your app

### vs. Celery:

✅ **Simpler** - No Redis/RabbitMQ required
✅ **Lightweight** - Perfect for scheduled tasks
✅ **Easier deployment** - No separate workers
✅ **Lower cost** - No additional services

---

## 📝 Summary

Your background job system is now **production-ready** and works on:

- ✅ Local development (tested)
- ✅ cPanel shared hosting (configured)
- ✅ VPS hosting (ready to deploy)

**Key Points**:

1. Scheduler runs **inside** your FastAPI app
2. **No external dependencies** (no Redis, no separate cron)
3. **Automatic startup** when app starts
4. **Monitoring** via `/health/scheduler` endpoint
5. **Works everywhere** your FastAPI app runs

**Next Steps**:

1. Test locally: `./start_dev.sh`
2. Deploy to cPanel: Follow `CPANEL_DEPLOYMENT.md`
3. Monitor: Check `/health/scheduler` endpoint
4. Enjoy automated post publishing! 🎉

---

## 🆘 Support

If you encounter issues:

1. Check `/health/scheduler` endpoint
2. Review application logs
3. Verify `apscheduler` is installed: `pip list | grep apscheduler`
4. Test manually: `python -c "from src.cj36.scheduler import publish_scheduled_posts; publish_scheduled_posts()"`

For cPanel-specific issues, consult `CPANEL_DEPLOYMENT.md`.
