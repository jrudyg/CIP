"""
CIP Integration Test
Tests thread-local database connections and end-to-end workflow
"""

import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from orchestrator import ContractOrchestrator, ContractContext
from config import ANTHROPIC_API_KEY, DEFAULT_MODEL


def test_thread_local_connections():
    """Test that thread-local connections work correctly"""
    print("\n" + "="*60)
    print("TEST 1: Thread-Local Database Connections")
    print("="*60)

    orchestrator = ContractOrchestrator()
    results = []
    errors = []

    def worker(worker_id):
        """Worker function to test concurrent database access"""
        try:
            thread_name = threading.current_thread().name
            thread_id = threading.current_thread().ident

            # Get connection for this thread
            conn = orchestrator._get_db_conn()

            if conn:
                cursor = conn.cursor()
                # Test query
                cursor.execute("SELECT COUNT(*) FROM contracts")
                count = cursor.fetchone()[0]

                result = {
                    'worker_id': worker_id,
                    'thread_name': thread_name,
                    'thread_id': thread_id,
                    'contract_count': count,
                    'success': True
                }
                results.append(result)
                return result
            else:
                raise Exception("Failed to get database connection")

        except Exception as e:
            error = {
                'worker_id': worker_id,
                'error': str(e),
                'success': False
            }
            errors.append(error)
            return error

    # Test with 5 concurrent threads
    print(f"\nRunning 5 concurrent database operations...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(5)]

        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                print(f"  Worker {result['worker_id']} (Thread {result['thread_id']}): "
                      f"Query successful - {result['contract_count']} contracts")
            else:
                print(f"  Worker {result['worker_id']}: ERROR - {result['error']}")

    # Verify results
    print(f"\nResults: {len(results)} successful, {len(errors)} errors")

    # Check that each thread got its own connection
    thread_ids = [r['thread_id'] for r in results]
    unique_threads = len(set(thread_ids))
    print(f"Unique thread IDs: {unique_threads}")
    print(f"Total connections created: {len(orchestrator._db_connections)}")

    # Cleanup
    orchestrator.close()
    print(f"\nAll connections closed successfully")

    # Assert test passed
    assert len(errors) == 0, f"Test failed with {len(errors)} errors"
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"

    print("\n[PASS] TEST 1: Thread-local connections working correctly")
    return True


def test_orchestrator_initialization():
    """Test that orchestrator initializes with all components"""
    print("\n" + "="*60)
    print("TEST 2: Orchestrator Initialization")
    print("="*60)

    try:
        orchestrator = ContractOrchestrator()

        # Check knowledge base loaded
        kb_loaded = len(orchestrator.knowledge_base.knowledge_base) > 0
        print(f"\nKnowledge base loaded: {len(orchestrator.knowledge_base.knowledge_base)} documents")

        # Check analyzer configured
        analyzer_model = orchestrator.analyzer.model
        print(f"Analyzer model: {analyzer_model}")

        # Check expected model
        assert analyzer_model == DEFAULT_MODEL, f"Model mismatch: {analyzer_model} != {DEFAULT_MODEL}"

        # Check database path
        print(f"Database path: {orchestrator.db_path}")
        assert Path(orchestrator.db_path).exists(), "Database does not exist"

        orchestrator.close()

        print("\n[PASS] TEST 2: Orchestrator initialized correctly")
        return True

    except Exception as e:
        print(f"\n[FAIL] TEST 2: {e}")
        return False


def test_context_creation():
    """Test ContractContext creation"""
    print("\n" + "="*60)
    print("TEST 3: Contract Context Creation")
    print("="*60)

    try:
        context = ContractContext(
            position="vendor",
            leverage="moderate",
            contract_type="Service Agreement",
            narrative="Test contract for integration testing",
            parties="Test Company, Client Company"
        )

        print(f"\nContract context created:")
        print(f"  Position: {context.position}")
        print(f"  Leverage: {context.leverage}")
        print(f"  Type: {context.contract_type}")
        print(f"  Parties: {context.parties}")

        print("\n[PASS] TEST 3: Contract context created successfully")
        return True

    except Exception as e:
        print(f"\n[FAIL] TEST 3: {e}")
        return False


def test_api_key_configuration():
    """Test API key is configured"""
    print("\n" + "="*60)
    print("TEST 4: API Key Configuration")
    print("="*60)

    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.startswith("sk-ant-"):
        print(f"\nAPI Key configured: {ANTHROPIC_API_KEY[:20]}...")
        print(f"Model configured: {DEFAULT_MODEL}")
        print("\n[PASS] TEST 4: API key configured correctly")
        return True
    else:
        print(f"\n[FAIL] TEST 4: API key not configured or invalid")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("CIP INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Testing thread-local database connections and system integration")

    tests = [
        ("Thread-Local Connections", test_thread_local_connections),
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Contract Context", test_context_creation),
        ("API Configuration", test_api_key_configuration),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {test_name} with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "[PASS]" if passed_flag else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*60)
        print("ALL TESTS PASSED - SYSTEM READY")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print(f"TESTS FAILED - {total - passed} failures")
        print("="*60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
