# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import io
from unittest.mock import MagicMock, patch

# First party libraries
from tsfpga.vivado.build_result import BuildResult as build_result_spec
from tsfpga.vivado.build_result_checker import (
    DspBlocks,
    EqualTo,
    LessThan,
    MaximumLogicLevel,
    TotalLuts,
)


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_less_than_pass(mock_stdout):
    build_result = MagicMock(spec=build_result_spec)
    build_result.synthesis_size = {"Total LUTs": 5}
    assert TotalLuts(LessThan(10)).check(build_result)
    assert mock_stdout.getvalue() == "Result check passed for Total LUTs: 5 (< 10)\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_equal_to_fail(mock_stdout):
    build_result = MagicMock(spec=build_result_spec)
    build_result.synthesis_size = {"Total LUTs": 5}
    assert not TotalLuts(EqualTo(50)).check(build_result)
    assert mock_stdout.getvalue() == "Result check failed for Total LUTs. Got 5, expected 50.\n"


def test_size_checker_dsp_blocks_has_two_names():
    build_result = MagicMock(spec=build_result_spec)

    build_result.synthesis_size = {"DSP Blocks": 5}

    assert DspBlocks(EqualTo(5)).check(build_result)
    assert not DspBlocks(EqualTo(2)).check(build_result)

    build_result.synthesis_size = {"DSP48 Blocks": 7}

    assert DspBlocks(EqualTo(7)).check(build_result)
    assert not DspBlocks(EqualTo(2)).check(build_result)


@patch("sys.stdout", new_callable=io.StringIO)
def test_logic_level_checker_equal_to_pass(mock_stdout):
    build_result = MagicMock(spec=build_result_spec)
    build_result.maximum_logic_level = 5
    assert MaximumLogicLevel(EqualTo(5)).check(build_result)
    assert mock_stdout.getvalue() == "Result check passed for maximum logic level: 5 (5)\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_logic_level_checker_less_than_fail(mock_stdout):
    build_result = MagicMock(spec=build_result_spec)
    build_result.maximum_logic_level = 11
    assert not MaximumLogicLevel(LessThan(7)).check(build_result)
    assert (
        mock_stdout.getvalue()
        == "Result check failed for maximum logic level. Got 11, expected < 7.\n"
    )
