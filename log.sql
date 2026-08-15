CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    category TEXT,
    urgency TEXT,
    confidence REAL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
 