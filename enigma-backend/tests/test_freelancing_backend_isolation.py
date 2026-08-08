"""
Architecture Tests: Freelancing Backend Isolation

These tests ensure that the Freelancing layer does not bypass
the proper application layer and directly access Cognitive Core internals.

FORBIDDEN: Freelancing → MasterBrain, Planner, Workers, Database directly
ALLOWED: Freelancing → Application Layer → Cognitive Core
"""
import ast
import sys
from pathlib import Path
from typing import List, Set


class FreelancingBackendValidator:
    """Validates that freelancing backend does not import cognitive core internals directly."""

    # Cognitive core modules that freelancing must NOT import directly
    FORBIDDEN_DIRECT_IMPORTS = {
        "app.ai.master_brain",
        "app.ai.product_brain",
        "app.engine.planner",
        "app.engine.engine",
        "app.engine.registry",
        "app.workers.worker",
        "app.database",
    }

    # Allowed imports (application layer and domain models)
    ALLOWED_IMPORTS = {
        "app.work_market",  # Freelancing domain layer
        "app.profession",   # Profession integration
        "app.knowledge",    # Knowledge integration
        "app.knowledge_governance",  # Governance integration
        "app.intelligence", # Intelligence integration
    }

    def __init__(self, work_market_path: Path):
        self.work_market_path = work_market_path
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
        # Check if it's a forbidden direct import
        for forbidden in self.FORBIDDEN_DIRECT_IMPORTS:
            if module_name.startswith(forbidden):
                self.violations.append(
                    f"{file_path}: Forbidden direct import of cognitive core: {module_name}"
                )
                return

    def validate_directory(self) -> bool:
        """Validate all Python files in the work_market directory."""
        if not self.work_market_path.exists():
            print(f"Work market directory not found: {self.work_market_path}")
            return True  # Pass if directory doesn't exist yet

        for py_file in self.work_market_path.rglob("*.py"):
            self.check_file(py_file)

        return len(self.violations) == 0


def test_freelancing_no_direct_cognitive_core_imports():
    """
    TEST: Freelancing backend must not import cognitive core internals directly.
    
    This ensures the Freelancing layer uses the proper application layer
    and does not bypass the architecture.
    """
    backend_path = Path(__file__).parent.parent / "app"
    work_market_path = backend_path / "work_market"
    
    validator = FreelancingBackendValidator(work_market_path)
    is_valid = validator.validate_directory()
    
    if not is_valid:
        print("\n[X] FREELANCING BACKEND VIOLATIONS:")
        for violation in validator.violations:
            print(f"  - {violation}")
        print("\nFreelancing must use application layer only. Direct cognitive core access is forbidden.")
        assert False, "Freelancing backend architecture violations detected"
    
    print("[OK] Freelancing backend is properly isolated (uses application layer)")
    assert True


def test_freelancing_uses_integrators_not_direct_access():
    """
    TEST: Freelancing should use integrators, not direct cognitive core access.
    
    This ensures that freelancing uses the proper integrator pattern
    (ProfessionIntegrator, KnowledgeGovernanceIntegrator) instead of
    directly accessing cognitive core modules.
    """
    backend_path = Path(__file__).parent.parent / "app"
    work_market_path = backend_path / "work_market"
    
    # Check that integrator files exist
    profession_integrator = work_market_path / "profession_integrator.py"
    governance_integrator = work_market_path / "governance_integrator.py"
    
    if not profession_integrator.exists():
        print("[!] ProfessionIntegrator not found (may be added later)")
    else:
        print("[OK] ProfessionIntegrator exists")
    
    if not governance_integrator.exists():
        print("[!] KnowledgeGovernanceIntegrator not found (may be added later)")
    else:
        print("[OK] KnowledgeGovernanceIntegrator exists")
    
    # Check that main freelancing files use integrators
    main_files = [
        work_market_path / "evaluator.py",
        work_market_path / "learning_analyzer.py",
        work_market_path / "application_draft_generator.py",
    ]
    
    for file_path in main_files:
        if not file_path.exists():
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for forbidden direct cognitive core imports
        forbidden_patterns = [
            "from app.ai.master_brain",
            "from app.engine.planner",
            "from app.engine.engine import engine",
            "from app.workers",
        ]
        
        violations = []
        for pattern in forbidden_patterns:
            if pattern in content:
                violations.append(f"{file_path.name}: Contains forbidden import: {pattern}")
        
        if violations:
            print(f"\n[X] {file_path.name} uses direct cognitive core access:")
            for v in violations:
                print(f"  - {v}")
            assert False, f"{file_path.name} should use integrators, not direct access"
    
    print("[OK] Freelancing uses integrator pattern (no direct cognitive core access)")
    assert True


