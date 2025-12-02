# Notification System Configuration

This document explains how to configure the Firebase Cloud Messaging (FCM) notification system.

## Environment Variables

Add these variables to your `main.env` file:

```env
# ============================================================
# Firebase Cloud Messaging (FCM) Notification Settings
# ============================================================

# Enable/disable notification system globally
NOTIFICATION_ENABLED=true

# Enable/disable FCM push notifications specifically
NOTIFICATION_FCM_ENABLED=true

# Path to Firebase service account credentials JSON file
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json

# Application name displayed in notifications
FCM_APP_NAME=Simpled Alert

# ============================================================
# Notification Thresholds and Limits
# ============================================================

# Battery percentage threshold for low battery alerts (default: 20%)
LOW_BATTERY_THRESHOLD=20

# Hours to wait between low battery alerts for same device (default: 24h)
LOW_BATTERY_COOLDOWN_HOURS=24

# Minimum battery drop percentage to trigger new alert (default: 5%)
LOW_BATTERY_MIN_DROP=5

# Maximum notifications per user per hour (rate limiting, default: 50)
MAX_NOTIFICATIONS_PER_USER_PER_HOUR=50

# ============================================================
# Debug Mode
# ============================================================

# Enable debug mode to allow test notification endpoint (default: false)
# WARNING: Only enable in development environment
DEBUG=false
```

## Configuration Details

### Core Settings

#### `NOTIFICATION_ENABLED`
- **Type**: Boolean (true/false)
- **Default**: true
- **Description**: Master switch for entire notification system. Set to `false` to completely disable notifications.

#### `NOTIFICATION_FCM_ENABLED`
- **Type**: Boolean (true/false)
- **Default**: true
- **Description**: Enable/disable Firebase Cloud Messaging. Set to `false` to disable push notifications while keeping notification system active.

#### `FIREBASE_CREDENTIALS_PATH`
- **Type**: String (file path)
- **Default**: app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
- **Description**: Path to Firebase service account credentials JSON file. Can be absolute or relative to project root.

#### `FCM_APP_NAME`
- **Type**: String
- **Default**: Simpled Alert
- **Description**: Application name displayed in notifications. Used for branding.

### Battery Alert Settings

#### `LOW_BATTERY_THRESHOLD`
- **Type**: Integer (0-100)
- **Default**: 20
- **Description**: Battery percentage at or below which low battery alerts are triggered.
- **Example**: If set to 20, alerts trigger when battery ≤ 20%

#### `LOW_BATTERY_COOLDOWN_HOURS`
- **Type**: Integer (hours)
- **Default**: 24
- **Description**: Minimum hours to wait between alerts for the same device to prevent spam.
- **Example**: If set to 24, user won't receive another alert for 24 hours unless battery drops significantly

#### `LOW_BATTERY_MIN_DROP`
- **Type**: Integer (percentage)
- **Default**: 5
- **Description**: Minimum battery percentage drop required to trigger new alert during cooldown period.
- **Example**: If set to 5 and last alert was at 20%, new alert only sent if battery drops to ≤15%

#### `MAX_NOTIFICATIONS_PER_USER_PER_HOUR`
- **Type**: Integer
- **Default**: 50
- **Description**: Rate limiting - maximum notifications a single user can receive per hour.

### Debug Settings

#### `DEBUG`
- **Type**: Boolean (true/false)
- **Default**: false
- **Description**: Enable debug mode. When true, enables test notification endpoint `/v1/test_notification`.
- **WARNING**: Never enable in production!

## Firebase Credentials Setup

The Firebase credentials file is already configured at:
```
app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
```

This file contains:
- `type`: "service_account"
- `project_id`: "ttlock-notifications"
- `private_key_id`: Service account key ID
- `private_key`: Private key for authentication
- `client_email`: Service account email
- `client_id`: Client ID
- `auth_uri`: OAuth2 authentication endpoint
- `token_uri`: Token endpoint
- `auth_provider_x509_cert_url`: Certificate provider URL
- `client_x509_cert_url`: Client certificate URL

**IMPORTANT**: Never commit this file to public repositories!

## Configuration Examples

### Production Configuration
```env
NOTIFICATION_ENABLED=true
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert
LOW_BATTERY_THRESHOLD=20
LOW_BATTERY_COOLDOWN_HOURS=24
LOW_BATTERY_MIN_DROP=5
MAX_NOTIFICATIONS_PER_USER_PER_HOUR=50
DEBUG=false
```

