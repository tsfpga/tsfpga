# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

"""
Common functions and definitions in the example build environment.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsfpga.module_list import ModuleList

# Import before others since it modifies PYTHONPATH.
import tsfpga.examples.example_pythonpath

from hdl_registers.register import Register
from hdl_registers.register_modes import REGISTER_MODES

import tsfpga
from tsfpga.module import get_modules

TSFPGA_EXAMPLES_TEMP_DIR = tsfpga.TSFPGA_GENERATED


def get_default_registers() -> list[Register]:
    """
    Default registers for tsfpga examples.
    """
    return [
        Register("conf", 0, REGISTER_MODES["r_w"], "Configuration register."),
        Register(
            "command",
            1,
            REGISTER_MODES["wpulse"],
            "When this register is written, all '1's in the written word will be asserted for one "
            "clock cycle in the FPGA logic.",
        ),
        Register("status", 2, REGISTER_MODES["r"], "Status register."),
        Register(
            "irq_status",
            3,
            REGISTER_MODES["r_wpulse"],
            "Reading a '1' in this register means the corresponding interrupt has triggered.\n"
            "Writing to this register will clear the interrupts where there is a '1' in the "
            "written word.",
        ),
        Register(
            "irq_mask",
            4,
            REGISTER_MODES["r_w"],
            "A '1' in this register means that the corresponding interrupt is enabled.",
        ),
    ]


def get_tsfpga_example_modules(
    names_include: set[str] | None = None, names_avoid: set[str] | None = None
) -> ModuleList:
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


def get_hdl_modules(
    names_include: set[str] | None = None, names_avoid: set[str] | None = None
) -> ModuleList:
    """
    Wrapper of :func:`.get_modules` which returns the ``hdl-modules`` module objects
    (https://hdl-modules.com), if available.

    If ``hdl-modules`` can not be found in the default repo checkout location,
    the function will assert False.

    Arguments will be passed on to :func:`.get_modules`.

    Return:
        :class:`.ModuleList`: The module objects.
    """
    # Presumed location of the hdl-modules repo
    hdl_modules_repo_root = tsfpga.REPO_ROOT.parent.parent.resolve() / "hdl-modules" / "hdl-modules"
    if (hdl_modules_repo_root / "modules").exists():
        return get_modules(
            modules_folders=[hdl_modules_repo_root / "modules"],
            names_include=names_include,
            names_avoid=names_avoid,
            library_name_has_lib_suffix=False,
        )

    raise FileNotFoundError(
        f"The hdl-modules modules could not be found. Searched in {hdl_modules_repo_root}"
    )
