# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import io
from unittest.mock import Mock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.vivado.build_result import BuildResult
from tsfpga.vivado.build_result_checker import (
    DspBlocks,
    EqualTo,
    GreaterThan,
    LessThan,
    MaximumLogicLevel,
    Ramb,
    Ramb36,
    TotalLuts,
)


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_less_than_pass(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    assert TotalLuts(LessThan(10)).check(build_result)
    assert mock_stdout.getvalue() == "Result check passed for Total LUTs: 5 (< 10)\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_less_than_fail(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    assert not TotalLuts(LessThan(5)).check(build_result)
    assert mock_stdout.getvalue() == "Result check failed for Total LUTs. Got 5, expected < 5.\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_greater_than_pass(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    assert TotalLuts(GreaterThan(2)).check(build_result)
    assert mock_stdout.getvalue() == "Result check passed for Total LUTs: 5 (> 2)\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_greater_than_fail(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    assert not TotalLuts(GreaterThan(5)).check(build_result)
    assert mock_stdout.getvalue() == "Result check failed for Total LUTs. Got 5, expected > 5.\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_equal_to_pass(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"RAMB36": 0, "Total LUTs": 5}

    assert Ramb36(EqualTo(0)).check(build_result)
    assert TotalLuts(EqualTo(5)).check(build_result)

    assert mock_stdout.getvalue() == (
        "Result check passed for RAMB36: 0 (0)\nResult check passed for Total LUTs: 5 (5)\n"
    )


@patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_equal_to_fail(mock_stdout):
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    assert not TotalLuts(EqualTo(50)).check(build_result)
    assert mock_stdout.getvalue() == "Result check failed for Total LUTs. Got 5, expected 50.\n"


def test_size_checker_dsp_blocks_has_two_names():
    build_result = BuildResult(name="")

    build_result.synthesis_size = {"DSP Blocks": 5}
    assert DspBlocks(EqualTo(5)).check(build_result)
    assert not DspBlocks(EqualTo(2)).check(build_result)

    build_result.synthesis_size = {"DSP48 Blocks": 7}
    assert DspBlocks(EqualTo(7)).check(build_result)
    assert not DspBlocks(EqualTo(2)).check(build_result)


def test_size_checker_aggregated_ramb():
    build_result = BuildResult(name="")

    build_result.synthesis_size = {"RAMB18": 5, "RAMB36": 20}
    assert Ramb(EqualTo(22.5)).check(build_result)
    assert not Ramb(EqualTo(22)).check(build_result)

    build_result.synthesis_size = {"RAMB18": 5, "RAMB36": 0}
    assert Ramb(EqualTo(2.5)).check(build_result)

    build_result.synthesis_size = {"RAMB18": 0, "RAMB36": 20}
    assert Ramb(EqualTo(20)).check(build_result)


def test_size_checker_raises_exception_if_synthesis_size_is_not_set():
    build_result = BuildResult(name="")
    build_result.synthesis_size = None

    with pytest.raises(ValueError) as exception_info:
        assert Ramb36(EqualTo(0)).check(build_result)
    assert str(exception_info.value) == "Should only call after successful synthesis"


def test_size_checker_raises_exception_if_synthesis_size_does_not_have_requested_resource():
    build_result = BuildResult(name="")
    build_result.synthesis_size = {"Total LUTs": 5}

    with pytest.raises(ValueError) as exception_info:
        assert Ramb36(EqualTo(0)).check(build_result)
    assert (
        str(exception_info.value)
        == 'Synthesis result size does not contain the requested resource: "RAMB36"'
    )


@patch("sys.stdout", new_callable=io.StringIO)
def test_logic_level_checker_equal_to_pass(mock_stdout):
    build_result = Mock(spec=BuildResult)
    build_result.maximum_logic_level = 5

    assert MaximumLogicLevel(EqualTo(5)).check(build_result)
    assert mock_stdout.getvalue() == "Result check passed for maximum logic level: 5 (5)\n"


@patch("sys.stdout", new_callable=io.StringIO)
def test_logic_level_checker_less_than_fail(mock_stdout):
    build_result = Mock(spec=BuildResult)
    build_result.maximum_logic_level = 11
    assert not MaximumLogicLevel(LessThan(7)).check(build_result)
    assert (
        mock_stdout.getvalue()
        == "Result check failed for maximum logic level. Got 11, expected < 7.\n"
    )


def test_logic_level_checker_raises_exception_if_logic_level_is_not_set():
    build_result = BuildResult(name="")

    with pytest.raises(ValueError) as exception_info:
        MaximumLogicLevel(LessThan(7)).check(build_result)
    assert str(exception_info.value) == "Should only call after successful synthesis"
