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


package artyz7_top_pkg is

  ------------------------------------------------------------------------------
  constant resync_hp0_regs_idx : natural := 0;
  constant resync_ext_regs_idx : natural := 1;
  constant ddr_buffer_regs_idx : natural := 2;

  constant regs_base_addresses : addr_vec_t(0 to 3 - 1) := (
    resync_hp0_regs_idx => x"0000_0000",
    resync_ext_regs_idx => x"0000_1000",
    ddr_buffer_regs_idx => x"0000_2000"
  );


  ------------------------------------------------------------------------------
  constant m_gp0_id_width : natural := 12;
  constant m_gp0_addr_width : positive := 32;
  constant m_gp0_data_width : positive := 32;

  constant s_hp0_id_width : natural := 6;
  constant s_hp0_addr_width : positive := 32;
  constant s_hp0_data_width : positive := 64;

end;
