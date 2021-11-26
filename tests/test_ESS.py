import itertools
import logging
from pathlib import Path
import pandas as pd
import pytest
import pyscal
from pyscal import pyscalcli


def test_logger(capsys):
    """
    Test the getLogger_pyscal from init.py.
    Check for correct logger setup and splitting logs.
    """
    logger = pyscal.getLogger_pyscal("testESS1", {"verbose": True, "output": "-"})
    assert len(logger.handlers) == 1
    assert logger.level == logging.INFO
    
    logger.info("INFO-text")
    captured = capsys.readouterr()
    
    assert "INFO" not in captured.out
    assert "INFO" in captured.err
    
    logger = pyscal.getLogger_pyscal("testESS2", {"verbose": False, "output": "out.inc"})
    assert len(logger.handlers) == 2
    assert logger.level == logging.WARNING
    
    logger.info("INFO-text")
    captured = capsys.readouterr()
    assert "INFO" not in captured.out
    assert "INFO" not in captured.err
    
    logger.warning("WARNING-text")
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "WARNING" not in captured.err


def test_gaswater(capsys):
    """
    Test the GasWater object.
    First check for error, while no WaterOil and GasOil provided.
    Then check for expected output covering line 264.
    """
    gw = pyscal.GasWater()
    gw.wateroil = None
    assert gw.selfcheck()  == False
    
    gw = pyscal.GasWater()
    
    gw.wateroil = pyscal.WaterOil()
    gw.wateroil.table = pd.DataFrame()
    
    gw.gasoil = pyscal.GasOil()
    d = {"KRG":[0, 0.2], "SG":[0.1, 0.2]}
    gw.gasoil.table = pd.DataFrame(data = d, columns = ["SL", "KRG", "SG"])
    assert gw.SGFN() is not None


def test_wateroil(capsys):   
    """
    Test the WaterOil object.
    Check the object consistence, expected False because of the too big args.
    Check the expected estimate_socr() result.
    """
    wo = pyscal.WaterOil()
    d = {"KRO":[0.5, 0.2, 0.8], "SW":[5.0, 10.5, 200.4],}
    wo.table = pd.DataFrame(data = d, columns = ["KRO", "SW", "SG"])
    
    assert isinstance(wo, pyscal.WaterOil)
    assert wo.selfcheck() == False
    assert 189.9 == wo.estimate_socr()
    
    
def test_cli(capsys):
    """
    Test the main function using fake CLI client.
    """
    
    class CLI:
        def __init__(self, input_file, verbose, debug, output_file):
            self.input_file = input_file
            self.verbose = verbose
            self.debug = debug
            self.output_file = output_file
        
        def call_main(self):
            pyscalcli.pyscal_main(
                parametertable = self.input_file, 
                verbose = self.verbose, 
                debug = self.debug, 
                output = self.output_file,
                )
    

    testdir = Path(__file__).absolute().parent
    relperm_file = testdir / "data/relperm-input-example.xlsx"

    cli = CLI(
        input_file = relperm_file, 
        verbose = True, 
        debug = False, 
        output_file = "-",
        )
    cli.call_main()
    
    captured = capsys.readouterr()
    assert "SATNUM 1" in captured.out
    assert "SATNUM 2" in captured.out
    assert "SATNUM 3" in captured.out
    
def test_pyscal_logging(tmp_path, mocker, capsys):
    """
    Test that the command line client logs correctly.
    """

    testdir = Path(__file__).absolute().parent
    relperm_file = testdir / "data/relperm-input-example.xlsx"
    commands = ["pyscal", str(relperm_file), "--output", "-", "-v"]

    mocker.patch("sys.argv", commands)

    pyscalcli.main()
    captured = capsys.readouterr()
    stdout_output = captured.out
    stderr_output = captured.err

    assert "INFO:" not in stdout_output
    assert "WARNING:" not in stdout_output

    
def test_pyscallist(capsys):
    """
    Test the PyscalList object.
    """
    
    pl = pyscal.PyscalList()
    
    """WaterOilGas"""
    with pytest.raises(ValueError):
        pl.relevant_keywords(family = 5)
    pl.pyscaltype = pyscal.WaterOilGas
    assert pl.relevant_keywords(family = 2) == ["SWFN", "SGFN", "SOF3"]
    
    """GasOil"""
    pl.pyscaltype = pyscal.GasOil
    with pytest.raises(ValueError):
        pl.relevant_keywords(family = 2)
        
    """Build eclipse data"""
    with pytest.raises(ValueError):
        pl.build_eclipse_data(family = 5)
    
    
    
    