"""
Core Notification Service

Central orchestrator for notification creation, delivery, and management.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User
from app.notification_system.DB.notification_models import Notification
from app.notification_system.services.fcm_service import FCMService
from app.notification_system.services.notification_messages import NotificationMessageBuilder
from app.notification_system.utils.notification_types import NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Core notification orchestration service

    Responsibilities:
    - Create notification records in database
    - Build notification messages
    - Send via FCM
    - Track delivery status
    - Provide notification history
    """

    def __init__(self):
        """Initialize notification service"""
        self.fcm_service = FCMService()
        self.message_builder = NotificationMessageBuilder()

    async def create_and_send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[Notification]:
        """
        Create notification record and send via FCM.

        This is the main entry point for sending notifications.

        Args:
            user_id: User to notify
            notification_type: Type of notification
            context: Context data (device_id, battery_level, device_name, etc.)
            db: Database session

        Returns:
            Notification: Created notification record, or None if user has no FCM token

        Example:
            await service.create_and_send_notification(
                user_id=user.id,
                notification_type=NotificationType.LOW_BATTERY,
                context={
                    "device_id": 123,
                    "device_name": "Front Door",
                    "battery_level": 15,
                    "timestamp": datetime.utcnow().isoformat()
                },
                db=db
            )
        """
        try:
            # Get user with FCM token
            user = await db.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None

            if not user.fcm_token:
                logger.warning(f"User {user_id} has no FCM token - skipping notification")
                return None

            # Build notification message
            message = self.message_builder.build_notification(
                notification_type, context
            )

            # Create database record
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type.value,
                priority=message["priority"],
                title=message["title"],
                body=message["body"],
                data=message["data"],
                device_id=context.get("device_id"),
                gateway_id=context.get("gateway_id"),
                ekey_id=context.get("ekey_id"),
                metadata=context,
                status="pending"
            )
            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            logger.info(
                f"📝 Notification created: ID={notification.id}, "
                f"Type={notification_type.value}, User={user_id}"
            )

            # Send via FCM
            success = await self.fcm_service.send_push_notification(
                fcm_token=user.fcm_token,
                title=message["title"],
                body=message["body"],
                data=message["data"],
                priority=message["priority"],
                notification_id=notification.id,
                db=db
            )

            # Update notification status
            if success:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                logger.info(f"✅ Notification {notification.id} sent successfully")
            else:
                notification.status = "failed"
                logger.error(f"❌ Notification {notification.id} failed to send")

            await db.commit()
            return notification

        except Exception as e:
            logger.error(f"❌ Failed to create/send notification: {str(e)}")
            await db.rollback()
            return None

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession = None
    ) -> List[Notification]:
        """
        Get user's notification history.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            db: Database session

        Returns:
            List of Notification objects
        """
        try:
            query = select(Notification).where(Notification.user_id == user_id)

            if unread_only:
                query = query.where(Notification.read_at.is_(None))

            query = query.order_by(Notification.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            notifications = result.scalars().all()

            logger.debug(f"📋 Retrieved {len(notifications)} notifications for user {user_id}")

            return list(notifications)

        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []

    async def mark_as_read(
        self,
        notification_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)
            db: Database session

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = await db.get(Notification, notification_id)

            if not notification:
                logger.warning(f"Notification {notification_id} not found")
                return False

            # Verify ownership
            if notification.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to mark notification {notification_id} "
                    f"belonging to user {notification.user_id}"
                )
                return False

            # Mark as read
            notification.read_at = datetime.utcnow()
            notification.status = "read"
            await db.commit()

            logger.debug(f"✅ Notification {notification_id} marked as read")
            return True

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            await db.rollback()
            return False

    async def mark_all_as_read(
        self,
        user_id: int,
        db: AsyncSession
    ) -> int:
        """
        Mark all user's notifications as read.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            int: Number of notifications marked as read
        """
        try:
            # Get all unread notifications
            query = select(Notification).where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None)
            )
            result = await db.execute(query)
            notifications = result.scalars().all()

            count = 0
            for notif in notifications:
                notif.read_at = datetime.utcnow()
                notif.status = "read"
                count += 1

            await db.commit()

            logger.info(f"✅ Marked {count} notifications as read for user {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to mark all as read: {str(e)}")
            await db.rollback()
            return 0

    async def get_notification_stats(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get notification statistics for user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            dict: Statistics including total, unread count, by type, etc.
        """
        try:
            # Get all notifications
            all_query = select(Notification).where(Notification.user_id == user_id)
            all_result = await db.execute(all_query)
            all_notifs = all_result.scalars().all()

            # Count unread
            unread = sum(1 for n in all_notifs if n.read_at is None)

            # Count by type
            by_type = {}
            for notif in all_notifs:
                by_type[notif.notification_type] = by_type.get(notif.notification_type, 0) + 1

            # Count by priority
            by_priority = {}
            for notif in all_notifs:
                by_priority[notif.priority] = by_priority.get(notif.priority, 0) + 1

            return {
                "total": len(all_notifs),
                "unread": unread,
                "by_type": by_type,
                "by_priority": by_priority
            }

        except Exception as e:
            logger.error(f"Failed to get notification stats: {str(e)}")
            return {
                "total": 0,
                "unread": 0,
                "by_type": {},
                "by_priority": {}
            }
