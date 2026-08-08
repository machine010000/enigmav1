from app.profession import ProfessionRegistry
from app.profession.reference_professions import create_marketing_social_selling_pack


def test_profession_registry_register_and_get():
    """Registry should register and retrieve profession packs."""
    registry = ProfessionRegistry()
    pack = create_marketing_social_selling_pack()

    registry.register(pack)

    retrieved = registry.get(pack.profession.id)
    assert retrieved is not None
    assert retrieved.profession.id == pack.profession.id
    assert retrieved.profession.name == pack.profession.name


def test_profession_registry_find_by_name():
    """Registry should find profession pack by name."""
    registry = ProfessionRegistry()
    pack = create_marketing_social_selling_pack()

    registry.register(pack)

    retrieved = registry.find_by_name("Marketing & Social Selling")
    assert retrieved is not None
    assert retrieved.profession.name == "Marketing & Social Selling"


def test_profession_registry_list_all():
    """Registry should list all registered professions."""
    registry = ProfessionRegistry()
    pack = create_marketing_social_selling_pack()

    registry.register(pack)

    all_professions = registry.list_all()
    assert len(all_professions) == 1
    assert all_professions[0].id == pack.profession.id


def test_profession_registry_list_active():
    """Registry should list only active professions."""
    registry = ProfessionRegistry()
    pack = create_marketing_social_selling_pack()

    registry.register(pack)

    active_professions = registry.list_active()
    assert len(active_professions) == 1
    assert active_professions[0].status == "active"


def test_profession_registry_get_nonexistent():
    """Registry should return None for nonexistent profession."""
    registry = ProfessionRegistry()

    retrieved = registry.get("nonexistent")
    assert retrieved is None


def test_profession_registry_overwrite():
    """Registry should allow overwriting existing profession."""
    registry = ProfessionRegistry()
    pack1 = create_marketing_social_selling_pack()
    pack2 = create_marketing_social_selling_pack()

    registry.register(pack1)
    registry.register(pack2)

    # Should have the last registered pack
    retrieved = registry.get(pack1.profession.id)
    assert retrieved is not None
