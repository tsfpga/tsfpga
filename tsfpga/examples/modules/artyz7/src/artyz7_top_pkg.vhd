-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;


package artyz7_top_pkg is

  ------------------------------------------------------------------------------
  -- Register bus.
  constant resync_ext_regs_idx : natural := 0;
  constant resync_pl_regs_idx : natural := 1;
  constant resync_pl_div4_regs_idx : natural := 2;
  constant ddr_buffer_regs_idx : natural := 3;

  constant regs_base_addresses : addr_vec_t(0 to 4 - 1) := (
    resync_ext_regs_idx => x"0000_0000",
    resync_pl_regs_idx => x"0000_1000",
    resync_pl_div4_regs_idx => x"0000_2000",
    ddr_buffer_regs_idx => x"0000_3000"
  );

end;
