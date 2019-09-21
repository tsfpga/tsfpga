-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;


entity tb_resync_slv_level is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_resync_slv_level is
  signal clk_out : std_logic := '0';
  signal data_in, data_out : std_logic_vector(16-1 downto 0) := (others => '0');
begin

  test_runner_watchdog(runner, 10 ms);
  clk_out <= not clk_out after 2 ns;


  ------------------------------------------------------------------------------
  main : process
    procedure wait_cycles(signal clk : std_logic; num_cycles : in integer) is
    begin
      for i in 0 to num_cycles-1 loop
        wait until rising_edge(clk);
      end loop;
    end procedure;
    constant zero : std_logic_vector(data_in'range) := (others => '0');
    constant value : std_logic_vector(data_in'range) := x"BAAD";
  begin
    test_runner_setup(runner, runner_cfg);

    -- Module functionality is very simple. This is basically a connectivity test.

    wait until rising_edge(clk_out);
    check_equal(data_out, zero);

    wait_cycles(clk_out, 40);
    check_equal(data_out, zero);
    data_in <= value;

    wait until rising_edge(clk_out);
    wait until rising_edge(clk_out);
    wait until rising_edge(clk_out);
    check_equal(data_out, value);

    wait_cycles(clk_out, 40);
    check_equal(data_out, value);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.resync_slv_level
    port map (
      data_in => data_in,

      clk_out => clk_out,
      data_out => data_out);

end architecture;
