"""
Notification API Routes

Endpoints for FCM token registration and notification management.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models.database import User
from app.notification_system.DB.notification_schemas import (
    FCMTokenRequest,
    NotificationResponse,
    NotificationStatsResponse,
    TestNotificationRequest
)
from app.notification_system.services.notification_service import NotificationService
from app.notification_system.utils.notification_types import NotificationType
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["notifications"])


@router.post("/register_fcm_token", status_code=status.HTTP_200_OK)
async def register_fcm_token(
    token_data: FCMTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register FCM device token for push notifications.

    Called by Android app after user login to enable push notifications.

    **Request Body:**
    ```json
    {
        "fcm_token": "fcm_device_token_string"
    }
    ```

    **Response:**
    ```json
    {
        "message": "FCM token registered successfully"
    }
    ```
    """
    try:
        # Update user's FCM token
        current_user.fcm_token = token_data.fcm_token
        current_user.fcm_token_updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"✅ FCM token registered for user {current_user.id}")

        return {
            "message": "FCM token registered successfully",
            "user_id": current_user.id
        }

    except Exception as e:
        logger.error(f"Failed to register FCM token: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register FCM token"
        )


@router.delete("/fcm_token", status_code=status.HTTP_200_OK)
async def remove_fcm_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remove FCM token (called on logout or app uninstall).

    **Response:**
    ```json
    {
        "message": "FCM token removed successfully"
    }
    ```
    """
    try:
        current_user.fcm_token = None
        current_user.fcm_token_updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"✅ FCM token removed for user {current_user.id}")

        return {
            "message": "FCM token removed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to remove FCM token: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove FCM token"
        )


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get user's notification history.

    **Query Parameters:**
    - `unread_only`: Only return unread notifications (default: false)
    - `limit`: Maximum number of notifications (default: 50, max: 100)
    - `offset`: Offset for pagination (default: 0)

    **Response:**
    ```json
    [
        {
            "id": 1,
            "user_id": 123,
            "notification_type": "low_battery",
            "priority": "high",
            "title": "⚠️ Low Battery Alert",
            "body": "Front Door battery is at 15%. Please replace soon.",
            "data": {
                "notification_type": "low_battery",
                "device_id": "456",
                "battery_level": "15",
                "device_name": "Front Door"
            },
            "device_id": 456,
            "status": "sent",
            "created_at": "2025-01-15T10:30:00Z",
            "sent_at": "2025-01-15T10:30:01Z",
            "read_at": null
        }
    ]
    ```
    """
    try:
        notification_service = NotificationService()
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
            db=db
        )

        return notifications

    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark a notification as read.

    **Path Parameters:**
    - `notification_id`: Notification ID to mark as read

    **Response:**
    ```json
    {
        "message": "Notification marked as read"
    }
    ```
    """
    try:
        notification_service = NotificationService()
        success = await notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
            db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )

        return {
            "message": "Notification marked as read",
            "notification_id": notification_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.put("/notifications/read_all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark all user's notifications as read.

    **Response:**
    ```json
    {
        "message": "All notifications marked as read",
        "count": 15
    }
    ```
    """
    try:
        notification_service = NotificationService()
        count = await notification_service.mark_all_as_read(
            user_id=current_user.id,
            db=db
        )

        return {
            "message": "All notifications marked as read",
            "count": count
        }

    except Exception as e:
        logger.error(f"Failed to mark all as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get notification statistics for current user.

    **Response:**
    ```json
    {
        "total": 50,
        "unread": 12,
        "by_type": {
            "low_battery": 15,
            "device_unlock": 20,
            "gateway_offline": 5
        },
        "by_priority": {
            "high": 15,
            "normal": 35
        }
    }
    ```
    """
    try:
        notification_service = NotificationService()
        stats = await notification_service.get_notification_stats(
            user_id=current_user.id,
            db=db
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to get notification stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics"
        )


@router.post("/test_notification", status_code=status.HTTP_200_OK)
async def send_test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send test notification (DEBUG MODE ONLY).

    Used for testing FCM integration during development.

    **Request Body:**
    ```json
    {
        "notification_type": "low_battery",
        "context": {
            "device_id": 123,
            "device_name": "Test Device",
            "battery_level": 15
        }
    }
    ```

    **Response:**
    ```json
    {
        "message": "Test notification sent successfully",
        "notification_id": 456
    }
    ```
    """
    # Only allow in DEBUG mode
    if not getattr(settings, "DEBUG", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test notifications are only available in DEBUG mode"
        )

    try:
        # Check if user has FCM token
        if not current_user.fcm_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no FCM token registered. Please register FCM token first."
            )

        # Validate notification type
        try:
            notification_type = NotificationType(test_data.notification_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification type: {test_data.notification_type}"
            )

        # Send test notification
        notification_service = NotificationService()
        notification = await notification_service.create_and_send_notification(
            user_id=current_user.id,
            notification_type=notification_type,
            context=test_data.context,
            db=db
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test notification"
            )

        return {
            "message": "Test notification sent successfully",
            "notification_id": notification.id,
            "notification_type": notification.notification_type,
            "status": notification.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )
