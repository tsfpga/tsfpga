library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.addr_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library resync;
library reg_file;

use work.artyz7_top_pkg.all;
use work.artyz7_regs_pkg.all;


entity artyz7_top is
  port (
    clk_ext : in std_logic;
    led : out std_logic_vector(0 to 3)
  );
end entity;

architecture a of artyz7_top is

  signal clk_m_gp0 : std_logic := '0';
  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axil_m2s_vec_t(reg_slaves'range) := (others => axil_m2s_init);
  signal regs_s2m : axil_s2m_vec_t(reg_slaves'range) := (others => axil_s2m_init);

  type reg_values_t is array(reg_slaves'range) of reg_vec_t(artyz7_reg_map'range);
  signal reg_values_out, reg_values_in : reg_values_t;
  type reg_was_written_t is array(reg_slaves'range) of std_logic_vector(artyz7_reg_map'range);
  signal reg_was_written : reg_was_written_t;

begin

  ------------------------------------------------------------------------------
  blink_int : process
    variable count : unsigned(27 - 1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk_m_gp0);
    led(0) <= count(count'high);

    count := count + 1;
  end process;


  ------------------------------------------------------------------------------
  regs_block : block
    subtype clk_m_gp0_rng is integer range 0 to reg_slaves'length / 2 - 1;
    subtype clk_ext_rng is integer range reg_slaves'length / 2 to reg_slaves'length - 1;

    -- Set up half the registers to be in same clock domain as AXI port,
    -- and second half to be in another clock domain.
    signal reg_clks : std_logic_vector(reg_slaves'range) := (others => '0');
    constant clocks_are_the_same : boolean_vector(reg_slaves'range) :=
      (0 to 5 => true, 6 to 11 => false);

    -- @TODO Workaround while theres a bug in GHDL: https://github.com/ghdl/ghdl/issues/707
    --(clk_m_gp0_rng => true, clk_ext_rng => false);
  begin

    reg_clks <= (0 to 5 => clk_m_gp0, 6 to 11 => clk_ext);

    ------------------------------------------------------------------------------
    axi_to_regs_inst : entity axi.axi_to_axil_vec
      generic map (
        axil_slaves => reg_slaves,
        clocks_are_the_same => clocks_are_the_same
      )
      port map (
        clk_axi => clk_m_gp0,
        axi_m2s => m_gp0_m2s,
        axi_s2m => m_gp0_s2m,

        clk_axil_vec => reg_clks,
        axil_vec_m2s => regs_m2s,
        axil_vec_s2m => regs_s2m
      );


    ------------------------------------------------------------------------------
    register_maps : for slave in reg_slaves'range generate
      axil_reg_file_inst : entity reg_file.axil_reg_file
        generic map (
          regs => artyz7_reg_map
        )
        port map (
          clk => reg_clks(slave),

          axil_m2s => regs_m2s(slave),
          axil_s2m => regs_s2m(slave),

          reg_values_in => reg_values_in(slave),
          reg_values_out => reg_values_out(slave),
          reg_was_written => reg_was_written(slave)
        );
    end generate;
  end block;

  reg_values_in <= (others => (others => (others => '1')));


  ------------------------------------------------------------------------------
  block_design : block
    signal pl_clk0 : std_logic := '0';
  begin

    clk_m_gp0 <= pl_clk0;

    block_design_inst : entity work.block_design_wrapper
    port map (
      clk_m_gp0 => clk_m_gp0,
      m_gp0_m2s => m_gp0_m2s,
      m_gp0_s2m => m_gp0_s2m,

      pl_clk0 => pl_clk0
    );
  end block;

end architecture;
