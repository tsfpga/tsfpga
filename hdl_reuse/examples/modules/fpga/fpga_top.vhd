library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library resync;
library reg_file;

use work.fpga_top_pkg.all;


entity fpga_top is
  port (
    input : in std_logic;
    output : out std_logic
  );
end entity;

architecture a of fpga_top is
  signal pl_clk0 : std_logic := '0';

  signal clk_hpm0 : std_logic := '0';
  signal hpm0_m2s : axi_m2s_t := axi_m2s_init;
  signal hpm0_s2m : axi_s2m_t := axi_s2m_init;

  signal clk_hp0 : std_logic := '0';
  signal hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axil_m2s_vec_t(reg_slaves'range) := (others => axil_m2s_init);
  signal regs_s2m : axil_s2m_vec_t(reg_slaves'range) := (others => axil_s2m_init);

  type reg_values_t is array(reg_slaves'range) of reg_vec_t(reg_map'range);
  signal reg_values_out, reg_values_in : reg_values_t;
  type reg_was_written_t is array(reg_slaves'range) of std_logic_vector(reg_map'range);
  signal reg_was_written : reg_was_written_t;

begin


  ------------------------------------------------------------------------------
  axi_to_regs_inst : entity work.axi_to_regs
  generic map (
    reg_slaves => reg_slaves
  )
  port map (
    clk_axi => clk_hpm0,
    axi_m2s => hpm0_m2s,
    axi_s2m => hpm0_s2m,

    regs_m2s => regs_m2s,
    regs_s2m => regs_s2m
  );


  ------------------------------------------------------------------------------
  register_maps : for slave in reg_slaves'range generate
    dut : entity reg_file.axil_reg_file
    generic map (
      regs => reg_map
    )
    port map (
      clk => clk_hpm0,

      axil_m2s => regs_m2s(slave),
      axil_s2m => regs_s2m(slave),

      reg_values_in => reg_values_in(slave),
      reg_values_out => reg_values_out(slave),
      reg_was_written => reg_was_written(slave)
    );
  end generate;

  reg_values_in <= (others => (others => (others => input)));


  ------------------------------------------------------------------------------
  block_design : block
  begin

    clk_hpm0 <= pl_clk0;
    clk_hp0 <= pl_clk0;

    block_design_inst : entity work.block_design
    port map (
      clk_hpm0 => clk_hpm0,
      hpm0_m2s => hpm0_m2s,
      hpm0_s2m => hpm0_s2m,

      clk_hp0 => clk_hp0,
      hp0_m2s => hp0_m2s,
      hp0_s2m => hp0_s2m,

      pl_clk0 => pl_clk0
    );
  end block;

end architecture;
