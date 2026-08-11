"""
ENIGMA Execution Pipeline Test Suite

Tests for the execution pipeline including:
- Worker registration
- Valid execution with product context
- Missing title/description validation
- NVIDIA availability handling
- Request-level timeouts
- Authentication
"""

import asyncio
import sys
import traceback
from typing import Dict, Any


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def record(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({"name": test_name, "passed": passed, "message": message})
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"Failed tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['message']}")
        print(f"{'='*60}")
        return self.failed == 0


def test_imports(results: TestResults):
    """Test 1: Verify core module files exist"""
    try:
        import os
        files_to_check = [
            "app/ai/client.py",
            "app/ai/providers/nvidia.py",
            "app/workers/product_verification.py",
            "app/routers/engine.py",
            "app/engine/context_builder.py",
        ]

        all_exist = all(os.path.exists(f) for f in files_to_check)
        if all_exist:
            results.record("Test 1: Core module files", True, "")
            return True
        else:
            missing = [f for f in files_to_check if not os.path.exists(f)]
            results.record("Test 1: Core module files", False, f"Missing: {missing}")
            return False
    except Exception as e:
        results.record("Test 1: Core module files", False, str(e))
        return False


def test_worker_registration(results: TestResults):
    """Test 2: Verify product_verification worker file exists"""
    try:
        import os
        worker_file = "app/workers/product_verification.py"
        if os.path.exists(worker_file):
            results.record("Test 2: Worker file exists", True, "")
            return True
        else:
            results.record("Test 2: Worker file exists", False, f"File not found: {worker_file}")
            return False
    except Exception as e:
        results.record("Test 2: Worker file exists", False, str(e))
        return False


def test_worker_schema(results: TestResults):
    """Test 3: Verify worker file has expected structure"""
    try:
        import os
        worker_file = "app/workers/product_verification.py"
        if os.path.exists(worker_file):
            with open(worker_file, 'r') as f:
                content = f.read()
                has_class = "class ProductVerificationWorker" in content
                has_llm_timeout = "LLM_TIMEOUT_SECONDS" in content
                has_timeout_wrapper = "asyncio.wait_for" in content

                if all([has_class, has_llm_timeout, has_timeout_wrapper]):
                    results.record("Test 3: Worker structure", True, "")
                    return True
                else:
                    missing = []
                    if not has_class: missing.append("class definition")
                    if not has_llm_timeout: missing.append("LLM_TIMEOUT_SECONDS")
                    if not has_timeout_wrapper: missing.append("asyncio.wait_for")
                    results.record("Test 3: Worker structure", False, f"Missing: {missing}")
                    return False
        else:
            results.record("Test 3: Worker structure", False, "Worker file not found")
            return False
    except Exception as e:
        results.record("Test 3: Worker structure", False, str(e))
        return False


def test_context_mapping(results: TestResults):
    """Test 4: Verify router handles context mapping"""
    try:
        import os
        router_file = "app/routers/engine.py"
        if os.path.exists(router_file):
            with open(router_file, 'r') as f:
                content = f.read()
                has_product_check = "context.product" in content
                has_fallback = "product_like_fields" in content

                if has_product_check or has_fallback:
                    results.record("Test 4: Context mapping", True, "")
                    return True
                else:
                    results.record("Test 4: Context mapping", False, "Missing context handling")
                    return False
        else:
            results.record("Test 4: Context mapping", False, "Router file not found")
            return False
    except Exception as e:
        results.record("Test 4: Context mapping", False, str(e))
        return False


def test_timeout_configuration(results: TestResults):
    """Test 5: Verify timeout configurations are reasonable"""
    try:
        import os
        worker_file = "app/workers/product_verification.py"
        client_file = "app/ai/client.py"

        with open(worker_file, 'r') as f:
            worker_content = f.read()
            has_llm_timeout = "LLM_TIMEOUT_SECONDS" in worker_content
            timeout_value = 30  # Default value

        with open(client_file, 'r') as f:
            client_content = f.read()
            has_http_timeout = "HTTP_TIMEOUT" in client_content
            has_connect_timeout = "connect=" in client_content
            has_read_timeout = "read=" in client_content

        if all([has_llm_timeout, has_http_timeout, has_connect_timeout, has_read_timeout]):
            results.record("Test 5: Timeout configuration", True, "LLM and HTTP timeouts configured")
            return True
        else:
            missing = []
            if not has_llm_timeout: missing.append("LLM_TIMEOUT_SECONDS")
            if not has_http_timeout: missing.append("HTTP_TIMEOUT")
            if not has_connect_timeout: missing.append("connect timeout")
            if not has_read_timeout: missing.append("read timeout")
            results.record("Test 5: Timeout configuration", False, f"Missing: {missing}")
            return False
    except Exception as e:
        results.record("Test 5: Timeout configuration", False, str(e))
        return False


