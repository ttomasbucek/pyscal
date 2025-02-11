"""Test the pyscal client"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from pyscal import pyscalcli
from pyscal.utils.testing import sat_table_str_ok


@pytest.mark.integration
def test_installed():
    """Test that the command line client is installed in PATH and
    starts up nicely"""
    assert subprocess.check_output(["pyscal", "-h"])
    assert subprocess.check_output(["pyscal", "--help"])

    assert subprocess.check_output(["pyscal", "--version"])


@pytest.mark.skipif(sys.version_info < (3, 7), reason="Requires Python 3.7 or higher")
@pytest.mark.parametrize("verbosity_flag", [None, "--verbose", "--debug"])
def test_log_levels(tmp_path, verbosity_flag):
    """Test that we can control the log level from the command line
    client, and get log output from modules deep down"""

    relperm_file = str(
        Path(__file__).absolute().parent / "data" / "relperm-input-example.xlsx"
    )

    commands = ["pyscal", relperm_file]
    if verbosity_flag is not None:
        commands.append(verbosity_flag)

    result = subprocess.run(commands, cwd=tmp_path, capture_output=True, check=True)
    output = result.stdout.decode() + result.stderr.decode()

    if verbosity_flag is None:
        assert "INFO:" not in output
        assert "DEBUG:" not in output
    elif verbosity_flag == "--verbose":
        assert "INFO:" in output
        assert "DEBUG:" not in output
        assert "Loaded input data" in output
        assert "Keywords SWOF, SGOF (family 1) for 3 SATNUMs generated" in output
    elif verbosity_flag == "--debug":
        assert "INFO:" in output
        assert "DEBUG:" in output
        assert "Initialized GasOil with" in output
        assert "Initialized WaterOil with" in output
    else:
        raise ValueError("Unknown value for 'verbosity_flag'")


def test_pyscal_client_static(tmp_path, caplog, default_loglevel, mocker):
    # pylint: disable=unused-argument
    # default_loglevel fixture is in conftest.py
    """Test pyscal client for static relperm input"""
    testdir = Path(__file__).absolute().parent
    relperm_file = testdir / "data/relperm-input-example.xlsx"

    os.chdir(tmp_path)

    caplog.clear()
    mocker.patch("sys.argv", ["pyscal", str(relperm_file)])
    pyscalcli.main()
    assert Path("relperm.inc").is_file()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    assert not any(record.levelno == logging.INFO for record in caplog.records)

    # We get one warning due to empty cells in xlsx:
    assert sum(record.levelno == logging.WARNING for record in caplog.records) == 1

    relpermlines = "\n".join(open("relperm.inc").readlines())
    assert "SWOF" in relpermlines
    assert "SGOF" in relpermlines
    assert "SLGOF" not in relpermlines
    assert "SOF3" not in relpermlines
    sat_table_str_ok(relpermlines)

    caplog.clear()
    mocker.patch(
        "sys.argv", ["pyscal", str(relperm_file), "--output", "alt2relperm.inc"]
    )
    pyscalcli.main()
    assert Path("alt2relperm.inc").is_file()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    caplog.clear()
    mocker.patch("sys.argv", ["pyscal", str(relperm_file), "-o", "altrelperm.inc"])
    pyscalcli.main()
    assert Path("altrelperm.inc").is_file()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    caplog.clear()
    mocker.patch(
        "sys.argv", ["pyscal", str(relperm_file), "--family2", "-o", "relperm-fam2.inc"]
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    assert Path("relperm-fam2.inc").is_file()
    relpermlines = "\n".join(open("relperm-fam2.inc").readlines())
    assert "SWFN" in relpermlines
    assert "SGFN" in relpermlines
    assert "SOF3" in relpermlines
    assert "SWOF" not in relpermlines
    assert "SGOF" not in relpermlines
    sat_table_str_ok(relpermlines)

    caplog.clear()
    mocker.patch(
        "sys.argv",
        ["pyscal", str(relperm_file), "--slgof", "--output", "relperm-slgof.inc"],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    assert Path("relperm-slgof.inc").is_file()
    relpermlines = "\n".join(open("relperm-slgof.inc").readlines())
    assert "SWOF" in relpermlines
    assert "SGOF" not in relpermlines
    assert "SLGOF" in relpermlines
    assert "SOF3" not in relpermlines
    sat_table_str_ok(relpermlines)

    caplog.clear()
    # Dump to deep directory structure that does not exists
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(relperm_file),
            "--family2",
            "-o",
            "eclipse/include/props/relperm-fam2.inc",
        ],
    )
    pyscalcli.main()
    assert Path("eclipse/include/props/relperm-fam2.inc").is_file()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    caplog.clear()
    mocker.patch(
        "sys.argv", ["pyscal", str(relperm_file), "-o", "include/props/relperm.inc"]
    )
    pyscalcli.main()
    assert Path("include/props/relperm.inc").is_file()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    caplog.clear()
    # Check that we can read specific sheets
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(relperm_file),
            "--sheet_name",
            "relperm",
            "--output",
            "relperm-firstsheet.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    # Identical files:
    assert len(open("relperm-firstsheet.inc").readlines()) == len(
        open("relperm.inc").readlines()
    )

    # Check that we can read specific sheets
    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(relperm_file),
            "--sheet_name",
            "simple",
            "--output",
            "relperm-secondsheet.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    secondsheet = "\n".join(open("relperm-secondsheet.inc").readlines())
    assert "SATNUM 3" not in secondsheet
    assert "sand" in secondsheet
    assert "mud" in secondsheet  # From the comment column in sheet: simple

    # Check that we can read specific sheets
    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(relperm_file),
            "--sheet_name",
            u"NOTEXISTINGÆÅ",
            "--output",
            "relperm-empty.inc",
        ],
    )
    with pytest.raises(SystemExit):
        pyscalcli.main()
    assert not Path("relperm-empty.inc").is_file()

    caplog.clear()
    mocker.patch(
        "sys.argv",
        ["pyscal", str(relperm_file), "--delta_s", "0.1", "-o", "deltas0p1.inc"],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    linecount1 = len(open("deltas0p1.inc").readlines())

    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(relperm_file),
            "--delta_s",
            "0.01",
            "-o",
            "deltas0p01.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    linecount2 = len(open("deltas0p01.inc").readlines())
    assert linecount2 > linecount1 * 4  # since we don't filter out non-numerical lines


def test_pyscalcli_exception_catching(capsys, mocker):
    """The command line client catches selected exceptions.

    Traceback is always included."""
    mocker.patch("sys.argv", ["pyscal", "notexisting.xlsx"])
    with pytest.raises(SystemExit, match="File not found"):
        pyscalcli.main()
    outerr = capsys.readouterr().out + capsys.readouterr().err
    assert "raise" in outerr  # This is the traceback.


def test_pyscalcli_oilwater(tmp_path, caplog, mocker):
    """Test the command line client in two-phase oil-water"""
    os.chdir(tmp_path)
    relperm_file = "oilwater.csv"
    pd.DataFrame(
        columns=["SATNUM", "nw", "now", "tag"], data=[[1, 2, 3, "fooå"]]
    ).to_csv(relperm_file, index=False)
    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            relperm_file,
            "--output",
            "ow.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    lines = open("ow.inc").readlines()
    joined = "\n".join(lines)
    assert "fooå" in joined
    assert 100 < len(lines) < 120  # weak test..

    # Test with SCAL recommendation:
    pd.DataFrame(
        columns=["SATNUM", "case", "nw", "now", "tag"],
        data=[
            [1, "low", 2, 3, "fooå"],
            [1, "base", 2, 3, "fooå"],
            [1, "high", 2, 3, "fooå"],
        ],
    ).to_csv(relperm_file, index=False)
    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            relperm_file,
            "--int_param_wo",
            "-0.1",
            "--output",
            "ow-int.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)


def test_pyscalcli_gaswater(tmp_path, caplog, mocker):
    """Test the command line endpoint on gas-water problems"""
    os.chdir(tmp_path)
    relperm_file = "gaswater.csv"
    pd.DataFrame(columns=["SATNUM", "nw", "ng"], data=[[1, 2, 3]]).to_csv(
        relperm_file, index=False
    )
    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            relperm_file,
            "--output",
            "gw.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    lines = open("gw.inc").readlines()
    joined = "\n".join(lines)
    assert "SWFN" in joined
    assert "SGFN" in joined
    assert "SWOF" not in joined
    assert "sgrw" in joined
    assert "krgendanchor" not in joined
    assert "sorw" not in joined
    assert "sorg" not in joined
    assert len(lines) > 40


def test_pyscalcli_gaswater_scal(tmp_path, caplog, mocker):
    """Test the command line endpoint on gas-water problems, with
    interpolation"""
    os.chdir(tmp_path)
    relperm_file = "gaswater.csv"
    pd.DataFrame(
        columns=["SATNUM", "CASE", "nw", "ng"],
        data=[[1, "pess", 2, 3], [1, "base", 3, 4], [1, "opt", 5, 6]],
    ).to_csv(relperm_file, index=False)

    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            relperm_file,
            "--int_param_wo",
            "-0.2",
            "--output",
            "gw.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.INFO for record in caplog.records)
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    lines = open("gw.inc").readlines()
    joined = "\n".join(lines)
    assert "SWFN" in joined
    assert "SGFN" in joined
    assert "SWOF" not in joined
    assert "sgrw" in joined
    assert "krgendanchor" not in joined
    assert "sorw" not in joined
    assert "sorg" not in joined
    assert len(lines) > 40


def test_pyscal_client_scal(tmp_path, caplog, default_loglevel, mocker):
    # pylint: disable=unused-argument
    # default_loglevel fixture is in conftest.py
    """Test the command line endpoint on SCAL recommendation"""
    scalrec_file = Path(__file__).absolute().parent / "data/scal-pc-input-example.xlsx"

    os.chdir(tmp_path)

    mocker.patch("sys.argv", ["pyscal", str(scalrec_file)])
    with pytest.raises(SystemExit):
        pyscalcli.main()

    caplog.clear()
    mocker.patch(
        "sys.argv",
        ["pyscal", str(scalrec_file), "--int_param_wo", 0, "-o", "relperm1.inc"],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.INFO for record in caplog.records)
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)

    relpermlines = "\n".join(open("relperm1.inc").readlines())
    assert "SWOF" in relpermlines
    assert "SGOF" in relpermlines
    assert "SLGOF" not in relpermlines
    assert "SOF3" not in relpermlines
    sat_table_str_ok(relpermlines)
    # assert "int_param_wo: 0\n" in relpermlines  # this should be in the tag.

    caplog.clear()
    mocker.patch(
        "sys.argv",
        [
            "pyscal",
            str(scalrec_file),
            "--int_param_wo",
            "-0.5",
            "-o",
            "relperm2.inc",
        ],
    )
    pyscalcli.main()
    assert not any(record.levelno == logging.INFO for record in caplog.records)
    assert not any(record.levelno == logging.WARNING for record in caplog.records)
    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    # assert something about -0.5 in the comments

    # Multiple interpolation parameters, this was supported in pyscal <= 0.7.7,
    # but is now an error:
    mocker.patch(
        "sys.argv", ["pyscal", str(scalrec_file), "--int_param_wo", "-0.5", "0"]
    )
    with pytest.raises(SystemExit):
        pyscalcli.main()
