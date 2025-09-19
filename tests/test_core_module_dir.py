import importlib


def test_core_dir_includes_module_metadata() -> None:
    core = importlib.import_module("plantguard.core")
    names = dir(core)

    assert "__name__" in names
    assert "__doc__" in names
    assert "AudioAdapter" in names
    assert "VisionAdapter" in names
    assert "TextAdapter" in names
