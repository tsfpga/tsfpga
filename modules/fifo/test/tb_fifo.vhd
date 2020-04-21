-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
use vunit_lib.axi_stream_pkg.all;
use vunit_lib.sync_pkg.all;
context vunit_lib.com_context;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.all;

library common;
use common.types_pkg.all;


entity tb_fifo is
  generic (
    depth : integer;
    almost_full_level : integer;
    almost_empty_level : integer;
    runner_cfg : string;
    read_stall_probability_percent : integer := 0;
    write_stall_probability_percent : integer := 0;
    enable_last : boolean := false
  );
end entity;

architecture tb of tb_fifo is

  constant width : integer := 8;

  signal clk : std_logic := '0';

  signal read_ready, read_valid, read_last, almost_empty : std_logic := '0';
  signal write_ready, write_valid, write_last, almost_full : std_logic := '0';
  signal read_data, write_data : std_logic_vector(width - 1 downto 0) := (others => '0');

  signal has_gone_full_times, has_gone_empty_times : integer := 0;

  constant read_stall_config : stall_config_t := new_stall_config(
    stall_probability => real(read_stall_probability_percent) / 100.0,
    min_stall_cycles => 0,
    max_stall_cycles => 4);
  constant read_slave : axi_stream_slave_t := new_axi_stream_slave(
    data_length => width,
    stall_config => read_stall_config,
    protocol_checker => new_axi_stream_protocol_checker(data_length => width,
                                                        logger => get_logger("read_slave")));

  constant write_stall_config : stall_config_t := new_stall_config(
    stall_probability => real(write_stall_probability_percent) / 100.0,
    min_stall_cycles => 0,
    max_stall_cycles => 4);
  constant write_master : axi_stream_master_t := new_axi_stream_master(
    data_length => width,
    stall_config => write_stall_config,
    protocol_checker => new_axi_stream_protocol_checker(data_length => width,
                                                        logger => get_logger("write_master")));

begin

  test_runner_watchdog(runner, 1 ms);
  clk <= not clk after 2 ns;


  ------------------------------------------------------------------------------
  main : process

    variable data_queue, last_queue, axi_stream_pop_reference_queue : queue_t := new_queue;
    variable rnd : RandomPType;

    procedure run_test(read_count, write_count : natural) is
      variable data : std_logic_vector(write_data'range);
      variable last, last_expected : std_logic := '0';
      variable axi_stream_pop_reference : axi_stream_reference_t;
    begin
      for write_idx in 0 to write_count - 1 loop
        data := rnd.RandSLV(data'length);
        last := to_sl(write_idx = write_count - 1);

        push_axi_stream(net, write_master, data, last);

        push(data_queue, data);
        push(last_queue, last);
      end loop;

      -- Queue up reads in order to get full throughput
      for read_idx in 0 to read_count - 1 loop
        pop_axi_stream(net, read_slave, axi_stream_pop_reference);
        -- We need to keep track of the pop_reference when we read the reply later.
        -- Hence it is pushed to a queue.
        push(axi_stream_pop_reference_queue, axi_stream_pop_reference);
      end loop;

      for read_idx in 0 to read_count - 1 loop
        axi_stream_pop_reference := pop(axi_stream_pop_reference_queue);
        await_pop_axi_stream_reply(net, axi_stream_pop_reference, data, last);

        check_equal(data, pop_std_ulogic_vector(data_queue), "read_idx " & to_string(read_idx));
        last_expected := pop(last_queue);
        if enable_last then
          check_equal(last, last_expected, "read_idx " & to_string(read_idx));
        end if;
      end loop;

      wait_until_idle(net, as_sync(write_master));
      wait until rising_edge(clk);
    end procedure;

    procedure run_read(count : natural) is
    begin
      run_test(count, 0);
    end procedure;

    procedure run_write(count : natural) is
    begin
      run_test(0, count);
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    -- Decrease noise
    disable(get_logger("read_slave:rule 4"), warning);
    disable(get_logger("write_master:rule 4"), warning);
    -- Some tests leave data unread in the FIFO
    disable(get_logger("read_slave:rule 9"), error);

    if run("test_write_faster_than_read") then
      run_test(8000, 8000);
      check_true(is_empty(data_queue));
      check_relation(has_gone_full_times > 500, "Got " & to_string(has_gone_full_times));

    elsif run("test_read_faster_than_write") then
      run_test(8000, 8000);
      check_true(is_empty(data_queue));
      check_relation(has_gone_empty_times > 500, "Got " & to_string(has_gone_empty_times));

    elsif run("test_almost_full") then
      check_equal(almost_full, '0');

      run_write(almost_full_level - 1);
      check_equal(almost_full, '0');

      run_write(1);
      check_equal(almost_full, '1');

      run_read(1);
      check_equal(almost_full, '0');

    elsif run("test_almost_empty") then
      check_equal(almost_empty, '1');

      run_write(almost_empty_level);
      check_equal(almost_empty, '1');

      run_write(1);
      if almost_empty_level = 0 then
        -- almost_empty is updated one cycle later, since write must propagate into RAM before
        -- read data is valid
        wait until rising_edge(clk);
      end if;
      check_equal(almost_empty, '0');

      run_read(1);
      check_equal(almost_empty, '1');
    end if;

    test_runner_cleanup(runner, allow_disabled_errors => true);
  end process;


  ------------------------------------------------------------------------------
  status_tracking : process
    variable read_transaction, write_transaction : std_logic := '0';
  begin
    wait until rising_edge(clk);

    -- If there was a read transaction last clock cycle, and we now want to read but there is no data available.
    if read_transaction and read_ready and not read_valid then
      has_gone_empty_times <= has_gone_empty_times + 1;
    end if;

    -- If there was a write transaction last clock cycle, and we now want to write but the fifo is full.
    if write_transaction and write_valid and not write_ready then
      has_gone_full_times <= has_gone_full_times + 1;
    end if;

    read_transaction := read_ready and read_valid;
    write_transaction := write_ready and write_valid;
  end process;


  ------------------------------------------------------------------------------
  axi_stream_slave_inst : entity vunit_lib.axi_stream_slave
    generic map(
      slave => read_slave
    )
    port map(
      aclk => clk,
      tvalid => read_valid,
      tready => read_ready,
      tdata => read_data,
      tlast => read_last
    );


  ------------------------------------------------------------------------------
  axi_stream_master_inst : entity vunit_lib.axi_stream_master
    generic map(
      master => write_master)
    port map(
      aclk => clk,
      tvalid => write_valid,
      tready => write_ready,
      tdata => write_data,
      tlast => write_last
    );


  ------------------------------------------------------------------------------
  dut : entity work.fifo
    generic map (
      width => width,
      depth => depth,
      almost_full_level => almost_full_level,
      almost_empty_level => almost_empty_level,
      enable_last => enable_last
    )
    port map (
      clk => clk,

      read_ready => read_ready,
      read_valid => read_valid,
      read_data => read_data,
      read_last => read_last,
      almost_empty => almost_empty,

      write_ready => write_ready,
      write_valid => write_valid,
      write_data => write_data,
      write_last => write_last,
      almost_full => almost_full
    );

end architecture;
