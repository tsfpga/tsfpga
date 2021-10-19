Added

* Add ``common.handshake_master``, ``common.handshake_slave``, ``common.axi_stream_master``
  and ``common.axi_stream_slave`` VHDL BMFs.
* Add ``common.keep_remover`` and ``common.strobe_on_last`` VHDL entities.
* Add "peek read" mode to ``fifo.fifo``.
* Add :class:`.ModuleDocumentation` class for generating Sphinx RST documentation of a module.


Bug fixes

* Fix bug where ``common.width_conversion`` would set ``output_last`` on the wrong beat
  when downconverting.

* Fix bug in ``reg_file.reg_operations_pkg.read_modify_reg_bit``.


Changes

* Update so that ``reg_file.axi_lite_reg_file`` asserts ``reg_was_read[i]`` the exact same cycle as
  the AXI-Lite ``R`` transaction occurs (used to be cycle after).


Breaking changes

* Add ``common.width_conversion`` generic ``enable_last`` with default value ``false``
  (used to be implied value ``true``).

* Move example scripts from ``examples`` to ``tsfpga/examples``. This renames the corresponding
  python package from ``examples`` to ``tsfpga.examples``.
