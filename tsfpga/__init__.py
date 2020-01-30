# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

"""
A set of reusable functions for working with HDL projects.
"""


from os.path import dirname, abspath, join
from tsfpga.about import get_version


THIS_DIR = dirname(__file__)
ROOT = abspath(join(THIS_DIR, ".."))  # Root of the git repo

TSFPGA_MODULES = join(ROOT, "modules")
TSFPGA_TCL = join(THIS_DIR, "tcl")

TSFPGA_EXAMPLES = join(ROOT, "examples")
TSFPGA_EXAMPLE_MODULES = join(TSFPGA_EXAMPLES, "modules")
TSFPGA_EXAMPLE_MODULES_WITH_IP = join(TSFPGA_EXAMPLES, "modules_with_ip")

ALL_TSFPGA_MODULES_FOLDERS = [TSFPGA_MODULES, TSFPGA_EXAMPLE_MODULES, TSFPGA_EXAMPLE_MODULES_WITH_IP]

__version__ = get_version()
