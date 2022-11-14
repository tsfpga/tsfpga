# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Common functions and definitions in the example build environment.
"""

# Import before others since it modifies PYTHONPATH. pylint: disable=unused-import
import tsfpga.examples.example_pythonpath  # noqa: F401

# Third party libraries
from hdl_registers.register_list import Register

# First party libraries
import tsfpga
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


def get_hdl_modules(names_include=None, names_avoid=None):
    """
    Wrapper of :func:`.get_modules` which returns the ``hdl_modules`` module objects.

    If ``hdl_modules`` can not be found in the default repo checkout location,
    the function will assert False.

    Arguments will be passed on to :func:`.get_modules`.

    Return:
        :class:`.ModuleList`: The module objects.
    """
    # Presumed location of the hdl_modules repo
    hdl_modules_repo_root = tsfpga.REPO_ROOT.parent.parent.resolve() / "hdl_modules" / "hdl_modules"
    if (hdl_modules_repo_root / "modules").exists():
        return get_modules(
            modules_folders=[hdl_modules_repo_root / "modules"],
            names_include=names_include,
            names_avoid=names_avoid,
            library_name_has_lib_suffix=False,
        )

    raise FileNotFoundError(
        f"The hdl_modules modules could not be found. Searched in {hdl_modules_repo_root}"
    )
