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
    depth : integer;
    almost_empty_level : natural;
    almost_full_level : natural;
    read_clock_is_faster : boolean;
    runner_cfg : string
    );
end entity;

architecture tb of tb_afifo is

  constant width : integer := 8;

  signal clk_read, clk_write : std_logic := '0';

  signal read_ready, read_valid    : std_logic := '0';
  signal write_ready, write_valid  : std_logic := '0';
  signal read_data, write_data     : std_logic_vector(width - 1 downto 0) := (others => '0');

  signal read_level, write_level : integer;
  signal read_almost_empty, write_almost_full : std_logic := '0';

  signal start, writer_done, reader_done : boolean := false;

  signal num_read, num_write : integer;
  signal write_max_jitter, read_max_jitter : integer := 0;

  signal has_gone_full_times, has_gone_empty_times : integer := 0;

  shared variable rnd : RandomPType;
  signal data_queue   : queue_t := new_queue;

begin

  test_runner_watchdog(runner, 2 ms);

  clocks : if read_clock_is_faster generate
    clk_read  <= not clk_read after 2 ns;
    clk_write <= not clk_write after 3 ns;
  else  generate
    clk_read  <= not clk_read after 3 ns;
    clk_write <= not clk_write after 2 ns;
  end generate;


  ------------------------------------------------------------------------------
  main : process

    procedure run_test(read_count, write_count : natural) is
    begin
      num_read <= read_count;
      num_write <= write_count;

      start <= true;
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
      start <= false;

      wait until writer_done and reader_done;
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
    end procedure;

    procedure run_read(count : natural) is
    begin
      run_test(count, 0);
    end procedure;

    procedure run_write(count : natural) is
    begin
      run_test(0, count);
    end procedure;

    procedure wait_for_read_to_propagate is
    begin
      wait until rising_edge(clk_write);
      wait until rising_edge(clk_write);
    end procedure;

    procedure wait_for_write_to_propagate is
    begin
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_read);
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("test_init_state") then
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(write_almost_full, '0');
      check_equal(read_almost_empty, '1');
      wait until read_valid'event or write_ready'event or write_almost_full'event or read_almost_empty'event for 1 us;
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(write_almost_full, '0');
      check_equal(read_almost_empty, '1');

    elsif run("test_write_faster_than_read") then
      read_max_jitter <= 8;
      write_max_jitter <= 1;

      run_test(50 * depth, 50 * depth);
      check_relation(has_gone_full_times > 200);
      check_true(is_empty(data_queue));

    elsif run("test_read_faster_than_write") then
      read_max_jitter <= 1;
      write_max_jitter <= 8;

      run_test(50 * depth, 50 * depth);
      check_relation(has_gone_empty_times > 200);
      check_true(is_empty(data_queue));

    elsif run("test_levels_full_range") then
      -- Check empty status
      check_equal(write_level, 0);
      check_equal(read_level, 0);

      -- Fill the FIFO
      run_write(depth);

      -- Check full status. Must wait a while before all writes have propagated to read side.
      check_equal(write_level, depth);
      wait_for_write_to_propagate;
      check_equal(read_level, depth);

      -- Empty the FIFO
      run_read(depth);

      -- Check empty status. Must wait a while before all reads have propagated to write side.
      check_equal(read_level, 0);
      wait_for_read_to_propagate;
      check_equal(write_level, 0);

    elsif run("test_write_almost_full") then
      check_equal(write_almost_full, '0');

      run_write(almost_full_level - 1);
      check_equal(write_almost_full, '0');

      run_write(1);
      check_equal(write_almost_full, '1');

      run_read(1);
      wait_for_read_to_propagate;
      check_equal(write_almost_full, '0');

    elsif run("test_read_almost_empty") then
      check_equal(read_almost_empty, '1');

      run_write(almost_empty_level);
      check_equal(read_almost_empty, '1');

      run_write(1);
      wait_for_write_to_propagate;
      check_equal(read_almost_empty, '0');

      run_read(1);
      check_equal(read_almost_empty, '1');
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  write_stimuli : process
  begin
    wait until rising_edge(clk_write) and start;
    writer_done <= false;

    for stimuli_idx in 1 to num_write loop
      write_valid <= '1';
      write_data  <= rnd.RandSlv(write_data'length);
      wait until (write_ready and write_valid) = '1' and rising_edge(clk_write);
      push(data_queue, write_data);

      write_valid <= '0';
      for delay in 1 to rnd.FavorSmall(0, write_max_jitter) loop
        wait until rising_edge(clk_write);
      end loop;
    end loop;

    wait until rising_edge(clk_write);
    writer_done <= true;
  end process;


  ------------------------------------------------------------------------------
  read_stimuli : process
  begin
    wait until rising_edge(clk_read) and start;
    reader_done <= false;

    for stimuli_idx in 1 to num_read loop
      read_ready <= '1';
      wait until (read_ready and read_valid) = '1' and rising_edge(clk_read);
      check_equal(read_data, pop_std_ulogic_vector(data_queue));

      read_ready <= '0';
      for delay in 1 to rnd.FavorSmall(0, read_max_jitter) loop
        wait until rising_edge(clk_read);
      end loop;
    end loop;

    wait until rising_edge(clk_read);
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
      almost_full_level  => almost_full_level,
      almost_empty_level => almost_empty_level
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
