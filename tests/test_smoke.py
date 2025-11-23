def test_import_version():
    import evidec

    assert evidec.__version__ == "0.1.0"


def test_example_script_runs_and_returns_report():
    import importlib

    example = importlib.import_module("examples.basic_ab")
    report = example.main()

    assert hasattr(report, "markdown")
    assert "エビデンスレポート" in report.markdown
