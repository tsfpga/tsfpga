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

library trail;
use trail.trail_pkg.all;

library common;
use common.attribute_pkg.all;

library artyz7_block_design;
use artyz7_block_design.block_design_pkg.all;

use work.register_top_level_pkg.all;
use work.register_top_level_regs_pkg.all;
use work.register_top_level_register_record_pkg.all;


entity trail_register_test_top is
  port (
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of trail_register_test_top is

  signal pl_clk : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal trail_operations : trail_operation_vec_t(base_addresses'range) := (
    others => trail_operation_init
  );
  signal trail_responses : trail_response_vec_t(base_addresses'range) := (
    others => trail_response_init
  );

begin

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


  ------------------------------------------------------------------------------
  axi_to_axi_lite_vec_inst : entity trail.axi_to_trail_vector
    generic map (
      axi_address_width => m_gp0_addr_width,
      axi_id_width => m_gp0_id_width,
      data_width => m_gp0_data_width,
      base_addresses => base_addresses
    )
    port map (
      clk_axi => pl_clk,
      axi_m2s => m_gp0_m2s,
      axi_s2m => m_gp0_s2m,
      --
      trail_operations => trail_operations,
      trail_responses => trail_responses
    );


  ------------------------------------------------------------------------------
  register_file_gen : for register_list_index in trail_operations'range generate
    signal regs_down : register_top_level_regs_down_t := register_top_level_regs_down_init;

    -- Make sure that nothing is optimized away.
    attribute dont_touch of regs_down : signal is "true";
  begin

    ------------------------------------------------------------------------------
    register_file_inst : entity work.register_top_level_register_file_trail
      port map (
        clk => pl_clk,
        --
        trail_operation => trail_operations(register_list_index),
        trail_response => trail_responses(register_list_index),
        --
        regs_down => regs_down
      );

  end generate;

end architecture;
