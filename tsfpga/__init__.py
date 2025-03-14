# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path

from .about import get_short_slogan

THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parent.resolve()

TSFPGA_PATH = REPO_ROOT / "tsfpga"
TSFPGA_DOC = REPO_ROOT / "doc"
TSFPGA_TCL = THIS_DIR / "vivado" / "tcl"
TSFPGA_GENERATED = REPO_ROOT / "generated"

TSFPGA_EXAMPLES = TSFPGA_PATH / "examples"
TSFPGA_EXAMPLE_MODULES = TSFPGA_EXAMPLES / "modules"

# Default encoding when opening files
DEFAULT_FILE_ENCODING = "utf-8"

__version__ = "13.2.0"

# We have the slogan in one place only, instead of repeating it here in a proper docstring.
__doc__ = get_short_slogan()
