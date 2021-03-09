-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Wrapper around VUnit BFM that uses record types for the AXI signals.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library axi;
use axi.axi_pkg.all;

library vunit_lib;
context vunit_lib.vc_context;


entity axi_slave is
  generic (
    axi_slave : axi_slave_t;
    data_width : positive;
    -- Note that the VUnit BFM creates and integer_vector_ptr of length 2**id_width, so a large
    -- value for id_width might crash your simulator.
    id_width : natural := 8;
    w_fifo_depth : natural := 0
  );
  port (
    clk : in std_logic;

    axi_read_m2s : in axi_read_m2s_t := axi_read_m2s_init;
    axi_read_s2m : out axi_read_s2m_t := axi_read_s2m_init;

    axi_write_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    axi_write_s2m : out axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_slave is

begin

  ------------------------------------------------------------------------------
  axi_read_slave_wrapper_inst : entity work.axi_read_slave_wrapper
    generic map (
      axi_slave => axi_slave,
      data_width => data_width,
      id_width => id_width
    )
    port map (
      clk => clk,
      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m
    );


  ------------------------------------------------------------------------------
  axi_write_slave_wrapper_inst : entity work.axi_write_slave_wrapper
    generic map (
      axi_slave => axi_slave,
      data_width => data_width,
      id_width => id_width,
      w_fifo_depth => w_fifo_depth
    )
    port map (
      clk => clk,
      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m
    );

end architecture;