def test_freelancing_models_are_immutable():
    """
    TEST: Freelancing domain models should be immutable (frozen dataclasses).
    
    This ensures that domain models cannot be mutated accidentally,
    which is important for maintaining data integrity.
    """
    backend_path = Path(__file__).parent.parent / "app"
    models_file = backend_path / "work_market" / "models.py"
    
    if not models_file.exists():
        print("[!] Models file not found")
        return
    
    with open(models_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check that key models use @dataclass(frozen=True)
    key_models = [
        "FreelanceJob",
        "JobClassification",
        "JobEvaluation",
        "JobAssessment",
        "Application",
        "Platform",
    ]
    
    violations = []
    for model_name in key_models:
        if f"@dataclass(frozen=True)" in content and model_name in content:
            # Check if this specific model is frozen
            model_start = content.find(model_name)
            if model_start > 0:
                # Look for the decorator before this model
                preceding_content = content[:model_start]
                last_decorator = preceding_content.rfind("@dataclass")
                if last_decorator > 0:
                    decorator_line = preceding_content[last_decorator:last_decorator + 50]
                    if "frozen=True" not in decorator_line:
                        violations.append(f"{model_name} is not frozen (should be immutable)")
    
    if violations:
        print("\n[X] IMMUTABILITY VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        assert False, "Domain models should be immutable (frozen dataclasses)"
    
    print("[OK] Freelancing domain models are immutable (frozen dataclasses)")
    assert True


def test_freelancing_readiness_service_no_calculation_in_frontend():
    """
    TEST: Readiness calculation must be backend-only.
    
    This is a cross-cutting test to ensure that readiness calculation
    is not accidentally moved to the frontend.
    """
    frontend_path = Path(__file__).parent.parent.parent / "enigma-frontend"
    freelancing_js = frontend_path / "js" / "freelancing.js"
    
    if not freelancing_js.exists():
        print("[!] Freelancing frontend module not found")
        return
    
    with open(freelancing_js, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check that readiness calculation is not in frontend
    forbidden_patterns = [
        "calculateReadiness",
        "computeReadiness",
        "scoreReadiness",
        "assessReadiness",
    ]
    
    violations = []
    for pattern in forbidden_patterns:
        if pattern in content:
            violations.append(f"Found forbidden pattern: {pattern}")
    
    # Check that readiness comes from backend API
    if "checkJobReadiness" in content:
        if "apiCall" not in content:
            violations.append("checkJobReadiness should use apiCall to get data from backend")
    
    if violations:
        print("\n[X] FRONTEND READINESS CALCULATION VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
        assert False, "Readiness calculation must be backend-only"
    
    print("[OK] Readiness calculation is backend-only (frontend displays only)")
    assert True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FREELANCING BACKEND ISOLATION VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Freelancing No Direct Cognitive Core Imports", test_freelancing_no_direct_cognitive_core_imports),
        ("Freelancing Uses Integrators Not Direct Access", test_freelancing_uses_integrators_not_direct_access),
        ("Freelancing Models Are Immutable", test_freelancing_models_are_immutable),
        ("Freelancing Readiness Service No Calculation In Frontend", test_freelancing_readiness_service_no_calculation_in_frontend),
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
