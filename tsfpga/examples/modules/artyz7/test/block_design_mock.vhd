-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;

library bfm;

library reg_file;
use reg_file.reg_operations_pkg.all;

use work.top_level_sim_pkg.all;
use work.artyz7_top_pkg.all;


entity block_design_mock is
  port (
    clk_m_gp0 : in std_ulogic;
    m_gp0_m2s : out axi_m2s_t;
    m_gp0_s2m : in axi_s2m_t;

    clk_s_hp0 : in std_ulogic;
    s_hp0_m2s : in axi_m2s_t;
    s_hp0_s2m : out axi_s2m_t;

    pl_clk0 : out std_ulogic := '0';
    pl_clk1 : out std_ulogic := '0'
  );
end entity;

architecture a of block_design_mock is

  constant pl_clk0_period : time := 10 ns; -- 100 MHz
  constant pl_clk1_period : time := 5 ns; -- 200 MHz

  constant axi_read_slave, axi_write_slave : axi_slave_t := new_axi_slave(
    address_fifo_depth => 1,
    memory => axi_memory
  );

begin

  pl_clk0 <= not pl_clk0 after pl_clk0_period / 2;
  pl_clk1 <= not pl_clk1 after pl_clk1_period / 2;


  ------------------------------------------------------------------------------
  -- If our register AXI master port used different dimensions than these
  -- we would need to create another bus master, probably in top_level_sim_pkg.
  assert m_gp0_data_width = data_length(regs_bus_master);
  assert m_gp0_addr_width = address_length(regs_bus_master);

  axi_master_inst : entity bfm.axi_master
  generic map (
    bus_handle => regs_bus_master
  )
  port map (
    clk => clk_m_gp0,

    axi_read_m2s => m_gp0_m2s.read,
    axi_read_s2m =>  m_gp0_s2m.read,

    axi_write_m2s => m_gp0_m2s.write,
    axi_write_s2m =>  m_gp0_s2m.write
  );


  ------------------------------------------------------------------------------
  axi_slave_inst : entity bfm.axi_slave
    generic map (
      axi_read_slave => axi_read_slave,
      axi_write_slave => axi_write_slave,
      data_width => s_hp0_data_width,
      id_width => s_hp0_id_width
    )
    port map (
      clk => clk_s_hp0,

      axi_read_m2s => s_hp0_m2s.read,
      axi_read_s2m => s_hp0_s2m.read,

      axi_write_m2s => s_hp0_m2s.write,
      axi_write_s2m => s_hp0_s2m.write
    );

end architecture;
