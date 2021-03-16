# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest import mock
import io

from tsfpga.vivado.size_checker import (
    UtilizationParser,
    EqualTo,
    DspBlocks,
    LessThan,
    TotalLuts,
)


def test_utilization_parser():
    report = """
Writing top or top) or (top here should not cause issues
Also writing pipes | | | | should be fine
Random sections of dashes should be fine:
---------------------------------------------------------------
-----------------------+----------------------------+----------
But this should hit:
| x | x | a | b | c | d |
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
| x | (top) | 1 | 2 | 3 | 4 |
"""

    result = UtilizationParser.get_size(report)
    assert result["a"] == 1
    assert result["b"] == 2
    assert result["c"] == 3
    assert result["d"] == 4
    assert len(result) == 4


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_less_than_pass(mock_stdout):
    result_size = {"Total LUTs": 5}
    assert TotalLuts(LessThan(10)).check(result_size)
    assert mock_stdout.getvalue() == "Result size check passed for Total LUTs: 5 (< 10)\n"


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_equal_to_fail(mock_stdout):
    result_size = {"Total LUTs": 5}
    assert not TotalLuts(EqualTo(50)).check(result_size)
    assert (
        mock_stdout.getvalue() == "Result size check failed for Total LUTs. Got 5, expected 50.\n"
    )


def test_size_checker_dsp_blocks_has_two_names():
    result_size = {"DSP48 Blocks": 5}

    assert DspBlocks(EqualTo(5)).check(result_size)
    assert DspBlocks(EqualTo(5)).check(result_size)
    assert not DspBlocks(EqualTo(2)).check(result_size)
    assert not DspBlocks(EqualTo(2)).check(result_size)

    result_size = {"DSP Blocks": 5}

    assert DspBlocks(EqualTo(5)).check(result_size)
    assert DspBlocks(EqualTo(5)).check(result_size)
    assert not DspBlocks(EqualTo(2)).check(result_size)
    assert not DspBlocks(EqualTo(2)).check(result_size)
