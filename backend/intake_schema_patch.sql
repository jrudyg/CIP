-- ============================================================================
-- INTAKE ENHANCEMENT SCHEMA PATCH
-- ============================================================================
-- Purpose: Enable comprehensive intake with risk scoring, RAG, and metadata
-- Apply: Before deploying enhanced intake engine
-- Date: 2026-01-02
-- Principle: Lean - only add what's needed, nothing more
-- ============================================================================

-- ============================================================================
-- ENHANCED CLAUSES TABLE
-- ============================================================================

-- Verbatim text storage (current 'text' field is AI-summarized)
ALTER TABLE clauses ADD COLUMN verbatim_text TEXT;

-- Section identification
ALTER TABLE clauses ADD COLUMN section_number VARCHAR(20);
ALTER TABLE clauses ADD COLUMN section_title VARCHAR(200);

-- Text metrics
ALTER TABLE clauses ADD COLUMN word_count INTEGER DEFAULT 0;

-- CCE-Plus risk scoring (at intake)
ALTER TABLE clauses ADD COLUMN cce_risk_score DECIMAL(3,1);
ALTER TABLE clauses ADD COLUMN cce_risk_level VARCHAR(10);
ALTER TABLE clauses ADD COLUMN cce_statutory_flag VARCHAR(20);
ALTER TABLE clauses ADD COLUMN cce_cascade_risk BOOLEAN DEFAULT 0;

-- RAG reference
ALTER TABLE clauses ADD COLUMN embedding_id VARCHAR(64);
ALTER TABLE clauses ADD COLUMN chunk_hash VARCHAR(64);

-- ============================================================================
-- ENHANCED CONTRACTS TABLE
-- ============================================================================

-- Extracted parties
ALTER TABLE contracts ADD COLUMN party_client VARCHAR(200);
ALTER TABLE contracts ADD COLUMN party_vendor VARCHAR(200);

-- Key dates
ALTER TABLE contracts ADD COLUMN effective_date DATE;
ALTER TABLE contracts ADD COLUMN expiration_date DATE;

-- Financial
ALTER TABLE contracts ADD COLUMN contract_value DECIMAL(15,2);
ALTER TABLE contracts ADD COLUMN currency VARCHAR(3) DEFAULT 'USD';

-- Legal
ALTER TABLE contracts ADD COLUMN governing_law VARCHAR(50);

-- Market Intelligence link (public companies only)
ALTER TABLE contracts ADD COLUMN vendor_ticker VARCHAR(10);
ALTER TABLE contracts ADD COLUMN vendor_cik VARCHAR(20);

-- Intake status
ALTER TABLE contracts ADD COLUMN intake_status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE contracts ADD COLUMN intake_completed_at TIMESTAMP;
ALTER TABLE contracts ADD COLUMN intake_risk_summary TEXT;

-- Document integrity
ALTER TABLE contracts ADD COLUMN document_hash VARCHAR(64);
ALTER TABLE contracts ADD COLUMN clause_count INTEGER DEFAULT 0;

-- ============================================================================
-- ANNOTATIONS TABLE (NEW)
-- ============================================================================

CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    clause_id INTEGER,
    annotation_type VARCHAR(20) NOT NULL,  -- RISK, STATUTORY, CASCADE, METADATA, USER
    severity VARCHAR(10),                   -- CRITICAL, HIGH, MEDIUM, LOW, INFO
    title VARCHAR(200),
    content TEXT NOT NULL,
    source VARCHAR(50) DEFAULT 'INTAKE',    -- INTAKE, ANALYSIS, COMPARE, USER
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (clause_id) REFERENCES clauses(id) ON DELETE CASCADE
);

-- ============================================================================
-- PUBLIC COMPANY LOOKUP TABLE (NEW)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR(200) NOT NULL,
    ticker VARCHAR(10),
    cik VARCHAR(20),
    exchange VARCHAR(20),
    sector VARCHAR(100),
    aliases TEXT,                           -- JSON array of alternate names
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker),
    UNIQUE(cik)
);

