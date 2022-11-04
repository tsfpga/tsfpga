# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Configuration file for the Sphinx documentation builder.
"""

# Standard libraries
import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
TSFPGA_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(TSFPGA_ROOT))
PATH_TO_HDL_REGISTERS = TSFPGA_ROOT.parent.parent.resolve() / "hdl_registers" / "hdl_registers"
sys.path.insert(0, str(PATH_TO_HDL_REGISTERS))
PATH_TO_VUNIT = TSFPGA_ROOT.parent.parent / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT.resolve()))

project = "tsfpga"
copyright = "Lukas Vik"
author = "Lukas Vik"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "sphinx_sitemap",
]

# Types that are used but sphinx cant find, because they are external
nitpick_ignore = [
    ("py:class", "vunit.test.report.TestReport"),
    ("py:class", "vunit.test.report.TestResult"),
    ("py:class", "vunit.test.runner.TestRunner"),
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "hdl_modules": ("https://hdl-modules.com", None),
    "hdl_registers": ("https://hdl-registers.com", None),
}

# Base URL for generated sitemap XML
html_baseurl = "https://tsfpga.com"

# Include robots.txt which points to sitemap
html_extra_path = ["robots.txt"]

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "prev_next_buttons_location": "both",
    "analytics_id": "G-GN3TVQGSHC",
}


# Make autodoc include __init__ class method.
# https://stackoverflow.com/a/5599712


def skip(app, what, name, obj, would_skip, options):
    if name == "__init__":
        return False
    return would_skip


def setup(app):
    app.connect("autodoc-skip-member", skip)
