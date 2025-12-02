# Notification System Deployment Guide

Quick deployment checklist and step-by-step guide for activating the notification system.

## Pre-Deployment Checklist

- [ ] Firebase project created and active
- [ ] Firebase credentials JSON file obtained
- [ ] PostgreSQL database accessible
- [ ] Python 3.11+ installed
- [ ] FastAPI application running
- [ ] Android app development team notified

## Step-by-Step Deployment

### 1. Install Dependencies

```bash
pip install firebase-admin==6.4.0
```

Verify installation:
```bash
pip list | grep firebase-admin
```

### 2. Database Migration

#### Option A: Using psql

```bash
cd /path/to/ttlock_webapp

psql -U your_username -d your_database_name -f app/notification_system/DB/migration_add_notification_tables.sql
```

#### Option B: Using pgAdmin or DBeaver

1. Open SQL editor
2. Load file: `app/notification_system/DB/migration_add_notification_tables.sql`
3. Execute the script
4. Verify tables created:
   ```sql
   SELECT tablename FROM pg_tables
   WHERE tablename LIKE '%notification%'
   OR tablename LIKE '%battery_alert%';
   ```

Expected output:
```
 tablename
---------------------------------
 notification_table
 notification_log_table
 battery_alert_tracker_table
```

#### Option C: Using Python Script

Create `run_migration.py`:
```python
import asyncio
from sqlalchemy import text
from app.core.database import async_engine

async def run_migration():
    with open('app/notification_system/DB/migration_add_notification_tables.sql', 'r') as f:
        sql = f.read()

    async with async_engine.begin() as conn:
        await conn.execute(text(sql))

    print("✅ Migration completed successfully")

if __name__ == "__main__":
    asyncio.run(run_migration())
```

Run:
```bash
python run_migration.py
```

### 3. Configure Environment Variables

Edit `main.env`:

```env
# ============================================================
# Firebase Cloud Messaging (FCM) Notification Settings
# ============================================================

NOTIFICATION_ENABLED=true
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert

# Notification thresholds
LOW_BATTERY_THRESHOLD=20
LOW_BATTERY_COOLDOWN_HOURS=24
LOW_BATTERY_MIN_DROP=5
MAX_NOTIFICATIONS_PER_USER_PER_HOUR=50

# Debug mode (ONLY for development)
DEBUG=false
```

**Production Settings:**
- `NOTIFICATION_ENABLED=true`
- `NOTIFICATION_FCM_ENABLED=true`
- `DEBUG=false`

**Development Settings:**
- `NOTIFICATION_ENABLED=true`
- `NOTIFICATION_FCM_ENABLED=true`
- `DEBUG=true` (enables test endpoint)

### 4. Verify Firebase Credentials

Check credentials file exists:
```bash
ls -l app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
```

Verify JSON structure:
```bash
cat app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json | python -m json.tool
```

Expected fields:
- `type`: "service_account"
- `project_id`: "ttlock-notifications"
- `private_key_id`: (exists)
- `private_key`: (exists)
- `client_email`: (exists)

### 5. Start Application

```bash
python main.py
```

or

```bash
uvicorn main:app --host 0.0.0.0 --port 6500 --reload
```

### 6. Verify Startup Logs

Look for these log messages:

```
✅ Database initialized
✅ Firebase initialized for FCM notifications (App: Simpled Alert)
INFO:     Application startup complete.
```

If you see errors:
```
❌ Database initialization failed: ...
⚠️ Firebase initialization failed: ...
```

Check:
1. Database connection string in `main.env`
2. Firebase credentials path
3. Credentials file is valid JSON
4. Firebase project is active

### 7. Test API Endpoints

#### Check API Documentation

Open browser:
```
http://localhost:6500/docs
```

Look for notification endpoints:
- `POST /v1/register_fcm_token`
- `GET /v1/notifications`
- `PUT /v1/notifications/{notification_id}/read`
- `PUT /v1/notifications/read_all`
- `GET /v1/notifications/stats`
- `POST /v1/test_notification` (if DEBUG=true)

#### Test Health Check

```bash
curl http://localhost:6500/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 8. Test Notification Flow (Development Only)

#### Step 1: Get JWT Token

Login to get token:
```bash
curl -X POST http://localhost:6500/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your_password"
  }'
