-- CIP Database Migration: Add new metadata fields
-- Run against: data/contracts.db
-- Date: 2026-01-05

-- New columns for enhanced metadata extraction
ALTER TABLE contracts ADD COLUMN counterparty_role TEXT;
ALTER TABLE contracts ADD COLUMN payment_terms TEXT;
ALTER TABLE contracts ADD COLUMN liability_cap TEXT;
ALTER TABLE contracts ADD COLUMN governing_law TEXT;
ALTER TABLE contracts ADD COLUMN warranty_period TEXT;
ALTER TABLE contracts ADD COLUMN file_size INTEGER;

-- Verify columns added
-- Run: sqlite3 data/contracts.db ".schema contracts"
