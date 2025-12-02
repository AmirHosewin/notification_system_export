"""
Firebase Cloud Messaging (FCM) Service

Handles sending push notifications to Android devices via FCM.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession

from app.notification_system.FB.firebase_config import get_firebase_app
from app.notification_system.DB.notification_models import NotificationLog

logger = logging.getLogger(__name__)


class FCMService:
    """
    Firebase Cloud Messaging service for push notifications

    Features:
    - Send individual push notifications
    - Batch notifications to multiple devices
    - FCM token validation
    - Delivery logging
    """

    def __init__(self):
        """Initialize FCM service with Firebase app"""
        self.app = get_firebase_app()
        if not self.app:
            logger.warning("Firebase app not initialized - FCM notifications disabled")

    async def send_push_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        notification_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Send push notification via FCM to a single device.

        Args:
            fcm_token: User's FCM device token
            title: Notification title
            body: Notification body
            data: Data payload (all values must be strings)
            priority: "high" or "normal" (high for low battery only)
            notification_id: Notification ID for logging
            db: Database session for logging delivery attempts

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.app:
            logger.error("Firebase not initialized - cannot send notification")
            return False

        if not fcm_token:
            logger.warning("No FCM token provided - skipping notification")
            return False

        try:
            # Ensure all data values are strings (FCM requirement)
            string_data = {}
            if data:
                string_data = {k: str(v) for k, v in data.items()}

            # Build Android-specific configuration
            android_config = messaging.AndroidConfig(
                priority="high" if priority == "high" else "normal",
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    icon="@drawable/ic_notification",  # App default icon
                    sound="default",  # System default sound
                    channel_id="default"
                )
            )

            # Build FCM message
            message = messaging.Message(
                token=fcm_token,
                android=android_config,
                data=string_data
            )

            # Send message (run in thread pool since firebase_admin is sync)
            response = await asyncio.to_thread(
                messaging.send,
                message,
                app=self.app
            )

            logger.info(f"✅ FCM notification sent successfully: {response}")

            # Log success to database
            if db and notification_id:
                await self._log_delivery(
                    db=db,
                    notification_id=notification_id,
                    fcm_response=response,
                    status="success"
                )

            return True

        except messaging.UnregisteredError:
            # Token is invalid or app was uninstalled
            logger.warning(f"FCM token is invalid or unregistered: {fcm_token[:20]}...")

            if db and notification_id:
                await self._log_delivery(
                    db=db,
                    notification_id=notification_id,
                    status="failed",
                    error_message="Token unregistered or invalid"
                )

            return False

        except Exception as e:
            logger.error(f"❌ FCM send failed: {str(e)}")

            # Log failure to database
            if db and notification_id:
                await self._log_delivery(
                    db=db,
                    notification_id=notification_id,
                    status="failed",
                    error_message=str(e)
                )

            return False

    async def send_batch_notifications(
        self,
        notifications: list[Dict[str, Any]],
        priority: str = "normal"
    ) -> Dict[str, int]:
        """
        Send notifications to multiple devices in batch.

        Args:
            notifications: List of dicts with keys:
                - fcm_token: str
                - title: str
                - body: str
                - data: dict (optional)
            priority: "high" or "normal"

        Returns:
            dict: {"success_count": int, "failure_count": int}
        """
        if not self.app:
            logger.error("Firebase not initialized")
            return {"success_count": 0, "failure_count": len(notifications)}

        success_count = 0
        failure_count = 0

        # Send notifications in parallel
        tasks = []
        for notif in notifications:
            task = self.send_push_notification(
                fcm_token=notif.get("fcm_token"),
                title=notif.get("title"),
                body=notif.get("body"),
                data=notif.get("data"),
                priority=priority
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, bool) and result:
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"📊 Batch send complete: {success_count} success, {failure_count} failed")

        return {
            "success_count": success_count,
            "failure_count": failure_count
        }

    async def validate_fcm_token(self, token: str) -> bool:
        """
        Check if FCM token is valid by sending a test message with dry_run=True.

        Args:
            token: FCM token to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not self.app or not token:
            return False

        try:
            message = messaging.Message(
                token=token,
                data={"test": "true"}
            )

            # Dry run doesn't actually send, just validates
            await asyncio.to_thread(
                messaging.send,
                message,
                dry_run=True,
                app=self.app
            )

            logger.debug(f"✅ FCM token is valid: {token[:20]}...")
            return True

        except Exception as e:
            logger.debug(f"❌ FCM token is invalid: {str(e)}")
            return False

    async def _log_delivery(
        self,
        db: AsyncSession,
        notification_id: int,
        fcm_response: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        attempt_number: int = 1
    ):
        """
        Log FCM delivery attempt to database.

        Args:
            db: Database session
            notification_id: Notification ID
            fcm_response: FCM API response
            status: "success" or "failed"
            error_message: Error message if failed
            attempt_number: Attempt number
        """
        try:
            log = NotificationLog(
                notification_id=notification_id,
                attempt_number=attempt_number,
                fcm_response=fcm_response,
                status=status,
                error_message=error_message
            )
            db.add(log)
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to log notification delivery: {str(e)}")
            # Don't fail the notification send just because logging failed
            await db.rollback()
