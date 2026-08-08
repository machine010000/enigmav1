import sys


def test_no_legacy_import_names_present():
    # There must be no modules or attributes referencing legacy master brain
    for mod in list(sys.modules.values()):
        name = getattr(mod, "__name__", None)
        if name:
            assert "legacy_master_brain" not in name
