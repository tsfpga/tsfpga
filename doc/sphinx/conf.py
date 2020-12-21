# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import builtins
from pathlib import Path
import sys

TSFPGA_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(TSFPGA_ROOT))
PATH_TO_VUNIT = TSFPGA_ROOT.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT.resolve()))


# -- Project information -----------------------------------------------------

project = "tsfpga"
copyright = "Lukas Vik"
author = "Lukas Vik"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.graphviz",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "sphinx_sitemap",
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# Remove warning that built-in types cannot be referenced.
nitpick_ignore = []
for name in dir(builtins):
    nitpick_ignore.append(("py:class", name))

# Base URL for generated sitemap XML
html_baseurl = "tsfpga.com"

# Include robots.txt which points to sitemap
html_extra_path = ["robots.txt"]


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "prev_next_buttons_location": "both",
}

html_context = {
    "display_gitlab": True,
    "gitlab_user": "tsfpga",
    "gitlab_repo": "tsfpga",
    "gitlab_version": "master",
    "conf_py_path": "/doc/sphinx/",
}


# Make autodoc include __init__ class method.
# https://stackoverflow.com/a/5599712


def skip(app, what, name, obj, would_skip, options):
    if name == "__init__":
        return False
    return would_skip


def setup(app):
    app.connect("autodoc-skip-member", skip)
