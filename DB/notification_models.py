"""
Database models for notification system
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.database import Base


class Notification(Base):
    """
    Notification records sent to users via FCM
    """
    __tablename__ = "notification_table"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user_table.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    notification_type = Column(String(50), nullable=False)
    priority = Column(String(10), nullable=False, default="normal")  # 'high' or 'normal'
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)

    # Context references
    device_id = Column(
        Integer,
        ForeignKey("device_table.id", ondelete="SET NULL"),
        nullable=True
    )
    gateway_id = Column(
        Integer,
        ForeignKey("gateway_table.id", ondelete="SET NULL"),
        nullable=True
    )
    ekey_id = Column(
        Integer,
        ForeignKey("ekey_table.id", ondelete="SET NULL"),
        nullable=True
    )

    # Delivery tracking
    status = Column(String(20), default="pending")  # pending, sent, failed, read
    fcm_message_id = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Additional data
    data = Column(JSONB, nullable=True)  # FCM data payload
    metadata = Column(JSONB, nullable=True)  # Extra context

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_notification_user_created', 'user_id', 'created_at'),
        Index('idx_notification_device_type', 'device_id', 'notification_type'),
        Index('idx_notification_status', 'status'),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    device = relationship("Device", foreign_keys=[device_id])

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"


class NotificationLog(Base):
    """
    Audit trail for FCM delivery attempts
    """
    __tablename__ = "notification_log_table"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    notification_id = Column(
        BigInteger,
        ForeignKey("notification_table.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attempt_number = Column(Integer, default=1)
    fcm_response = Column(Text, nullable=True)  # FCM API response
    status = Column(String(20))  # success, failed
    error_message = Column(Text, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    notification = relationship("Notification", foreign_keys=[notification_id])

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, notification_id={self.notification_id}, status={self.status})>"


class BatteryAlertTracker(Base):
    """
    Prevents duplicate low battery alerts with cooldown logic
    """
    __tablename__ = "battery_alert_tracker_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        Integer,
        ForeignKey("device_table.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    last_battery_level = Column(Integer, nullable=True)
    last_alert_sent_at = Column(DateTime, nullable=True)
    alert_threshold = Column(Integer, default=20)  # Alert when battery <= 20%
    cooldown_hours = Column(Integer, default=24)  # Don't re-alert for 24 hours

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    device = relationship("Device", foreign_keys=[device_id])

    def __repr__(self):
        return f"<BatteryAlertTracker(device_id={self.device_id}, last_level={self.last_battery_level})>"
