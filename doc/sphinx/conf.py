# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Configuration file for the Sphinx documentation builder.
"""

# Standard libraries
import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Import before others since it modifies PYTHONPATH. pylint: disable=unused-import
import tsfpga.examples.example_pythonpath  # noqa: F401

project = "tsfpga"
copyright = "Lukas Vik"
author = "Lukas Vik"

extensions = [
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
    "git": ("https://gitpython.readthedocs.io/en/stable/", None),
    "vunit": ("https://vunit.github.io/", None),
    "hdl_modules": ("https://hdl-modules.com", None),
    "hdl_registers": ("https://hdl-registers.com", None),
}

# Base URL for generated sitemap.xml.
html_baseurl = "https://tsfpga.com"

# To avoid "en" in the sitemap.xml URL.
# https://sphinx-sitemap.readthedocs.io/en/latest/advanced-configuration.html
sitemap_url_scheme = "{link}"

# Include robots.txt which points to sitemap
html_extra_path = ["robots.txt"]

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "prev_next_buttons_location": "both",
    "analytics_id": "G-GN3TVQGSHC",
    "logo_only": True,
}

html_logo = "tsfpga_sphinx.png"


# Make autodoc include __init__ class method.
# https://stackoverflow.com/a/5599712


def skip(app, what, name, obj, would_skip, options):
    if name == "__init__":
        return False
    return would_skip


def setup(app):
    app.connect("autodoc-skip-member", skip)
