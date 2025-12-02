"""
Notification type enums and constants
"""
from enum import Enum


class NotificationType(str, Enum):
    """
    Supported notification types for FCM push notifications
    """
    # Device events
    LOW_BATTERY = "low_battery"  # HIGH PRIORITY
    DEVICE_UNLOCK = "device_unlock"
    DEVICE_LOCK = "device_lock"

    # E-key events
    EKEY_SHARED = "ekey_shared"
    EKEY_REVOKED = "ekey_revoked"

    # Gateway events
    GATEWAY_OFFLINE = "gateway_offline"
    GATEWAY_ONLINE = "gateway_online"

    # Security events
    SECURITY_ALERT = "security_alert"

    # User account events
    NEW_DEVICE_LOGIN = "new_device_login"


class NotificationPriority(str, Enum):
    """FCM notification priority levels"""
    HIGH = "high"  # For urgent notifications (low battery)
    NORMAL = "normal"  # For standard notifications


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"  # Created but not yet sent
    SENT = "sent"  # Successfully sent to FCM
    FAILED = "failed"  # Failed to send
    READ = "read"  # User has read the notification


# Priority mapping for each notification type
NOTIFICATION_PRIORITIES = {
    NotificationType.LOW_BATTERY: NotificationPriority.HIGH,  # Only this is HIGH
    NotificationType.DEVICE_UNLOCK: NotificationPriority.NORMAL,
    NotificationType.DEVICE_LOCK: NotificationPriority.NORMAL,
    NotificationType.EKEY_SHARED: NotificationPriority.NORMAL,
    NotificationType.EKEY_REVOKED: NotificationPriority.NORMAL,
    NotificationType.GATEWAY_OFFLINE: NotificationPriority.NORMAL,
    NotificationType.GATEWAY_ONLINE: NotificationPriority.NORMAL,
    NotificationType.SECURITY_ALERT: NotificationPriority.NORMAL,
    NotificationType.NEW_DEVICE_LOGIN: NotificationPriority.NORMAL,
}


def get_notification_priority(notification_type: NotificationType) -> NotificationPriority:
    """
    Get the priority level for a notification type

    Args:
        notification_type: Type of notification

    Returns:
        NotificationPriority: HIGH for low battery, NORMAL for others
    """
    return NOTIFICATION_PRIORITIES.get(notification_type, NotificationPriority.NORMAL)
