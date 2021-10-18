Bug fixes

* Fix bug where ``common.width_conversion`` would set ``output_last`` on the wrong beat
  when downconverting.


Changes

* Update so that ``reg_file.axi_lite_reg_file`` asserts ``reg_was_read[i]`` the exact same cycle as
  the AXI-Lite ``R`` transaction occurs (used to be cycle after).


Breaking changes

* Add ``common.width_conversion`` generic ``enable_last`` with default value ``false``
  (used to be implied value ``true``).

* Move example scripts from ``examples`` to ``tsfpga/examples``. This renames the corresponding
  python package from ``examples`` to ``tsfpga.examples``.
