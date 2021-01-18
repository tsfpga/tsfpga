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

import tsfpga
from tsfpga.module import get_modules

from tsfpga.registers.register_list import Register


TSFPGA_EXAMPLES_TEMP_DIR = tsfpga.TSFPGA_GENERATED


def get_tsfpga_modules(modules_folders=None, names_include=None, names_avoid=None):
    """
    Wrapper of the regular get_modules call with correct settings for tsfpga modules.
    """
    modules_folders = (
        tsfpga.ALL_TSFPGA_MODULES_FOLDERS if modules_folders is None else modules_folders
    )
    return get_modules(
        modules_folders,
        names_include=names_include,
        names_avoid=names_avoid,
        library_name_has_lib_suffix=False,
        default_registers=get_default_registers(),
    )


def get_default_registers():
    """
    tsfpga default registers
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
