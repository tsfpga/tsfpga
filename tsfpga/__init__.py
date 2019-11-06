# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

"""
A set of reusable functions for working with HDL projects.
"""


from os.path import dirname, abspath, join


THIS_DIR = dirname(__file__)
ROOT = abspath(join(THIS_DIR, ".."))  # Root of the git repo
TSFPGA_EXAMPLES = join(THIS_DIR, "examples")
TSFPGA_MODULES = join(ROOT, "modules")
TSFPGA_TCL = join(THIS_DIR, "tcl")