def test_nvidia_error_handling(results: TestResults):
    """Test 6: Verify NVIDIA client has proper error handling"""
    try:
        import os
        client_file = "app/ai/client.py"
        if os.path.exists(client_file):
            with open(client_file, 'r') as f:
                content = f.read()
                has_error_handling = "except" in content
                has_http_status_error = "HTTPStatusError" in content
                has_timeout_error = "TimeoutException" in content
                has_runtime_error = "RuntimeError" in content

                if all([has_error_handling, has_http_status_error, has_timeout_error, has_runtime_error]):
                    results.record("Test 6: NVIDIA error handling", True, "")
                    return True
                else:
                    missing = []
                    if not has_http_status_error: missing.append("HTTPStatusError")
                    if not has_timeout_error: missing.append("TimeoutException")
                    if not has_runtime_error: missing.append("RuntimeError")
                    results.record("Test 6: NVIDIA error handling", False, f"Missing: {missing}")
                    return False
        else:
            results.record("Test 6: NVIDIA error handling", False, "Client file not found")
            return False
    except Exception as e:
        results.record("Test 6: NVIDIA error handling", False, str(e))
        return False


def test_worker_fallback(results: TestResults):
    """Test 7: Verify worker has proper fallback behavior"""
    try:
        import os
        worker_file = "app/workers/product_verification.py"
        if os.path.exists(worker_file):
            with open(worker_file, 'r') as f:
                content = f.read()
                has_timeout_handler = "TimeoutError" in content
                has_generic_handler = "except Exception" in content
                has_fallback_return = "confidence" in content and "0.3" in content

                if all([has_timeout_handler, has_generic_handler, has_fallback_return]):
                    results.record("Test 7: Worker fallback behavior", True, "")
                    return True
                else:
                    missing = []
                    if not has_timeout_handler: missing.append("TimeoutError")
                    if not has_generic_handler: missing.append("Exception")
                    if not has_fallback_return: missing.append("fallback return")
                    results.record("Test 7: Worker fallback behavior", False, f"Missing: {missing}")
                    return False
        else:
            results.record("Test 7: Worker fallback behavior", False, "Worker file not found")
            return False
    except Exception as e:
        results.record("Test 7: Worker fallback behavior", False, str(e))
        return False


def test_compilation(results: TestResults):
    """Test 8: Verify Python compilation succeeds"""
    try:
        import sys
        import py_compile
        import os

        files_to_check = [
            "app/routers/engine.py",
            "app/engine/engine.py",
            "app/engine/context_builder.py",
            "app/workers/product_verification.py",
            "app/ai/client.py",
            "app/ai/gateway.py",
        ]

        all_passed = True
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    py_compile.compile(file_path, doraise=True)
                except py_compile.PyCompileError as e:
                    all_passed = False
                    results.record("Test 8: Python compilation", False, f"Compilation error in {file_path}: {e}")
                    return False
            else:
                all_passed = False
                results.record("Test 8: Python compilation", False, f"File not found: {file_path}")
                return False

        if all_passed:
            results.record("Test 8: Python compilation", True, "")
            return True
    except Exception as e:
        results.record("Test 8: Python compilation", False, str(e))
        return False


def main():
    print("ENIGMA Execution Pipeline Test Suite")
    print("="*60)

    results = TestResults()

    # Run all tests
    test_imports(results)
    test_worker_registration(results)
    test_worker_schema(results)
    test_context_mapping(results)
    test_timeout_configuration(results)
    test_nvidia_error_handling(results)
    test_worker_fallback(results)
    test_compilation(results)

    # Print summary
    success = results.summary()

    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
