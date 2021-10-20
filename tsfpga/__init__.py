# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
A set of reusable functions for working with HDL projects.
"""


from pathlib import Path


THIS_DIR = Path(__file__).parent
REPO_ROOT = (THIS_DIR / "..").resolve()

TSFPGA_PATH = REPO_ROOT / "tsfpga"
TSFPGA_DOC = REPO_ROOT / "doc"
TSFPGA_TCL = THIS_DIR / "vivado" / "tcl"
TSFPGA_GENERATED = REPO_ROOT / "generated"

TSFPGA_EXAMPLES = TSFPGA_PATH / "examples"
TSFPGA_EXAMPLE_MODULES = TSFPGA_EXAMPLES / "modules"

# Default encoding when opening files
DEFAULT_FILE_ENCODING = "utf-8"

__version__ = "9.0.1-dev"

# Releases to PyPI are bundled with a release version of the hdl_modules
# project (https://hdl-modules.com). These three definitions will be filled in that case.
# This is a Path object pointing to the 'modules' folder where the hdl_modules can be found.
HDL_MODULES_LOCATION = None
# This is a string of the git tag the modules were fetched from
HDL_MODULES_TAG = None
# This is a string of the git sha the modules were fetched from
HDL_MODULES_SHA = None
