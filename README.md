# Firebase Cloud Messaging (FCM) Notification System

Complete push notification system for TTLock smart lock management application.

## Overview

This notification system provides real-time push notifications to Android devices via Firebase Cloud Messaging (FCM). It's designed as a standalone, modular system that can be deployed independently.

**Key Features:**
- 🔔 Real-time push notifications via FCM
- 🔋 Intelligent low battery alerts with cooldown logic
- 📊 Complete notification history and statistics
- 🔒 Secure JWT-based authentication
- 📱 Android app integration ready
- 🚀 High-performance async implementation
- 📝 Comprehensive delivery logging
- ⚙️ Configurable thresholds and limits

## System Architecture

```
app/notification_system/
├── DB/                          # Database layer
│   ├── notification_models.py   # SQLAlchemy models
│   ├── notification_schemas.py  # Pydantic schemas
│   └── migration_add_notification_tables.sql  # Database migration
├── FB/                          # Firebase integration
│   ├── firebase_config.py       # Firebase initialization
│   ├── README.md               # Firebase setup guide
│   └── ttlock-notifications-firebase-adminsdk-*.json  # Credentials
├── services/                    # Business logic
│   ├── fcm_service.py          # FCM communication
│   ├── notification_service.py  # Core orchestration
│   └── notification_messages.py # Message builder
├── hooks/                       # Integration hooks
│   └── device_hooks.py         # Battery alerts & device events
├── api/                         # API routes
│   └── notification_routes.py  # FastAPI endpoints
├── utils/                       # Utilities
│   └── notification_types.py   # Enums and constants
├── CONFIGURATION.md             # Configuration guide
└── README.md                    # This file
```

## Supported Notification Types

### 1. Low Battery Alert (HIGH PRIORITY)
- **Trigger**: Battery ≤ 20%
- **Priority**: HIGH (immediate delivery)
- **Cooldown**: 24 hours (configurable)
- **Icon**: ⚠️
- **Example**: "Front Door battery is at 15%. Please replace soon."

### 2. Device Unlock
- **Trigger**: Device unlocked
- **Priority**: NORMAL
- **Icon**: 🔓
- **Example**: "Front Door was unlocked by John via app"

### 3. Device Lock
- **Trigger**: Device locked
- **Priority**: NORMAL
- **Icon**: 🔒
- **Example**: "Front Door has been locked"

### 4. E-key Shared
- **Trigger**: Access shared with user
- **Priority**: NORMAL
- **Icon**: 🔑
- **Example**: "John shared access to Front Door with you"

### 5. E-key Revoked
- **Trigger**: Access revoked
- **Priority**: NORMAL
- **Icon**: 🔑
- **Example**: "Your access to Front Door has been revoked"

### 6. Gateway Offline
- **Trigger**: Gateway loses connection
- **Priority**: NORMAL
- **Icon**: 📡
- **Example**: "Home Gateway is offline. 3 devices affected."

### 7. Gateway Online
- **Trigger**: Gateway reconnects
- **Priority**: NORMAL
- **Icon**: 📡
- **Example**: "Home Gateway is back online"

### 8. Security Alert
- **Trigger**: Unauthorized access attempts
- **Priority**: NORMAL
- **Icon**: 🚨
- **Example**: "Unauthorized access attempts detected on Front Door (5x)"

### 9. New Device Login
- **Trigger**: Login from new device
- **Priority**: NORMAL
- **Icon**: 🔐
- **Example**: "Login detected from Samsung Galaxy at Tehran, Iran"

## Quick Start

### 1. Database Setup

Run the migration to create notification tables:

```bash
psql -U your_username -d your_database -f app/notification_system/DB/migration_add_notification_tables.sql
```

This creates:
- `notification_table` - Main notification records
- `notification_log_table` - FCM delivery tracking
- `battery_alert_tracker_table` - Cooldown tracking
- Adds `fcm_token` fields to `user_table`

### 2. Configuration

Add to `main.env`:

```env
# Firebase Cloud Messaging
NOTIFICATION_ENABLED=true
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert

# Thresholds
LOW_BATTERY_THRESHOLD=20
LOW_BATTERY_COOLDOWN_HOURS=24
LOW_BATTERY_MIN_DROP=5
MAX_NOTIFICATIONS_PER_USER_PER_HOUR=50

# Debug (development only)
DEBUG=false
```

### 3. Start Application

The notification system initializes automatically on startup:

```bash
python main.py
```

Look for:
```
✅ Database initialized
✅ Firebase initialized for FCM notifications (App: Simpled Alert)
```

### 4. Register FCM Token (Android App)

After user login, Android app must register FCM token:

```http
POST /v1/register_fcm_token
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "fcm_token": "fcm_device_token_string"
}
```

Response:
```json
{
  "message": "FCM token registered successfully",
  "user_id": 123
}
```

## API Endpoints

### Register FCM Token
```http
POST /v1/register_fcm_token
```
Register device token for push notifications (called after login).

