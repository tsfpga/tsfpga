# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

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
