# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Import this file in order to have the default locations of the hdl_registers/hdl_registers
and vunit/vunit repos added to PYTHONPATH.
"""

# Standard libraries
import sys

# First party libraries
import tsfpga

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install

# Paths e.g.
# repo/tsfpga/tsfpga
# repo/hdl_registers/hdl_registers
PATH_TO_HDL_REGISTERS = tsfpga.REPO_ROOT.parent.parent.resolve() / "hdl_registers" / "hdl_registers"
sys.path.insert(0, str(PATH_TO_HDL_REGISTERS))

# Paths e.g.
# repo/tsfpga/tsfpga
# repo/vunit/vunit
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent.parent.resolve() / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))

# Alternative repo layout where tsfpga and hdl_registers are git submodules in a development repo,
# and VUnit is outside of this structure.
# Paths e.g.
# repo/path_a/path_b/external/tsfpga/tsfpga
# repo/vunit/vunit
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent.parent.parent.parent.parent.resolve() / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))