### Remove FCM Token
```http
DELETE /v1/fcm_token
```
Remove token on logout or app uninstall.

### Get Notifications
```http
GET /v1/notifications?unread_only=false&limit=50&offset=0
```
Retrieve user's notification history with pagination.

### Mark as Read
```http
PUT /v1/notifications/{notification_id}/read
```
Mark single notification as read.

### Mark All as Read
```http
PUT /v1/notifications/read_all
```
Mark all user's notifications as read.

### Get Statistics
```http
GET /v1/notifications/stats
```
Get notification statistics (total, unread, by type, by priority).

### Test Notification (DEBUG Mode)
```http
POST /v1/test_notification
```
Send test notification (only available when `DEBUG=true`).

## Integration Guide

### Low Battery Alerts

Battery alerts are automatically triggered when records are added. The system:

1. **Checks battery level** against threshold (default 20%)
2. **Applies cooldown logic** (24h default)
3. **Prevents duplicates** unless battery drops 5%+ more
4. **Creates notification record** in database
5. **Sends via FCM** to user's device
6. **Logs delivery** for tracking

**Integration in `records.py`:**
```python
from app.notification_system.hooks import check_and_notify_low_battery
from app.config.settings import settings

# After creating record
if settings.NOTIFICATION_ENABLED and record_info.electric_quantity is not None:
    await check_and_notify_low_battery(
        device_id=device_id,
        battery_level=record_info.electric_quantity,
        db=db
    )
```

### Other Notification Types

Use `NotificationService` for other events:

```python
from app.notification_system.services.notification_service import NotificationService
from app.notification_system.utils.notification_types import NotificationType

notification_service = NotificationService()

# Send device unlock notification
await notification_service.create_and_send_notification(
    user_id=user.id,
    notification_type=NotificationType.DEVICE_UNLOCK,
    context={
        "device_id": device.id,
        "device_name": device.device_name,
        "user_name": "John",
        "method": "app",
        "timestamp": datetime.utcnow().isoformat()
    },
    db=db
)
```

## Database Schema

### notification_table
```sql
- id (BIGSERIAL PRIMARY KEY)
- user_id (INTEGER, FK to user_table)
- notification_type (VARCHAR(50))
- priority (VARCHAR(10), "high" or "normal")
- title (VARCHAR(255))
- body (TEXT)
- data (JSONB) - FCM data payload
- device_id (INTEGER, FK to device_table)
- gateway_id (INTEGER, FK to gateway_table)
- ekey_id (INTEGER, FK to ekey_table)
- metadata (JSONB)
- status (VARCHAR(20)) - pending, sent, failed, read
- created_at (TIMESTAMP)
- sent_at (TIMESTAMP)
- read_at (TIMESTAMP)
```

### notification_log_table
```sql
- id (BIGSERIAL PRIMARY KEY)
- notification_id (BIGINT, FK to notification_table)
- attempt_number (INTEGER)
- fcm_response (TEXT)
- status (VARCHAR(20))
- error_message (TEXT)
- created_at (TIMESTAMP)
```

