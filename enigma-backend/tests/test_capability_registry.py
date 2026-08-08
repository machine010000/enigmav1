import pytest
from app.engine.capabilities import Capability, capability_registry

@pytest.fixture(autouse=True)
def clear_registry():
    capability_registry._capabilities.clear()
    capability_registry._worker_capabilities.clear()
    yield
    capability_registry._capabilities.clear()
    capability_registry._worker_capabilities.clear()



def test_register_capability():
    cap = Capability(id="category_detection", description="Detect product category", category="product_intelligence")
    capability_registry.register(cap, "product_verification")
    retrieved = capability_registry.get_capability("category_detection")
    assert retrieved is not None
    assert retrieved.id == "category_detection"

def test_register_worker_capabilities():
    capability_registry.register_worker_capabilities("product_verification", ["category_detection", "attribute_extraction", "title_validation"])
    caps = capability_registry.get_worker_capabilities("product_verification")
    assert "category_detection" in caps
    assert "attribute_extraction" in caps
    assert "title_validation" in caps

def test_find_worker_for_capability():
    capability_registry.register_worker_capabilities("product_verification", ["category_detection", "attribute_extraction"])
    worker = capability_registry.find_worker_for_capability("category_detection")
    assert worker == "product_verification"

def test_find_worker_for_unknown_capability():
    worker = capability_registry.find_worker_for_capability("nonexistent")
    assert worker is None

def test_list_capabilities():
    cap1 = Capability(id="cap_a", description="Capability A")
    cap2 = Capability(id="cap_b", description="Capability B")
    capability_registry.register(cap1, "worker_a")
    capability_registry.register(cap2, "worker_a")
    caps = capability_registry.list_capabilities()
    assert len(caps) == 2

def test_capability_to_dict():
    cap = Capability(id="test_cap", description="Test capability", category="test", parameters={"threshold": 0.5})
    d = cap.to_dict()
    assert d["id"] == "test_cap"
    assert d["description"] == "Test capability"
    assert d["category"] == "test"
    assert d["parameters"] == {"threshold": 0.5}

def test_to_dict_includes_workers():
    capability_registry.register_worker_capabilities("product_verification", ["category_detection"])
    d = capability_registry.to_dict()
    assert "workers" in d
    assert "product_verification" in d["workers"]
