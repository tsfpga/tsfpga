# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


def get_slogan():
    return "Tsfpga is a project platform for modern FPGA development."


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

* Source code centric project structure: Build projects, test configurations, constraints, IP cores, etc. \
are handled "close" to the source code.
* Complete Vivado build system.
* Ideal for setting up VUnit simulation projects.
* Handling of IP cores and simlib for your simulation project, with automatic re-compile when necessary.
* Register code generation from JSON: VHDL package, HTML documentation, C header, C++ class.
* VHDL AXI components that enable the register bus: AXI-to-AXI-Lite converter, AXI-Lite interconnect, \
AXI-Lite mux (splitter), AXI-Lite clock domain crossing, AXI-Lite generic register file.

The maintainers place high focus on quality, with everything having good unit test coverage and a \
though-out structure.
The project is mature and used in many production environments.


License
-------

This project is released under the terms of the BSD 3-Clause License. See ``license.txt`` for details."""
