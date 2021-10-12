Changes

* Update so that ``reg_file.axi_lite_reg_file`` asserts ``reg_was_read[i]`` the exact same cycle as
  the AXI-Lite ``R`` transaction occurs (used to be cycle after).
