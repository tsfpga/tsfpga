# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.vivado.hierarchical_utilization_parser import HierarchicalUtilizationParser


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

    result = HierarchicalUtilizationParser.get_size(report)
    assert result["a"] == 1
    assert result["b"] == 2
    assert result["c"] == 3
    assert result["d"] == 4
    assert len(result) == 4
