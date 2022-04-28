Breaking changes

* Add mandatory ``heading_character_2`` argument to :meth:`.ModuleDocumentation.get_submodule_rst`.
* Remove support for formal flow. It's still a bit too experimental for us to support.

Added

* Add table with netlist build resource utilization to sphinx documentation in
  :class:`.ModuleDocumentation`.

* Add :func:`.create_ghdl_ls_configuration` function to generate a configuration file
  (``hdl-prj.json``) for the ``ghdl-ls`` language server
  (https://github.com/ghdl/ghdl-language-server).

* Add support for string and bit vector generics in :class:`.VivadoProject` using the
  types :class:`.StringGenericValue` and :class:`.BitVectorGenericValue`.
