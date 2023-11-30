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
  subtype dummy_reg_slaves is integer range 0 to 2;
  constant ddr_buffer_regs_idx : integer := 3;

  constant ddr_buffer_regs_base_addr : addr_t := x"0000_3000";

  constant regs_base_addresses : addr_vec_t(0 to 4 - 1) := (
    0 => x"0000_0000",
    1 => x"0000_1000",
    2 => x"0000_2000",
    ddr_buffer_regs_idx => ddr_buffer_regs_base_addr
  );


  ------------------------------------------------------------------------------
  constant m_gp0_id_width : integer := 12;
  constant m_gp0_addr_width : integer := 32;
  constant m_gp0_data_width : integer := 32;

  constant s_hp0_id_width : integer := 6;
  constant s_hp0_addr_width : integer := 32;
  constant s_hp0_data_width : integer := 64;

end;
