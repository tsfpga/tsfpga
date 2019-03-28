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

  signal clk_read  : std_logic := '0';
  signal clk_write : std_logic := '0';

  signal read_ready, read_valid                  : std_logic                            := '0';
  signal write_ready, write_valid                : std_logic                            := '0';
  signal almost_empty, almost_full               : std_logic                            := '0';
  signal read_data, write_data                   : std_logic_vector(width - 1 downto 0) := (others => '0');
  signal start_stimuli, writer_done, reader_done : boolean                              := false;
  signal stop_read_clk, stop_write_clk           : std_logic                            := '0';

  shared variable rnd : RandomPType;
  signal queue        : queue_t := new_queue;

begin

  test_runner_watchdog(runner, 2 ms);
  clk_read  <= (not clk_read) or stop_read_clk   after 2 ns;
  clk_write <= (not clk_write) or stop_write_clk after 3 ns;


  ------------------------------------------------------------------------------
  main : process
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("random_read_and_write") then
      start_stimuli <= true;
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
      start_stimuli <= false;

      wait until writer_done and reader_done;

    elsif run("very_strange_clocks") then
      start_stimuli <= true;
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
      start_stimuli <= false;

      -- Stop read clock and wait until full
      stop_read_clk <= '1';
      wait until write_ready = '0';
      -- Wait one cycle so address is clocked into cdc
      wait until rising_edge(clk_write);
      stop_read_clk <= '0';
      wait until rising_edge(clk_write);
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_read);
      check_equal(read_valid, '1');

      -- Stop write clock and read all data
      stop_write_clk <= '1';
      wait until read_valid = '0';
      -- Wait one cycle so address is clocked into cdc
      wait until rising_edge(clk_read);
      stop_write_clk <= '0';
      wait until rising_edge(clk_read);
      wait until rising_edge(clk_write);
      wait until rising_edge(clk_write);
      wait until rising_edge(clk_write);
      check_equal(write_ready, '1');

      wait until writer_done and reader_done;

    elsif run("check_init_state") then
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(almost_full, '0');
      check_equal(almost_empty, '1');
      wait until read_valid = '1' or write_ready = '0' or almost_full = '1' or almost_empty = '0' for 1 us;
      check_equal(read_valid, '0');
      check_equal(write_ready, '1');
      check_equal(almost_full, '0');
      check_equal(almost_empty, '1');
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
      push(queue, write_data);
      write_valid <= '0';
    end procedure;
  begin
    wait until rising_edge(clk_write) and start_stimuli;
    while now < 1 ms loop
      wait until rising_edge(clk_write);
      write_fifo;
      for delay in 1 to rnd.FavorSmall(0, 0) loop
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
      check_equal(read_data, pop_std_ulogic_vector(queue));
      read_ready <= '0';
    end procedure;
  begin
    wait until rising_edge(clk_read) and start_stimuli;
    while now < 1 ms loop
      wait until rising_edge(clk_read);
      read_fifo;
      for delay in 1 to rnd.FavorSmall(0, 4) loop
        wait until rising_edge(clk_read);
      end loop;
    end loop;

    reader_done <= true;
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
      almost_empty => almost_empty,

      clk_write => clk_write,

      write_ready => write_ready,
      write_valid => write_valid,
      write_data  => write_data,
      almost_full => almost_full
      );

end architecture;
