# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

"""
A set of reusable functions for working with HDL projects.
"""


from pathlib import Path


THIS_DIR = Path(__file__).parent
REPO_ROOT = (THIS_DIR / "..").resolve()

TSFPGA_PATH = REPO_ROOT / "tsfpga"
TSFPGA_DOC = REPO_ROOT / "doc"
TSFPGA_MODULES = REPO_ROOT / "modules"
TSFPGA_TCL = THIS_DIR / "tcl"
TSFPGA_GENERATED = REPO_ROOT / "generated"

TSFPGA_EXAMPLES = REPO_ROOT / "examples"
TSFPGA_EXAMPLE_MODULES = TSFPGA_EXAMPLES / "modules"
TSFPGA_EXAMPLE_MODULES_WITH_IP = TSFPGA_EXAMPLES / "modules_with_ip"

ALL_TSFPGA_MODULES_FOLDERS = [TSFPGA_MODULES, TSFPGA_EXAMPLE_MODULES, TSFPGA_EXAMPLE_MODULES_WITH_IP]

__version__ = "3.0.0"
