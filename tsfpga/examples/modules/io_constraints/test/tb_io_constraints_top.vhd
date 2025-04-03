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
use vunit_lib.run_pkg.all;

library artyz7;
use artyz7.block_design_pkg.all;


entity tb_io_constraints_top is
  generic (
    mock_unisim : boolean := false;
    runner_cfg : string
  );
end entity;

architecture tb of tb_io_constraints_top is

  signal input_source_synchronous_clock : std_ulogic := '0';
  signal input_source_synchronous_data : std_ulogic_vector(3 downto 0) := (others => '0');

  signal input_system_synchronous_clock : std_ulogic := '0';
  signal input_system_synchronous_data : std_ulogic_vector(3 downto 0) := (others => '0');

  signal input_sink_synchronous_clock : std_ulogic := '0';
  signal input_sink_synchronous_data : std_ulogic_vector(3 downto 0) := (others => '0');

  signal ddr : zynq7000_ddr_t;
  signal fixed_io : zynq7000_fixed_io_t;

  constant clock_period : time := 8 ns;

begin

  test_runner_watchdog(runner, 200 us);

  input_source_synchronous_clock <= not input_source_synchronous_clock after clock_period / 2;
  input_system_synchronous_clock <= not input_system_synchronous_clock after clock_period / 2;


  ------------------------------------------------------------------------------
  main : process
  begin
    test_runner_setup(runner, runner_cfg);

    if run("test_do_nothing_except_let_the_design_execute_and_print_status") then
      wait for 1000 * clock_period;
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.io_constraints_top
    generic map (
      mock_unisim => mock_unisim
    )
    port map (
      input_source_synchronous_clock => input_source_synchronous_clock,
      input_source_synchronous_data => input_source_synchronous_data,
      --
      input_system_synchronous_clock => input_system_synchronous_clock,
      input_system_synchronous_data => input_system_synchronous_data,
      --
      input_sink_synchronous_clock => input_sink_synchronous_clock,
      input_sink_synchronous_data => input_sink_synchronous_data,
      --
      ddr => ddr,
      fixed_io => fixed_io
    );

end architecture;
