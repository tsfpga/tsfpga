-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Settings in the Zynq block design.
-- -------------------------------------------------------------------------------------------------

package block_design_pkg is

  ------------------------------------------------------------------------------
  -- PL clock settings.
  constant pl_clk_frequency_hz : real := 100.0e6;


  ------------------------------------------------------------------------------
  -- AXI ports.
  constant m_gp0_id_width : natural := 12;
  constant m_gp0_addr_width : positive := 32;
  constant m_gp0_data_width : positive := 32;

  constant s_hp0_id_width : natural := 6;
  constant s_hp0_addr_width : positive := 32;
  constant s_hp0_data_width : positive := 64;

end package;
