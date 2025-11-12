def test_import():
    # pylint: disable=import-outside-toplevel
    import tkstatistics

    assert tkstatistics
    # pylint: disable=import-outside-toplevel
    import tkstatistics.cli

    assert tkstatistics.cli
    # pylint: disable=import-outside-toplevel
    import tkstatistics.core.dataset

    assert tkstatistics.core.dataset
    # pylint: disable=import-outside-toplevel
    import tkstatistics.core.io_csv

    assert tkstatistics.core.io_csv
    # pylint: disable=import-outside-toplevel
    import tkstatistics.core.project

    assert tkstatistics.core.project
    # pylint: disable=import-outside-toplevel
    import tkstatistics.core.specs

    assert tkstatistics.core.specs
