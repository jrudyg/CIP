"""
CIP Test Database Generator
Generates a complete test database with 100 contracts covering all types,
purposes, relationships, versions, and related documents.
"""

import sqlite3
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# =============================================================================
# CONFIGURATION - All enumerations from CIP backend
# =============================================================================

CONTRACT_TYPES = [
    ("NDA", "Non-Disclosure Agreement"),
    ("MNDA", "Mutual NDA"),
    ("MSA", "Master Service Agreement"),
    ("SOW", "Statement of Work"),
    ("SLA", "Service Level Agreement"),
    ("MOU", "Memorandum of Understanding"),
    ("LOI", "Letter of Intent"),
    ("AMENDMENT", "Contract Amendment"),
    ("ADDENDUM", "Contract Addendum"),
    ("ORDER", "Purchase/Sales Order"),
    ("LICENSE", "License Agreement"),
    ("LEASE", "Lease Agreement"),
    ("EMPLOYMENT", "Employment Contract"),
    ("OTHER", "Custom Contract"),
]

PARTY_RELATIONSHIPS = [
    ("CUSTOMER", "They pay us"),
    ("VENDOR", "We pay them"),
    ("PARTNER", "Mutual value exchange"),
    ("RESELLER", "They sell our products"),
    ("CONSULTANT", "They advise us"),
]

CONTRACT_PURPOSES = [
    ("SERVICES", "Professional services delivery"),
    ("PRODUCTS", "Goods purchase/sale"),
    ("LICENSING", "IP/software rights"),
    ("DISTRIBUTION", "Channel/resale arrangements"),
    ("PARTNERSHIP", "Joint ventures, alliances"),
    ("CONFIDENTIALITY", "Information protection only"),
    ("OTHER", "Custom purpose"),
]

CLM_STAGES = [
    "NEW CONTRACT",
    "REVIEWING",
    "NEGOTIATING",
    "APPROVING",
    "EXECUTING",
    "IN_EFFECT",
    "AMENDING",
    "RENEWAL",
    "EXPIRED",
]

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "DEALBREAKER"]

POSITIONS = ["vendor", "customer", "landlord", "tenant", "employer",
             "employee", "buyer", "seller", "other"]

LEVERAGE_LEVELS = ["strong", "moderate", "balanced", "weak", "unknown"]

RISK_CATEGORIES = [
    "payment", "liability", "indemnification", "intellectual_property",
    "termination", "warranties", "assignment", "confidentiality",
    "compliance", "regulatory", "insurance", "dispute_resolution",
    "governing_law", "notices", "general"
]

REDLINE_STATUSES = ["suggested", "accepted", "modified", "rejected", "needs_cm_legal_review"]
CONTRACT_POSITIONS = ["upstream", "downstream", "teaming", "other"]
RISK_PRIORITIES = ["CRITICAL", "HIGH", "MODERATE", "ADMINISTRATIVE"]

# =============================================================================
# REALISTIC TEST DATA
# =============================================================================

COMPANY_NAMES = [
    "Acme Corporation", "TechFlow Solutions", "GlobalTech Industries",
    "Nexus Systems Inc", "Pioneer Manufacturing", "Summit Partners LLC",
    "Vertex Analytics", "Quantum Dynamics", "Atlas Enterprises",
    "Phoenix Digital", "Stellar Innovations", "Meridian Group",
    "Horizon Software", "Catalyst Technologies", "Apex Services",
    "Omega Industries", "Delta Consulting", "Sigma Analytics",
    "Nova Systems", "Prism Technologies", "Vector Solutions",
    "Titan Corporation", "Eclipse Partners", "Zenith Holdings",
    "Compass Technologies", "Beacon Software", "Pinnacle Services",
    "Ascend Industries", "Momentum Corp", "Elevate Solutions",
    "Synergy Systems", "Fusion Tech", "Clarity Consulting",
    "Impact Analytics", "Insight Partners", "Forge Industries",
    "Spark Innovations", "Bridge Technologies", "Core Systems",
    "Edge Computing Inc", "Peak Performance LLC", "Stride Solutions"
]

VENDOR_COMPANIES = [
    "CloudServe Inc", "DataPro Solutions", "SecureNet Systems",
    "InfraTech Partners", "SupplyChain Global", "LogiSoft Corp",
    "PaymentPro Services", "HRCloud Solutions", "MarketEdge Inc",
    "AnalyticsPro LLC", "DevOps Masters", "CyberShield Security",
    "NetworkPro Systems", "StorageTech Inc", "BackupCloud Services"
]

CUSTOMER_COMPANIES = [
    "RetailMax Corp", "HealthCare Plus", "FinServ Holdings",
    "EduTech Academy", "ManufacturingPro", "TransportLogix",
    "EnergyFirst Corp", "MediaStream Inc", "TravelPro Services",
    "InsurancePlus LLC", "RealEstate Global", "FoodService Corp",
    "AutoParts Inc", "AeroSpace Systems", "TelecomNet Services"
]

