library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.com_context;

use work.fpga_top_pkg.all;
use work.fpga_top_sim_pkg.all;


entity tb_fpga_top is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_fpga_top is

begin

  test_runner_watchdog(runner, 2 ms);


  ------------------------------------------------------------------------------
  main : process
    constant beef : std_logic_vector(32 - 1 downto 0) := x"beef_beef";
    constant dead : std_logic_vector(32 - 1 downto 0) := x"dead_dead";
  begin
    test_runner_setup(runner, runner_cfg);

    write_bus(net, hpm0_master, reg_slaves(0).addr, beef);
    check_bus(net, hpm0_master, reg_slaves(0).addr, beef);

    write_bus(net, hpm0_master, reg_slaves(1).addr, dead);
    check_bus(net, hpm0_master, reg_slaves(1).addr, dead);

    check_bus(net, hpm0_master, reg_slaves(0).addr, beef);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.fpga_top
  port map (
    input => '1',
    output => open
  );

end architecture;
