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
TSFPGA_MODULES = REPO_ROOT / "modules"
TSFPGA_TCL = THIS_DIR / "vivado" / "tcl"
TSFPGA_GENERATED = REPO_ROOT / "generated"

TSFPGA_EXAMPLES = REPO_ROOT / "examples"
TSFPGA_EXAMPLE_MODULES = TSFPGA_EXAMPLES / "modules"

ALL_TSFPGA_MODULES_FOLDERS = [
    TSFPGA_MODULES,
    TSFPGA_EXAMPLE_MODULES,
]

# Default encoding when opening files
DEFAULT_FILE_ENCODING = "utf-8"

__version__ = "8.0.1"