CONTRACT_TITLES = {
    "NDA": ["Mutual Confidentiality Agreement", "Information Protection Agreement",
            "Non-Disclosure Agreement", "Confidential Information Agreement"],
    "MNDA": ["Bilateral NDA", "Two-Way Confidentiality Agreement", "Mutual NDA"],
    "MSA": ["Master Services Agreement", "Framework Agreement", "General Services Contract",
            "Master Professional Services Agreement"],
    "SOW": ["Statement of Work", "Project Scope Document", "Work Order",
            "Service Deliverables Agreement", "Project Statement of Work"],
    "SLA": ["Service Level Agreement", "Performance Standards Agreement",
            "Uptime Commitment Agreement", "Service Guarantee Agreement"],
    "MOU": ["Memorandum of Understanding", "Letter of Understanding",
            "Preliminary Agreement", "Framework Understanding"],
    "LOI": ["Letter of Intent", "Expression of Interest", "Preliminary Commitment"],
    "AMENDMENT": ["First Amendment", "Second Amendment", "Contract Modification",
                  "Terms Update Agreement", "Amendment to Agreement"],
    "ADDENDUM": ["Addendum A", "Supplemental Terms", "Additional Terms Agreement",
                 "Contract Supplement", "Addendum to Master Agreement"],
    "ORDER": ["Purchase Order", "Sales Order", "Work Order", "Service Order"],
    "LICENSE": ["Software License Agreement", "Technology License",
                "IP License Agreement", "End User License Agreement"],
    "LEASE": ["Equipment Lease Agreement", "Facility Lease", "Office Lease Agreement",
              "Technology Lease Agreement"],
    "EMPLOYMENT": ["Employment Agreement", "Executive Employment Contract",
                   "Contractor Agreement", "Consulting Agreement"],
    "OTHER": ["Partnership Agreement", "Joint Venture Agreement",
              "Teaming Agreement", "Collaboration Agreement"],
}

CLAUSE_TEMPLATES = {
    "payment": [
        "Payment shall be due within {days} days of invoice receipt.",
        "All fees are payable in {currency} via wire transfer.",
        "Late payments shall accrue interest at {rate}% per annum.",
    ],
    "liability": [
        "Neither party's liability shall exceed {amount} in aggregate.",
        "Liability is limited to direct damages only.",
        "Consequential damages are expressly excluded.",
    ],
    "indemnification": [
        "Each party shall indemnify the other against third-party claims.",
        "Indemnification shall cover reasonable attorney fees.",
        "The indemnifying party shall have control of the defense.",
    ],
    "intellectual_property": [
        "All pre-existing IP remains with the original owner.",
        "Work product shall be owned by {owner}.",
        "A perpetual license is granted for all deliverables.",
    ],
    "termination": [
        "Either party may terminate with {days} days written notice.",
        "Termination for cause requires {days} days cure period.",
        "Upon termination, all confidential information must be returned.",
    ],
    "confidentiality": [
        "Confidential information shall be protected for {years} years.",
        "Disclosure requires prior written consent.",
        "Standard industry security measures shall be maintained.",
    ],
    "warranties": [
        "Services shall be performed in a professional manner.",
        "All deliverables shall conform to specifications.",
        "Warranty period is {months} months from acceptance.",
    ],
    "insurance": [
        "Contractor shall maintain ${amount}M in general liability insurance.",
        "Professional liability coverage of ${amount}M is required.",
        "Certificates of insurance shall be provided upon request.",
    ],
    "dispute_resolution": [
        "Disputes shall be resolved through binding arbitration.",
        "Mediation shall be attempted before litigation.",
        "Arbitration shall be conducted under {rules} rules.",
    ],
    "governing_law": [
        "This agreement shall be governed by the laws of {state}.",
        "Venue shall be in {city}, {state}.",
        "Federal courts shall have exclusive jurisdiction.",
    ],
}

US_STATES = ["California", "New York", "Texas", "Florida", "Illinois",
             "Delaware", "Washington", "Massachusetts", "Colorado", "Georgia"]

# =============================================================================
# DATABASE SCHEMA
# =============================================================================

CONTRACTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT,
    title TEXT,
    counterparty TEXT,
    contract_type TEXT,
    contract_role TEXT,
    status TEXT DEFAULT 'intake',
    effective_date TEXT,
    expiration_date TEXT,
    contract_value REAL,
    parent_id INTEGER,
    relationship_type TEXT,
    version_number INTEGER DEFAULT 1,
    is_latest_version INTEGER DEFAULT 1,
    last_amended_date TEXT,
    risk_level TEXT,
    metadata_verified INTEGER DEFAULT 0,
    parsed_metadata TEXT,
    position TEXT,
    leverage TEXT,
    narrative TEXT,
    parties TEXT,
    metadata_json TEXT,
    upload_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    archived INTEGER DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_contracts_type ON contracts(contract_type);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_counterparty ON contracts(counterparty);
