# About tsfpga
This repo contains a set of tools for working in a modern FPGA project.
It consists of two distinct parts that can be used independently of each other.

## A reusable set of HDL building blocks
The `modules` folder contains a set of VHDL modules/IP that are common in many FPGA projects.
The modules have been developed with quality and reusability in mind.
Having these high quality building blocks available will make it easier to add new functionality to your project.

### Requirements
The modules make heavy use of `VHDL-2008` so you will need a recent simulator and synthesis tool.

## A project platform for FPGA development
The `tsfpga` folder contains a Python package for working with modules and chips in an FPGA project.
The goal is a highly useable system for working in a multi-chip and multi-vendor environment.
Focus has been placed on modularization and enabling a high level of scalability.

### Key features
* Source code centric project structure: Constraints, IP cores, test configurations, build projects, etc. are handled "close" to the source code.
See e.g. [resync_counter.tcl](modules/resync/scoped_constraints/resync_counter.tcl), [mult_u12_u5.tcl](examples/modules_with_ip/module_with_ip_cores/ip_cores/mult_u12_u5.tcl), [module_math.py](modules/math/module_math.py), [project_artyz7.py](examples/modules/artyz7/project_artyz7.py).
* Generic AXI-Lite register file, with automatic register generation from JSON: VHDL package, C header, C++ class, HTML documentation. See e.g. [ddr_buffer_regs.json](examples/modules/ddr_buffer/ddr_buffer_regs.json) and [build.py](examples/build.py#L100).
* Automatic (re)compile of simlib and IP core simulation files. See e.g. [vivado_simlib.py](tsfpga/vivado_simlib.py), [vivado_ip_cores.py](tsfpga/vivado_ip_cores.py) and [simulate.py](examples/simulate.py#L41).

### Requirements
In order to use the package you will need
* Python 3.6+
* [VUnit](https://vunit.github.io/) in your `PYTHONPATH`, with a functioning VHDL simulator in your `PATH`
* Python package: `toml`

To run the bundled tests you must have
* Python packages: `pytest`, `pylint`, `pycodestyle`
* Xilinx Vivado 2018.3+ in your `PATH`
* GCC in your `PATH`

# Main contributors
* Olof Kraigher
* Ludvig Vidlid
* Lukas Vik

# License
This project is released under the terms of the BSD 3-Clause License. See `license.txt` for details.
