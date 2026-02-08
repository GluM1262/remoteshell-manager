-- Database schema for RemoteShell Manager

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    device_token TEXT NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'offline',  -- online, offline
    metadata TEXT  -- JSON for additional device info
);

-- Commands table
CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_id TEXT UNIQUE NOT NULL,
    device_id TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, sent, executing, completed, failed, timeout
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    completed_at TIMESTAMP,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    execution_time REAL,
    error_message TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_commands_device_id ON commands(device_id);
CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status);
CREATE INDEX IF NOT EXISTS idx_commands_created_at ON commands(created_at);
