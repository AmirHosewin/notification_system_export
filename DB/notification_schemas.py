"""
Pydantic schemas for notification system
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Base schema for notifications"""
    notification_type: str
    title: str
    body: str
    priority: str = "normal"


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: int
    device_id: Optional[int] = None
    gateway_id: Optional[int] = None
    ekey_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: int
    user_id: int
    device_id: Optional[int] = None
    gateway_id: Optional[int] = None
    ekey_id: Optional[int] = None
    status: str
    fcm_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FCMTokenRequest(BaseModel):
    """Schema for FCM token registration"""
    fcm_token: str = Field(..., min_length=1, description="Firebase Cloud Messaging device token")


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics"""
    total: int
    unread: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