### battery_alert_tracker_table
```sql
- id (BIGSERIAL PRIMARY KEY)
- device_id (INTEGER, FK to device_table, UNIQUE)
- last_alert_at (TIMESTAMP)
- battery_level_at_alert (INTEGER)
- alert_count (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## FCM Message Format

All notifications follow this structure:

```json
{
  "android": {
    "priority": "high",  // or "normal"
    "notification": {
      "title": "⚠️ Low Battery Alert",
      "body": "Front Door battery is at 15%. Please replace soon.",
      "icon": "@drawable/ic_notification",
      "sound": "default",
      "channel_id": "default"
    }
  },
  "data": {
    "notification_type": "low_battery",
    "device_id": "123",
    "battery_level": "15",
    "device_name": "Front Door",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

**Important**: All data payload values must be strings (FCM requirement).

## Android Integration

### 1. Add Firebase SDK

Add to `build.gradle`:
```gradle
implementation 'com.google.firebase:firebase-messaging:23.0.0'
```

### 2. Get FCM Token

```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Register token with backend after login
        registerFcmToken(token)
    }
}
```

### 3. Register Token with Backend

```kotlin
fun registerFcmToken(token: String) {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("https://your-api.com/v1/register_fcm_token")
        .header("Authorization", "Bearer $jwtToken")
        .post(
            JSONObject().apply {
                put("fcm_token", token)
            }.toString().toRequestBody("application/json".toMediaType())
        )
        .build()

    client.newCall(request).enqueue(object : Callback {
        override fun onResponse(call: Call, response: Response) {
            // Token registered successfully
        }

        override fun onFailure(call: Call, e: IOException) {
            // Handle error
        }
    })
}
```

### 4. Handle Incoming Notifications

```kotlin
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val notificationType = remoteMessage.data["notification_type"]
        val deviceId = remoteMessage.data["device_id"]

        // Handle navigation based on notification type
        when (notificationType) {
            "low_battery" -> navigateToBatteryScreen(deviceId)
            "device_unlock" -> navigateToDeviceHistory(deviceId)
            "ekey_shared" -> navigateToSharedDevices()
            // ... handle other types
        }
    }
}
```

### 5. Create Notification Channel

```kotlin
private fun createNotificationChannel() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(
            "default",
            "Smart Lock Notifications",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Notifications for smart lock events"
            enableLights(true)
            lightColor = Color.BLUE
            enableVibration(true)
        }

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)
    }
}
```

## Testing

### 1. Enable Debug Mode

```env
DEBUG=true
```

### 2. Register FCM Token

```bash
curl -X POST http://localhost:6500/v1/register_fcm_token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "YOUR_FCM_TOKEN"}'
```

### 3. Send Test Notification

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

### 4. Check Notification History

```bash
curl -X GET http://localhost:6500/v1/notifications?limit=10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Check Statistics

```bash
curl -X GET http://localhost:6500/v1/notifications/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Monitoring & Troubleshooting

### Check Firebase Initialization

Startup logs should show:
```
✅ Firebase initialized for FCM notifications (App: Simpled Alert)
```

If you see errors:
- Verify `FIREBASE_CREDENTIALS_PATH` is correct
- Check credentials file exists and is valid JSON
- Ensure Firebase project is active

### Check Notification Delivery

Query notification logs:
```sql
SELECT
    n.id,
    n.notification_type,
    n.status,
    nl.fcm_response,
    nl.error_message
FROM notification_table n
LEFT JOIN notification_log_table nl ON nl.notification_id = n.id
WHERE n.user_id = 123
ORDER BY n.created_at DESC;
```

### Common Issues

#### "User has no FCM token"
- User must register token via `/v1/register_fcm_token`
- Check `user_table.fcm_token` is populated

#### "Token unregistered or invalid"
- User uninstalled app or token expired
- User needs to re-register token

#### "Firebase app not initialized"
- Check `NOTIFICATION_FCM_ENABLED=true`
- Verify credentials file path
- Check Firebase credentials are valid

#### Notifications not triggering
- Check battery level ≤ threshold (default 20%)
- Verify cooldown period hasn't blocked alert
- Check `NOTIFICATION_ENABLED=true`
- Verify hook integration in `records.py`

## Performance Optimization

### High-Volume Deployments

1. **Database Indexing**
   - Already optimized with indexes on common queries
   - Monitor slow queries with `EXPLAIN ANALYZE`

2. **Batch Notifications**
   - Use `send_batch_notifications()` for multiple devices
   - Parallel delivery with asyncio

3. **Rate Limiting**
   - Configure `MAX_NOTIFICATIONS_PER_USER_PER_HOUR`
   - Prevent notification spam

4. **Cooldown Tuning**
   - Adjust `LOW_BATTERY_COOLDOWN_HOURS` based on usage
   - Increase `LOW_BATTERY_MIN_DROP` to reduce alerts

5. **Archive Old Data**
   - Periodically clean up old notifications
   - Keep logs for compliance/audit requirements

### Example Cleanup Script

```sql
-- Archive notifications older than 90 days
INSERT INTO notification_archive
SELECT * FROM notification_table
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM notification_table
WHERE created_at < NOW() - INTERVAL '90 days';

-- Clean up old logs
DELETE FROM notification_log_table
WHERE created_at < NOW() - INTERVAL '30 days';
```

## Security Considerations

1. **Firebase Credentials**
   - Never commit to version control
   - Use environment variables
   - Restrict file permissions (chmod 600)

2. **API Authentication**
   - All endpoints require JWT authentication
   - Token validation via existing auth system

3. **Rate Limiting**
   - Implemented per-user rate limits
   - Configurable via `MAX_NOTIFICATIONS_PER_USER_PER_HOUR`

4. **Input Validation**
   - Pydantic schemas validate all input
   - SQL injection protection via SQLAlchemy

5. **Debug Mode**
   - Test endpoint only available when `DEBUG=true`
   - Never enable in production

## Migration from Email to FCM

If migrating from email notifications:

1. **Remove email-related code**
   - This system uses FCM ONLY
   - No email functionality included

2. **Update user notification preferences**
   - Users must register FCM tokens
   - Old email notification settings can be deprecated

3. **Data migration**
   - No data migration needed
   - Fresh notification system with new tables

## Support & Documentation

- **Configuration Guide**: [CONFIGURATION.md](CONFIGURATION.md)
- **Firebase Setup**: [FB/README.md](FB/README.md)
- **API Documentation**: Visit `/docs` endpoint (Swagger UI)

## Changelog

### Version 1.0.0 (2025-01-15)
- ✅ Initial implementation
- ✅ 9 notification types supported
- ✅ FCM integration with Firebase Admin SDK
- ✅ Low battery alerts with cooldown logic
- ✅ Complete API endpoints
- ✅ Database models and migration
- ✅ Comprehensive logging and tracking
- ✅ Android integration ready
- ✅ Configuration documentation

## License

Part of TTLock Smart Lock Management System.
