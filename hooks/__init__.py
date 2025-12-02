"""
Notification Hooks

Event hooks that trigger notifications based on device operations.
"""
from app.notification_system.hooks.device_hooks import (
    check_and_notify_low_battery,
    notify_device_unlock,
    notify_gateway_offline
)

__all__ = [
    "check_and_notify_low_battery",
    "notify_device_unlock",
    "notify_gateway_offline"
]
