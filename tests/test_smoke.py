def test_バージョンが読み込める():
    # Arrange & Act
    import evidec

    # Assert
    assert evidec.__version__ == "0.1.0"


def test_サンプルスクリプトが実行されレポートを返す():
    # Arrange
    import importlib

    # Act
    example = importlib.import_module("examples.basic_ab")
    report = example.main()

    # Assert
    assert hasattr(report, "markdown")
    assert "エビデンスレポート" in report.markdown
