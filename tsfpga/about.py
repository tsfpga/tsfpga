# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


def get_slogan():
    return (
        "tsfpga is a development platform that aims to streamline all aspects of your FPGA project."
    )


def get_short_doc():
    return f"""{get_slogan()}
With its python build/simulation flow, along with complementary VHDL components, it is perfect \
for CI/CD and test-driven development.
Focus has been placed on flexibility and modularization, achieving scalability even in very \
large multi-vendor code bases.
"""


def get_doc():
    """
    Prepend get_short_doc() to this to get the complete doc.
    """
    return """Key features
------------

* Source code centric project structure: Build projects, test configurations, constraints, \
IP cores, etc. are handled close to the source code.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables local VUnit configuration setup without multiple ``run.py``.
* Handling of IP cores and simlib for your simulation project, with automatic re-compile when \
necessary.
* Python-based parallel Vivado build system.
* Register code generation from TOML: VHDL package, HTML documentation, C header, C++ class.
* VHDL AXI components that enable the register bus: AXI-to-AXI-Lite converter, \
AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, AXI-Lite generic \
register file.

The maintainers place high focus on quality, with everything having good unit test coverage and a \
thought-out structure.
The project is mature and used in many production environments.
"""
