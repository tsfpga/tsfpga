-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library axi_lite;
use axi_lite.axi_lite_pkg.all;

library common;
use common.common_pkg.all;

library artyz7_block_design;
use artyz7_block_design.block_design_pkg.all;

library ddr_buffer;

use work.register_top_level_register_record_pkg.all;


entity axi_lite_register_top_level is
  port (
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of axi_lite_register_top_level is

  signal pl_clk : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axi_lite_m2s_vec_t(regs_base_addresses'range) := (others => axi_lite_m2s_init);
  signal regs_s2m : axi_lite_s2m_vec_t(regs_base_addresses'range) := (others => axi_lite_s2m_init);

begin

  ------------------------------------------------------------------------------
  regs_block : block
    -- Set up some registers to be in same clock domain as AXI port,
    -- and some to be in another clock domain.
    constant clocks_are_the_same : boolean_vector(regs_base_addresses'range) := (
      resync_ext_regs_idx => false,
      resync_pl_regs_idx => true,
      resync_pl_div4_regs_idx => false,
      ddr_buffer_regs_idx => true
    );
  begin

  end block;


  ------------------------------------------------------------------------------
  block_design_wrapper_inst : entity artyz7_block_design.block_design_wrapper
    port map (
      m_gp0_m2s => m_gp0_m2s,
      m_gp0_s2m => m_gp0_s2m,
      --
      s_hp0_m2s => axi_m2s_init,
      s_hp0_s2m => open,
      --
      pl_clk => pl_clk,
      --
      ddr => ddr,
      fixed_io => fixed_io
    );

end architecture;
