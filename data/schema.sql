-- data/schema.sql
-- Run this once to initialize tables (or via migration script)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,          -- Use hashed passwords!
    role TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,                   -- e.g. 'CAN_TX', 'ATTACK', 'BLE_RX'
    angle REAL,
    latency_us INTEGER,
    queue_size INTEGER,
    priority INTEGER,
    timestamp_us INTEGER,
    extra_json TEXT,                      -- JSON for flexible fields (e.g. attack severity)
    anomaly_score REAL DEFAULT NULL,
    attack_label TEXT DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_type ON telemetry(type);