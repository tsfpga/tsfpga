# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

"""
Common functions and definitions in the example build environment.
"""

from os.path import join

import tsfpga
from tsfpga.module import get_modules
from tsfpga.registers import get_default_registers


TSFPGA_EXAMPLES_TEMP_DIR = join(tsfpga.ROOT, "generated")


def get_tsfpga_modules(modules_folders):
    """
    Wrapper of the regular get_modules call with correct settings for tsfpga modules.
    """
    return get_modules(modules_folders,
                       library_name_has_lib_suffix=False,
                       default_registers=get_default_registers())
