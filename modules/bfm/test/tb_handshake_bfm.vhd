-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;


entity tb_handshake_bfm is
  generic (
    master_stall_probability_percent : natural;
    slave_stall_probability_percent : natural;
    data_width : natural;
    runner_cfg : string
  );
end entity;

architecture tb of tb_handshake_bfm is

  constant max_stall_cycles : natural := 5;

  signal clk : std_logic := '0';
  constant clk_period : time := 10 ns;

  signal data_ready, data_valid : std_logic := '0';
  signal data_is_ready, data_is_valid : std_logic := '0';
  signal data : std_logic_vector(data_width - 1 downto 0) := (others => '0');

begin

  test_runner_watchdog(runner, 2 ms);
  clk <= not clk after clk_period / 2;


  ------------------------------------------------------------------------------
  main : process

  begin
    test_runner_setup(runner, runner_cfg);

    wait until rising_edge(clk);

    if run("test_full_master_throughput") then
      data_is_valid <= '1';

      wait until rising_edge(clk);
      check_equal(data_valid, '1');

      wait until data_valid'event for 100 * clk_period;
      check_equal(data_valid, '1');

      -- Should still be full throughput even when we start popping words
      data_is_ready <= '1';
      wait until data_valid'event for 100 * clk_period;
      check_equal(data_valid, '1');

    elsif run("test_full_slave_throughput") then
      data_is_ready <= '1';

      wait until rising_edge(clk);
      check_equal(data_ready, '1');

      wait until data_ready'event for 100 * clk_period;
      check_equal(data_ready, '1');

      -- Should still be full throughput even when we start popping words
      data_is_valid <= '1';
      wait until data_ready'event for 100 * clk_period;
      check_equal(data_ready, '1');

    elsif run("test_random") then
      data_is_ready <= '1';
      data_is_valid <= '1';

      wait for 1000 * clk_period;

    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  -- Show that it can be instantiated with or without data/generics
  instantiate_dut : if data_width > 0 generate

    ------------------------------------------------------------------------------
    handshake_master_inst : entity work.handshake_master
      generic map (
        stall_probability_percent => master_stall_probability_percent,
        max_stall_cycles => max_stall_cycles,
        logger_prefix => "foo_",
        data_width => data'length
      )
      port map (
        clk => clk,
        --
        data_is_valid => data_is_valid,
        --
        data_ready => data_ready,
        data_valid => data_valid,
        data => data
      );


    ------------------------------------------------------------------------------
    handshake_slave_inst : entity work.handshake_slave
      generic map (
        stall_probability_percent => slave_stall_probability_percent,
        max_stall_cycles => max_stall_cycles,
        logger_prefix => "foo_",
        data_width => data'length
      )
      port map (
        clk => clk,
        --
        data_is_ready => data_is_ready,
        --
        data_ready => data_ready,
        data_valid => data_valid,
        data => data
      );


  else generate

    ------------------------------------------------------------------------------
    handshake_master_inst : entity work.handshake_master
      generic map (
        stall_probability_percent => master_stall_probability_percent,
        max_stall_cycles => max_stall_cycles
      )
      port map (
        clk => clk,
        --
        data_is_valid => data_is_valid,
        --
        data_ready => data_ready,
        data_valid => data_valid
      );

    ------------------------------------------------------------------------------
    handshake_slave_inst : entity work.handshake_slave
      generic map (
        stall_probability_percent => slave_stall_probability_percent,
        max_stall_cycles => max_stall_cycles
      )
      port map (
        clk => clk,
        --
        data_ready => data_ready,
        data_valid => data_valid
      );

  end generate;

end architecture;
