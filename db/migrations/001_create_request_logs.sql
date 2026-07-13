-- db/migrations/001_create_request_logs.sql

CREATE TABLE IF NOT EXISTS request_logs (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'RECEIVED',
    sender_email VARCHAR(255) NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Note: The UNIQUE constraint on message_id provides our idempotency.
-- If an email is processed twice, the second insert will fail.