```

Copy the `access_token` from response.

#### Step 2: Register FCM Token

```bash
curl -X POST http://localhost:6500/v1/register_fcm_token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "test_fcm_token_for_development"
  }'
```

Expected response:
```json
{
  "message": "FCM token registered successfully",
  "user_id": 123
}
```

#### Step 3: Verify Token in Database

```sql
SELECT id, email, fcm_token, fcm_token_updated_at
FROM user_table
WHERE email = 'test@example.com';
```

#### Step 4: Send Test Notification (DEBUG mode only)

```bash
curl -X POST http://localhost:6500/v1/test_notification \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "low_battery",
    "context": {
      "device_id": 123,
      "device_name": "Test Device",
      "battery_level": 15
    }
  }'
```

Expected response:
```json
{
  "message": "Test notification sent successfully",
  "notification_id": 1,
  "notification_type": "low_battery",
  "status": "sent"
}
```

#### Step 5: Check Notification in Database

```sql
SELECT
    id,
    notification_type,
    title,
    body,
    priority,
    status,
    created_at,
    sent_at
FROM notification_table
ORDER BY created_at DESC
LIMIT 5;
```

#### Step 6: Check Delivery Log

```sql
SELECT
    nl.id,
    nl.notification_id,
    nl.attempt_number,
    nl.status,
    nl.fcm_response,
    nl.error_message,
    nl.created_at
FROM notification_log_table nl
ORDER BY nl.created_at DESC
LIMIT 5;
```

### 9. Production Deployment Checklist

#### Pre-Production

- [ ] Run migration on production database
- [ ] Configure environment variables in production `main.env`
- [ ] Set `DEBUG=false`
- [ ] Verify Firebase credentials on production server
- [ ] Check file permissions (chmod 600 for credentials)
- [ ] Test database connectivity
- [ ] Verify port 6500 is accessible (or your production port)

#### Deployment

- [ ] Stop application
- [ ] Pull latest code
- [ ] Install dependencies: `pip install firebase-admin`
- [ ] Run database migration
- [ ] Update `main.env`
- [ ] Start application
- [ ] Check startup logs for Firebase initialization
- [ ] Test `/health` endpoint
- [ ] Verify `/docs` shows notification endpoints

#### Post-Deployment Verification

- [ ] Check application logs for errors
- [ ] Monitor Firebase console for service status
- [ ] Test token registration with real Android device
- [ ] Send test notification (if DEBUG enabled temporarily)
- [ ] Monitor notification delivery success rate
- [ ] Check database for notification records
- [ ] Verify FCM logs don't show credential errors

### 10. Android Team Handoff

Share these documents with Android team:

1. **API Documentation**
   - Share Swagger URL: `https://your-api.com/docs`
   - Focus on `/v1/register_fcm_token` endpoint

2. **Integration Guide**
   - See `README.md` section "Android Integration"
   - Provide example code for FCM token registration

3. **Notification Format**
   - Share FCM message structure
   - Explain data payload format

4. **Testing**
   - Provide test credentials
   - Share test server URL (if available)

5. **Support**
   - Provide backend team contact
   - Share monitoring dashboard access (if available)

## Monitoring Setup

### Application Logs

Monitor these log messages:

**Success:**
```
✅ Firebase initialized for FCM notifications (App: Simpled Alert)
✅ FCM token registered for user 123
✅ Low battery notification sent for device 456 (Front Door) at 15%
✅ FCM notification sent successfully: projects/ttlock-notifications/messages/...
```

**Warnings:**
```
⚠️ User 123 has no FCM token - skipping notification
⚠️ Firebase initialization returned None - FCM notifications disabled
⚠️ Within cooldown period - last alert was 12.5h ago
```

**Errors:**
```
❌ Failed to create/send notification: ...
❌ FCM send failed: ...
❌ Database initialization failed: ...
```

### Database Monitoring

Create monitoring queries:

**Daily notification count:**
```sql
SELECT
    DATE(created_at) as date,
    notification_type,
    COUNT(*) as count
FROM notification_table
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at), notification_type
ORDER BY date DESC, notification_type;
```

**Delivery success rate:**
```sql
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM notification_table
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;
```

**Failed deliveries:**
```sql
SELECT
    n.id,
    n.notification_type,
    n.created_at,
    nl.error_message
FROM notification_table n
JOIN notification_log_table nl ON nl.notification_id = n.id
WHERE n.status = 'failed'
AND n.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY n.created_at DESC;
```

