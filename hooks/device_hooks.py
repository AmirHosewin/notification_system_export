"""
Device Event Hooks for Notifications

Hooks that integrate with existing device operations to trigger notifications.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Device, User
from app.notification_system.DB.notification_models import BatteryAlertTracker
from app.notification_system.services.notification_service import NotificationService
from app.notification_system.utils.notification_types import NotificationType

logger = logging.getLogger(__name__)


async def check_and_notify_low_battery(
    device_id: int,
    battery_level: int,
    db: AsyncSession,
    threshold: int = 20,
    cooldown_hours: int = 24,
    min_drop: int = 5
) -> bool:
    """
    Check battery level and send notification if needed.

    Triggers notification when:
    1. Battery level <= threshold (default 20%)
    2. No alert sent in last cooldown_hours (default 24h)
    3. Battery dropped by at least min_drop% since last alert

    Args:
        device_id: Device ID to check
        battery_level: Current battery level (0-100)
        db: Database session
        threshold: Battery percentage threshold (default 20%)
        cooldown_hours: Hours to wait between alerts (default 24)
        min_drop: Minimum battery drop to trigger new alert (default 5%)

    Returns:
        bool: True if notification was sent, False otherwise

    Example:
        await check_and_notify_low_battery(
            device_id=123,
            battery_level=15,
            db=db
        )
    """
    try:
        # Check if battery is below threshold
        if battery_level > threshold:
            logger.debug(f"Battery level {battery_level}% is above threshold {threshold}%")
            return False

        # Get device with owner
        device = await db.get(Device, device_id)
        if not device:
            logger.warning(f"Device {device_id} not found")
            return False

        # Get device owner
        user = await db.get(User, device.user_id)
        if not user:
            logger.warning(f"User {device.user_id} not found for device {device_id}")
            return False

        # Check if user has FCM token
        if not user.fcm_token:
            logger.debug(f"User {user.id} has no FCM token - skipping notification")
            return False

        # Check last alert for this device
        query = select(BatteryAlertTracker).where(
            BatteryAlertTracker.device_id == device_id
        ).order_by(BatteryAlertTracker.last_alert_at.desc())

        result = await db.execute(query)
        tracker = result.scalars().first()

        now = datetime.utcnow()
        cooldown_threshold = now - timedelta(hours=cooldown_hours)

        # Check if we need to send notification
        should_notify = False

        if not tracker:
            # First time alert for this device
            should_notify = True
            logger.info(f"First low battery alert for device {device_id}")

        elif tracker.last_alert_at < cooldown_threshold:
            # Cooldown period has passed
            battery_drop = tracker.battery_level_at_alert - battery_level

            if battery_drop >= min_drop:
                should_notify = True
                logger.info(
                    f"Battery dropped by {battery_drop}% since last alert "
                    f"(from {tracker.battery_level_at_alert}% to {battery_level}%)"
                )
            else:
                logger.debug(
                    f"Battery drop of {battery_drop}% is below minimum {min_drop}% - "
                    f"skipping notification"
                )
        else:
            # Within cooldown period
            time_since_last = now - tracker.last_alert_at
            logger.debug(
                f"Within cooldown period - last alert was {time_since_last.total_seconds() / 3600:.1f}h ago"
            )

        if not should_notify:
            return False

        # Build notification context
        context = {
            "device_id": device_id,
            "device_name": device.device_name,
            "battery_level": battery_level,
            "timestamp": now.isoformat()
        }

        # Send notification via NotificationService
        notification_service = NotificationService()
        notification = await notification_service.create_and_send_notification(
            user_id=user.id,
            notification_type=NotificationType.LOW_BATTERY,
            context=context,
            db=db
        )

        if notification:
            # Update or create tracker
            if tracker:
                tracker.last_alert_at = now
                tracker.battery_level_at_alert = battery_level
                tracker.alert_count += 1
            else:
                tracker = BatteryAlertTracker(
                    device_id=device_id,
                    last_alert_at=now,
                    battery_level_at_alert=battery_level,
                    alert_count=1
                )
                db.add(tracker)

            await db.commit()

            logger.info(
                f"✅ Low battery notification sent for device {device_id} "
                f"({device.device_name}) at {battery_level}%"
            )
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Failed to check/send low battery notification: {str(e)}")
        await db.rollback()
        return False


async def notify_device_unlock(
    device_id: int,
    user_name: str,
    unlock_method: str,
    db: AsyncSession
) -> bool:
    """
    Send notification when device is unlocked.

    Args:
        device_id: Device ID
        user_name: Name of user who unlocked
        unlock_method: Method used (app, passcode, fingerprint, rfid, etc.)
        db: Database session

    Returns:
        bool: True if notification sent successfully
    """
    try:
        device = await db.get(Device, device_id)
        if not device:
            return False

        user = await db.get(User, device.user_id)
        if not user or not user.fcm_token:
            return False

        context = {
            "device_id": device_id,
            "device_name": device.device_name,
            "user_name": user_name,
            "method": unlock_method,
            "timestamp": datetime.utcnow().isoformat()
        }

        notification_service = NotificationService()
        notification = await notification_service.create_and_send_notification(
            user_id=user.id,
            notification_type=NotificationType.DEVICE_UNLOCK,
            context=context,
            db=db
        )

        return notification is not None

    except Exception as e:
        logger.error(f"Failed to send unlock notification: {str(e)}")
        return False


async def notify_gateway_offline(
    gateway_id: int,
    gateway_name: str,
    affected_device_count: int,
    db: AsyncSession
) -> bool:
    """
    Send notification when gateway goes offline.

    Args:
        gateway_id: Gateway ID
        gateway_name: Gateway name
        affected_device_count: Number of devices affected
        db: Database session

    Returns:
        bool: True if notification sent successfully
    """
    try:
        # Get gateway owner
        from app.models.database import Gateway
        gateway = await db.get(Gateway, gateway_id)
        if not gateway:
            return False

        user = await db.get(User, gateway.user_id)
        if not user or not user.fcm_token:
            return False

        context = {
            "gateway_id": gateway_id,
            "gateway_name": gateway_name,
            "affected_devices": affected_device_count,
            "timestamp": datetime.utcnow().isoformat()
        }

        notification_service = NotificationService()
        notification = await notification_service.create_and_send_notification(
            user_id=user.id,
            notification_type=NotificationType.GATEWAY_OFFLINE,
            context=context,
            db=db
        )

        return notification is not None

    except Exception as e:
        logger.error(f"Failed to send gateway offline notification: {str(e)}")
        return False
