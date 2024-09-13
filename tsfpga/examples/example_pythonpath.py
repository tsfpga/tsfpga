# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Import this file in order to have the default locations of the hdl-registers/hdl-registers
and vunit/vunit repos added to PYTHONPATH.
"""

# Standard libraries
import sys

# First party libraries
import tsfpga

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install.

# Paths e.g.
# repo/tsfpga/tsfpga
# repo/hdl-registers/hdl-registers
PATH_TO_HDL_REGISTERS = tsfpga.REPO_ROOT.parent.parent.resolve() / "hdl-registers" / "hdl-registers"
sys.path.insert(0, str(PATH_TO_HDL_REGISTERS))

# Paths e.g.
# repo/tsfpga/tsfpga
# repo/vunit/vunit
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent.parent.resolve() / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))