## Rollback Plan

If deployment fails:

### 1. Disable Notifications

Quick disable:
```env
NOTIFICATION_ENABLED=false
```

Restart application.

### 2. Rollback Database

If migration causes issues:

```sql
-- Drop notification tables
DROP TABLE IF EXISTS notification_log_table;
DROP TABLE IF EXISTS battery_alert_tracker_table;
DROP TABLE IF EXISTS notification_table;

-- Remove FCM token columns from user_table
ALTER TABLE user_table DROP COLUMN IF EXISTS fcm_token;
ALTER TABLE user_table DROP COLUMN IF EXISTS fcm_token_updated_at;
```

### 3. Rollback Code

```bash
git checkout HEAD~1  # or specific commit
pip install -r requirements.txt
python main.py
```

### 4. Restore Service

1. Verify application runs without notification system
2. Check logs for errors
3. Test core functionality (auth, devices, locks)
4. Notify users of temporary notification outage

## Troubleshooting

### Issue: Firebase Initialization Failed

**Symptoms:**
```
⚠️ Firebase initialization failed: [Errno 2] No such file or directory
```

**Solutions:**
1. Check `FIREBASE_CREDENTIALS_PATH` in `main.env`
2. Verify file exists: `ls app/notification_system/FB/*.json`
3. Use absolute path if relative path fails
4. Check file permissions: `chmod 600 credentials.json`

### Issue: Database Tables Not Created

**Symptoms:**
```
relation "notification_table" does not exist
```

**Solutions:**
1. Run migration script again
2. Check database connection
3. Verify user has CREATE TABLE permissions
4. Check for syntax errors in migration SQL

### Issue: FCM Tokens Not Registering

**Symptoms:**
```
User has no FCM token - skipping notification
```

**Solutions:**
1. Android app must call `/v1/register_fcm_token`
2. Check JWT token is valid
3. Verify API endpoint is accessible
4. Check request body format is correct

### Issue: Notifications Not Sending

**Symptoms:**
Notification created but status = "failed"

**Solutions:**
1. Check `notification_log_table` for error messages
2. Verify Firebase credentials are valid
3. Check Firebase project is active
4. Verify FCM token is valid (not expired/uninstalled)
5. Check user's `fcm_token` field is populated

### Issue: Too Many Notifications

**Symptoms:**
Users receiving duplicate or excessive alerts

**Solutions:**
1. Check cooldown settings: `LOW_BATTERY_COOLDOWN_HOURS`
2. Increase `LOW_BATTERY_MIN_DROP` threshold
3. Verify `battery_alert_tracker_table` is working
4. Check for race conditions in record creation

## Performance Tuning

### High Load Optimization

If handling 1000+ notifications per hour:

1. **Database Connection Pool**
   - Already optimized in `database.py`
   - Monitor connection usage

2. **Async Performance**
   - All operations are async
   - No additional tuning needed

3. **Batch Processing**
   - Use `send_batch_notifications()` for multiple users
   - Example: Gateway offline affects multiple users

4. **Rate Limiting**
   - Adjust `MAX_NOTIFICATIONS_PER_USER_PER_HOUR`
   - Implement circuit breaker if needed

5. **Caching**
   - Consider caching FCM tokens in Redis
   - Cache notification templates

## Security Hardening

### Production Security

1. **File Permissions**
   ```bash
   chmod 600 app/notification_system/FB/*.json
   chown www-data:www-data app/notification_system/FB/*.json
   ```

2. **Environment Variables**
   - Never commit `main.env` to git
   - Use secrets manager in production
   - Rotate Firebase credentials periodically

3. **API Security**
   - All endpoints require JWT authentication
   - Implement rate limiting at nginx/API gateway level
   - Monitor for abuse patterns

4. **Database Security**
   - Use separate database user for notifications
   - Grant minimum required permissions
   - Enable audit logging

## Support Contacts

- **Backend Team**: [Your contact]
- **Android Team**: [Android team contact]
- **DevOps**: [DevOps contact]
- **Firebase Support**: https://firebase.google.com/support

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [FCM HTTP v1 API](https://firebase.google.com/docs/cloud-messaging/http-server-ref)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

## Changelog

### Deployment v1.0.0
- Initial deployment documentation
- Step-by-step deployment guide
- Monitoring setup
- Troubleshooting guide
- Security hardening checklist
