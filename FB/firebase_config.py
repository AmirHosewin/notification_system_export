"""
Firebase Admin SDK Configuration

Initializes Firebase for FCM push notifications.
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

# Global Firebase app instance
_firebase_app = None


def get_firebase_app():
    """
    Get or initialize Firebase Admin SDK app.
    Called once at application startup.

    Returns:
        firebase_admin.App: Firebase app instance or None if FCM is disabled
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    # Check if FCM is enabled
    from app.config.settings import settings
    if not settings.NOTIFICATION_FCM_ENABLED:
        logger.warning("FCM notifications are disabled in settings")
        return None

    # Get credentials path
    cred_path = settings.FIREBASE_CREDENTIALS_PATH

    if not os.path.exists(cred_path):
        logger.error(f"Firebase credentials file not found at: {cred_path}")
        raise FileNotFoundError(
            f"Firebase credentials not found at {cred_path}. "
            "Please ensure the credentials file exists."
        )

    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)

        logger.info(f"✅ Firebase Admin SDK initialized successfully")
        logger.info(f"📁 Credentials: {cred_path}")
        logger.info(f"📱 App name: {settings.FCM_APP_NAME}")

        return _firebase_app

    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
        raise


def is_firebase_initialized() -> bool:
    """Check if Firebase has been initialized"""
    return _firebase_app is not None
