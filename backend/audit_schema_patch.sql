-- ============================================================================
-- AUDIT TRAIL SCHEMA FOR REPORT REPRODUCIBILITY
-- ============================================================================
-- Purpose: Track full provenance of every report for reproducibility
-- Date: 2026-01-03
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Report identification
    report_id VARCHAR(50) NOT NULL UNIQUE,  -- RPT-YYYY-MM-DD-NNN
    report_type VARCHAR(30) NOT NULL,        -- REDLINE_REPORT, COMPARISON_REPORT

    -- Input provenance
    contract_id INTEGER,
    v1_contract_id INTEGER,                  -- For comparisons
    v2_contract_id INTEGER,                  -- For comparisons
    input_hash VARCHAR(64) NOT NULL,         -- SHA-256 of input(s)

    -- System versions (for reproducibility)
    system_version VARCHAR(20) NOT NULL,
    risk_scorer_version VARCHAR(20) NOT NULL,
    ucc_logic_version VARCHAR(20) NOT NULL,
    prompt_name VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(20) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    template_name VARCHAR(50) NOT NULL,
    template_version VARCHAR(20) NOT NULL,
    template_hash VARCHAR(64) NOT NULL,

    -- Output
    output_hash VARCHAR(64) NOT NULL,        -- SHA-256 of report
    output_path VARCHAR(500),                -- Where saved

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),

    -- Verification
    last_verified_at TIMESTAMP,
    last_verified_by VARCHAR(50),
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED',
    verification_notes TEXT,

    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (v1_contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (v2_contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_report_id ON audit_trail(report_id);
CREATE INDEX IF NOT EXISTS idx_audit_contract ON audit_trail(contract_id);
CREATE INDEX IF NOT EXISTS idx_audit_output ON audit_trail(output_hash);

-- ============================================================================
-- END OF AUDIT TRAIL SCHEMA
-- ============================================================================
