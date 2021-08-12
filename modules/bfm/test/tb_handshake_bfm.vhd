-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
context vunit_lib.vunit_context;

library common;


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

  signal input_ready, input_valid, result_ready, result_valid : std_logic := '0';
  signal input_data, result_data : std_logic_vector(data_width - 1 downto 0) := (others => '0');

  signal result_is_ready, input_is_valid : std_logic := '0';

  constant reference_data_queue : queue_t := new_queue;

begin

  test_runner_watchdog(runner, 2 ms);
  clk <= not clk after clk_period / 2;


  ------------------------------------------------------------------------------
  main : process

    variable stimuli_data : std_logic_vector(input_data'range) := (others => '0');
    variable rnd : RandomPType;

  begin
    test_runner_setup(runner, runner_cfg);

    rnd.InitSeed(rnd'instance_name);

    -- Decrease noise. The loggers are named differently depending on what test case we are running.
    disable(get_logger("input_handshake_master:rule 4"), warning);
    disable(get_logger("result_handshake_slave:rule 4"), warning);
    disable(get_logger("handshake_master:rule 4"), warning);
    disable(get_logger("handshake_slave:rule 4"), warning);

    wait until rising_edge(clk);

    if run("test_full_master_throughput") then
      input_is_valid <= '1';

      -- Wait one clock for 'input_valid' to be asserted, and one clock for in to propagate through
      -- the handshake pipeline
      wait until rising_edge(clk);
      wait until rising_edge(clk);
      check_equal(result_valid, '1');

      wait until result_valid'event for 100 * clk_period;
      check_equal(result_valid, '1');

      -- Should still be full throughput even when we start popping words
      result_is_ready <= '1';
      wait until result_valid'event for 100 * clk_period;
      check_equal(result_valid, '1');

    elsif run("test_full_slave_throughput") then
      result_is_ready <= '1';

      wait until rising_edge(clk);
      check_equal(input_ready, '1');

      wait until input_ready'event for 100 * clk_period;
      check_equal(input_ready, '1');

      -- Should still be full throughput even when we start popping words
      input_is_valid <= '1';
      wait until input_ready'event for 100 * clk_period;
      check_equal(input_ready, '1');

    elsif run("test_random_data") then
      result_is_ready <= '1';
      input_is_valid <= '1';

      for idx in 0 to 1000 loop
        stimuli_data := rnd.RandSlv(stimuli_data'length);
        push(reference_data_queue, stimuli_data);

        input_data <= stimuli_data;
        wait until (input_ready and input_valid) = '1' and rising_edge(clk);
      end loop;

      input_is_valid <= '0';

      wait until is_empty(reference_data_queue) and rising_edge(clk);
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
        logger_prefix => "input_",
        data_width => input_data'length
      )
      port map (
        clk => clk,
        --
        data_is_valid => input_is_valid,
        --
        data_ready => input_ready,
        data_valid => input_valid,
        data => input_data
      );


    ------------------------------------------------------------------------------
    handshake_slave_inst : entity work.handshake_slave
      generic map (
        stall_probability_percent => slave_stall_probability_percent,
        max_stall_cycles => max_stall_cycles,
        logger_prefix => "result_",
        data_width => result_data'length
      )
      port map (
        clk => clk,
        --
        data_is_ready => result_is_ready,
        --
        data_ready => result_ready,
        data_valid => result_valid,
        data => result_data
      );

    ------------------------------------------------------------------------------
    data_check : process
      variable reference_data : std_logic_vector(result_data'range) := (others => '0');
    begin
      wait until (result_ready and result_valid) = '1' and rising_edge(clk);
      reference_data := pop(reference_data_queue);
      check_equal(result_data, reference_data);
    end process;

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
        data_is_valid => input_is_valid,
        --
        data_ready => input_ready,
        data_valid => input_valid
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
        data_ready => result_ready,
        data_valid => result_valid
      );

  end generate;


  ------------------------------------------------------------------------------
  -- Pass data and control signals through something that performs proper handshaking
  handshake_pipeline_inst : entity common.handshake_pipeline
    generic map (
      data_width => data_width
    )
    port map (
      clk => clk,
      --
      input_ready => input_ready,
      input_valid => input_valid,
      input_data => input_data,
      --
      output_ready => result_ready,
      output_valid => result_valid,
      output_data => result_data
    );

end architecture;
