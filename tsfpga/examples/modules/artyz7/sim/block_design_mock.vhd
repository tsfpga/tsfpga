-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.axi_slave_pkg.axi_slave_t;
use vunit_lib.axi_slave_pkg.new_axi_slave;
use vunit_lib.bus_master_pkg.address_length;
use vunit_lib.bus_master_pkg.data_length;

library axi;
use axi.axi_pkg.all;

library bfm;

library common;
use common.time_pkg.to_period;

library reg_file;
use reg_file.reg_operations_pkg.regs_bus_master;

use work.block_design_mock_pkg.all;
use work.block_design_pkg.all;


entity block_design_mock is
  port (
    m_gp0_m2s : out axi_m2s_t;
    m_gp0_s2m : in axi_s2m_t;
    --# {{}}
    s_hp0_m2s : in axi_m2s_t;
    s_hp0_s2m : out axi_s2m_t;
    --# {{}}
    pl_clk : out std_ulogic := '0'
  );
end entity;

architecture a of block_design_mock is

  constant pl_clk_period : time := to_period(frequency_hz=>pl_clk_frequency_hz);

  constant axi_read_slave, axi_write_slave : axi_slave_t := new_axi_slave(
    address_fifo_depth => 1,
    memory => axi_memory
  );

begin

  pl_clk <= not pl_clk after pl_clk_period / 2;


  ------------------------------------------------------------------------------
  axi_master_inst : entity bfm.axi_master
    generic map (
      bus_handle => regs_bus_master
    )
    port map (
      clk => pl_clk,
      --
      axi_read_m2s => m_gp0_m2s.read,
      axi_read_s2m =>  m_gp0_s2m.read,
      --
      axi_write_m2s => m_gp0_m2s.write,
      axi_write_s2m =>  m_gp0_s2m.write
    );

  -- If our register AXI master port used different dimensions than these
  -- we would need to create another bus master, probably in block_design_mock_pkg.
  assert m_gp0_data_width = data_length(regs_bus_master);
  assert m_gp0_addr_width = address_length(regs_bus_master);


  ------------------------------------------------------------------------------
  axi_read_range_checker_inst : entity axi.axi_read_range_checker
    generic map (
      address_width => s_hp0_addr_width,
      id_width => s_hp0_id_width,
      data_width => s_hp0_data_width,
      enable_axi3 => true,
      supports_narrow_burst => false
    )
    port map (
      clk => pl_clk,
      --
      read_m2s => s_hp0_m2s.read,
      read_s2m => s_hp0_s2m.read
    );


  ------------------------------------------------------------------------------
  axi_read_slave_inst : entity bfm.axi_read_slave
    generic map (
      axi_slave => axi_read_slave,
      data_width => s_hp0_data_width,
      id_width => s_hp0_id_width
    )
    port map (
      clk => pl_clk,
      --
      axi_read_m2s => s_hp0_m2s.read,
      axi_read_s2m => s_hp0_s2m.read
    );


  ------------------------------------------------------------------------------
  axi_write_range_checker_inst : entity axi.axi_write_range_checker
    generic map (
      address_width => s_hp0_addr_width,
      id_width => s_hp0_id_width,
      data_width => s_hp0_data_width,
      enable_axi3 => true,
      supports_narrow_burst => false
    )
    port map (
      clk => pl_clk,
      --
      write_m2s => s_hp0_m2s.write,
      write_s2m => s_hp0_s2m.write
    );


  ------------------------------------------------------------------------------
  axi_write_slave_inst : entity bfm.axi_write_slave
    generic map (
      axi_slave => axi_write_slave,
      data_width => s_hp0_data_width,
      id_width => s_hp0_id_width
    )
    port map (
      clk => pl_clk,
      --
      axi_write_m2s => s_hp0_m2s.write,
      axi_write_s2m => s_hp0_s2m.write
    );

end architecture;
