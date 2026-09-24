# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.yosys.utilization_parser import (
    YosysIntelUtilizationParser,
    YosysMicrochipUtilizationParser,
    YosysUtilizationParser,
    YosysXilinxUtilizationParser,
)

# A cut-down version of a real report produced by the Yosys "stat" command.
REPORT = """
=== smoke_top ===

        +----------Local Count, excluding submodules.
        |
       14 wires
       35 wire bits
        4 public wires
       25 public wire bits
        3 ports
       17 port bits
       26 cells
        1   BUFG
        8   FDRE
        9   IBUF
        8   OBUF

End of script. Logfile hash: 304ba4a04e, time: 1.05s
"""


def test_get_size():
    result = YosysUtilizationParser.get_size(report=REPORT)

    assert result["BUFG"] == 1
    assert result["FDRE"] == 8
    assert result["IBUF"] == 9
    assert result["OBUF"] == 8


def test_get_size_does_not_aggregate_by_default():
    report = """
       10 cells
        3   LUT2
        2   LUT4
        1   LUT6
        4   FDRE
"""
    result = YosysUtilizationParser.get_size(report=report)

    assert "Total LUTs" not in result
    assert "FFs" not in result
    assert result["LUT2"] == 3
    assert result["FDRE"] == 4


def test_get_size_aggregates_lut_count():
    report = """
       10 cells
        3   LUT2
        2   LUT4
        1   LUT6
        4   FDRE
"""
    result = YosysXilinxUtilizationParser.get_size(report=report)

    assert result["Total LUTs"] == 6
    assert result["FFs"] == 4


def test_get_size_aggregates_ramb_and_dsp_counts():
    report = """
        4 cells
        1   RAMB18E2
        1   RAMB36E2
        2   DSP48E2
"""
    result = YosysXilinxUtilizationParser.get_size(report=report)

    assert result["RAMB18"] == 1
    assert result["RAMB36"] == 1
    assert result["Block RAMs"] == 2
    assert result["DSP Blocks"] == 2
    assert result["RAMB18E2"] == 1
    assert result["RAMB36E2"] == 1
    assert result["DSP48E2"] == 2


def test_get_size_aggregates_intel_resource_counts():
    report = """
       19 cells
        1   $not
        8   dffeas
       10   fiftyfivenm_lcell_comb
        1   altsyncram
        1   fiftyfivenm_mac_mult
        1   fiftyfivenm_mac_out
"""
    result = YosysIntelUtilizationParser.get_size(report=report)

    assert result["Total LUTs"] == 10
    assert result["FFs"] == 8
    assert result["Block RAMs"] == 1
    # One mapped multiplier yields both a "_mac_mult" and a "_mac_out" cell, but is one DSP.
    assert result["DSP Blocks"] == 1


def test_get_size_aggregates_microchip_resource_counts():
    report = """
       10 cells
        1   CFG1
        2   CFG2
        2   CFG4
        8   SLE
        1   RAM1K20
        1   MACC_PA
"""
    result = YosysMicrochipUtilizationParser.get_size(report=report)

    assert result["Total LUTs"] == 5
    assert result["FFs"] == 8
    assert result["Block RAMs"] == 1
    assert result["DSP Blocks"] == 1


def test_get_size_ignores_scopeinfo_cells():
    report = """
        2 cells
        1   FDRE
        1   $scopeinfo
"""
    result = YosysUtilizationParser.get_size(report=report)

    assert "$scopeinfo" not in result
    assert result["FDRE"] == 1


def test_get_size_with_no_cells_present():
    report = """
        0 cells
"""
    result = YosysXilinxUtilizationParser.get_size(report=report)

    assert result["Total LUTs"] == 0
    assert result["FFs"] == 0
    assert result["RAMB36"] == 0
    assert result["RAMB18"] == 0
    assert result["Block RAMs"] == 0
    assert result["DSP Blocks"] == 0
    assert result["SRLs"] == 0


def test_get_size_with_duplicate_cell_names_are_summed():
    report = """
        2 cells
        1   FDRE
        1   FDRE
"""
    result = YosysUtilizationParser.get_size(report=report)

    assert result["FDRE"] == 2