### Development Configuration
```env
NOTIFICATION_ENABLED=true
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=app/notification_system/FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert (Dev)
LOW_BATTERY_THRESHOLD=30
LOW_BATTERY_COOLDOWN_HOURS=1
LOW_BATTERY_MIN_DROP=2
MAX_NOTIFICATIONS_PER_USER_PER_HOUR=100
DEBUG=true
```

### Disabled Notifications
```env
NOTIFICATION_ENABLED=false
NOTIFICATION_FCM_ENABLED=false
```

## Database Setup

Run the migration SQL script to create notification tables:

```bash
psql -U your_username -d your_database -f app/notification_system/DB/migration_add_notification_tables.sql
```

Or use your database management tool to execute the SQL file.

## Testing Configuration

With `DEBUG=true`, you can test notifications using the test endpoint:

```bash
POST /v1/test_notification
Authorization: Bearer <your_jwt_token>

{
  "notification_type": "low_battery",
  "context": {
    "device_id": 123,
    "device_name": "Test Device",
    "battery_level": 15
  }
}
```

## Troubleshooting

### Notifications Not Sending

1. **Check Firebase initialization logs**:
   - Look for "✅ Firebase initialized for FCM notifications" in startup logs
   - If you see "⚠️ Firebase initialization failed", check credentials path

2. **Verify environment variables**:
   - Ensure `NOTIFICATION_ENABLED=true`
   - Ensure `NOTIFICATION_FCM_ENABLED=true`
   - Check `FIREBASE_CREDENTIALS_PATH` points to valid file

3. **Check user FCM token**:
   - User must register FCM token via `/v1/register_fcm_token`
   - Token must be valid (not expired or uninstalled)

4. **Check database**:
   - Verify notification tables exist
   - Check `notification_table` for status field
   - Check `notification_log_table` for error messages

### Firebase Errors

#### "Firebase app not initialized"
- Check `NOTIFICATION_FCM_ENABLED=true`
- Verify credentials file exists at specified path
- Check credentials file is valid JSON

#### "Token unregistered or invalid"
- User uninstalled app or token expired
- User needs to re-register FCM token
- Token is automatically handled by FCM service

#### "Permission denied"
- Firebase credentials may be invalid
- Check service account has correct permissions
- Verify project ID matches credentials

## Monitoring

### Check Notification Stats

```bash
GET /v1/notifications/stats
Authorization: Bearer <your_jwt_token>
```

Returns:
```json
{
  "total": 50,
  "unread": 12,
  "by_type": {
    "low_battery": 15,
    "device_unlock": 20
  },
  "by_priority": {
    "high": 15,
    "normal": 35
  }
}
```

### View Notification History

```bash
GET /v1/notifications?limit=50&unread_only=false
Authorization: Bearer <your_jwt_token>
```

### Check Delivery Logs

Query `notification_log_table` to see FCM delivery attempts and errors:

```sql
SELECT
    n.id,
    n.notification_type,
    n.status,
    nl.attempt_number,
    nl.fcm_response,
    nl.error_message,
    nl.created_at
FROM notification_table n
LEFT JOIN notification_log_table nl ON nl.notification_id = n.id
ORDER BY n.created_at DESC
LIMIT 100;
```

## Security Considerations

1. **Never commit Firebase credentials to version control**
2. **Use environment variables for all sensitive configuration**
3. **Enable DEBUG mode only in development**
4. **Restrict test endpoint access in production**
5. **Implement rate limiting for notification endpoints**
6. **Validate FCM tokens before storage**
7. **Clean up expired tokens periodically**

## Performance Tuning

### High-Volume Deployments

For deployments with many users and devices:

1. **Adjust rate limits**:
   ```env
   MAX_NOTIFICATIONS_PER_USER_PER_HOUR=100
   ```

2. **Increase cooldown periods**:
   ```env
   LOW_BATTERY_COOLDOWN_HOURS=48
   ```

3. **Tune battery thresholds**:
   ```env
   LOW_BATTERY_THRESHOLD=15
   LOW_BATTERY_MIN_DROP=10
   ```

4. **Monitor database performance**:
   - Add indexes if notification queries are slow
   - Archive old notifications periodically
   - Clean up old notification logs

### Database Maintenance

Periodically clean up old notifications:

```sql
-- Delete notifications older than 90 days
DELETE FROM notification_table
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete notification logs older than 30 days
DELETE FROM notification_log_table
WHERE created_at < NOW() - INTERVAL '30 days';
```

## Support

For issues or questions:
1. Check application logs for error messages
2. Verify Firebase console for service status
3. Review notification_log_table for delivery errors
4. Check user FCM token is valid and up-to-date
