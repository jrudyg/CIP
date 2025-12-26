"""
Add Sample Contracts to CIP Database
Creates 10 diverse test contracts for UI testing.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("C:/Users/jrudy/CIP/data/contracts.db")

def add_sample_contracts():
    """Add 10 sample contracts to the database."""

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    today = datetime.now()

    contracts = [
        {
            'filename': 'Acme_Corp_MSA_2024.pdf',
            'title': 'Master Services Agreement - Acme Corporation',
            'counterparty': 'Acme Corporation',
            'contract_type': 'MSA',
            'status': 'active',
            'risk_level': 'MEDIUM',
            'contract_value': 500000,
            'effective_date': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'expiration_date': (today + timedelta(days=545)).strftime('%Y-%m-%d'),
            'purpose': 'Enterprise software development services',
        },
        {
            'filename': 'TechStart_SOW_Phase1.docx',
            'title': 'Statement of Work - Phase 1 Implementation',
            'counterparty': 'TechStart Inc',
            'contract_type': 'SOW',
            'status': 'active',
            'risk_level': 'LOW',
            'contract_value': 125000,
            'effective_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            'expiration_date': (today + timedelta(days=90)).strftime('%Y-%m-%d'),
            'purpose': 'Cloud migration Phase 1',
        },
        {
            'filename': 'GlobalTech_NDA_Mutual.pdf',
            'title': 'Mutual Non-Disclosure Agreement',
            'counterparty': 'GlobalTech Solutions',
            'contract_type': 'NDA',
            'status': 'active',
            'risk_level': 'LOW',
            'contract_value': 0,
            'effective_date': (today - timedelta(days=365)).strftime('%Y-%m-%d'),
            'expiration_date': (today + timedelta(days=365)).strftime('%Y-%m-%d'),
            'purpose': 'Protect confidential information during partnership discussions',
        },
        {
            'filename': 'DataCorp_Amendment_3.pdf',
            'title': 'Third Amendment to Services Agreement',
            'counterparty': 'DataCorp Analytics',
            'contract_type': 'Amendment',
            'status': 'negotiating',
            'risk_level': 'HIGH',
            'contract_value': 75000,
            'effective_date': None,
            'expiration_date': (today + timedelta(days=30)).strftime('%Y-%m-%d'),
            'purpose': 'Expand data processing scope and adjust pricing',
        },
        {
            'filename': 'CloudFirst_SaaS_Agreement.pdf',
            'title': 'SaaS Subscription Agreement',
            'counterparty': 'CloudFirst Platform',
            'contract_type': 'Service Agreement',
            'status': 'active',
            'risk_level': 'MEDIUM',
            'contract_value': 48000,
            'effective_date': (today - timedelta(days=60)).strftime('%Y-%m-%d'),
            'expiration_date': (today + timedelta(days=305)).strftime('%Y-%m-%d'),
            'purpose': 'Annual SaaS platform subscription',
        },
        {
            'filename': 'BuildRight_EPC_Contract.pdf',
            'title': 'EPC Contract - Warehouse Facility',
            'counterparty': 'BuildRight Construction',
            'contract_type': 'EPC',
            'status': 'review',
            'risk_level': 'CRITICAL',
            'contract_value': 2500000,
            'effective_date': None,
            'expiration_date': (today + timedelta(days=730)).strftime('%Y-%m-%d'),
            'purpose': 'Design and construction of new distribution center',
        },
        {
            'filename': 'SecureIT_Consulting_MSA.pdf',
            'title': 'Security Consulting Master Agreement',
            'counterparty': 'SecureIT Consulting',
            'contract_type': 'MSA',
            'status': 'intake',
            'risk_level': None,
            'contract_value': 200000,
            'effective_date': None,
            'expiration_date': None,
            'purpose': 'Cybersecurity assessment and remediation services',
        },
        {
            'filename': 'OldVendor_License_2019.pdf',
            'title': 'Software License Agreement',
            'counterparty': 'OldVendor Systems',
            'contract_type': 'License',
            'status': 'expired',
            'risk_level': 'LOW',
            'contract_value': 35000,
            'effective_date': (today - timedelta(days=730)).strftime('%Y-%m-%d'),
            'expiration_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            'purpose': 'Legacy system license - expired, pending renewal decision',
        },
        {
            'filename': 'PartnerCo_Reseller_Agreement.pdf',
            'title': 'Channel Partner Reseller Agreement',
            'counterparty': 'PartnerCo Distribution',
            'contract_type': 'Partnership',
            'status': 'active',
            'risk_level': 'MEDIUM',
            'contract_value': 0,
            'effective_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'expiration_date': (today + timedelta(days=275)).strftime('%Y-%m-%d'),
            'purpose': 'Revenue sharing partnership for product distribution',
        },
        {
            'filename': 'RapidDev_SOW_Urgent.docx',
            'title': 'Emergency Development Services',
            'counterparty': 'RapidDev Solutions',
            'contract_type': 'SOW',
            'status': 'negotiating',
            'risk_level': 'HIGH',
            'contract_value': 85000,
            'effective_date': None,
            'expiration_date': (today + timedelta(days=14)).strftime('%Y-%m-%d'),
            'purpose': 'Urgent security patch development - tight deadline',
        },
    ]

    # Insert contracts
    for c in contracts:
        cursor.execute('''
            INSERT INTO contracts (
                filename, title, counterparty, contract_type, status,
                risk_level, contract_value, effective_date, expiration_date,
                purpose, upload_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            c['filename'], c['title'], c['counterparty'], c['contract_type'],
            c['status'], c['risk_level'], c['contract_value'],
            c['effective_date'], c['expiration_date'], c['purpose'],
            today.strftime('%Y-%m-%d'), today.isoformat()
        ))

    conn.commit()

    # Verify
    cursor.execute('SELECT COUNT(*) FROM contracts')
    count = cursor.fetchone()[0]

    print(f"Inserted {count} contracts:")
    print()
    print(f"{'ID':<4} {'Title':<45} {'Status':<12} {'Risk'}")
    print("-" * 75)

    cursor.execute('SELECT id, title, status, risk_level FROM contracts')
    for row in cursor.fetchall():
        title = row[1][:42] + '...' if len(row[1]) > 45 else row[1]
        risk = row[3] or '-'
        print(f"{row[0]:<4} {title:<45} {row[2]:<12} {risk}")

    conn.close()
    print(f"\nDone! Database: {DB_PATH}")


if __name__ == "__main__":
    add_sample_contracts()
