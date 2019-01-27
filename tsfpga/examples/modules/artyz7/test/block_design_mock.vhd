library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;

library bfm;

use work.top_level_sim_pkg.all;


entity block_design_mock is
  port (
    clk_m_gp0 : in std_logic;
    m_gp0_m2s : out axi_m2s_t;
    m_gp0_s2m : in axi_s2m_t;

    clk_s_hp0 : in std_logic;
    s_hp0_m2s : in axi_m2s_t;
    s_hp0_s2m : out axi_s2m_t;

    pl_clk0 : out std_logic := '0';
    pl_clk1 : out std_logic := '0'
  );
end entity;

architecture a of block_design_mock is

  constant pl_clk0_period : time := 10 ns; -- 100 MHz
  constant pl_clk1_period : time := 5 ns; -- 200 MHz

  constant axi_slave : axi_slave_t := new_axi_slave(address_fifo_depth => 1, memory => axi_memory);

begin

  pl_clk0 <= not pl_clk0 after pl_clk0_period / 2;
  pl_clk1 <= not pl_clk1 after pl_clk1_period / 2;


  ------------------------------------------------------------------------------
  axi_master_inst : entity bfm.axi_master
  generic map (
    bus_handle => regs_axi_master
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
      axi_slave => axi_slave,
      data_width => 64
    )
    port map (
      clk => clk_s_hp0,

      axi_read_m2s => s_hp0_m2s.read,
      axi_read_s2m => s_hp0_s2m.read,

      axi_write_m2s => s_hp0_m2s.write,
      axi_write_s2m => s_hp0_s2m.write
    );

end architecture;
