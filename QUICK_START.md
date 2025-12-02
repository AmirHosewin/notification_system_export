# Quick Start Guide

Get the notification system running in 5 minutes.

## ⚡ Prerequisites

- [✅] PostgreSQL database accessible
- [✅] Python 3.11+ with FastAPI installed
- [✅] Firebase credentials file exists
- [✅] Application runs successfully

## 🚀 3-Step Quick Start

### Step 1: Database (2 minutes)

```bash
cd /path/to/ttlock_webapp

psql -U your_username -d your_database -f app/notification_system/DB/migration_add_notification_tables.sql
```

**Expected output:**
```
NOTICE: ✅ All notification tables created successfully
NOTICE: ✅ FCM token columns added to user_table
```

### Step 2: Configuration (1 minute)

Add to `main.env`:
```env
NOTIFICATION_ENABLED=true
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert
LOW_BATTERY_THRESHOLD=20
LOW_BATTERY_COOLDOWN_HOURS=24
LOW_BATTERY_MIN_DROP=5
DEBUG=false
```

### Step 3: Start Application (1 minute)

```bash
python main.py
```

**Look for:**
```
✅ Database initialized
✅ Firebase initialized for FCM notifications (App: Simpled Alert)
INFO:     Application startup complete.
```

## ✅ Verify Installation

### Check API Documentation

Open browser: `http://localhost:6500/docs`

Look for these endpoints:
- `POST /v1/register_fcm_token`
- `GET /v1/notifications`
- `PUT /v1/notifications/{notification_id}/read`
- `PUT /v1/notifications/read_all`
- `GET /v1/notifications/stats`

### Check Database

```sql
SELECT tablename FROM pg_tables
WHERE tablename LIKE '%notification%';
```

**Expected:**
- notification_table
- notification_log_table
- battery_alert_tracker_table

### Check User Table

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'user_table'
AND column_name LIKE 'fcm_%';
```

**Expected:**
- fcm_token
- fcm_token_updated_at

## 🧪 Test It (Optional)

### Enable Debug Mode

In `main.env`:
```env
DEBUG=true
```

Restart application.

### Test Notification

1. **Get JWT Token:**
   ```bash
   curl -X POST http://localhost:6500/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "your@email.com", "password": "your_password"}'
   ```

2. **Register FCM Token:**
   ```bash
   curl -X POST http://localhost:6500/v1/register_fcm_token \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"fcm_token": "test_token_123"}'
   ```

3. **Send Test Notification:**
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

4. **Check Result:**
   ```sql
   SELECT id, notification_type, title, status
   FROM notification_table
   ORDER BY created_at DESC
   LIMIT 1;
   ```

## 🎉 You're Done!

The notification system is now:
- ✅ Installed and configured
- ✅ Integrated with your application
- ✅ Ready to send notifications
- ✅ Tracking delivery status

## 📱 Android Integration

Android team needs to:
1. Add Firebase SDK to Android app
2. Get FCM token after user login
3. Call `POST /v1/register_fcm_token` with the token
4. Handle incoming notifications

See [README.md](README.md) section "Android Integration" for complete guide.

## 📚 Next Steps

- Read [README.md](README.md) for complete documentation
- See [CONFIGURATION.md](CONFIGURATION.md) for tuning options
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details

## 🆘 Troubleshooting

### Firebase Not Initialized

**Problem:**
```
⚠️ Firebase initialization failed: [Errno 2] No such file or directory
```

**Solution:**
Check `FIREBASE_CREDENTIALS_PATH` in `main.env` points to existing file.

### Tables Not Created

**Problem:**
```
relation "notification_table" does not exist
```

**Solution:**
Run migration script again:
```bash
psql -U user -d db -f app/notification_system/DB/migration_add_notification_tables.sql
```

### Notifications Not Sending

**Problem:**
User receives no notifications

**Solution:**
1. User must register FCM token first
2. Check `user_table.fcm_token` is populated
3. Check `notification_table.status` for errors
4. Query `notification_log_table` for FCM error messages

## 📞 Support

- **Full Documentation:** [README.md](README.md)
- **Configuration Guide:** [CONFIGURATION.md](CONFIGURATION.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Technical Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

**Quick Start Complete! 🎉**

Your notification system is ready to use.
