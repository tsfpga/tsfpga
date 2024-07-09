-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;

use work.block_design_pkg.all;


package artyz7_top_pkg is

  ------------------------------------------------------------------------------
  -- Assigned in top level.
  constant clk_m_gp0_frequency_hz : real := pl_clk0_frequency_hz;
  constant clk_s_hp0_frequency_hz : real := pl_clk1_frequency_hz;


  ------------------------------------------------------------------------------
  -- Register bus.
  constant resync_hp0_regs_idx : natural := 0;
  constant resync_ext_regs_idx : natural := 1;
  constant resync_synchronous_regs_idx : natural := 2;
  constant ddr_buffer_regs_idx : natural := 3;

  constant regs_base_addresses : addr_vec_t(0 to 4 - 1) := (
    resync_hp0_regs_idx => x"0000_0000",
    resync_ext_regs_idx => x"0000_1000",
    resync_synchronous_regs_idx => x"0000_2000",
    ddr_buffer_regs_idx => x"0000_3000"
  );

end;
