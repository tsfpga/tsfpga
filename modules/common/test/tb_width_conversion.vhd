-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.all;

use work.types_pkg.all;


entity tb_width_conversion is
  generic (
    input_width : integer;
    output_width : integer;
    data_jitter : boolean := true;
    runner_cfg : string
  );
end entity;

architecture tb of tb_width_conversion is

  signal clk : std_logic := '0';
  constant clk_period : time := 10 ns;

  signal input_ready, input_valid, input_last : std_logic := '0';
  signal output_ready, output_valid, output_last : std_logic := '0';
  signal input_data : std_logic_vector(input_width - 1 downto 0);
  signal output_data : std_logic_vector(output_width - 1 downto 0);

  constant num_input_words : integer := 8_000;
  constant num_output_words : integer := num_input_words * input_width / output_width;
  constant num_cycles : integer := maximum(num_input_words, num_output_words);

  signal start, stimuli_done, data_check_done : boolean := false;

  procedure random_slv(rnd : inout RandomPType; data : out std_logic_vector) is
    variable random_sl : std_logic_vector(0 downto 0);
  begin
    -- Build up a word from LSB to MSB, which corresponds to little endian when
    -- comparing wide words with packed thin words.
    for i in 0 to data'length - 1 loop
      random_sl := rnd.RandSlv(1);
      data(i) := random_sl(0);
    end loop;
  end procedure;
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

      check_relation(time_diff < (num_cycles + 3) * clk_period);
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  stimuli : process
    variable rnd_jitter, rnd_data : RandomPType;
    variable input_data_v : std_logic_vector(input_data'range);
  begin
    rnd_jitter.InitSeed(rnd_jitter'instance_name);
    rnd_data.InitSeed("rnd_data");

    wait until start and rising_edge(clk);
    stimuli_done <= false;

    for i in 0 to num_input_words - 1 loop
      input_valid <= '1';
      random_slv(rnd_data, input_data_v);
      input_data <= input_data_v;
      input_last <= to_sl(i = num_input_words - 1);
      wait until (input_ready and input_valid) = '1' and rising_edge(clk);

      if data_jitter then
        input_valid <= '0';
        for wait_cycle in 1 to rnd_jitter.FavorSmall(0, 2) loop
          wait until rising_edge(clk);
        end loop;
      end if;
    end loop;

    input_valid <= '0';
    stimuli_done <= true;
  end process;


  ------------------------------------------------------------------------------
  data_check : process
    variable rnd_jitter, rnd_data : RandomPType;
    variable expected_data : std_logic_vector(output_data'range);
  begin
    rnd_jitter.InitSeed(rnd_jitter'instance_name);
    rnd_data.InitSeed("rnd_data");

    wait until start and rising_edge(clk);
    data_check_done <= false;

    for i in 0 to num_output_words - 1 loop
      output_ready <= '1';
      wait until (output_ready and output_valid) = '1' and rising_edge(clk);

      -- Build up the expected output data vector in same way that input data
      -- is generated above. Note that the same random seed is used.
      random_slv(rnd_data, expected_data);
      check_equal(output_data, expected_data, "i=" & to_string(i));
      check_equal(output_last, to_sl(i = num_output_words - 1), "i=" & to_string(i));

      if data_jitter then
        output_ready <= '0';
        for wait_cycle in 1 to rnd_jitter.FavorSmall(0, 2) loop
          wait until rising_edge(clk);
        end loop;
      end if;
    end loop;

    output_ready <= '0';
    data_check_done <= true;
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.width_conversion
    generic map (
      input_width => input_width,
      output_width => output_width
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
