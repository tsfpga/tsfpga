-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Wrapper around VUnit BFM that uses convenient record types for the AXI signals.
-- Will instantiate read and/or write BFMs based on what generics are provided.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

use work.axi_slave_pkg.all;


entity axil_slave is
  generic (
    axi_read_slave : axi_slave_t := axi_slave_init;
    axi_write_slave : axi_slave_t := axi_slave_init;
    data_width : integer
  );
  port (
    clk : in std_logic;
    --
    axil_read_m2s : in axil_read_m2s_t := axil_read_m2s_init;
    axil_read_s2m : out axil_read_s2m_t := axil_read_s2m_init;
    --
    axil_write_m2s : in axil_write_m2s_t := axil_write_m2s_init;
    axil_write_s2m : out axil_write_s2m_t := axil_write_s2m_init
  );
end entity;

architecture a of axil_slave is

begin

  ------------------------------------------------------------------------------
  axi_read_slave_gen : if axi_read_slave /= axi_slave_init generate

    axil_read_slave_inst : entity work.axil_read_slave
      generic map (
        axi_slave => axi_read_slave,
        data_width => data_width
      )
      port map (
        clk => clk,
        --
        axil_read_m2s => axil_read_m2s,
        axil_read_s2m => axil_read_s2m
      );
  end generate;


  ------------------------------------------------------------------------------
  axi_write_slave_gen : if axi_write_slave /= axi_slave_init generate

    axil_write_slave_inst : entity work.axil_write_slave
      generic map (
        axi_slave => axi_write_slave,
        data_width => data_width
      )
      port map (
        clk => clk,
        --
        axil_write_m2s => axil_write_m2s,
        axil_write_s2m => axil_write_s2m
      );

  end generate;


end architecture;
