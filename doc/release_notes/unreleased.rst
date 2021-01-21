Added

* Add optional ``clk_in`` port to ``resync.resync_level`` which enables a more deterministic latency constraint.
* Add support for HTML paragraph breaks in register/bit descriptions.
  Consecutive newlines will be converted to paragraph breaks.
* Add support for parallel builds of FPGA projects using the :class:`.BuildProjectList` class.
* Add support for register constants in TOML file.
* Add ``axi.axi_read_throttle`` and ``axi.axi_write_throttle`` VHDL entities.
* Add :meth:`.BaseModule.pre_build` hook function.
* Add time saving mechanism to only re-create the register VHDL package when necessary.
* Add ``common.debounce`` VHDL entity.
* Add ``reg_was_read`` port to ``reg_file.axil_reg_file``.
* Add :meth:`.VivadoProject.pre_create` hook function.
* Allow Vivado project source files to contain spaces.

Breaking changes

* Rename ``resync.resync_on_signal`` to ``resync.resync_level_on_signal`` and ``resync.resync_slv_on_signal`` to ``resync.resync_slv_level_on_signal``.
  This is more descriptive and follows the naming of the other resync blocks.
* The generated register HTML page no longer supports markdown flavor of using underscores to annotate.
  Instead use **\*\*double asterisks for bold\*\*** and *\*single asterisks for emphasis\**.
  This change is done to make it easier to refer to other registers/constants/signals who very often have underscores in their name.
* Rename ``axi.axi_interconnect`` to ``axi.axi_simple_crossbar`` and ``axi.axil_interconnect`` to ``axi.axil_simple_crossbar``.
  This naming is factual (it is a crossbar, not an interconnect) and more descriptive.
* Rename ``RegisterList.create_html_table()`` to :meth:`.RegisterList.create_html_register_table`.
  Add :meth:`.RegisterList.create_html_constant_table`.
* Deprecate ``BaseModule.setup_simulations()`` in favor of :meth:`.BaseModule.setup_vunit`.
* Rework :class:`.BuildProjectList` class completely.
  See the :class:`class documentation <.BuildProjectList>`, the :ref:`minimal usage example <example_build_py>` and the `build.py example in the repo <https://gitlab.com/tsfpga/tsfpga/-/blob/master/examples/build.py>`__.
* Change :class:`.VivadoProject` to catch non-zero exit code exception if Vivado call fails.
  If :meth:`.VivadoProject.create` or :meth:`.VivadoProject.open` fail they will return ``False``.
  If :meth:`.VivadoProject.build` fails, the returned :class:`.BuildResult` object will have ``success`` set to ``False``.
* Rename ``<module>_reg_was_written_t`` to ``<module>_reg_was_accessed_t`` in generated register VHDL package.
* Add mandatory generic ``width`` to ``resync.resync_slv_level`` and ``resync.resync_slv_level_on_signal``.
* Rename ``BaseModule.add_config`` to :meth:`.BaseModule.add_vunit_config`.
* Rename ``types_pkg.swap_bytes`` to ``types_pkg.swap_byte_order``.

Changes

* Add TCL sources before adding modules in :class:`.VivadoTcl`.
