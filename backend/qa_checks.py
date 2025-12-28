"""
CIP QA/QC Check Engine

Comprehensive quality assurance checks for the Contract Intelligence Platform.
Follows existing health_api.py patterns with 15 checks across 4 categories:
- Data Quality (30%): Metadata completeness, duplicates, validation rules
- Analysis Quality (30%): Risk assessments, confidence, stale analysis
- Process Quality (20%): Workflow stages, audit completeness
- System Integrity (20%): Orphans, referential integrity, relationships
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple

# Configuration
CIP_ROOT = Path(r"C:\Users\jrudy\CIP")
CONTRACTS_DB = CIP_ROOT / "data" / "contracts.db"

# Thresholds (aligned with existing config.py)
CONFIDENCE_THRESHOLD_STANDARD = 0.85
CONFIDENCE_THRESHOLD_CRITICAL = 0.93
STALE_ANALYSIS_DAYS = 30
STALE_CRITICAL_DAYS = 7
STALE_INTAKE_DAYS = 7

# Critical categories requiring higher confidence
CRITICAL_CATEGORIES = ['liability', 'indemnity', 'ip', 'intellectual_property', 'limitation_of_liability']

# Valid workflow stages
VALID_WORKFLOW_STAGES = [0, 1, 2, 3, 4, 5]

# Category weights (must sum to 100)
CATEGORY_WEIGHTS = {
    'data_quality': 30,
    'analysis_quality': 30,
    'process_quality': 20,
    'system_integrity': 20
}

# Grade thresholds (matches health_api.py)
QA_GRADES = {
    'A': {'min': 90, 'color': '#22C55E', 'label': 'Excellent'},
    'B': {'min': 75, 'color': '#84CC16', 'label': 'Good'},
    'C': {'min': 60, 'color': '#EAB308', 'label': 'Fair'},
    'D': {'min': 40, 'color': '#F97316', 'label': 'Poor'},
    'F': {'min': 0, 'color': '#EF4444', 'label': 'Critical'},
}


@dataclass
class QACheckResult:
    """Result of a single QA check."""
    check_id: str
    check_name: str
    category: str
    severity: str  # critical, high, medium, low
    passed: bool
    score: float  # 0.0-1.0
    message: str
    affected_count: int = 0
    affected_ids: List[int] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QAReport:
    """Complete QA report with all check results."""
    overall_score: float
    grade: str
    grade_color: str
    grade_label: str
    generated_at: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    categories: Dict[str, Dict[str, Any]]
    checks: List[QACheckResult]
    critical_issues: List[QACheckResult]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['checks'] = [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.checks]
        result['critical_issues'] = [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.critical_issues]
        return result


class QACheckEngine:
    """Main QA check execution engine."""

    def __init__(self, db_path: Path = CONTRACTS_DB):
        self.db_path = db_path
        self.results: List[QACheckResult] = []

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def run_all_checks(self, contract_id: Optional[int] = None) -> QAReport:
        """Run all QA checks and return complete report."""
        self.results = []

        # Data Quality checks
        self.check_metadata_completeness(contract_id)
        self.check_duplicate_detection(contract_id)
        self.check_validation_rules(contract_id)

        # Analysis Quality checks
        self.check_missing_risk_assessment(contract_id)
        self.check_low_confidence(contract_id)
        self.check_stale_analysis(contract_id)
        self.check_clause_consistency(contract_id)

        # Process Quality checks
        self.check_invalid_workflow_stage(contract_id)
        self.check_stale_intake(contract_id)
        self.check_audit_completeness(contract_id)

        # System Integrity checks
        self.check_orphaned_risk_assessments()
        self.check_orphaned_clauses()
        self.check_orphaned_snapshots()
        self.check_invalid_parent_references()
        self.check_circular_relationships()

        return self._generate_report()

    def run_category_checks(self, category: str, contract_id: Optional[int] = None) -> QAReport:
        """Run checks for a specific category only."""
        self.results = []

        if category == 'data_quality':
            self.check_metadata_completeness(contract_id)
            self.check_duplicate_detection(contract_id)
            self.check_validation_rules(contract_id)
        elif category == 'analysis_quality':
            self.check_missing_risk_assessment(contract_id)
            self.check_low_confidence(contract_id)
            self.check_stale_analysis(contract_id)
            self.check_clause_consistency(contract_id)
        elif category == 'process_quality':
            self.check_invalid_workflow_stage(contract_id)
            self.check_stale_intake(contract_id)
            self.check_audit_completeness(contract_id)
        elif category == 'system_integrity':
            self.check_orphaned_risk_assessments()
            self.check_orphaned_clauses()
            self.check_orphaned_snapshots()
            self.check_invalid_parent_references()
            self.check_circular_relationships()

        return self._generate_report()

    # ========== DATA QUALITY CHECKS ==========

    def check_metadata_completeness(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts with incomplete metadata."""
        conn = self.get_connection()
        try:
            query = """
                SELECT id, title, counterparty, contract_type,
                       effective_date, expiration_date, metadata_verified
                FROM contracts
                WHERE archived = 0
            """
            params = []
            if contract_id:
                query += " AND id = ?"
                params.append(contract_id)

            rows = conn.execute(query, params).fetchall()

            incomplete = []
            for row in rows:
                missing = []
                if not row['title']:
                    missing.append('title')
                if not row['counterparty']:
                    missing.append('counterparty')
                if not row['contract_type']:
                    missing.append('contract_type')
                if not row['effective_date']:
                    missing.append('effective_date')
                if not row['expiration_date']:
                    missing.append('expiration_date')
                if row['metadata_verified'] == 0:
                    missing.append('unverified')

                if missing:
                    incomplete.append({'id': row['id'], 'missing': missing})

            total = len(rows)
            failed = len(incomplete)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='metadata_completeness',
                check_name='Metadata Completeness',
                category='data_quality',
                severity='high',
                passed=failed == 0,
                score=score,
                message=f"{failed} of {total} contracts have incomplete metadata" if failed else "All contracts have complete metadata",
                affected_count=failed,
                affected_ids=[c['id'] for c in incomplete],
                details={'incomplete_contracts': incomplete[:10]},  # Limit details
                recommendation="Review and complete missing metadata fields" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_duplicate_detection(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for duplicate contracts by content hash or title+counterparty."""
        conn = self.get_connection()
        try:
            # Check by content hash
            hash_query = """
                SELECT content_hash, GROUP_CONCAT(id) as ids, COUNT(*) as count
                FROM contracts
                WHERE content_hash IS NOT NULL AND content_hash != '' AND archived = 0
                GROUP BY content_hash
                HAVING count > 1
            """
            hash_dupes = conn.execute(hash_query).fetchall()

            # Check by title + counterparty
            title_query = """
                SELECT LOWER(title) || '|' || LOWER(counterparty) as key,
                       GROUP_CONCAT(id) as ids, COUNT(*) as count
                FROM contracts
                WHERE title IS NOT NULL AND counterparty IS NOT NULL AND archived = 0
                GROUP BY LOWER(title), LOWER(counterparty)
                HAVING count > 1
            """
            title_dupes = conn.execute(title_query).fetchall()

            duplicates = []
            affected_ids = set()

            for row in hash_dupes:
                ids = [int(x) for x in row['ids'].split(',')]
                duplicates.append({'type': 'content_hash', 'ids': ids})
                affected_ids.update(ids)

            for row in title_dupes:
                ids = [int(x) for x in row['ids'].split(',')]
                duplicates.append({'type': 'title_counterparty', 'ids': ids})
                affected_ids.update(ids)

            total_contracts = conn.execute(
                "SELECT COUNT(*) FROM contracts WHERE archived = 0"
            ).fetchone()[0]

            failed = len(affected_ids)
            score = 1.0 if total_contracts == 0 else (total_contracts - failed) / total_contracts

            result = QACheckResult(
                check_id='duplicate_detection',
                check_name='Duplicate Detection',
                category='data_quality',
                severity='medium',
                passed=len(duplicates) == 0,
                score=score,
                message=f"Found {len(duplicates)} duplicate groups ({failed} contracts)" if duplicates else "No duplicate contracts found",
                affected_count=failed,
                affected_ids=list(affected_ids),
                details={'duplicate_groups': duplicates[:5]},
                recommendation="Review and merge or archive duplicate contracts" if duplicates else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_validation_rules(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts violating validation rules."""
        conn = self.get_connection()
        try:
            violations = []

            # Date validation: effective_date must be before expiration_date
            date_query = """
                SELECT id, effective_date, expiration_date
                FROM contracts
                WHERE effective_date IS NOT NULL
                  AND expiration_date IS NOT NULL
                  AND DATE(effective_date) > DATE(expiration_date)
                  AND archived = 0
            """
            params = []
            if contract_id:
                date_query = date_query.replace("AND archived = 0", "AND archived = 0 AND id = ?")
                params.append(contract_id)

            for row in conn.execute(date_query, params).fetchall():
                violations.append({
                    'id': row['id'],
                    'rule': 'date_order',
                    'message': f"Effective date ({row['effective_date']}) after expiration ({row['expiration_date']})"
                })

            # Value validation: contract_value must be non-negative
            value_query = """
                SELECT id, contract_value
                FROM contracts
                WHERE contract_value IS NOT NULL AND contract_value < 0
                  AND archived = 0
            """
            if contract_id:
                value_query = value_query.replace("AND archived = 0", "AND archived = 0 AND id = ?")

            for row in conn.execute(value_query, params).fetchall():
                violations.append({
                    'id': row['id'],
                    'rule': 'negative_value',
                    'message': f"Negative contract value: {row['contract_value']}"
                })

            # Risk level validation
            risk_query = """
                SELECT id, risk_level
                FROM contracts
                WHERE risk_level IS NOT NULL
                  AND risk_level NOT IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
                  AND archived = 0
            """
            if contract_id:
                risk_query = risk_query.replace("AND archived = 0", "AND archived = 0 AND id = ?")

            for row in conn.execute(risk_query, params).fetchall():
                violations.append({
                    'id': row['id'],
                    'rule': 'invalid_risk_level',
                    'message': f"Invalid risk level: {row['risk_level']}"
                })

            total_contracts = conn.execute(
                "SELECT COUNT(*) FROM contracts WHERE archived = 0"
            ).fetchone()[0]

            affected_ids = list(set(v['id'] for v in violations))
            failed = len(affected_ids)
            score = 1.0 if total_contracts == 0 else (total_contracts - failed) / total_contracts

            result = QACheckResult(
                check_id='validation_rules',
                check_name='Validation Rules',
                category='data_quality',
                severity='high',
                passed=len(violations) == 0,
                score=score,
                message=f"Found {len(violations)} validation violations in {failed} contracts" if violations else "All contracts pass validation rules",
                affected_count=failed,
                affected_ids=affected_ids,
                details={'violations': violations[:10]},
                recommendation="Fix validation errors in affected contracts" if violations else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    # ========== ANALYSIS QUALITY CHECKS ==========

    def check_missing_risk_assessment(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for analyzed contracts without risk assessments."""
        conn = self.get_connection()
        try:
            query = """
                SELECT c.id, c.title, c.last_analyzed_at
                FROM contracts c
                LEFT JOIN risk_assessments ra ON c.id = ra.contract_id
                WHERE c.last_analyzed_at IS NOT NULL
                  AND ra.id IS NULL
                  AND c.archived = 0
            """
            params = []
            if contract_id:
                query += " AND c.id = ?"
                params.append(contract_id)

            missing = conn.execute(query, params).fetchall()

            total_analyzed = conn.execute("""
                SELECT COUNT(*) FROM contracts
                WHERE last_analyzed_at IS NOT NULL AND archived = 0
            """).fetchone()[0]

            failed = len(missing)
            score = 1.0 if total_analyzed == 0 else (total_analyzed - failed) / total_analyzed

            result = QACheckResult(
                check_id='missing_risk_assessment',
                check_name='Missing Risk Assessment',
                category='analysis_quality',
                severity='critical',
                passed=failed == 0,
                score=score,
                message=f"{failed} analyzed contracts missing risk assessments" if failed else "All analyzed contracts have risk assessments",
                affected_count=failed,
                affected_ids=[r['id'] for r in missing],
                details={'missing': [{'id': r['id'], 'title': r['title']} for r in missing[:10]]},
                recommendation="Re-run analysis on affected contracts" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_low_confidence(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for risk assessments with low confidence scores."""
        conn = self.get_connection()
        try:
            # Standard threshold check
            query = """
                SELECT ra.id, ra.contract_id, ra.confidence_score, ra.overall_risk
                FROM risk_assessments ra
                JOIN contracts c ON ra.contract_id = c.id
                WHERE ra.confidence_score < ?
                  AND c.archived = 0
            """
            params = [CONFIDENCE_THRESHOLD_STANDARD]
            if contract_id:
                query += " AND c.id = ?"
                params.append(contract_id)

            low_confidence = conn.execute(query, params).fetchall()

            total_assessments = conn.execute("""
                SELECT COUNT(*) FROM risk_assessments ra
                JOIN contracts c ON ra.contract_id = c.id
                WHERE c.archived = 0
            """).fetchone()[0]

            failed = len(low_confidence)
            score = 1.0 if total_assessments == 0 else (total_assessments - failed) / total_assessments

            result = QACheckResult(
                check_id='low_confidence',
                check_name='Low Confidence Scores',
                category='analysis_quality',
                severity='high',
                passed=failed == 0,
                score=score,
                message=f"{failed} assessments below {CONFIDENCE_THRESHOLD_STANDARD} confidence" if failed else "All assessments meet confidence threshold",
                affected_count=failed,
                affected_ids=[r['contract_id'] for r in low_confidence],
                details={'low_confidence': [
                    {'contract_id': r['contract_id'], 'score': r['confidence_score']}
                    for r in low_confidence[:10]
                ]},
                recommendation="Review and re-analyze low confidence contracts" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_stale_analysis(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts with outdated analysis."""
        conn = self.get_connection()
        try:
            # Standard stale check (30 days)
            stale_query = f"""
                SELECT c.id, c.title, c.risk_level, MAX(a.created_at) as last_analysis
                FROM contracts c
                LEFT JOIN analysis_snapshots a ON c.id = a.contract_id
                WHERE c.archived = 0
                  AND c.last_analyzed_at IS NOT NULL
                GROUP BY c.id
                HAVING DATE(last_analysis) < DATE('now', '-{STALE_ANALYSIS_DAYS} days')
                   OR last_analysis IS NULL
            """
            params = []
            if contract_id:
                stale_query = stale_query.replace("WHERE c.archived = 0", "WHERE c.archived = 0 AND c.id = ?")
                params.append(contract_id)

            stale = conn.execute(stale_query, params).fetchall()

            # Critical contracts stale check (7 days)
            critical_stale_query = f"""
                SELECT c.id, c.title, MAX(a.created_at) as last_analysis
                FROM contracts c
                LEFT JOIN analysis_snapshots a ON c.id = a.contract_id
                WHERE c.archived = 0
                  AND c.risk_level IN ('HIGH', 'CRITICAL')
                  AND c.last_analyzed_at IS NOT NULL
                GROUP BY c.id
                HAVING DATE(last_analysis) < DATE('now', '-{STALE_CRITICAL_DAYS} days')
            """
            if contract_id:
                critical_stale_query = critical_stale_query.replace("WHERE c.archived = 0", "WHERE c.archived = 0 AND c.id = ?")

            critical_stale = conn.execute(critical_stale_query, params).fetchall()

            total_analyzed = conn.execute("""
                SELECT COUNT(*) FROM contracts
                WHERE last_analyzed_at IS NOT NULL AND archived = 0
            """).fetchone()[0]

            all_stale = {r['id'] for r in stale} | {r['id'] for r in critical_stale}
            failed = len(all_stale)
            score = 1.0 if total_analyzed == 0 else (total_analyzed - failed) / total_analyzed

            result = QACheckResult(
                check_id='stale_analysis',
                check_name='Stale Analysis',
                category='analysis_quality',
                severity='medium',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts have stale analysis (>{STALE_ANALYSIS_DAYS} days, or >{STALE_CRITICAL_DAYS} for high-risk)" if failed else "All analyses are current",
                affected_count=failed,
                affected_ids=list(all_stale),
                details={
                    'stale_standard': [{'id': r['id'], 'last': r['last_analysis']} for r in stale[:5]],
                    'stale_critical': [{'id': r['id'], 'last': r['last_analysis']} for r in critical_stale[:5]]
                },
                recommendation="Re-run analysis on stale contracts" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_clause_consistency(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for clause data consistency issues."""
        conn = self.get_connection()
        try:
            issues = []

            # Clauses without risk level
            no_risk_query = """
                SELECT cl.id, cl.contract_id, cl.section_number
                FROM clauses cl
                JOIN contracts c ON cl.contract_id = c.id
                WHERE (cl.risk_level IS NULL OR cl.risk_level = '')
                  AND c.archived = 0
            """
            params = []
            if contract_id:
                no_risk_query += " AND c.id = ?"
                params.append(contract_id)

            for row in conn.execute(no_risk_query, params).fetchall():
                issues.append({
                    'contract_id': row['contract_id'],
                    'issue': 'clause_no_risk_level',
                    'clause_id': row['id']
                })

            # Analyzed contracts with no clauses
            no_clauses_query = """
                SELECT c.id, c.title
                FROM contracts c
                LEFT JOIN clauses cl ON c.id = cl.contract_id
                WHERE c.last_analyzed_at IS NOT NULL
                  AND cl.id IS NULL
                  AND c.archived = 0
            """
            if contract_id:
                no_clauses_query += " AND c.id = ?"

            for row in conn.execute(no_clauses_query, params).fetchall():
                issues.append({
                    'contract_id': row['id'],
                    'issue': 'no_clauses_extracted'
                })

            affected_ids = list(set(i['contract_id'] for i in issues))
            total_analyzed = conn.execute("""
                SELECT COUNT(*) FROM contracts
                WHERE last_analyzed_at IS NOT NULL AND archived = 0
            """).fetchone()[0]

            failed = len(affected_ids)
            score = 1.0 if total_analyzed == 0 else (total_analyzed - failed) / total_analyzed

            result = QACheckResult(
                check_id='clause_consistency',
                check_name='Clause Consistency',
                category='analysis_quality',
                severity='medium',
                passed=len(issues) == 0,
                score=score,
                message=f"{len(issues)} clause consistency issues in {failed} contracts" if issues else "All clauses are consistent",
                affected_count=failed,
                affected_ids=affected_ids,
                details={'issues': issues[:10]},
                recommendation="Review clause extraction for affected contracts" if issues else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    # ========== PROCESS QUALITY CHECKS ==========

    def check_invalid_workflow_stage(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts with invalid workflow stages."""
        conn = self.get_connection()
        try:
            valid_stages_str = ','.join(str(s) for s in VALID_WORKFLOW_STAGES)
            query = f"""
                SELECT id, workflow_stage, status
                FROM contracts
                WHERE workflow_stage NOT IN ({valid_stages_str})
                  AND archived = 0
            """
            params = []
            if contract_id:
                query += " AND id = ?"
                params.append(contract_id)

            invalid = conn.execute(query, params).fetchall()

            total = conn.execute(
                "SELECT COUNT(*) FROM contracts WHERE archived = 0"
            ).fetchone()[0]

            failed = len(invalid)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='invalid_workflow_stage',
                check_name='Invalid Workflow Stage',
                category='process_quality',
                severity='high',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts have invalid workflow stages" if failed else "All workflow stages are valid",
                affected_count=failed,
                affected_ids=[r['id'] for r in invalid],
                details={'invalid': [
                    {'id': r['id'], 'stage': r['workflow_stage'], 'status': r['status']}
                    for r in invalid
                ]},
                recommendation="Reset workflow stage to valid value" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_stale_intake(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts stuck in intake for too long."""
        conn = self.get_connection()
        try:
            query = f"""
                SELECT id, title, upload_date, created_at
                FROM contracts
                WHERE workflow_stage = 0
                  AND DATE(COALESCE(upload_date, created_at)) < DATE('now', '-{STALE_INTAKE_DAYS} days')
                  AND archived = 0
            """
            params = []
            if contract_id:
                query += " AND id = ?"
                params.append(contract_id)

            stale = conn.execute(query, params).fetchall()

            total_intake = conn.execute("""
                SELECT COUNT(*) FROM contracts
                WHERE workflow_stage = 0 AND archived = 0
            """).fetchone()[0]

            failed = len(stale)
            score = 1.0 if total_intake == 0 else (total_intake - failed) / total_intake

            result = QACheckResult(
                check_id='stale_intake',
                check_name='Stale Intake',
                category='process_quality',
                severity='medium',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts stuck in intake for >{STALE_INTAKE_DAYS} days" if failed else "No contracts stuck in intake",
                affected_count=failed,
                affected_ids=[r['id'] for r in stale],
                details={'stale': [
                    {'id': r['id'], 'title': r['title'], 'uploaded': r['upload_date'] or r['created_at']}
                    for r in stale[:10]
                ]},
                recommendation="Review and process stale intake contracts" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_audit_completeness(self, contract_id: Optional[int] = None) -> QACheckResult:
        """Check for contracts with insufficient audit trail."""
        conn = self.get_connection()
        try:
            query = """
                SELECT c.id, c.title, COUNT(al.id) as audit_count
                FROM contracts c
                LEFT JOIN audit_log al ON c.id = al.contract_id
                WHERE c.archived = 0
            """
            params = []
            if contract_id:
                query += " AND c.id = ?"
                params.append(contract_id)

            query += " GROUP BY c.id HAVING audit_count < 2"

            incomplete = conn.execute(query, params).fetchall()

            total = conn.execute(
                "SELECT COUNT(*) FROM contracts WHERE archived = 0"
            ).fetchone()[0]

            failed = len(incomplete)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='audit_completeness',
                check_name='Audit Completeness',
                category='process_quality',
                severity='low',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts have incomplete audit trails" if failed else "All contracts have audit trails",
                affected_count=failed,
                affected_ids=[r['id'] for r in incomplete],
                details={'incomplete': [
                    {'id': r['id'], 'audit_count': r['audit_count']}
                    for r in incomplete[:10]
                ]},
                recommendation="Ensure all contract actions are logged" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    # ========== SYSTEM INTEGRITY CHECKS ==========

    def check_orphaned_risk_assessments(self) -> QACheckResult:
        """Check for risk assessments without parent contracts."""
        conn = self.get_connection()
        try:
            query = """
                SELECT ra.id, ra.contract_id
                FROM risk_assessments ra
                LEFT JOIN contracts c ON ra.contract_id = c.id
                WHERE c.id IS NULL
            """
            orphans = conn.execute(query).fetchall()

            total = conn.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0]
            failed = len(orphans)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='orphaned_risk_assessments',
                check_name='Orphaned Risk Assessments',
                category='system_integrity',
                severity='critical',
                passed=failed == 0,
                score=score,
                message=f"{failed} orphaned risk assessments found" if failed else "No orphaned risk assessments",
                affected_count=failed,
                affected_ids=[r['contract_id'] for r in orphans],
                details={'orphans': [{'ra_id': r['id'], 'contract_id': r['contract_id']} for r in orphans]},
                recommendation="Delete orphaned risk assessment records" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_orphaned_clauses(self) -> QACheckResult:
        """Check for clauses without parent contracts."""
        conn = self.get_connection()
        try:
            query = """
                SELECT cl.id, cl.contract_id
                FROM clauses cl
                LEFT JOIN contracts c ON cl.contract_id = c.id
                WHERE c.id IS NULL
            """
            orphans = conn.execute(query).fetchall()

            total = conn.execute("SELECT COUNT(*) FROM clauses").fetchone()[0]
            failed = len(orphans)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='orphaned_clauses',
                check_name='Orphaned Clauses',
                category='system_integrity',
                severity='critical',
                passed=failed == 0,
                score=score,
                message=f"{failed} orphaned clauses found" if failed else "No orphaned clauses",
                affected_count=failed,
                affected_ids=[r['contract_id'] for r in orphans],
                details={'orphan_count': failed},
                recommendation="Delete orphaned clause records" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_orphaned_snapshots(self) -> QACheckResult:
        """Check for analysis/comparison snapshots without parent contracts."""
        conn = self.get_connection()
        try:
            # Analysis snapshots
            analysis_query = """
                SELECT a.snapshot_id, a.contract_id
                FROM analysis_snapshots a
                LEFT JOIN contracts c ON a.contract_id = c.id
                WHERE c.id IS NULL
            """
            analysis_orphans = conn.execute(analysis_query).fetchall()

            # Comparison snapshots
            comparison_query = """
                SELECT cs.comparison_id, cs.v1_contract_id, cs.v2_contract_id
                FROM comparison_snapshots cs
                LEFT JOIN contracts c1 ON cs.v1_contract_id = c1.id
                LEFT JOIN contracts c2 ON cs.v2_contract_id = c2.id
                WHERE c1.id IS NULL OR c2.id IS NULL
            """
            comparison_orphans = conn.execute(comparison_query).fetchall()

            total_analysis = conn.execute("SELECT COUNT(*) FROM analysis_snapshots").fetchone()[0]
            total_comparison = conn.execute("SELECT COUNT(*) FROM comparison_snapshots").fetchone()[0]
            total = total_analysis + total_comparison

            failed = len(analysis_orphans) + len(comparison_orphans)
            score = 1.0 if total == 0 else (total - failed) / total

            result = QACheckResult(
                check_id='orphaned_snapshots',
                check_name='Orphaned Snapshots',
                category='system_integrity',
                severity='high',
                passed=failed == 0,
                score=score,
                message=f"{failed} orphaned snapshots found ({len(analysis_orphans)} analysis, {len(comparison_orphans)} comparison)" if failed else "No orphaned snapshots",
                affected_count=failed,
                affected_ids=[],
                details={
                    'analysis_orphans': len(analysis_orphans),
                    'comparison_orphans': len(comparison_orphans)
                },
                recommendation="Delete orphaned snapshot records" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_invalid_parent_references(self) -> QACheckResult:
        """Check for contracts with invalid parent_id references."""
        conn = self.get_connection()
        try:
            query = """
                SELECT c.id, c.parent_id, c.title
                FROM contracts c
                LEFT JOIN contracts parent ON c.parent_id = parent.id
                WHERE c.parent_id IS NOT NULL AND parent.id IS NULL
            """
            invalid = conn.execute(query).fetchall()

            total_with_parent = conn.execute("""
                SELECT COUNT(*) FROM contracts WHERE parent_id IS NOT NULL
            """).fetchone()[0]

            failed = len(invalid)
            score = 1.0 if total_with_parent == 0 else (total_with_parent - failed) / total_with_parent

            result = QACheckResult(
                check_id='invalid_parent_references',
                check_name='Invalid Parent References',
                category='system_integrity',
                severity='high',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts reference non-existent parents" if failed else "All parent references are valid",
                affected_count=failed,
                affected_ids=[r['id'] for r in invalid],
                details={'invalid': [
                    {'id': r['id'], 'parent_id': r['parent_id'], 'title': r['title']}
                    for r in invalid
                ]},
                recommendation="Clear or fix invalid parent_id references" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    def check_circular_relationships(self) -> QACheckResult:
        """Check for circular parent-child relationships."""
        conn = self.get_connection()
        try:
            # Get all contracts with parents
            contracts = conn.execute("""
                SELECT id, parent_id FROM contracts WHERE parent_id IS NOT NULL
            """).fetchall()

            # Build parent map
            parent_map = {r['id']: r['parent_id'] for r in contracts}

            # Check for cycles
            circular = []
            for contract_id in parent_map:
                visited = set()
                current = contract_id
                while current in parent_map:
                    if current in visited:
                        circular.append(contract_id)
                        break
                    visited.add(current)
                    current = parent_map.get(current)
                    if len(visited) > 100:  # Safety limit
                        break

            total_with_parent = len(contracts)
            failed = len(circular)
            score = 1.0 if total_with_parent == 0 else (total_with_parent - failed) / total_with_parent

            result = QACheckResult(
                check_id='circular_relationships',
                check_name='Circular Relationships',
                category='system_integrity',
                severity='medium',
                passed=failed == 0,
                score=score,
                message=f"{failed} contracts involved in circular relationships" if failed else "No circular relationships",
                affected_count=failed,
                affected_ids=circular,
                details={'circular_ids': circular[:10]},
                recommendation="Break circular parent-child relationships" if failed else ""
            )
            self.results.append(result)
            return result
        finally:
            conn.close()

    # ========== REPORT GENERATION ==========

    def _generate_report(self) -> QAReport:
        """Generate complete QA report from check results."""
        # Calculate category scores
        categories = {}
        for category, weight in CATEGORY_WEIGHTS.items():
            category_results = [r for r in self.results if r.category == category]
            if category_results:
                avg_score = sum(r.score for r in category_results) / len(category_results)
                categories[category] = {
                    'score': round(avg_score * 100, 1),
                    'weight': weight,
                    'checks': [r.to_dict() for r in category_results],
                    'passed': sum(1 for r in category_results if r.passed),
                    'failed': sum(1 for r in category_results if not r.passed)
                }
            else:
                categories[category] = {
                    'score': 100,
                    'weight': weight,
                    'checks': [],
                    'passed': 0,
                    'failed': 0
                }

        # Calculate overall score (weighted average)
        overall_score = sum(
            categories[cat]['score'] * CATEGORY_WEIGHTS[cat] / 100
            for cat in CATEGORY_WEIGHTS
        )

        # Determine grade
        grade = 'F'
        grade_info = QA_GRADES['F']
        for g, info in sorted(QA_GRADES.items(), key=lambda x: -x[1]['min']):
            if overall_score >= info['min']:
                grade = g
                grade_info = info
                break

        # Collect critical issues
        critical_issues = [r for r in self.results if not r.passed and r.severity in ('critical', 'high')]

        # Collect recommendations
        recommendations = [r.recommendation for r in self.results if r.recommendation]

        return QAReport(
            overall_score=round(overall_score, 1),
            grade=grade,
            grade_color=grade_info['color'],
            grade_label=grade_info['label'],
            generated_at=datetime.now().isoformat(),
            total_checks=len(self.results),
            passed_checks=sum(1 for r in self.results if r.passed),
            failed_checks=sum(1 for r in self.results if not r.passed),
            categories=categories,
            checks=self.results,
            critical_issues=critical_issues,
            recommendations=recommendations
        )


# ========== UTILITY FUNCTIONS ==========

def run_qa_checks(contract_id: Optional[int] = None, category: Optional[str] = None) -> QAReport:
    """Convenience function to run QA checks."""
    engine = QACheckEngine()
    if category:
        return engine.run_category_checks(category, contract_id)
    return engine.run_all_checks(contract_id)


def get_qa_dashboard_summary() -> Dict[str, Any]:
    """Get summary data for dashboard widget."""
    engine = QACheckEngine()
    report = engine.run_all_checks()

    return {
        'overall_score': report.overall_score,
        'grade': report.grade,
        'grade_color': report.grade_color,
        'grade_label': report.grade_label,
        'total_checks': report.total_checks,
        'passed': report.passed_checks,
        'failed': report.failed_checks,
        'critical_count': len([c for c in report.critical_issues if c.severity == 'critical']),
        'high_count': len([c for c in report.critical_issues if c.severity == 'high']),
        'categories': {
            cat: {'score': info['score'], 'status': 'pass' if info['failed'] == 0 else 'fail'}
            for cat, info in report.categories.items()
        }
    }


def fix_orphaned_records() -> Dict[str, int]:
    """Delete orphaned records from all tables. Returns count of deleted records."""
    conn = sqlite3.connect(str(CONTRACTS_DB))
    try:
        deleted = {}

        # Delete orphaned risk assessments
        cursor = conn.execute("""
            DELETE FROM risk_assessments
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        deleted['risk_assessments'] = cursor.rowcount

        # Delete orphaned clauses
        cursor = conn.execute("""
            DELETE FROM clauses
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        deleted['clauses'] = cursor.rowcount

        # Delete orphaned analysis snapshots
        cursor = conn.execute("""
            DELETE FROM analysis_snapshots
            WHERE contract_id NOT IN (SELECT id FROM contracts)
        """)
        deleted['analysis_snapshots'] = cursor.rowcount

        conn.commit()
        return deleted
    finally:
        conn.close()


if __name__ == '__main__':
    # CLI execution
    import sys

    print("CIP QA/QC Check Engine")
    print("=" * 50)

    report = run_qa_checks()

    print(f"\nOverall Score: {report.overall_score} ({report.grade})")
    print(f"Checks: {report.passed_checks}/{report.total_checks} passed\n")

    for category, info in report.categories.items():
        status = "PASS" if info['failed'] == 0 else "FAIL"
        print(f"  {category}: {info['score']}% [{status}]")

    if report.critical_issues:
        print(f"\nCritical Issues ({len(report.critical_issues)}):")
        for issue in report.critical_issues[:5]:
            print(f"  - {issue.check_name}: {issue.message}")

    if report.recommendations:
        print(f"\nRecommendations:")
        for rec in report.recommendations[:5]:
            print(f"  - {rec}")
