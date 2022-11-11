-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;


entity tb_multiplication is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_multiplication is

  signal clk : std_ulogic := '0';

  signal multiplicand : u_unsigned(12 - 1 downto 0);
  signal multiplier : u_unsigned(5 - 1 downto 0);
  signal product : u_unsigned(17 - 1 downto 0);

begin

  test_runner_watchdog(runner, 2 ms);
  clk <= not clk after 5 ns;


  ------------------------------------------------------------------------------
  main : process
  begin
    test_runner_setup(runner, runner_cfg);

    check_equal(product, 0);

    multiplicand <= to_unsigned(3125, multiplicand);
    multiplier <= to_unsigned(18, multiplier);

    wait until rising_edge(clk);
    wait until rising_edge(clk);
    check_equal(product, 3125 * 18);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.multiplication
    port map (
      clk => clk,

      multiplicand => multiplicand,
      multiplier => multiplier,

      product => product
    );

end architecture;
