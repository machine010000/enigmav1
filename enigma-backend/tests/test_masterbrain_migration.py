import sys
import warnings

from app.ai.master_brain import MasterBrain, master_brain


def test_master_brain_v2_is_active_implementation():
    brain = MasterBrain()
    assert brain.__class__.__module__ == "app.ai.master_brain.orchestrator"


def test_no_runtime_legacy_imports():
    # Ensure legacy module name is not present anywhere
    assert all("legacy_master_brain" not in (m.__name__ if hasattr(m, "__name__") else str(m)) for m in list(sys.modules.values()))
