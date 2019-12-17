-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.data_types_context;

library osvvm;
use osvvm.RandomPkg.all;


entity tb_afifo is
  generic (
    width      : integer;
    depth      : integer;
    runner_cfg : string
    );
end entity;

architecture tb of tb_afifo is

  signal clk_read, clk_write : std_logic := '0';

  signal read_ready, read_valid    : std_logic := '0';
  signal write_ready, write_valid  : std_logic := '0';
  signal read_data, write_data     : std_logic_vector(width - 1 downto 0) := (others => '0');

  signal read_level, write_level : integer;
  signal read_almost_empty, write_almost_full : std_logic := '0';

  signal start_stimuli, writer_done, reader_done : boolean   := false;

  constant num_stimuli : integer := 50 * depth;
  signal write_max_jitter, read_max_jitter : integer := 0;

  signal has_gone_full_times, has_gone_empty_times : integer := 0;

  shared variable rnd : RandomPType;
  signal data_queue   : queue_t := new_queue;

begin

  test_runner_watchdog(runner, 2 ms);
  clk_read  <= not clk_read after 2 ns;
  clk_write <= not clk_write after 3 ns;


  ------------------------------------------------------------------------------
  main : process
    procedure start is
    begin
      start_stimuli <= true;
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
      start_stimuli <= false;
    end procedure;

    procedure run_test is
    begin
      start;
      wait until writer_done and reader_done;
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("random_read_and_write") then
      run_test;

    elsif run("random_read_and_write_with_more_write_jitter") then
      read_max_jitter <= 1;
      write_max_jitter <= 8;

      run_test;
      check_relation(has_gone_empty_times > 200, "Got " & to_string(has_gone_empty_times));
      check_true(is_empty(data_queue));

    elsif run("random_read_and_write_with_more_read_jitter") then
      read_max_jitter <= 8;
      write_max_jitter <= 1;

      run_test;
      check_relation(has_gone_full_times > 200, "Got " & to_string(has_gone_full_times));
      check_true(is_empty(data_queue));

    elsif run("levels_as_well_as_empty_and_full_flags_are_updated") then
      -- Check empty status
      check_equal(write_almost_full, '0');
      check_equal(write_level, 0);
      check_equal(read_almost_empty, '1');
      check_equal(read_level, 0);

      start;

      -- Fill the FIFO
      read_max_jitter <= 5000;
      write_max_jitter <= 0;
      for delay in 1 to 5000 loop
        wait until rising_edge(clk_read);
        wait until rising_edge(clk_write);
      end loop;

      -- Check full status
      check_equal(write_almost_full, '1');
      check_equal(write_level, depth);
      check_equal(read_almost_empty, '0');
      check_equal(read_level, depth);

      -- Empty the FIFO
      read_max_jitter <= 0;
      write_max_jitter <= 5000;
      for delay in 1 to 5000 loop
        wait until rising_edge(clk_read);
        wait until rising_edge(clk_write);
      end loop;

      -- Check empty status
      check_equal(write_almost_full, '0');
      check_equal(write_level, 0);
      check_equal(read_almost_empty, '1');
      check_equal(read_level, 0);

    elsif run("check_init_state") then
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(write_almost_full, '0');
      check_equal(read_almost_empty, '1');
      wait until read_valid = '1' or write_ready = '0' or write_almost_full = '1' or read_almost_empty = '0' for 1 us;
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(write_almost_full, '0');
      check_equal(read_almost_empty, '1');
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  write_stimuli : process
    procedure write_fifo is
    begin
      write_valid <= '1';
      write_data  <= rnd.RandSlv(write_data'length);
      wait until (write_ready and write_valid) = '1' and rising_edge(clk_write);
      push(data_queue, write_data);
      write_valid <= '0';
    end procedure;
  begin
    wait until rising_edge(clk_write) and start_stimuli;
    writer_done <= false;

    for stimuli_idx in 1 to num_stimuli loop
      write_fifo;
      for delay in 1 to rnd.FavorSmall(0, write_max_jitter) loop
        wait until rising_edge(clk_write);
      end loop;
    end loop;

    writer_done <= true;
  end process;


  ------------------------------------------------------------------------------
  read_stimuli : process
    procedure read_fifo is
    begin
      read_ready <= '1';
      wait until (read_ready and read_valid) = '1' and rising_edge(clk_read);
      check_equal(read_data, pop_std_ulogic_vector(data_queue));
      read_ready <= '0';
    end procedure;
  begin
    wait until rising_edge(clk_read) and start_stimuli;
    reader_done <= false;

    for stimuli_idx in 1 to num_stimuli loop
      read_fifo;
      for delay in 1 to rnd.FavorSmall(0, read_max_jitter) loop
        wait until rising_edge(clk_read);
      end loop;
    end loop;

    reader_done <= true;
  end process;


  ------------------------------------------------------------------------------
  read_status_tracking : process
    variable read_transaction : std_logic := '0';
  begin
    wait until rising_edge(clk_read);

    -- If there was a read transaction last clock cycle, and we now want to read but there is no data available.
    if read_transaction and read_ready and not read_valid then
      has_gone_empty_times <= has_gone_empty_times + 1;
    end if;

    read_transaction := read_ready and read_valid;
  end process;


  ------------------------------------------------------------------------------
  write_status_tracking : process
    variable write_transaction : std_logic := '0';
  begin
    wait until rising_edge(clk_write);

    -- If there was a write transaction last clock cycle, and we now want to write but the fifo is full.
    if write_transaction and write_valid and not write_ready then
      has_gone_full_times <= has_gone_full_times + 1;
    end if;

    write_transaction := write_ready and write_valid;
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.afifo
    generic map (
      width              => width,
      depth              => depth,
      almost_full_level  => depth - 1,
      almost_empty_level => 1
    )
    port map (
      clk_read => clk_read,
      read_ready   => read_ready,
      read_valid   => read_valid,
      read_data    => read_data,
      --
      read_level => read_level,
      read_almost_empty => read_almost_empty,
      --
      clk_write => clk_write,
      write_ready => write_ready,
      write_valid => write_valid,
      write_data  => write_data,
      --
      write_level => write_level,
      write_almost_full => write_almost_full
    );

end architecture;
