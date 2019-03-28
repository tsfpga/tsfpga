-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.all;

use work.types_pkg.all;


entity tb_handshake_pipeline is
  generic (
    data_jitter : boolean := true;
    runner_cfg : string
  );
end entity;

architecture tb of tb_handshake_pipeline is

  signal clk : std_logic := '0';
  constant clk_period : time := 10 ns;

  constant data_width : integer := 16;

  signal input_ready, input_valid, input_last : std_logic := '0';
  signal output_ready, output_valid, output_last : std_logic := '0';
  signal input_data, output_data : std_logic_vector(data_width - 1 downto 0);

  constant num_words : integer := 8_000;
  signal queue : queue_t := new_queue;

  signal start, stimuli_done, data_check_done : boolean := false;

begin

  test_runner_watchdog(runner, 2 ms);
  clk <= not clk after clk_period / 2;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;

    procedure run_test is
    begin
      report "Starting test";
      start <= true;
      wait until rising_edge(clk);
      start <= false;
      wait until rising_edge(clk);
      wait until stimuli_done and data_check_done and rising_edge(clk);
    end procedure;

    variable start_time, time_diff : time;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("test_data") then
      run_test;
      run_test;
      run_test;
      run_test;

    elsif run("test_full_throughput") then
      start_time := now;
      run_test;
      time_diff := now - start_time;

      check_relation(time_diff < (num_words + 3) * clk_period);
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  stimuli : process
    variable rnd : RandomPType;
    variable input_data_v : std_logic_vector(input_data'range);
  begin
    rnd.InitSeed(rnd'instance_name);

    loop
      wait until start and rising_edge(clk);
      stimuli_done <= false;

      for i in 0 to num_words - 1 loop
        input_valid <= '1';
        input_data_v := rnd.RandSlv(input_data_v'length);
        input_data <= input_data_v;
        input_last <= to_sl(i = num_words - 1);
        wait until (input_ready and input_valid) = '1' and rising_edge(clk);
        push(queue, input_data_v);

        input_valid <= '0';
        if data_jitter then
          for wait_cycle in 1 to rnd.FavorSmall(0, 2) loop
            wait until rising_edge(clk);
          end loop;
        end if;
      end loop;

      input_valid <= '0';
      stimuli_done <= true;
    end loop;
  end process;


  ------------------------------------------------------------------------------
  data_check : process
    variable rnd : RandomPType;
  begin
    rnd.InitSeed(rnd'instance_name);

    loop
      wait until start and rising_edge(clk);
      data_check_done <= false;

      for i in 0 to num_words - 1 loop
        output_ready <= '1';
        wait until (output_ready and output_valid) = '1' and rising_edge(clk);
        check_equal(output_data, pop_std_ulogic_vector(queue));
        check_equal(output_last, i = num_words - 1);

        output_ready <= '0';
        if data_jitter then
          for wait_cycle in 1 to rnd.FavorSmall(0, 2) loop
            wait until rising_edge(clk);
          end loop;
        end if;
      end loop;

      data_check_done <= true;
    end loop;
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.handshake_pipeline
    generic map (
      data_width => data_width
    )
    port map (
      clk => clk,
      --
      input_ready => input_ready,
      input_valid => input_valid,
      input_last => input_last,
      input_data => input_data,
      --
      output_ready => output_ready,
      output_valid => output_valid,
      output_last => output_last,
      output_data => output_data
    );

end architecture;
