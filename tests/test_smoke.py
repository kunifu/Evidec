import pytest


def test_import_version():
    import evidec

    assert evidec.__version__ == "0.1.0"


def test_example_script_stub():
    import importlib

    example = importlib.import_module("examples.basic_ab")
    with pytest.raises(NotImplementedError):
        example.main()
