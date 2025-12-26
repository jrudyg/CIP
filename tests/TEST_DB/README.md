# CIP Test Database

A comprehensive test database with 100 contracts for testing the Contract Intelligence Platform (CIP).

## Database Location

```
C:/Users/jrudy/CIP/tests/TEST_DB/test_contracts.db
```

## Quick Start

```bash
# Regenerate the test database
python generate_test_db.py

# Verify database integrity
python verify_db.py
```

## Database Schema

### Core Tables

| Table | Description | Records |
|-------|-------------|---------|
| `contracts` | Main contract records | 100 |
| `clauses` | Individual contract clauses | ~1000 |
| `risk_assessments` | Risk analysis per contract | 100 |
| `negotiations` | Negotiation strategies | ~60 |
| `analysis_snapshots` | Point-in-time analysis | 100 |
| `comparison_snapshots` | Version comparisons | ~10 |
| `contract_relationships` | Parent-child links | ~40 |
| `redline_snapshots` | Redline sessions | ~15 |
| `redlines` | Individual redline items | ~65 |
| `audit_log` | Activity tracking | ~450 |
| `comparisons` | Comparison reports | ~10 |
| `risk_reports` | Risk report records | ~90 |
| `related_documents` | Attached documents | ~100 |
| `contract_versions` | Version history | ~20 |

## Data Distribution

### Contract Types (14 types)
- NDA, MNDA, MSA, SOW, SLA, MOU, LOI
- AMENDMENT, ADDENDUM, ORDER
- LICENSE, LEASE, EMPLOYMENT, OTHER

### Party Relationships (5 types)
- CUSTOMER - They pay us
- VENDOR - We pay them
- PARTNER - Mutual value exchange
- RESELLER - They sell our products
- CONSULTANT - They advise us

### Contract Purposes (7 types)
- SERVICES, PRODUCTS, LICENSING
- DISTRIBUTION, PARTNERSHIP, CONFIDENTIALITY, OTHER

### CLM Lifecycle Stages (9 stages)
- NEW CONTRACT, REVIEWING, NEGOTIATING
- APPROVING, EXECUTING, IN_EFFECT
- AMENDING, RENEWAL, EXPIRED

### Risk Levels (5 levels)
- LOW, MEDIUM, HIGH, CRITICAL, DEALBREAKER

### Position Types (9 types)
- vendor, customer, landlord, tenant
- employer, employee, buyer, seller, other

### Leverage Levels (5 levels)
- strong, moderate, balanced, weak, unknown

## Key Relationships

### Parent-Child Contracts
- MSAs serve as parents to SOWs
- Amendments reference parent contracts
- Addendums reference parent contracts

### Contract Versions
- MSAs have version chains (v1, v2, v3...)
- Version history tracked in `contract_versions` table

### Related Documents
- Exhibits, attachments, certificates
- Amendments, correspondence

## Sample Queries

### Get all MSAs with their SOWs
```sql
SELECT
    p.id as msa_id,
    p.title as msa_title,
    p.counterparty,
    c.id as sow_id,
    c.title as sow_title
FROM contracts p
JOIN contracts c ON c.parent_id = p.id
WHERE p.contract_type = 'MSA' AND c.contract_type = 'SOW';
```

### Get high-risk contracts
```sql
SELECT
    c.id,
    c.title,
    c.counterparty,
    c.contract_type,
    c.risk_level,
    r.overall_risk,
    r.confidence_score
FROM contracts c
JOIN risk_assessments r ON c.id = r.contract_id
WHERE c.risk_level IN ('HIGH', 'CRITICAL', 'DEALBREAKER')
ORDER BY
    CASE c.risk_level
        WHEN 'DEALBREAKER' THEN 1
        WHEN 'CRITICAL' THEN 2
        ELSE 3
    END;
```

### Get contracts with most clauses
```sql
SELECT
    c.id,
    c.title,
    c.contract_type,
    COUNT(cl.id) as clause_count
FROM contracts c
JOIN clauses cl ON c.id = cl.contract_id
GROUP BY c.id
ORDER BY clause_count DESC
LIMIT 10;
```

### Get contracts in negotiation with redlines
```sql
SELECT
    c.id,
    c.title,
    c.counterparty,
    c.status,
    COUNT(r.id) as redline_count
FROM contracts c
LEFT JOIN redlines r ON c.id = r.contract_id
WHERE c.status = 'NEGOTIATING'
GROUP BY c.id
ORDER BY redline_count DESC;
```

### Audit trail for a contract
```sql
SELECT
    a.timestamp,
    a.action,
    a.user,
    a.details
FROM audit_log a
WHERE a.contract_id = 1
ORDER BY a.timestamp;
```

## Counterparty Companies

### Vendors (we pay them)
- CloudServe Inc, DataPro Solutions, SecureNet Systems
- InfraTech Partners, SupplyChain Global, LogiSoft Corp
- PaymentPro Services, HRCloud Solutions, MarketEdge Inc

### Customers (they pay us)
- RetailMax Corp, HealthCare Plus, FinServ Holdings
- EduTech Academy, ManufacturingPro, TransportLogix
- EnergyFirst Corp, MediaStream Inc, TravelPro Services

### General Partners
- Acme Corporation, TechFlow Solutions, GlobalTech Industries
- Nexus Systems Inc, Pioneer Manufacturing, Summit Partners LLC
- And 30+ more...

## Risk Categories Covered

| Category | Description |
|----------|-------------|
| payment | Payment terms, invoicing |
| liability | Liability caps, limitations |
| indemnification | Indemnification obligations |
| intellectual_property | IP ownership, licensing |
| termination | Termination rights, notice |
| warranties | Service warranties, guarantees |
| assignment | Assignment restrictions |
| confidentiality | NDA terms, information protection |
| compliance | Regulatory compliance |
| insurance | Insurance requirements |
| dispute_resolution | Arbitration, mediation |
| governing_law | Jurisdiction, venue |
| notices | Notice requirements |
| general | General provisions |

## Files in This Directory

| File | Description |
|------|-------------|
| `generate_test_db.py` | Database generator script |
| `verify_db.py` | Integrity verification script |
| `test_contracts.db` | Generated SQLite database |
| `README.md` | This documentation |

## Regenerating the Database

To regenerate with fresh random data:

```bash
cd C:/Users/jrudy/CIP/tests/TEST_DB
python generate_test_db.py
python verify_db.py
```

The generator ensures:
- All 14 contract types are represented
- All 5 party relationships are covered
- All 9 CLM stages have contracts
- All 5 risk levels are present
- Parent-child relationships exist (MSA-SOW, amendments)
- Version chains for some contracts
- Related documents attached
- Realistic clause distributions
