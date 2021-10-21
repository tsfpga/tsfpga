# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Common functions and definitions in the example build environment.
"""

import sys

import tsfpga

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_HDL_REGISTERS = tsfpga.REPO_ROOT.parent.resolve() / "hdl_registers"
sys.path.insert(0, str(PATH_TO_HDL_REGISTERS))
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent.parent.resolve() / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))

# pylint: disable=wrong-import-order
from hdl_registers.register_list import Register

from tsfpga.module import get_modules

TSFPGA_EXAMPLES_TEMP_DIR = tsfpga.TSFPGA_GENERATED


def get_default_registers():
    """
    Default registers for tsfpga examples.
    """
    registers = [
        Register("config", 0, "r_w", "Configuration register."),
        Register(
            "command",
            1,
            "wpulse",
            "When this register is written, all '1's in the written word will be asserted for one "
            "clock cycle in the FPGA logic.",
        ),
        Register("status", 2, "r", "Status register."),
        Register(
            "irq_status",
            3,
            "r_wpulse",
            "Reading a '1' in this register means the corresponding interrupt has triggered.\n"
            "Writing to this register will clear the interrupts where there is a '1' in the "
            "written word.",
        ),
        Register(
            "irq_mask",
            4,
            "r_w",
            "A '1' in this register means that the corresponding interrupt is enabled.",
        ),
    ]
    return registers


def get_tsfpga_example_modules(names_include=None, names_avoid=None):
    """
    Wrapper of the regular :func:`.get_modules`. call with correct settings for tsfpga
    example modules.
    This will include the example tsfpga modules, but not the "real" modules.

    Arguments will be passed on to :func:`.get_modules`.
    """
    return get_modules(
        modules_folders=[tsfpga.TSFPGA_EXAMPLE_MODULES],
        names_include=names_include,
        names_avoid=names_avoid,
        library_name_has_lib_suffix=False,
        default_registers=get_default_registers(),
    )
