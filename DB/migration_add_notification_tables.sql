-- Database Migration: Add Notification System Tables
-- Run this SQL script to add notification tables to your existing database

-- ============================================================
-- 1. Add FCM token fields to user_table
-- ============================================================

-- Check if columns don't exist before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_table' AND column_name = 'fcm_token'
    ) THEN
        ALTER TABLE user_table ADD COLUMN fcm_token VARCHAR(255);
        ALTER TABLE user_table ADD COLUMN fcm_token_updated_at TIMESTAMP;
    END IF;
END $$;


-- ============================================================
-- 2. Create notification_table
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_table (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_table(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'normal',
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    data JSONB,
    device_id INTEGER REFERENCES device_table(id) ON DELETE SET NULL,
    gateway_id INTEGER REFERENCES gateway_table(id) ON DELETE SET NULL,
    ekey_id INTEGER REFERENCES ekey_table(id) ON DELETE SET NULL,
    metadata JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    read_at TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notification_table(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_type ON notification_table(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_status ON notification_table(status);
CREATE INDEX IF NOT EXISTS idx_notification_created_at ON notification_table(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_read_at ON notification_table(read_at);
CREATE INDEX IF NOT EXISTS idx_notification_device_id ON notification_table(device_id);


-- ============================================================
-- 3. Create notification_log_table (FCM delivery tracking)
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_log_table (
    id BIGSERIAL PRIMARY KEY,
    notification_id BIGINT NOT NULL REFERENCES notification_table(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    fcm_response TEXT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_notification_log_notification_id ON notification_log_table(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_log_status ON notification_log_table(status);
CREATE INDEX IF NOT EXISTS idx_notification_log_created_at ON notification_log_table(created_at DESC);


-- ============================================================
-- 4. Create battery_alert_tracker_table (Prevent duplicate alerts)
-- ============================================================

CREATE TABLE IF NOT EXISTS battery_alert_tracker_table (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES device_table(id) ON DELETE CASCADE,
    last_alert_at TIMESTAMP NOT NULL,
    battery_level_at_alert INTEGER NOT NULL,
    alert_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add unique constraint and indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_battery_tracker_device_unique ON battery_alert_tracker_table(device_id);
CREATE INDEX IF NOT EXISTS idx_battery_tracker_last_alert ON battery_alert_tracker_table(last_alert_at);


-- ============================================================
-- 5. Verification queries
-- ============================================================

-- Check if all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN (
        'notification_table',
        'notification_log_table',
        'battery_alert_tracker_table'
    );

    IF table_count = 3 THEN
        RAISE NOTICE '✅ All notification tables created successfully';
    ELSE
        RAISE WARNING '⚠️ Some tables may be missing (found % of 3)', table_count;
    END IF;
END $$;

-- Check FCM token columns
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'user_table'
    AND column_name IN ('fcm_token', 'fcm_token_updated_at');

    IF column_count = 2 THEN
        RAISE NOTICE '✅ FCM token columns added to user_table';
    ELSE
        RAISE WARNING '⚠️ FCM token columns may be missing (found % of 2)', column_count;
    END IF;
END $$;


-- ============================================================
-- 6. Sample data verification (Optional - for testing)
-- ============================================================

-- View table structures
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name IN ('notification_table', 'notification_log_table', 'battery_alert_tracker_table')
-- ORDER BY table_name, ordinal_position;

-- View indexes
-- SELECT tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('notification_table', 'notification_log_table', 'battery_alert_tracker_table')
-- ORDER BY tablename, indexname;
