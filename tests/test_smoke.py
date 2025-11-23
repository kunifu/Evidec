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


def test_非劣性サンプルも実行できる():
    # Arrange
    import importlib

    # Act
    example = importlib.import_module("examples.non_inferiority")
    report = example.main()

    # Assert
    assert hasattr(report, "markdown")
    # "非劣性クリア" (reason) または "許容悪化幅" (decision rule) のいずれかが含まれる
    assert "非劣性" in report.markdown or "許容悪化幅" in report.markdown
