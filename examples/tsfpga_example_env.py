# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

"""
Common functions and definitions in the example build environment.
"""

import tsfpga
from tsfpga.module import get_modules
from tsfpga.register_list import get_default_registers


TSFPGA_EXAMPLES_TEMP_DIR = tsfpga.TSFPGA_GENERATED


def get_tsfpga_modules(modules_folders=None):
    """
    Wrapper of the regular get_modules call with correct settings for tsfpga modules.
    """
    modules_folders = tsfpga.ALL_TSFPGA_MODULES_FOLDERS if modules_folders is None \
        else modules_folders
    return get_modules(modules_folders,
                       library_name_has_lib_suffix=False,
                       default_registers=get_default_registers())
