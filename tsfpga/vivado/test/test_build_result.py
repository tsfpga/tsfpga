# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.vivado.build_result import BuildResult


def test_size_summary():
    build_result = BuildResult(name="apa")

    build_result.synthesis_size = dict(LUT=3, FFs=4)
    expected = """\
Size of apa after synthesis:
{
  "LUT": 3,
  "FFs": 4
}"""
    assert build_result.size_summary() == expected

    build_result.implementation_size = dict(LUT=8, FFs=9)
    expected = """\
Size of apa after implementation:
{
  "LUT": 8,
  "FFs": 9
}"""
    assert build_result.size_summary() == expected


def test_report():
    build_result = BuildResult(name="apa")

    build_result.synthesis_size = dict(LUT=3, FFs=4)
    expected = """\
Size of apa after synthesis:
{
  "LUT": 3,
  "FFs": 4
}"""
    assert build_result.report() == expected

    # Add a logic level distribution report
    build_result.logic_level_distribution = """\
+-----------------+-------------+-----+----+---+----+
| End Point Clock | Requirement |  0  |  1 | 2 |  3 |
+-----------------+-------------+-----+----+---+----+
| clk_fpga_0      | 2.000ns     | 491 | 12 | 1 | 11 |
+-----------------+-------------+-----+----+---+----+\
"""
    expected = """\
Size of apa after synthesis:
{
  "LUT": 3,
  "FFs": 4
}
Logic level distribution:
+-----------------+-------------+-----+----+---+----+
| End Point Clock | Requirement |  0  |  1 | 2 |  3 |
+-----------------+-------------+-----+----+---+----+
| clk_fpga_0      | 2.000ns     | 491 | 12 | 1 | 11 |
+-----------------+-------------+-----+----+---+----+\
"""
    assert build_result.report() == expected
    assert build_result.maximum_logic_level == 3


def test_maximum_logic_level_should_be_none_if_no_logic_level_distribution_is_set():
    build_result = BuildResult(name="apa")
    build_result.synthesis_size = dict(LUT=3, FFs=4)

    # maximum_logic_level is calculated based on the logic_level_distribution, which is not set
    # in this test case
    assert build_result.logic_level_distribution is None
    assert build_result.maximum_logic_level is None
    assert "level" not in build_result.report()
