-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library osvvm;
use osvvm.RandomPkg.all;

library axi;
use axi.axi_pkg.all;

library bfm;


entity tb_axi_interconnect is
  generic(
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_interconnect is

  constant num_inputs : integer := 4;
  constant clk_period : time := 5 ns;

  signal clk : std_logic := '0';

  signal inputs_read_m2s : axi_read_m2s_vec_t(0 to num_inputs - 1) := (others => axi_read_m2s_init);
  signal inputs_read_s2m : axi_read_s2m_vec_t(0 to num_inputs - 1) := (others => axi_read_s2m_init);

  signal output_read_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal output_read_s2m : axi_read_s2m_t := axi_read_s2m_init;

  constant axi_port_data_width : integer := 32;
  type bus_master_vec_t is array (integer range <>) of bus_master_t;
  constant axi_masters : bus_master_vec_t(inputs_read_m2s'range) := (
    0 => new_bus(data_length => axi_port_data_width, address_length => output_read_m2s.ar.addr'length),
    1 => new_bus(data_length => axi_port_data_width, address_length => output_read_m2s.ar.addr'length),
    2 => new_bus(data_length => axi_port_data_width, address_length => output_read_m2s.ar.addr'length),
    3 => new_bus(data_length => axi_port_data_width, address_length => output_read_m2s.ar.addr'length)
  );

  constant memory : memory_t := new_memory;
  constant axi_slave : axi_slave_t := new_axi_slave(
    memory => memory,
    address_fifo_depth => 8,
    write_response_fifo_depth => 8,
    address_stall_probability => 0.3,
    data_stall_probability => 0.3,
    write_response_stall_probability => 0.3,
    min_response_latency => 12 * clk_period,
    max_response_latency => 20 * clk_period,
    logger => get_logger("axi_rd_slave")
  );

begin

  clk <= not clk after clk_period / 2;
  test_runner_watchdog(runner, 1 ms);


  ------------------------------------------------------------------------------
  main : process
    constant num_words : integer := 1000;
    constant bytes_per_word : integer := axi_port_data_width / 8;
    variable got, expected : std_logic_vector(axi_port_data_width - 1 downto 0);
    variable address : integer;
    variable buf : buffer_t;
    variable rnd : RandomPType;

    variable input_select : integer;
    variable bus_reference : bus_reference_t;

    variable bus_reference_queue : queue_t := new_queue;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("read_random_data_from_random_input_master") then
      buf := allocate(memory, num_words * bytes_per_word);

      -- Set random data in read memory
      for idx in 0 to num_words - 1 loop
        address := idx * bytes_per_word;
        expected := rnd.RandSlv(expected'length);
        write_word(memory, address, expected);
      end loop;

      -- Queue up reads from random input master
      for idx in 0 to num_words - 1 loop
        input_select := rnd.RandInt(0, axi_masters'high);
        read_bus(net, axi_masters(input_select), address, bus_reference);
        push(bus_reference_queue, bus_reference);
      end loop;

      -- Verify read data
      for idx in 0 to num_words - 1 loop
        expected := read_word(memory, address, bytes_per_word);
        bus_reference := pop(bus_reference_queue);
        await_read_bus_reply(net, bus_reference, got);
        check_equal(got, expected, "idx=" & to_string(idx));
      end loop;
    end if;

    assert is_empty(bus_reference_queue);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axi_masters_gen : for idx in inputs_read_m2s'range generate
  begin
    axi_master_inst : entity bfm.axi_master
      generic map (
        bus_handle => axi_masters(idx)
      )
      port map (
        clk => clk,
        --
        axi_read_m2s => inputs_read_m2s(idx),
        --
        axi_read_s2m => inputs_read_s2m(idx)
      );
  end generate;


  ------------------------------------------------------------------------------
  axi_slave_inst : entity bfm.axi_slave
    generic map (
      axi_slave => axi_slave,
      data_width => axi_port_data_width
    )
    port map (
      clk => clk,
      --
      axi_read_m2s => output_read_m2s,
      --
      axi_read_s2m => output_read_s2m
    );


  ------------------------------------------------------------------------------
  dut : entity work.axi_interconnect
    generic map(
      num_inputs => num_inputs
    )
    port map(
      clk => clk,
      --
      inputs_read_m2s => inputs_read_m2s,
      inputs_read_s2m => inputs_read_s2m,
      --
      output_read_m2s => output_read_m2s,
      output_read_s2m => output_read_s2m
    );

end architecture;
