"""
Notification message builder for FCM push notifications

Builds title, body, and data payload for each notification type.
"""
from typing import Dict, Any
from app.notification_system.utils.notification_types import (
    NotificationType,
    get_notification_priority
)


class NotificationMessageBuilder:
    """
    Build FCM notification messages for each type

    App Name: "Simpled Alert"
    Icon: Application default
    Sound: System default
    Priority: HIGH for low battery, NORMAL for others
    """

    APP_NAME = "Simpled Alert"

    @staticmethod
    def build_notification(
        notification_type: NotificationType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build notification message for FCM.

        Args:
            notification_type: Type of notification
            context: Context data (device_id, battery_level, device_name, etc.)

        Returns:
            dict: {
                "title": str,
                "body": str,
                "data": dict,  # FCM data payload
                "priority": str  # "high" or "normal"
            }

        Raises:
            ValueError: If notification_type is unknown
        """
        builders = {
            NotificationType.LOW_BATTERY: NotificationMessageBuilder._build_low_battery,
            NotificationType.DEVICE_UNLOCK: NotificationMessageBuilder._build_device_unlock,
            NotificationType.DEVICE_LOCK: NotificationMessageBuilder._build_device_lock,
            NotificationType.EKEY_SHARED: NotificationMessageBuilder._build_ekey_shared,
            NotificationType.EKEY_REVOKED: NotificationMessageBuilder._build_ekey_revoked,
            NotificationType.GATEWAY_OFFLINE: NotificationMessageBuilder._build_gateway_offline,
            NotificationType.GATEWAY_ONLINE: NotificationMessageBuilder._build_gateway_online,
            NotificationType.SECURITY_ALERT: NotificationMessageBuilder._build_security_alert,
            NotificationType.NEW_DEVICE_LOGIN: NotificationMessageBuilder._build_new_device_login,
        }

        builder = builders.get(notification_type)
        if not builder:
            raise ValueError(f"Unknown notification type: {notification_type}")

        return builder(context)

    @staticmethod
    def _build_low_battery(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Low battery alert notification

        Priority: HIGH
        """
        device_name = context.get("device_name", "Your device")
        battery_level = context.get("battery_level", 0)

        return {
            "title": "⚠️ Low Battery Alert",
            "body": f"{device_name} battery is at {battery_level}%. Please replace soon.",
            "data": {
                "notification_type": "low_battery",
                "device_id": str(context.get("device_id", "")),
                "battery_level": str(battery_level),
                "device_name": device_name,
                "timestamp": context.get("timestamp", "")
            },
            "priority": "high"  # HIGH PRIORITY
        }

    @staticmethod
    def _build_device_unlock(context: Dict[str, Any]) -> Dict[str, Any]:
        """Device unlock notification"""
        device_name = context.get("device_name", "Your device")
        user_name = context.get("user_name", "Someone")
        method = context.get("method", "unknown")

        return {
            "title": "🔓 Device Unlocked",
            "body": f"{device_name} was unlocked by {user_name} via {method}",
            "data": {
                "notification_type": "device_unlock",
                "device_id": str(context.get("device_id", "")),
                "user_name": user_name,
                "method": method,
                "timestamp": context.get("timestamp", "")
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_device_lock(context: Dict[str, Any]) -> Dict[str, Any]:
        """Device lock notification"""
        device_name = context.get("device_name", "Your device")

        return {
            "title": "🔒 Device Locked",
            "body": f"{device_name} has been locked",
            "data": {
                "notification_type": "device_lock",
                "device_id": str(context.get("device_id", "")),
                "device_name": device_name,
                "timestamp": context.get("timestamp", "")
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_ekey_shared(context: Dict[str, Any]) -> Dict[str, Any]:
        """E-key shared notification"""
        device_name = context.get("device_name", "A device")
        issuer_name = context.get("issuer_name", "Someone")

        return {
            "title": "🔑 Access Shared",
            "body": f"{issuer_name} shared access to {device_name} with you",
            "data": {
                "notification_type": "ekey_shared",
                "device_id": str(context.get("device_id", "")),
                "ekey_id": str(context.get("ekey_id", "")),
                "issuer_name": issuer_name,
                "device_name": device_name
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_ekey_revoked(context: Dict[str, Any]) -> Dict[str, Any]:
        """E-key revoked notification"""
        device_name = context.get("device_name", "A device")

        return {
            "title": "🔑 Access Revoked",
            "body": f"Your access to {device_name} has been revoked",
            "data": {
                "notification_type": "ekey_revoked",
                "device_id": str(context.get("device_id", "")),
                "device_name": device_name
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_gateway_offline(context: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway offline alert"""
        gateway_name = context.get("gateway_name", "Your gateway")
        device_count = context.get("affected_devices", 0)

        return {
            "title": "📡 Gateway Offline",
            "body": f"{gateway_name} is offline. {device_count} devices affected.",
            "data": {
                "notification_type": "gateway_offline",
                "gateway_id": str(context.get("gateway_id", "")),
                "gateway_name": gateway_name,
                "affected_devices": str(device_count)
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_gateway_online(context: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway online notification"""
        gateway_name = context.get("gateway_name", "Your gateway")

        return {
            "title": "📡 Gateway Online",
            "body": f"{gateway_name} is back online",
            "data": {
                "notification_type": "gateway_online",
                "gateway_id": str(context.get("gateway_id", "")),
                "gateway_name": gateway_name
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_security_alert(context: Dict[str, Any]) -> Dict[str, Any]:
        """Security alert notification"""
        device_name = context.get("device_name", "Your device")
        attempt_count = context.get("attempt_count", 1)

        return {
            "title": "🚨 Security Alert",
            "body": f"Unauthorized access attempts detected on {device_name} ({attempt_count}x)",
            "data": {
                "notification_type": "security_alert",
                "device_id": str(context.get("device_id", "")),
                "device_name": device_name,
                "attempt_count": str(attempt_count),
                "attempt_type": context.get("attempt_type", "unknown")
            },
            "priority": "normal"
        }

    @staticmethod
    def _build_new_device_login(context: Dict[str, Any]) -> Dict[str, Any]:
        """New device login notification"""
        device_info = context.get("device_info", "Unknown device")
        location = context.get("location", "Unknown location")

        return {
            "title": "🔐 New Device Login",
            "body": f"Login detected from {device_info} at {location}",
            "data": {
                "notification_type": "new_device_login",
                "device_info": device_info,
                "location": location,
                "ip_address": context.get("ip_address", "")
            },
            "priority": "normal"
        }
