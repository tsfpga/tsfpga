library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.com_context;

use work.artyz7_top_pkg.all;
use work.top_level_sim_pkg.all;


entity tb_artyz7_top is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_artyz7_top is

  signal clk_ext : std_logic := '0';

begin

  test_runner_watchdog(runner, 200 us);
  clk_ext <= not clk_ext after 8 ns;


  ------------------------------------------------------------------------------
  main : process
    constant beef : std_logic_vector(32 - 1 downto 0) := x"beef_beef";
    constant dead : std_logic_vector(32 - 1 downto 0) := x"dead_dead";
  begin
    test_runner_setup(runner, runner_cfg);

    write_bus(net, register_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);
    check_bus(net, register_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);

    -- Write different value to same register in another register map.
    -- The last register map should be in another clock domain as well.
    write_bus(net, register_axi_master, reg_slaves(reg_slaves'high).addr or x"43c0_0000", dead);
    check_bus(net, register_axi_master, reg_slaves(reg_slaves'high).addr or x"43c0_0000", dead);

    check_bus(net, register_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.artyz7_top
  port map (
    clk_ext => clk_ext
  );

end architecture;