CREATE INDEX IF NOT EXISTS idx_contracts_risk ON contracts(risk_level);
CREATE INDEX IF NOT EXISTS idx_contracts_parent ON contracts(parent_id);
"""

CLAUSES_SCHEMA = """
CREATE TABLE IF NOT EXISTS clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    section_number TEXT,
    title TEXT,
    text TEXT NOT NULL,
    category TEXT,
    risk_level TEXT,
    pattern_id TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_clauses_contract ON clauses(contract_id);
CREATE INDEX IF NOT EXISTS idx_clauses_risk ON clauses(risk_level);
"""

RISK_ASSESSMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_risk TEXT,
    critical_items TEXT,
    dealbreakers TEXT,
    confidence_score REAL,
    analysis_json TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_contract ON risk_assessments(contract_id);
"""

NEGOTIATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS negotiations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    strategy TEXT,
    leverage TEXT,
    position TEXT,
    key_points TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_negotiations_contract ON negotiations(contract_id);
"""

ANALYSIS_SNAPSHOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    overall_risk TEXT NOT NULL,
    categories TEXT NOT NULL,
    clauses TEXT NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_contract_id ON analysis_snapshots(contract_id);
"""

COMPARISON_SNAPSHOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS comparison_snapshots (
    comparison_id INTEGER PRIMARY KEY AUTOINCREMENT,
    v1_contract_id INTEGER NOT NULL,
    v2_contract_id INTEGER NOT NULL,
    v1_snapshot_id INTEGER,
    v2_snapshot_id INTEGER,
    similarity_score REAL NOT NULL,
    changed_clauses TEXT NOT NULL,
    risk_delta TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (v1_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v2_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v1_snapshot_id) REFERENCES analysis_snapshots(snapshot_id),
    FOREIGN KEY (v2_snapshot_id) REFERENCES analysis_snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_comparison_snapshots_contracts ON comparison_snapshots(v1_contract_id, v2_contract_id);
"""

CONTRACT_RELATIONSHIPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contract_relationships (
    contract_id INTEGER PRIMARY KEY,
    parent_id INTEGER,
    children TEXT NOT NULL DEFAULT '[]',
    versions TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (parent_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_contract_relationships_parent ON contract_relationships(parent_id);
"""

REDLINE_SNAPSHOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS redline_snapshots (
    redline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    base_version_contract_id INTEGER NOT NULL,
    source_mode TEXT NOT NULL,
    created_at TEXT NOT NULL,
    overall_risk_before TEXT NOT NULL,
    overall_risk_after TEXT,
    clauses_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    contract_position TEXT,
    dealbreakers_detected INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (base_version_contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_redline_snapshots_contract_id ON redline_snapshots(contract_id);
"""

REDLINES_SCHEMA = """
CREATE TABLE IF NOT EXISTS redlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    section_number TEXT,
    original_text TEXT,
    revised_text TEXT,
    rationale TEXT,
    success_probability REAL,
    pattern_id TEXT,
    status TEXT DEFAULT 'proposed',
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_redlines_contract ON redlines(contract_id);
"""

AUDIT_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    contract_id INTEGER,
    user TEXT,
    details TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
"""

COMPARISONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    v1_contract_id INTEGER NOT NULL,
    v2_contract_id INTEGER NOT NULL,
    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    substantive_changes INTEGER,
    administrative_changes INTEGER,
    executive_summary TEXT,
    report_path TEXT,
    metadata_json TEXT,
    FOREIGN KEY (v1_contract_id) REFERENCES contracts(id),
    FOREIGN KEY (v2_contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_comparisons_dates ON comparisons(comparison_date);
"""

RISK_REPORTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS risk_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_type TEXT,
    findings TEXT,
    recommendations TEXT,
    report_path TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_risk_reports_contract ON risk_reports(contract_id);
"""

DOCUMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS related_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT,
    description TEXT,
    upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_contract ON related_documents(contract_id);
"""

VERSIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contract_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    change_summary TEXT,
    changed_by TEXT,
    change_date TEXT DEFAULT CURRENT_TIMESTAMP,
    previous_version_id INTEGER,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (previous_version_id) REFERENCES contract_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_versions_contract ON contract_versions(contract_id);
"""

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def random_date(start_year=2020, end_year=2025):
    """Generate a random date between start_year and end_year."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

def random_future_date(from_date, min_days=30, max_days=1095):
    """Generate a random future date from a given date."""
    base = datetime.strptime(from_date, "%Y-%m-%d")
    delta = timedelta(days=random.randint(min_days, max_days))
    return (base + delta).strftime("%Y-%m-%d")

def generate_contract_value(contract_type):
    """Generate realistic contract values based on type."""
    ranges = {
        "NDA": (0, 0),  # NDAs typically have no value
        "MNDA": (0, 0),
        "MSA": (100000, 10000000),
        "SOW": (25000, 2000000),
        "SLA": (10000, 500000),
        "MOU": (0, 0),
        "LOI": (50000, 5000000),
        "AMENDMENT": (10000, 1000000),
        "ADDENDUM": (5000, 500000),
        "ORDER": (1000, 500000),
        "LICENSE": (10000, 1000000),
        "LEASE": (12000, 600000),  # Annual lease values
        "EMPLOYMENT": (50000, 500000),  # Annual salary
        "OTHER": (10000, 1000000),
    }
    min_val, max_val = ranges.get(contract_type, (10000, 100000))
    if max_val == 0:
        return None
    return round(random.uniform(min_val, max_val), 2)

def generate_filename(contract_type, counterparty, version=1):
    """Generate a realistic filename."""
    date_str = datetime.now().strftime("%Y%m%d")
    clean_party = counterparty.replace(" ", "_").replace(".", "")[:20]
    return f"{contract_type}_{clean_party}_v{version}_{date_str}.pdf"

def generate_clauses(contract_id, contract_type, num_clauses=None):
    """Generate realistic clauses for a contract."""
    if num_clauses is None:
        num_clauses = random.randint(5, 15)

    clauses = []
    categories_used = random.sample(RISK_CATEGORIES, min(num_clauses, len(RISK_CATEGORIES)))

    for i, category in enumerate(categories_used):
        templates = CLAUSE_TEMPLATES.get(category, CLAUSE_TEMPLATES["payment"])
        template = random.choice(templates)

        # Fill in template variables
        text = template.format(
            days=random.choice([30, 45, 60, 90]),
            currency=random.choice(["USD", "EUR", "GBP"]),
            rate=random.choice([1.5, 2.0, 3.0, 5.0]),
            amount=random.choice(["100,000", "500,000", "1,000,000", "5,000,000"]),
            owner=random.choice(["Client", "Provider", "jointly"]),
            years=random.choice([2, 3, 5, 7]),
            months=random.choice([6, 12, 18, 24]),
            rules=random.choice(["AAA", "JAMS", "ICC"]),
            state=random.choice(US_STATES),
            city=random.choice(["San Francisco", "New York", "Chicago", "Austin", "Denver"]),
        )

        # Weighted risk levels - more realistic distribution
        clause_risk = random.choices(
            RISK_LEVELS,
            weights=[30, 35, 20, 10, 5]  # LOW, MEDIUM, HIGH, CRITICAL, DEALBREAKER
        )[0]

        clauses.append({
            "contract_id": contract_id,
            "section_number": f"{i+1}.0",
            "title": category.replace("_", " ").title(),
            "text": text,
            "category": category,
            "risk_level": clause_risk,
            "pattern_id": f"PAT-{category[:3].upper()}-{random.randint(100,999)}"
        })

    return clauses

def generate_risk_assessment(contract_id, clauses):
    """Generate a risk assessment based on clauses."""
    risk_counts = {}
    for clause in clauses:
        risk = clause["risk_level"]
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    # Determine overall risk based on highest risk clause present
    # with realistic distribution weighting
    if risk_counts.get("DEALBREAKER", 0) > 0:
        overall = "DEALBREAKER"
    elif risk_counts.get("CRITICAL", 0) >= 2:
        overall = "CRITICAL"
    elif risk_counts.get("CRITICAL", 0) == 1 or risk_counts.get("HIGH", 0) >= 3:
        overall = "HIGH"
    elif risk_counts.get("HIGH", 0) > 0 or risk_counts.get("MEDIUM", 0) >= 4:
        overall = "MEDIUM"
    else:
        overall = "LOW"

    critical_items = [c for c in clauses if c["risk_level"] in ["CRITICAL", "DEALBREAKER"]]
    dealbreakers = [c for c in clauses if c["risk_level"] == "DEALBREAKER"]

    return {
        "contract_id": contract_id,
        "overall_risk": overall,
        "critical_items": json.dumps([c["title"] for c in critical_items]),
        "dealbreakers": json.dumps([c["title"] for c in dealbreakers]),
        "confidence_score": round(random.uniform(0.75, 0.98), 2),
        "analysis_json": json.dumps({
            "risk_counts": risk_counts,
            "categories_analyzed": len(clauses),
            "analysis_version": "2.0"
        })
    }

def generate_negotiation(contract_id, position, leverage):
    """Generate negotiation strategy."""
    strategies = {
        "strong": "Push for maximum favorable terms, minimal concessions expected.",
        "moderate": "Balance firm positions with reasonable flexibility on secondary terms.",
        "balanced": "Mutual compromise approach, focus on win-win outcomes.",
        "weak": "Prioritize deal completion, accept reasonable counterparty requests.",
        "unknown": "Gather more information before committing to strategy.",
    }

    key_points = random.sample([
        "Payment terms flexibility",
        "Liability cap negotiation",
        "IP ownership clarity",
        "Termination provisions",
        "Warranty scope",
        "Indemnification limits",
        "Insurance requirements",
        "Governing law preference"
    ], random.randint(3, 5))

    return {
        "contract_id": contract_id,
        "strategy": strategies.get(leverage, strategies["balanced"]),
        "leverage": leverage,
        "position": position,
        "key_points": json.dumps(key_points)
    }

def generate_audit_entries(contract_id, status):
    """Generate audit log entries for a contract."""
    entries = []
    actions = ["CONTRACT_UPLOADED", "ANALYSIS_STARTED", "RISK_ASSESSED"]

    if status in ["REVIEWING", "NEGOTIATING", "APPROVING"]:
        actions.append("REVIEW_INITIATED")
    if status in ["NEGOTIATING", "APPROVING", "EXECUTING"]:
        actions.extend(["NEGOTIATION_STARTED", "REDLINE_GENERATED"])
    if status in ["EXECUTING", "IN_EFFECT"]:
        actions.append("CONTRACT_EXECUTED")
    if status == "EXPIRED":
        actions.append("CONTRACT_EXPIRED")

    for action in actions:
        entries.append({
            "action": action,
            "contract_id": contract_id,
            "user": random.choice(["jrudy", "admin", "legal_team", "contract_mgr"]),
            "details": json.dumps({"status": status, "automated": random.choice([True, False])})
        })

    return entries

# =============================================================================
# MAIN DATABASE GENERATOR
# =============================================================================

def create_database(db_path):
    """Create the database with all schemas."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create all tables
    schemas = [
        CONTRACTS_SCHEMA,
        CLAUSES_SCHEMA,
        RISK_ASSESSMENTS_SCHEMA,
        NEGOTIATIONS_SCHEMA,
        ANALYSIS_SNAPSHOTS_SCHEMA,
        COMPARISON_SNAPSHOTS_SCHEMA,
        CONTRACT_RELATIONSHIPS_SCHEMA,
        REDLINE_SNAPSHOTS_SCHEMA,
        REDLINES_SCHEMA,
        AUDIT_LOG_SCHEMA,
        COMPARISONS_SCHEMA,
        RISK_REPORTS_SCHEMA,
        DOCUMENTS_SCHEMA,
        VERSIONS_SCHEMA,
    ]

    for schema in schemas:
        cursor.executescript(schema)

    conn.commit()
    return conn

def populate_contracts(conn, num_contracts=100):
    """Populate the database with test contracts."""
    cursor = conn.cursor()

    # Track contracts for relationships
    contracts_by_type = {ct[0]: [] for ct in CONTRACT_TYPES}
    parent_contracts = []  # MSAs and other parent-capable contracts

    print(f"Generating {num_contracts} contracts...")

    for i in range(num_contracts):
        # Select contract type - ensure distribution
        if i < len(CONTRACT_TYPES):
            # First pass: one of each type
            contract_type = CONTRACT_TYPES[i][0]
        else:
            # Rest: weighted random
            weights = [3, 2, 5, 6, 2, 2, 2, 4, 3, 4, 3, 2, 2, 2]  # Higher for MSA, SOW, ORDER
            contract_type = random.choices([ct[0] for ct in CONTRACT_TYPES], weights=weights)[0]

        # Determine party relationship
        party_rel = random.choice(PARTY_RELATIONSHIPS)

        # Select counterparty based on relationship
        if party_rel[0] == "VENDOR":
            counterparty = random.choice(VENDOR_COMPANIES)
        elif party_rel[0] == "CUSTOMER":
            counterparty = random.choice(CUSTOMER_COMPANIES)
        else:
            counterparty = random.choice(COMPANY_NAMES)

        # Determine if this is a child contract
        parent_id = None
        relationship_type = None
        version_number = 1
        is_latest_version = 1

        # SOWs often have MSA parents
        if contract_type == "SOW" and parent_contracts:
            if random.random() > 0.3:  # 70% of SOWs have parents
                parent_id = random.choice(parent_contracts)
                relationship_type = "SOW_UNDER_MSA"

        # Amendments reference parent contracts
        if contract_type == "AMENDMENT" and contracts_by_type.get("MSA"):
            parent_id = random.choice(contracts_by_type["MSA"])
            relationship_type = "AMENDMENT"

        # Addendums reference parent contracts
        if contract_type == "ADDENDUM" and (contracts_by_type.get("MSA") or contracts_by_type.get("SOW")):
            candidates = contracts_by_type.get("MSA", []) + contracts_by_type.get("SOW", [])
            if candidates:
                parent_id = random.choice(candidates)
                relationship_type = "ADDENDUM"

        # Generate dates
        effective_date = random_date(2020, 2024)
        expiration_date = random_future_date(effective_date, 365, 1825)  # 1-5 years

        # Generate contract data
        status = random.choice(CLM_STAGES)
        position = random.choice(POSITIONS)
        leverage = random.choice(LEVERAGE_LEVELS)
        contract_value = generate_contract_value(contract_type)
        title = random.choice(CONTRACT_TITLES.get(contract_type, ["Contract Agreement"]))
        filename = generate_filename(contract_type, counterparty)

        # Parties JSON
        parties = json.dumps({
            "party_a": "Our Company Inc",
            "party_b": counterparty,
            "relationship": party_rel[0],
            "relationship_desc": party_rel[1]
        })

        # Metadata JSON
        metadata = json.dumps({
            "purpose": random.choice(CONTRACT_PURPOSES)[0],
            "department": random.choice(["Legal", "Procurement", "Sales", "Operations", "IT"]),
            "region": random.choice(["North America", "EMEA", "APAC", "LATAM"]),
            "currency": random.choice(["USD", "EUR", "GBP", "CAD"]),
            "auto_renewal": random.choice([True, False]),
            "renewal_notice_days": random.choice([30, 60, 90])
        })

        # Narrative
        narrative = f"This {contract_type} establishes the terms between Our Company Inc and {counterparty} for {random.choice(CONTRACT_PURPOSES)[1].lower()}."

        # Insert contract
        cursor.execute("""
            INSERT INTO contracts (
                filename, filepath, title, counterparty, contract_type, contract_role,
                status, effective_date, expiration_date, contract_value, parent_id,
                relationship_type, version_number, is_latest_version, risk_level,
                position, leverage, narrative, parties, metadata_json, upload_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename, f"/contracts/{filename}", title, counterparty, contract_type,
            party_rel[0], status, effective_date, expiration_date, contract_value,
            parent_id, relationship_type, version_number, is_latest_version,
            random.choice(RISK_LEVELS), position, leverage, narrative, parties,
            metadata, effective_date
        ))

        contract_id = cursor.lastrowid
        contracts_by_type[contract_type].append(contract_id)

        # Track potential parent contracts
        if contract_type in ["MSA", "LICENSE", "LEASE"]:
            parent_contracts.append(contract_id)

        # Generate clauses
        clauses = generate_clauses(contract_id, contract_type)
        for clause in clauses:
            cursor.execute("""
                INSERT INTO clauses (contract_id, section_number, title, text, category, risk_level, pattern_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (clause["contract_id"], clause["section_number"], clause["title"],
                  clause["text"], clause["category"], clause["risk_level"], clause["pattern_id"]))

        # Generate risk assessment
        assessment = generate_risk_assessment(contract_id, clauses)
        cursor.execute("""
            INSERT INTO risk_assessments (contract_id, overall_risk, critical_items, dealbreakers, confidence_score, analysis_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (assessment["contract_id"], assessment["overall_risk"], assessment["critical_items"],
              assessment["dealbreakers"], assessment["confidence_score"], assessment["analysis_json"]))

        # Update contract risk level based on assessment
        cursor.execute("UPDATE contracts SET risk_level = ? WHERE id = ?",
                      (assessment["overall_risk"], contract_id))

        # Generate negotiation record (for contracts in negotiation or later)
        if status in ["NEGOTIATING", "APPROVING", "EXECUTING", "IN_EFFECT", "AMENDING"]:
            negotiation = generate_negotiation(contract_id, position, leverage)
            cursor.execute("""
                INSERT INTO negotiations (contract_id, strategy, leverage, position, key_points)
                VALUES (?, ?, ?, ?, ?)
            """, (negotiation["contract_id"], negotiation["strategy"], negotiation["leverage"],
                  negotiation["position"], negotiation["key_points"]))

        # Generate analysis snapshot
        cursor.execute("""
            INSERT INTO analysis_snapshots (contract_id, created_at, overall_risk, categories, clauses)
            VALUES (?, ?, ?, ?, ?)
        """, (contract_id, datetime.now().isoformat(), assessment["overall_risk"],
              json.dumps([c["category"] for c in clauses]), json.dumps(clauses)))

        # Generate audit entries
        audit_entries = generate_audit_entries(contract_id, status)
        for entry in audit_entries:
            cursor.execute("""
                INSERT INTO audit_log (action, contract_id, user, details)
                VALUES (?, ?, ?, ?)
            """, (entry["action"], entry["contract_id"], entry["user"], entry["details"]))

        # Generate related documents for some contracts
        if random.random() > 0.5:
            doc_types = ["exhibit", "attachment", "certificate", "amendment", "correspondence"]
            num_docs = random.randint(1, 3)
            for j in range(num_docs):
                doc_type = random.choice(doc_types)
                cursor.execute("""
                    INSERT INTO related_documents (contract_id, document_type, filename, filepath, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (contract_id, doc_type,
                      f"{doc_type}_{contract_id}_{j+1}.pdf",
                      f"/documents/{doc_type}_{contract_id}_{j+1}.pdf",
                      f"{doc_type.title()} document for contract {contract_id}"))

        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1} contracts...")

    conn.commit()
    print(f"Completed generating {num_contracts} contracts")
    return contracts_by_type

def create_versions(conn, contracts_by_type):
    """Create version chains for some contracts."""
    cursor = conn.cursor()

    print("Creating contract versions...")

    # Create versions for MSAs
    for msa_id in contracts_by_type.get("MSA", [])[:5]:  # First 5 MSAs
        num_versions = random.randint(2, 4)
        prev_version_id = None

        for v in range(1, num_versions + 1):
            cursor.execute("""
                INSERT INTO contract_versions (contract_id, version_number, change_summary, changed_by, previous_version_id)
                VALUES (?, ?, ?, ?, ?)
            """, (msa_id, v,
                  f"Version {v} changes" if v > 1 else "Initial version",
                  random.choice(["jrudy", "legal_team", "contract_mgr"]),
                  prev_version_id))
            prev_version_id = cursor.lastrowid

        # Update contract to latest version
        cursor.execute("UPDATE contracts SET version_number = ?, is_latest_version = 1 WHERE id = ?",
                      (num_versions, msa_id))

    conn.commit()
    print("Completed creating versions")

def create_comparisons(conn, contracts_by_type):
    """Create comparison records between contract versions."""
    cursor = conn.cursor()

    print("Creating comparison snapshots...")

    # Compare SOWs under same MSA
    msa_ids = contracts_by_type.get("MSA", [])
    for msa_id in msa_ids[:3]:
        cursor.execute("SELECT id FROM contracts WHERE parent_id = ?", (msa_id,))
        children = [row[0] for row in cursor.fetchall()]

        if len(children) >= 2:
            for i in range(len(children) - 1):
                cursor.execute("""
                    INSERT INTO comparison_snapshots (v1_contract_id, v2_contract_id, similarity_score, changed_clauses, risk_delta, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (children[i], children[i+1],
                      round(random.uniform(0.6, 0.95), 2),
                      json.dumps({"modified": random.randint(1, 5), "added": random.randint(0, 2), "removed": random.randint(0, 2)}),
                      json.dumps({"before": random.choice(RISK_LEVELS), "after": random.choice(RISK_LEVELS)}),
                      datetime.now().isoformat()))

                # Also create comparison record
                cursor.execute("""
                    INSERT INTO comparisons (v1_contract_id, v2_contract_id, substantive_changes, administrative_changes, executive_summary)
                    VALUES (?, ?, ?, ?, ?)
                """, (children[i], children[i+1],
                      random.randint(1, 8),
                      random.randint(0, 5),
                      f"Comparison between contracts {children[i]} and {children[i+1]} shows moderate changes."))

    conn.commit()
    print("Completed creating comparisons")

def create_redlines(conn, contracts_by_type):
    """Create redline records for contracts in negotiation."""
    cursor = conn.cursor()

    print("Creating redline records...")

    cursor.execute("SELECT id, position FROM contracts WHERE status IN ('NEGOTIATING', 'APPROVING')")
    negotiating_contracts = cursor.fetchall()

    for contract_id, position in negotiating_contracts[:15]:  # First 15
        # Create redline snapshot
        cursor.execute("""
            INSERT INTO redline_snapshots (contract_id, base_version_contract_id, source_mode, created_at, overall_risk_before, overall_risk_after, clauses_json, status, contract_position, dealbreakers_detected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (contract_id, contract_id, "single", datetime.now().isoformat(),
              random.choice(RISK_LEVELS), random.choice(RISK_LEVELS),
              json.dumps([]), random.choice(["draft", "complete"]),
              random.choice(CONTRACT_POSITIONS), random.randint(0, 2)))

        # Create individual redlines
        num_redlines = random.randint(2, 6)
        for i in range(num_redlines):
            cursor.execute("""
                INSERT INTO redlines (contract_id, section_number, original_text, revised_text, rationale, success_probability, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (contract_id, f"{i+1}.0",
                  f"Original clause text for section {i+1}",
                  f"Revised clause text for section {i+1} with improved terms",
                  f"Rationale: Improve position on {random.choice(RISK_CATEGORIES)}",
                  round(random.uniform(0.5, 0.95), 2),
                  random.choice(REDLINE_STATUSES)))

    conn.commit()
    print("Completed creating redlines")

def create_contract_relationships(conn, contracts_by_type):
    """Create relationship records."""
    cursor = conn.cursor()

    print("Creating contract relationships...")

    # Get all contracts with parents
    cursor.execute("SELECT id, parent_id FROM contracts WHERE parent_id IS NOT NULL")
    child_contracts = cursor.fetchall()

    # Build parent-children mapping
    parent_children = {}
    for child_id, parent_id in child_contracts:
        if parent_id not in parent_children:
            parent_children[parent_id] = []
        parent_children[parent_id].append(child_id)

    # Create relationship records
    for parent_id, children in parent_children.items():
        cursor.execute("""
            INSERT OR REPLACE INTO contract_relationships (contract_id, parent_id, children, versions)
            VALUES (?, NULL, ?, '[]')
        """, (parent_id, json.dumps(children)))

        for child_id in children:
            cursor.execute("""
                INSERT OR REPLACE INTO contract_relationships (contract_id, parent_id, children, versions)
                VALUES (?, ?, '[]', '[]')
            """, (child_id, parent_id))

    conn.commit()
    print("Completed creating relationships")

def create_risk_reports(conn):
    """Create risk report records."""
    cursor = conn.cursor()

    print("Creating risk reports...")

    cursor.execute("SELECT id, risk_level FROM contracts WHERE risk_level IN ('HIGH', 'CRITICAL', 'DEALBREAKER')")
    high_risk_contracts = cursor.fetchall()

    for contract_id, risk_level in high_risk_contracts:
        cursor.execute("""
            INSERT INTO risk_reports (contract_id, report_type, findings, recommendations, report_path)
            VALUES (?, ?, ?, ?, ?)
        """, (contract_id, "RISK_ASSESSMENT",
              json.dumps({"risk_level": risk_level, "issues_found": random.randint(1, 5)}),
              json.dumps(["Review liability terms", "Negotiate indemnification cap", "Clarify IP ownership"]),
              f"/reports/risk_report_{contract_id}.pdf"))

    conn.commit()
    print("Completed creating risk reports")

def print_summary(conn):
    """Print database summary."""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("TEST DATABASE SUMMARY")
    print("="*60)

    tables = [
        ("contracts", "Total Contracts"),
        ("clauses", "Total Clauses"),
        ("risk_assessments", "Risk Assessments"),
        ("negotiations", "Negotiation Records"),
        ("analysis_snapshots", "Analysis Snapshots"),
        ("comparison_snapshots", "Comparison Snapshots"),
        ("contract_relationships", "Relationship Records"),
        ("redline_snapshots", "Redline Snapshots"),
        ("redlines", "Individual Redlines"),
        ("audit_log", "Audit Log Entries"),
        ("comparisons", "Comparisons"),
        ("risk_reports", "Risk Reports"),
        ("related_documents", "Related Documents"),
        ("contract_versions", "Version Records"),
    ]

    for table, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {label}: {count}")

    print("\n--- Contract Types Distribution ---")
    cursor.execute("SELECT contract_type, COUNT(*) FROM contracts GROUP BY contract_type ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\n--- Party Relationships ---")
    cursor.execute("SELECT contract_role, COUNT(*) FROM contracts GROUP BY contract_role ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\n--- Status Distribution ---")
    cursor.execute("SELECT status, COUNT(*) FROM contracts GROUP BY status ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\n--- Risk Level Distribution ---")
    cursor.execute("SELECT risk_level, COUNT(*) FROM contracts GROUP BY risk_level ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\n--- Contracts with Parent Relationships ---")
    cursor.execute("SELECT COUNT(*) FROM contracts WHERE parent_id IS NOT NULL")
    print(f"  Child contracts: {cursor.fetchone()[0]}")

    print("\n--- Contracts with Related Documents ---")
    cursor.execute("SELECT COUNT(DISTINCT contract_id) FROM related_documents")
    print(f"  Contracts with documents: {cursor.fetchone()[0]}")

    print("="*60)

def main():
    """Main entry point."""
    db_dir = Path("C:/Users/jrudy/CIP/tests/TEST_DB")
    db_dir.mkdir(parents=True, exist_ok=True)

    db_path = db_dir / "test_contracts.db"

    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print(f"Removed existing database: {db_path}")

    print(f"Creating test database: {db_path}")

    # Create and populate database
    conn = create_database(str(db_path))
    contracts_by_type = populate_contracts(conn, num_contracts=100)
    create_versions(conn, contracts_by_type)
    create_comparisons(conn, contracts_by_type)
    create_redlines(conn, contracts_by_type)
    create_contract_relationships(conn, contracts_by_type)
    create_risk_reports(conn)

    # Print summary
    print_summary(conn)

    conn.close()
    print(f"\nDatabase created successfully: {db_path}")
    print(f"File size: {db_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
