Fixes

* Improve Verilog and SystemVerilog support in Vivado project creation.
* Fix :func:`.create_directory` behavior when path already exists as a file.

Internal changes

* Rework :class:`.HdlFile` type indication using enumeration :class:`.HdlFile.Type`.
