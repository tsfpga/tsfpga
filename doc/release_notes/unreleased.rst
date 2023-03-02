Added

* Add table with netlist build resource utilization to Sphinx documentation in
  :class:`.ModuleDocumentation`.

* Add :func:`.create_ghdl_ls_configuration` function to generate a configuration file
  (``hdl-prj.json``) for the ``ghdl-ls`` language server
  (https://github.com/ghdl/ghdl-language-server).

* Add support for string and bit vector generics in :class:`.VivadoProject` using the
  types :class:`.StringGenericValue` and :class:`.BitVectorGenericValue`.

* Add check that fails Vivado build unless all bus skew constraints are met after implementation.

* Fail Vivado build if any messages with severity ``ERROR`` have been reported after synthesis
  or implementation.

Breaking changes

* Remove bundling of `hdl_modules <https://hdl-modules.com>`_ with PyPI release.
  This also removes the constants/functions ``tsfpga.HDL_MODULES_LOCATION``,
  ``tsfpga.HDL_MODULES_TAG``, ``tsfpga.HDL_MODULES_SHA`` and
  ``tsfpga.module.get_hdl_modules()``.

* Remove support for formal flow. It's still a bit too experimental for us to support.

* Add mandatory ``heading_character_2`` argument to :meth:`.ModuleDocumentation.get_submodule_rst`.

Bug fixes

* Fix bug where multiple build projects filters that match the same project would crash the build.

* Fix bug where Vivado build could crash when there was an ILA in the design in a very
  specific scenario.
