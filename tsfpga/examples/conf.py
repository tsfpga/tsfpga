# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Configuration file for the Sphinx documentation builder.
For building documentation of the example modules.
"""

project = "tsfpga example modules"
copyright = "Lukas Vik"
author = "Lukas Vik"

extensions = [
    "sphinx_rtd_theme",
    "symbolator_sphinx",
]

symbolator_output_format = "png"

html_theme = "sphinx_rtd_theme"
