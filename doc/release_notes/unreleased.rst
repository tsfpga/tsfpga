Breaking changes

* Add mandatory ``heading_character_2`` argument to :meth:`.ModuleDocumentation.get_submodule_rst`.
* Remove support for formal flow. It's still a bit too experimental for us to support.

Added

* Add table with netlist build resource utilization to sphinx documentation in
  :class:`.ModuleDocumentation`.

* Add :func:`.create_ghdl_ls_configuration` function to generate a configuration file
  (``hdl-prj.json``) for the ``vhdl-lsp`` language server
  (https://github.com/ghdl/ghdl-language-server).
