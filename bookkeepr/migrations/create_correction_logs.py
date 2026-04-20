"""
Database Migration: Add CorrectionLog Table for Phase 2

This migration creates the correction_logs table for the AI Learning System.

Run with: flask db migrate -m "Add correction_logs for AI learning"
           flask db upgrade
"""

# SQL to create correction_logs table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS correction_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    transaction_id INTEGER NOT NULL,
    original_account_id INTEGER,
    original_confidence FLOAT DEFAULT 0.0,
    corrected_account_id INTEGER NOT NULL,
    payee_name VARCHAR(256),
    description TEXT,
    amount DECIMAL(15, 2),
    transaction_type VARCHAR(50),
    ai_confidence FLOAT DEFAULT 0.0,
    ai_rules_matched JSON,
    correction_pattern VARCHAR(256),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (company_id) REFERENCES companies (id),
    FOREIGN KEY (transaction_id) REFERENCES transactions (id),
    FOREIGN KEY (original_account_id) REFERENCES accounts (id),
    FOREIGN KEY (corrected_account_id) REFERENCES accounts (id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS ix_correction_logs_user_id ON correction_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_correction_logs_company_id ON correction_logs (company_id);
CREATE INDEX IF NOT EXISTS ix_correction_logs_transaction_id ON correction_logs (transaction_id);
CREATE INDEX IF NOT EXISTS ix_correction_logs_payee_name ON correction_logs (payee_name);
CREATE INDEX IF NOT EXISTS ix_correction_logs_created_at ON correction_logs (created_at);
"""

print(CREATE_TABLE_SQL)