-- Seed with common vendors (expand as needed)
INSERT OR IGNORE INTO public_companies (company_name, ticker, cik, exchange, sector, aliases) VALUES
('Amazon.com Inc', 'AMZN', '0001018724', 'NASDAQ', 'Technology', '["Amazon", "AWS", "Amazon Web Services"]'),
('Microsoft Corporation', 'MSFT', '0000789019', 'NASDAQ', 'Technology', '["Microsoft", "Azure", "MS"]'),
('Alphabet Inc', 'GOOGL', '0001652044', 'NASDAQ', 'Technology', '["Google", "GCP", "Google Cloud"]'),
('Salesforce Inc', 'CRM', '0001108524', 'NYSE', 'Technology', '["Salesforce", "SFDC"]'),
('Oracle Corporation', 'ORCL', '0001341439', 'NYSE', 'Technology', '["Oracle"]'),
('SAP SE', 'SAP', '0001000184', 'NYSE', 'Technology', '["SAP"]'),
('International Business Machines', 'IBM', '0000051143', 'NYSE', 'Technology', '["IBM"]'),
('FedEx Corporation', 'FDX', '0001048911', 'NYSE', 'Logistics', '["FedEx", "Federal Express"]'),
('United Parcel Service', 'UPS', '0001090727', 'NYSE', 'Logistics', '["UPS"]'),
('XPO Inc', 'XPO', '0001166003', 'NYSE', 'Logistics', '["XPO Logistics"]'),
('Honeywell International', 'HON', '0000773840', 'NASDAQ', 'Industrial', '["Honeywell", "Honeywell Intelligrated"]'),
('Dematic', NULL, NULL, NULL, 'Automation', '["Dematic", "KION Dematic"]'),
('Zebra Technologies', 'ZBRA', '0000877212', 'NASDAQ', 'Technology', '["Zebra"]');

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Fast clause lookups
CREATE INDEX IF NOT EXISTS idx_clauses_contract ON clauses(contract_id);
CREATE INDEX IF NOT EXISTS idx_clauses_risk ON clauses(cce_risk_level);
CREATE INDEX IF NOT EXISTS idx_clauses_statutory ON clauses(cce_statutory_flag);

-- Fast annotation lookups
CREATE INDEX IF NOT EXISTS idx_annotations_contract ON annotations(contract_id);
CREATE INDEX IF NOT EXISTS idx_annotations_clause ON annotations(clause_id);
CREATE INDEX IF NOT EXISTS idx_annotations_type ON annotations(annotation_type);

-- Fast company lookups
CREATE INDEX IF NOT EXISTS idx_companies_name ON public_companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON public_companies(ticker);

-- ============================================================================
-- VIEWS FOR INTAKE SUMMARY
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_contract_risk_profile AS
SELECT 
    c.id AS contract_id,
    c.title,
    c.party_vendor,
    c.vendor_ticker,
    c.intake_status,
    c.clause_count,
    
    -- Risk distribution
    SUM(CASE WHEN cl.cce_risk_level = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_clauses,
    SUM(CASE WHEN cl.cce_risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_clauses,
    SUM(CASE WHEN cl.cce_risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_clauses,
    SUM(CASE WHEN cl.cce_risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_clauses,
    
    -- Aggregate scores
    ROUND(AVG(cl.cce_risk_score), 1) AS avg_risk_score,
    MAX(cl.cce_risk_score) AS max_risk_score,
    
    -- Flags
    SUM(CASE WHEN cl.cce_statutory_flag IS NOT NULL THEN 1 ELSE 0 END) AS statutory_flags,
    SUM(CASE WHEN cl.cce_cascade_risk = 1 THEN 1 ELSE 0 END) AS cascade_risks
    
FROM contracts c
LEFT JOIN clauses cl ON c.id = cl.contract_id
GROUP BY c.id;

CREATE VIEW IF NOT EXISTS v_intake_queue AS
SELECT 
    c.id,
    c.title,
    c.party_vendor,
    c.created_at,
    c.intake_status,
    CASE 
        WHEN c.intake_status = 'COMPLETE' THEN c.intake_completed_at
        ELSE NULL
    END AS completed_at
FROM contracts c
ORDER BY 
    CASE c.intake_status 
        WHEN 'PENDING' THEN 1 
        WHEN 'PROCESSING' THEN 2 
        WHEN 'COMPLETE' THEN 3 
        WHEN 'ERROR' THEN 0 
    END,
    c.created_at DESC;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- SELECT sql FROM sqlite_master WHERE name = 'clauses';
-- SELECT sql FROM sqlite_master WHERE name = 'contracts';
-- SELECT sql FROM sqlite_master WHERE name = 'annotations';
-- SELECT * FROM public_companies;

-- ============================================================================
-- END OF PATCH
-- ============================================================================
