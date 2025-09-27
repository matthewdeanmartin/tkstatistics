def test_import():
    import tkstatistics

    assert tkstatistics
    import tkstatistics.cli

    assert tkstatistics.cli
    import tkstatistics.core.dataset

    assert tkstatistics.core.dataset
    import tkstatistics.core.io_csv

    assert tkstatistics.core.io_csv
    import tkstatistics.core.project

    assert tkstatistics.core.project
    import tkstatistics.core.specs

    assert tkstatistics.core.specs
