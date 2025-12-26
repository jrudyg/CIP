"""
Compare v3 Integration Tests
Phase 5 - Task 5 Validation

Tests for:
1. Data binding correctness
2. Event rendering for all engines
3. Model validation
4. No truncation or shape mismatch
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# TEST DATA
# ============================================================================

VALID_API_RESPONSE = {
    "success": True,
    "data": {
        "id": 1,
        "v1_snapshot_id": 10,
        "v2_snapshot_id": 11,
        "created_at": "2025-12-09T10:00:00Z",
        "sae_matches": [
            {
                "v1_clause_id": 1,
                "v2_clause_id": 1,
                "similarity_score": 0.95,
                "threshold_used": 0.90,
                "match_confidence": "HIGH",
            },
            {
                "v1_clause_id": 2,
                "v2_clause_id": 3,
                "similarity_score": 0.78,
                "threshold_used": 0.75,
                "match_confidence": "MEDIUM",
            },
        ],
        "erce_results": [
            {
                "clause_pair_id": 1,
                "risk_category": "CRITICAL",
                "pattern_ref": "UNLIMITED_LIABILITY",
                "success_probability": 0.35,
                "confidence": 0.92,
            },
            {
                "clause_pair_id": 2,
                "risk_category": "MODERATE",
                "pattern_ref": None,
                "success_probability": 0.70,
                "confidence": 0.85,
            },
        ],
        "birl_narratives": [
            {
                "clause_pair_id": 1,
                "narrative": "This change introduces significant margin impact.",
                "impact_dimensions": ["MARGIN", "RISK"],
                "token_count": 45,
            },
        ],
        "flowdown_gaps": [
            {
                "gap_type": "Payment Terms",
                "severity": "HIGH",
                "upstream_value": "Net 30",
                "downstream_value": "Net 60",
                "recommendation": "Align payment terms with prime contract.",
            },
        ],
        "_meta": {
            "engine_version": "3.0.0",
            "pipeline_status": "COMPLETE",
        },
    },
    "intelligence_active": True,
    "error_category": None,
    "error_message_key": None,
}

ERROR_API_RESPONSE = {
    "success": False,
    "error_category": "network_error",
    "error_message_key": "compare.network_failure",
}

EMPTY_DATA_RESPONSE = {
    "success": True,
    "data": {
        "id": 2,
        "v1_snapshot_id": 20,
        "v2_snapshot_id": 21,
        "created_at": "2025-12-09T11:00:00Z",
        "sae_matches": [],
        "erce_results": [],
        "birl_narratives": [],
        "flowdown_gaps": [],
    },
}


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_api_response_shape_validation():
    """Test 1: Validate API response shape detection."""
    from compare_v3_integration import validate_api_response_shape

    results = []

    # Test valid response
    is_valid, errors = validate_api_response_shape(VALID_API_RESPONSE)
    results.append({
        "test": "valid_response",
        "passed": is_valid and len(errors) == 0,
        "errors": errors,
    })

    # Test error response
    is_valid, errors = validate_api_response_shape(ERROR_API_RESPONSE)
    results.append({
        "test": "error_response",
        "passed": is_valid,  # Should still be valid shape
        "errors": errors,
    })

    # Test null response
    is_valid, errors = validate_api_response_shape(None)
    results.append({
        "test": "null_response",
        "passed": not is_valid,  # Should be invalid
        "errors": errors,
    })

    # Test malformed response
    is_valid, errors = validate_api_response_shape({"foo": "bar"})
    results.append({
        "test": "malformed_response",
        "passed": not is_valid,  # Should be invalid
        "errors": errors,
    })

    return results


def test_data_binding():
    """Test 2: Validate data binding extracts all engines correctly."""
    from compare_v3_integration import CompareV3DataBinder

    results = []

    # Bind valid response
    binder = CompareV3DataBinder(VALID_API_RESPONSE)

    # Test SAE extraction
    sae = binder.get_sae_matches()
    results.append({
        "test": "sae_extraction",
        "passed": len(sae) == 2 and sae[0]["v1_clause_id"] == 1,
        "count": len(sae),
    })

    # Test ERCE extraction
    erce = binder.get_erce_results()
    results.append({
        "test": "erce_extraction",
        "passed": len(erce) == 2 and erce[0]["risk_category"] == "CRITICAL",
        "count": len(erce),
    })

    # Test BIRL extraction
    birl = binder.get_birl_narratives()
    results.append({
        "test": "birl_extraction",
        "passed": len(birl) == 1 and "MARGIN" in birl[0]["impact_dimensions"],
        "count": len(birl),
    })

    # Test FAR extraction
    far = binder.get_flowdown_gaps()
    results.append({
        "test": "far_extraction",
        "passed": len(far) == 1 and far[0]["severity"] == "HIGH",
        "count": len(far),
    })

    return results


def test_engine_field_validation():
    """Test 3: Validate engine fields match specification."""
    from compare_v3_integration import validate_engine_fields

    results = []

    # Test SAE fields
    sae_items = VALID_API_RESPONSE["data"]["sae_matches"]
    is_valid, errors = validate_engine_fields("SAE", sae_items)
    results.append({
        "test": "sae_fields",
        "passed": is_valid,
        "errors": errors,
    })

    # Test ERCE fields
    erce_items = VALID_API_RESPONSE["data"]["erce_results"]
    is_valid, errors = validate_engine_fields("ERCE", erce_items)
    results.append({
        "test": "erce_fields",
        "passed": is_valid,
        "errors": errors,
    })

    # Test BIRL fields
    birl_items = VALID_API_RESPONSE["data"]["birl_narratives"]
    is_valid, errors = validate_engine_fields("BIRL", birl_items)
    results.append({
        "test": "birl_fields",
        "passed": is_valid,
        "errors": errors,
    })

    # Test FAR fields
    far_items = VALID_API_RESPONSE["data"]["flowdown_gaps"]
    is_valid, errors = validate_engine_fields("FAR", far_items)
    results.append({
        "test": "far_fields",
        "passed": is_valid,
        "errors": errors,
    })

    return results


def test_empty_data_handling():
    """Test 4: Validate empty data arrays are handled correctly."""
    from compare_v3_integration import CompareV3DataBinder

    results = []

    binder = CompareV3DataBinder(EMPTY_DATA_RESPONSE)

    results.append({
        "test": "empty_sae",
        "passed": len(binder.get_sae_matches()) == 0,
    })
    results.append({
        "test": "empty_erce",
        "passed": len(binder.get_erce_results()) == 0,
    })
    results.append({
        "test": "empty_birl",
        "passed": len(binder.get_birl_narratives()) == 0,
    })
    results.append({
        "test": "empty_far",
        "passed": len(binder.get_flowdown_gaps()) == 0,
    })
    results.append({
        "test": "is_valid_empty",
        "passed": binder.is_valid(),
    })

    return results


def test_error_response_handling():
    """Test 5: Validate error responses are handled gracefully."""
    from compare_v3_integration import CompareV3DataBinder

    results = []

    binder = CompareV3DataBinder(ERROR_API_RESPONSE)
    outputs = binder.get_outputs()

    results.append({
        "test": "error_success_false",
        "passed": not outputs.success,
    })
    results.append({
        "test": "error_category_captured",
        "passed": outputs.error_category == "network_error",
    })
    results.append({
        "test": "error_no_crash",
        "passed": True,  # If we got here, no crash
    })

    return results


def test_no_data_truncation():
    """Test 6: Validate data is not truncated during extraction."""
    from compare_v3_integration import extract_all_engine_outputs

    results = []

    # Create response with many items
    large_response = {
        "success": True,
        "data": {
            "id": 3,
            "v1_snapshot_id": 30,
            "v2_snapshot_id": 31,
            "created_at": "2025-12-09T12:00:00Z",
            "sae_matches": [
                {"v1_clause_id": i, "v2_clause_id": i, "similarity_score": 0.9,
                 "threshold_used": 0.75, "match_confidence": "HIGH"}
                for i in range(100)
            ],
            "erce_results": [
                {"clause_pair_id": i, "risk_category": "MODERATE",
                 "pattern_ref": None, "success_probability": 0.5, "confidence": 0.8}
                for i in range(50)
            ],
            "birl_narratives": [
                {"clause_pair_id": i, "narrative": f"Narrative {i}",
                 "impact_dimensions": ["MARGIN"], "token_count": 20}
                for i in range(25)
            ],
            "flowdown_gaps": [
                {"gap_type": f"Gap {i}", "severity": "MODERATE",
                 "upstream_value": "A", "downstream_value": "B",
                 "recommendation": "Fix it"}
                for i in range(15)
            ],
        },
    }

    outputs = extract_all_engine_outputs(large_response)

    results.append({
        "test": "sae_no_truncation",
        "passed": len(outputs.sae_matches) == 100,
        "expected": 100,
        "actual": len(outputs.sae_matches),
    })
    results.append({
        "test": "erce_no_truncation",
        "passed": len(outputs.erce_results) == 50,
        "expected": 50,
        "actual": len(outputs.erce_results),
    })
    results.append({
        "test": "birl_no_truncation",
        "passed": len(outputs.birl_narratives) == 25,
        "expected": 25,
        "actual": len(outputs.birl_narratives),
    })
    results.append({
        "test": "far_no_truncation",
        "passed": len(outputs.flowdown_gaps) == 15,
        "expected": 15,
        "actual": len(outputs.flowdown_gaps),
    })

    return results


def test_full_diagnostics():
    """Test 7: Run full integration diagnostics."""
    from compare_v3_integration import run_integration_diagnostics

    results = []

    diag = run_integration_diagnostics(VALID_API_RESPONSE)

    results.append({
        "test": "diagnostics_overall",
        "passed": diag["overall_valid"],
    })
    results.append({
        "test": "diagnostics_shape",
        "passed": diag["shape_validation"]["valid"],
    })
    results.append({
        "test": "diagnostics_sae",
        "passed": diag["engine_validation"]["SAE"]["valid"],
    })
    results.append({
        "test": "diagnostics_erce",
        "passed": diag["engine_validation"]["ERCE"]["valid"],
    })
    results.append({
        "test": "diagnostics_birl",
        "passed": diag["engine_validation"]["BIRL"]["valid"],
    })
    results.append({
        "test": "diagnostics_far",
        "passed": diag["engine_validation"]["FAR"]["valid"],
    })

    return results


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all integration tests and return report."""
    all_results = []

    test_suites = [
        ("API Response Shape Validation", test_api_response_shape_validation),
        ("Data Binding", test_data_binding),
        ("Engine Field Validation", test_engine_field_validation),
        ("Empty Data Handling", test_empty_data_handling),
        ("Error Response Handling", test_error_response_handling),
        ("No Data Truncation", test_no_data_truncation),
        ("Full Diagnostics", test_full_diagnostics),
    ]

    for suite_name, test_func in test_suites:
        try:
            results = test_func()
            all_results.append({
                "suite": suite_name,
                "status": "PASSED" if all(r.get("passed", False) for r in results) else "FAILED",
                "tests": results,
            })
        except Exception as e:
            all_results.append({
                "suite": suite_name,
                "status": "ERROR",
                "error": str(e),
            })

    # Calculate totals
    total_suites = len(all_results)
    passed_suites = sum(1 for r in all_results if r["status"] == "PASSED")

    total_tests = sum(len(r.get("tests", [])) for r in all_results)
    passed_tests = sum(
        sum(1 for t in r.get("tests", []) if t.get("passed", False))
        for r in all_results
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "suites_total": total_suites,
            "suites_passed": passed_suites,
            "tests_total": total_tests,
            "tests_passed": passed_tests,
            "overall_status": "PASS" if passed_suites == total_suites else "FAIL",
        },
        "results": all_results,
    }


if __name__ == "__main__":
    # Run tests
    report = run_all_tests()

    # Print summary
    print("\n" + "=" * 60)
    print("CC3 INTEGRATION TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Overall Status: {report['summary']['overall_status']}")
    print(f"Suites: {report['summary']['suites_passed']}/{report['summary']['suites_total']} passed")
    print(f"Tests: {report['summary']['tests_passed']}/{report['summary']['tests_total']} passed")
    print("=" * 60)

    for result in report["results"]:
        status_icon = "PASS" if result["status"] == "PASSED" else "FAIL"
        print(f"\n[{status_icon}] {result['suite']}")
        if "tests" in result:
            for test in result["tests"]:
                test_icon = "+" if test.get("passed") else "-"
                print(f"  {test_icon} {test.get('test', 'unknown')}")

    # Save report
    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tests",
        "integration_test_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
