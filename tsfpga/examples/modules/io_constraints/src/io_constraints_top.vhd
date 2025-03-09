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
use common.attribute_pkg.all;

library resync;

library artyz7;
use artyz7.block_design_pkg.all;


entity io_constraints_top is
  port (
    input_source_synchronous_clock : in std_ulogic;
    input_source_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of io_constraints_top is

  signal pl_clk : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

begin

  ------------------------------------------------------------------------------
  input_source_synchronous_block : block
    signal data_p1 : std_ulogic_vector(input_source_synchronous_data'range) := (others => '0');
  begin

    data_p1 <= input_source_synchronous_data when rising_edge(input_source_synchronous_clock);


    -----------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data_p1'length
      )
      port map (
        clk_in => input_source_synchronous_clock,
        data_in => data_p1,
        --
        clk_out => pl_clk,
        data_out => m_gp0_s2m.read.r.data(3 downto 0)
      );

  end block;


  ------------------------------------------------------------------------------
  block_design : block
  begin

    ------------------------------------------------------------------------------
    block_design_inst : entity artyz7.block_design_wrapper
      port map (
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,
        --
        s_hp0_m2s => s_hp0_m2s,
        s_hp0_s2m => s_hp0_s2m,
        --
        pl_clk => pl_clk,
        --
        ddr => ddr,
        fixed_io => fixed_io
      );

  end block;

end architecture;
