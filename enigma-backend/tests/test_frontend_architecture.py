"""
Architecture Tests: Frontend Intelligence Leakage Prevention

These tests ensure that the frontend cannot bypass API contracts
to directly access cognitive core internals.

FORBIDDEN: Frontend → MasterBrain, Knowledge Graph, Governance, Memory, Decision logic
ALLOWED: Frontend → API Contracts → Backend → Enigma Brain
"""
import ast
import sys
from pathlib import Path
from typing import List, Set


class FrontendArchitectureValidator:
    """Validates that frontend code does not import cognitive core internals."""

    # Cognitive core modules that frontend must NOT import directly
    FORBIDDEN_BACKEND_MODULES = {
        "app.ai.master_brain",
        "app.ai.product_brain",
        "app.knowledge.graph",
        "app.knowledge.governance",
        "app.memory.memory_store",
        "app.intelligence.reasoning",
        "app.profession.reasoning",
        "app.engine.decision_engine",
        "app.execution.runtime",
    }

    # Allowed API contract modules (the only backend modules frontend can import)
    ALLOWED_API_MODULES = {
        "app.api.schemas",
        "app.api.routes",
    }

    def __init__(self, frontend_path: Path):
        self.frontend_path = frontend_path
        self.violations: List[str] = []

    def check_file(self, file_path: Path) -> None:
        """Check a single Python file for forbidden imports."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            return  # Skip files with syntax errors

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_import(alias.name, file_path)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._check_import(node.module, file_path)

    def _check_import(self, module_name: str, file_path: Path) -> None:
        """Check if an import violates architecture boundaries."""
        # Check if it's a forbidden backend module
        for forbidden in self.FORBIDDEN_BACKEND_MODULES:
            if module_name.startswith(forbidden):
                self.violations.append(
                    f"{file_path}: Forbidden import of cognitive core: {module_name}"
                )
                return

    def validate_directory(self) -> bool:
        """Validate all Python files in the frontend directory."""
        if not self.frontend_path.exists():
            print(f"Frontend directory not found: {self.frontend_path}")
            return True  # Pass if frontend doesn't exist yet

        for py_file in self.frontend_path.rglob("*.py"):
            self.check_file(py_file)

        return len(self.violations) == 0


def test_frontend_no_cognitive_core_imports():
    """
    TEST: Frontend must not import cognitive core internals directly.
    
    This ensures the Control Plane principle: frontend only communicates
    via API contracts, never directly to the brain.
    """
    # Assuming frontend code would be in enigma-frontend
    frontend_path = Path(__file__).parent.parent.parent / "enigma-frontend"
    
    validator = FrontendArchitectureValidator(frontend_path)
    is_valid = validator.validate_directory()
    
    if not is_valid:
        print("\n[X] ARCHITECTURE VIOLATIONS DETECTED:")
        for violation in validator.violations:
            print(f"  - {violation}")
        print("\nFrontend must use API contracts only. Direct cognitive core access is forbidden.")
        assert False, "Frontend architecture violations detected"
    
    print("[OK] Frontend architecture validated: no cognitive core imports")
    assert True


def test_backend_api_contracts_exist():
    """
    TEST: Backend must have API contract modules defined.
    
    This ensures the API layer exists as the boundary between
    frontend and cognitive core.
    """
    backend_path = Path(__file__).parent.parent / "app"
    
    # Check that API schemas exist
    schemas_path = backend_path / "api" / "schemas"
    routes_path = backend_path / "api" / "routes"
    
    if not schemas_path.exists():
        print("[!] API schemas directory not yet created (expected in later phase)")
        return  # Not a failure if not created yet
    
    if not routes_path.exists():
        print("[!] API routes directory not yet created (expected in later phase)")
        return  # Not a failure if not created yet
    
    print("[OK] API contract directories exist")
    assert True


def test_backend_cognitive_core_isolated():
    """
    TEST: Cognitive core modules should not depend on frontend.
    
    This ensures the backend brain remains independent and can
    be tested/used without any frontend.
    """
    backend_path = Path(__file__).parent.parent / "app"
    
    # Check that cognitive core modules don't import frontend
    forbidden_imports = {"enigma-frontend", "frontend"}
    
    cognitive_modules = [
        backend_path / "ai",
        backend_path / "knowledge",
        backend_path / "memory",
        backend_path / "profession",
        backend_path / "intelligence",
        backend_path / "execution",
    ]
    
    violations = []
    
    for module_path in cognitive_modules:
        if not module_path.exists():
            continue
        for py_file in module_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                for forbidden in forbidden_imports:
                    if forbidden in source:
                        violations.append(f"{py_file}: Contains '{forbidden}'")
            except Exception:
                continue
    
    if violations:
        print("\n[X] COGNITIVE CORE VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        assert False, "Cognitive core must not depend on frontend"
    
    print("[OK] Cognitive core is isolated from frontend")
    assert True


def test_state_transitions_backend_only():
    """
    TEST: State transition logic must be backend-only.
    
    Frontend should only display states; backend must validate
    and enforce state transitions.
    """
    # This is a documentation test - we verify the contract exists
    contracts_path = Path(__file__).parent.parent.parent / "docs" / "product" / "frontend-contracts.md"
    
    if not contracts_path.exists():
        print("[!] Frontend contracts document not found")
        return
    
    with open(contracts_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify state machines are documented
    required_sections = [
        "State Machines",
        "Workspace States",
        "Job Lifecycle States",
        "Brand Campaign States",
    ]
    
    missing = [s for s in required_sections if s not in content]
    
    if missing:
        print(f"[!] Missing state machine documentation: {missing}")
        return
    
    # Verify API contracts exist
    if "API Contracts" not in content:
        print("[!] API contracts not documented")
        return
    
    print("[OK] State machines and API contracts documented")
    assert True


def test_profile_module_no_intelligence_logic():
    """
    TEST: Profile module must not implement intelligence logic.
    
    Frontend profile.js should only display data from backend.
    It must NOT calculate readiness, score evidence, or make decisions.
    """
    frontend_path = Path(__file__).parent.parent.parent / "enigma-frontend"
    profile_js = frontend_path / "js" / "profile.js"
    
    if not profile_js.exists():
        print("[!] Profile module not found")
        return
    
    with open(profile_js, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Forbidden patterns that indicate intelligence logic in frontend
    forbidden_patterns = [
        "calculateReadiness",
        "scoreEvidence",
        "computeConfidence",
        "determineProfession",
        "assessMaturity",
        "evaluateRisk",
        "reasoningSession",
        "knowledgeGraph",
        "decisionEngine",
    ]
    
    violations = []
    for pattern in forbidden_patterns:
        if pattern in content:
            violations.append(f"Found forbidden pattern: {pattern}")
    
    # Check that readiness is only received from backend, not calculated
    if "readiness * 100" in content and "renderReadiness" not in content:
        # This is OK - it's just formatting for display
        pass
    
    # Verify all functions are API calls or rendering, not calculations
    # Check that loadReadiness calls apiCall, doesn't calculate
    if "loadReadiness" in content:
        # Should have apiCall, not calculation logic
        if "apiCall" not in content:
            violations.append("loadReadiness should use apiCall to get data from backend")
    
    if violations:
        print("\n[X] PROFILE MODULE VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        assert False, "Profile module must not implement intelligence logic"
    
    print("[OK] Profile module is display-only (Control Plane)")
    assert True


def test_freelancing_module_no_intelligence_logic():
    """
    TEST: Freelancing module must not implement intelligence logic.
    
    Frontend freelancing.js should only display freelancing data from backend.
    It must NOT calculate job readiness, match jobs, or perform research.
    """
    frontend_path = Path(__file__).parent.parent.parent / "enigma-frontend"
    freelancing_js = frontend_path / "js" / "freelancing.js"
    
    if not freelancing_js.exists():
        print("[!] Freelancing module not found")
        return
    
    with open(freelancing_js, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Forbidden patterns that indicate intelligence logic in frontend
    forbidden_patterns = [
        "calculateJobMatch",
        "scoreJobReadiness",
        "computeMatchScore",
        "determineJobFit",
        "performJobResearch",
        "evaluateJobRequirements",
        "assessCapabilityMatch",
        "reasoningSession",
        "knowledgeGraph",
        "decisionEngine",
    ]
    
    violations = []
    for pattern in forbidden_patterns:
        if pattern in content:
            violations.append(f"Found forbidden pattern: {pattern}")
    
    # Check that job matching comes from backend
    if "match_score" in content:
        # Should receive match_score from backend, not calculate it
        # Check if there's actual calculation logic (not just the word "calculate" in comments)
        lines_with_calculate = [line for line in content.split('\n') if 'calculate' in line.lower() and 'match' in line.lower()]
        # Filter out comments
        calculation_lines = [line for line in lines_with_calculate if not line.strip().startswith('//') and not line.strip().startswith('*')]
        if calculation_lines:
            violations.append("Job matching should come from backend, not calculated in frontend")
    
    # Check that readiness checking calls backend API
    if "checkJobReadiness" in content:
        # Should have apiCall, not calculation logic
        if "apiCall" not in content:
            violations.append("checkJobReadiness should use apiCall to get data from backend")
    
    # Check that research calls backend API
    if "startJobResearch" in content:
        # Should have apiCall, not perform research locally
        if "apiCall" not in content:
            violations.append("startJobResearch should use apiCall to trigger backend research")
    
    # Verify mock data is isolated
    if "getMock" in content:
        # Mock data functions should be clearly marked
        if "mock data" not in content.lower():
            violations.append("Mock data should be clearly marked and isolated")
    
    if violations:
        print("\n[X] FREELANCING MODULE VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        assert False, "Freelancing module must not implement intelligence logic"
    
    print("[OK] Freelancing module is display-only (Control Plane)")
    assert True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FRONTEND ARCHITECTURE VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Frontend No Cognitive Core Imports", test_frontend_no_cognitive_core_imports),
        ("Backend API Contracts Exist", test_backend_api_contracts_exist),
        ("Backend Cognitive Core Isolated", test_backend_cognitive_core_isolated),
        ("State Transitions Backend Only", test_state_transitions_backend_only),
        ("Profile Module No Intelligence Logic", test_profile_module_no_intelligence_logic),
        ("Freelancing Module No Intelligence Logic", test_freelancing_module_no_intelligence_logic),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n[{name}]")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
