Added

* Add :func:`.to_binary_nibble_string`, :func:`.to_hex_string`,
  :func:`.to_hex_byte_string` functions.
  Renames internal function :func:`.to_binary_string` argument ``int_value`` to ``value``.

Fixes

* Improve Verilog and SystemVerilog support in Vivado project creation.
* Fix :func:`.create_directory` behavior when path already exists as a file.
* Fix potential Vivado build crash when implementation explore is used.

Internal changes

* Rework :class:`.HdlFile` type indication using enumeration :class:`.HdlFile.Type`.
