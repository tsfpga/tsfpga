library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;


entity tb_edge_detector is
  generic (
    runner_cfg : string;
    wait_time_ms : integer
  );
end entity;

architecture tb of tb_edge_detector is
  signal clk : std_logic := '0';
  signal data_in, edge_detected : std_logic := '0';
begin

  test_runner_watchdog(runner, 10 ms);
  clk <= not clk after 2 ns;


  ------------------------------------------------------------------------------
  main : process
  begin
    test_runner_setup(runner, runner_cfg);

    wait for wait_time_ms * 1 ms;
    data_in <= '1';
    wait until rising_edge(clk);
    wait until rising_edge(clk);
    check_equal(edge_detected, '1');

    test_runner_cleanup(runner);
  end process;

  ------------------------------------------------------------------------------
  dut : entity work.edge_detector
    port map (
      clk => clk,

      data_in => data_in,
      edge_detected => edge_detected);

end architecture;
