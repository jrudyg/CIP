-- ============================================================================
-- CCE-PLUS INTEGRATION PATCH FOR CIP COMPARISON SCHEMA V3
-- ============================================================================
-- Purpose: Add CCE-Plus risk scoring and cascade detection to comparison_entries
-- Apply: BEFORE executing comparison_schema_v3_final.sql migration
-- Date: 2026-01-02
-- ============================================================================

-- ============================================================================
-- OPTION A: If schema v3 NOT YET MIGRATED (recommended)
-- Add these columns to comparison_entries table definition
-- ============================================================================

/*
Add to comparison_entries CREATE TABLE statement:

    -- CCE-Plus Integration (Risk Scoring)
    cce_risk_score      DECIMAL(3,1),                   -- 0.0-10.0 weighted score
    cce_risk_level      VARCHAR(10),                    -- CRITICAL/HIGH/MEDIUM/LOW/MINIMAL
    cce_severity        INTEGER,                        -- Raw severity (1-10)
    cce_complexity      INTEGER,                        -- Raw complexity (1-10)  
    cce_impact          INTEGER,                        -- Raw impact (1-10)
    
    -- CCE-Plus Integration (Statutory Detection)
    cce_statutory_flag  VARCHAR(20),                    -- UCC-2-719, UCC-2-302, UCC-2-717, NULL
    cce_statutory_cite  VARCHAR(50),                    -- Full citation: "6 Del. C. § 2-719(2)"
    
    -- CCE-Plus Integration (Cascade Analysis)
    cce_cascade_id      VARCHAR(20),                    -- CASCADE-001, CASCADE-002, CASCADE-003, NULL
    cce_cascade_name    VARCHAR(50),                    -- "Prepayment Trap", "Indemnification Collapse"
    
    -- Combined Priority Score (for display sorting)
    display_priority    DECIMAL(4,3),                   -- 0.000-1.000 (risk × delta weighted)
*/

-- ============================================================================
-- OPTION B: If schema v3 ALREADY MIGRATED (ALTER statements)
-- ============================================================================

-- Risk Scoring Columns
ALTER TABLE comparison_entries ADD COLUMN cce_risk_score DECIMAL(3,1);
ALTER TABLE comparison_entries ADD COLUMN cce_risk_level VARCHAR(10);
ALTER TABLE comparison_entries ADD COLUMN cce_severity INTEGER;
ALTER TABLE comparison_entries ADD COLUMN cce_complexity INTEGER;
ALTER TABLE comparison_entries ADD COLUMN cce_impact INTEGER;

-- Statutory Detection Columns
ALTER TABLE comparison_entries ADD COLUMN cce_statutory_flag VARCHAR(20);
ALTER TABLE comparison_entries ADD COLUMN cce_statutory_cite VARCHAR(50);

-- Cascade Analysis Columns
ALTER TABLE comparison_entries ADD COLUMN cce_cascade_id VARCHAR(20);
ALTER TABLE comparison_entries ADD COLUMN cce_cascade_name VARCHAR(50);

-- Display Priority Column
ALTER TABLE comparison_entries ADD COLUMN display_priority DECIMAL(4,3);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Fast lookup by risk level (for filtering)
CREATE INDEX idx_comparison_entries_risk_level 
ON comparison_entries(cce_risk_level);

-- Fast lookup by statutory flag (for compliance reports)
CREATE INDEX idx_comparison_entries_statutory 
ON comparison_entries(cce_statutory_flag);

-- Fast lookup by cascade (for cascade analysis views)
CREATE INDEX idx_comparison_entries_cascade 
ON comparison_entries(cce_cascade_id);

-- Sort by priority (for display)
CREATE INDEX idx_comparison_entries_priority 
ON comparison_entries(display_priority DESC);

-- ============================================================================
-- UPDATE v_comparison_display VIEW
-- ============================================================================

DROP VIEW IF EXISTS v_comparison_display;

CREATE VIEW v_comparison_display AS
SELECT 
    ce.id,
    ce.comparison_id,
    ce.clause_type,
    ce.section_number,
    ce.v1_content,
    ce.v2_content,
    ce.redline_html,
    ce.change_type,
    ce.match_confidence,
    ce.business_impact,
    ce.alignment_status,
    ce.qa_state,
    
    -- CCE-Plus Risk Data
    ce.cce_risk_score,
    ce.cce_risk_level,
    ce.cce_severity,
    ce.cce_complexity,
    ce.cce_impact,
    
    -- CCE-Plus Statutory Data
    ce.cce_statutory_flag,
    ce.cce_statutory_cite,
    
    -- CCE-Plus Cascade Data
    ce.cce_cascade_id,
    ce.cce_cascade_name,
    
    -- Display Priority
    ce.display_priority,
    
    -- Comparison Metadata
    c.v1_contract_id,
    c.v2_contract_id,
    c.created_at AS comparison_date
    
FROM comparison_entries ce
JOIN comparisons c ON ce.comparison_id = c.id
ORDER BY ce.display_priority DESC NULLS LAST;

-- ============================================================================
-- NEW VIEW: CASCADE ALERTS
-- ============================================================================

CREATE VIEW v_cascade_alerts AS
SELECT 
    c.id AS comparison_id,
    c.v1_contract_id,
    c.v2_contract_id,
    ce.cce_cascade_id,
    ce.cce_cascade_name,
    GROUP_CONCAT(ce.section_number, ', ') AS affected_sections,
    MAX(ce.cce_risk_score) AS max_risk,
    COUNT(*) AS clause_count,
    ce.cce_statutory_flag AS statutory_violation
FROM comparisons c
JOIN comparison_entries ce ON c.id = ce.comparison_id
WHERE ce.cce_cascade_id IS NOT NULL
GROUP BY c.id, ce.cce_cascade_id, ce.cce_cascade_name, ce.cce_statutory_flag
ORDER BY max_risk DESC;

-- ============================================================================
-- NEW VIEW: RISK SUMMARY BY COMPARISON
-- ============================================================================

CREATE VIEW v_comparison_risk_summary AS
SELECT 
    c.id AS comparison_id,
    c.v1_contract_id,
    c.v2_contract_id,
    c.created_at,
    
    -- Risk Distribution
    COUNT(*) AS total_clauses,
    SUM(CASE WHEN ce.cce_risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN ce.cce_risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN ce.cce_risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_count,
    SUM(CASE WHEN ce.cce_risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_count,
    
    -- Aggregate Scores
    ROUND(AVG(ce.cce_risk_score), 1) AS avg_risk_score,
    MAX(ce.cce_risk_score) AS max_risk_score,
    
    -- Statutory Flags
    SUM(CASE WHEN ce.cce_statutory_flag IS NOT NULL THEN 1 ELSE 0 END) AS statutory_conflicts,
    
    -- Cascade Alerts
    COUNT(DISTINCT ce.cce_cascade_id) AS cascade_count
    
FROM comparisons c
JOIN comparison_entries ce ON c.id = ce.comparison_id
GROUP BY c.id, c.v1_contract_id, c.v2_contract_id, c.created_at;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check columns added
-- SELECT sql FROM sqlite_master WHERE name = 'comparison_entries';

-- Check views created
-- SELECT name FROM sqlite_master WHERE type = 'view' AND name LIKE 'v_%';

-- Check indexes created
-- SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_comparison%';

-- ============================================================================
-- END OF PATCH
-- ============================================================================
