# Firebase Cloud Messaging (FCM) Setup

This directory contains Firebase configuration for push notifications.

## Files

- `firebase_config.py` - Firebase Admin SDK initialization
- `ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json` - Firebase credentials (already configured)

## Configuration

Firebase is configured via environment variables in `main.env`:

```env
NOTIFICATION_FCM_ENABLED=true
FIREBASE_CREDENTIALS_PATH=./FB/ttlock-notifications-firebase-adminsdk-fbsvc-a7d3badb9b.json
FCM_APP_NAME=Simpled Alert
```

## Usage

Firebase is automatically initialized at application startup in `main.py`.

## Android App Integration

The Android app must:

1. Add Firebase SDK to the app
2. Get FCM token after user login
3. Register token via API: `POST /v1/register_fcm_token`
4. Handle incoming notifications with data payload

## Notification Format

All notifications include:
- **Title**: Notification heading
- **Body**: Notification message
- **Data**: Custom payload with `notification_type`, `device_id`, etc.
- **Priority**: "high" for low battery, "normal" for others
- **Icon**: Application default icon
- **Sound**: System default sound

## Supported Notification Types

1. `low_battery` - Battery ≤20% (HIGH PRIORITY)
2. `device_unlock` - Device unlocked
3. `device_lock` - Device locked
4. `ekey_shared` - E-key shared with user
5. `ekey_revoked` - E-key access revoked
6. `gateway_offline` - Gateway lost connection
7. `gateway_online` - Gateway reconnected
8. `security_alert` - Unauthorized access attempt
9. `new_device_login` - Login from new device

## Troubleshooting

If notifications aren't working:

1. Check Firebase credentials file exists
2. Verify `NOTIFICATION_FCM_ENABLED=true` in main.env
3. Check logs for Firebase initialization errors
4. Verify user has registered FCM token
5. Test with `/v1/test_notification` endpoint (DEBUG mode)
