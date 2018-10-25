library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
use vunit_lib.axi_slave_pkg.all;
use vunit_lib.memory_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.com_context;

library osvvm;
use osvvm.RandomPkg.all;

library bfm;

use work.axi_pkg.all;
use work.axil_pkg.all;


entity tb_axil_cdc is
  generic (
    input_clk_fast : boolean := false;
    output_clk_fast : boolean := false;
    runner_cfg : string
  );
end entity;

architecture tb of tb_axil_cdc is

  constant data_width : integer := 32;
  constant num_words : integer := 2048;

  constant clk_fast_period : time := 3 ns;
  constant clk_slow_period : time := 7 ns;

  signal clk_input, clk_output : std_logic := '0';

  signal input_m2s, output_m2s : axil_m2s_t;
  signal input_s2m, output_s2m : axil_s2m_t;

  constant axil_input_master : bus_master_t := new_bus(data_length => data_width, address_length => input_m2s.read.ar.addr'length);

  constant memory : memory_t := new_memory;
  constant axil_output_slave : axi_slave_t := new_axi_slave(address_fifo_depth => 1, memory => memory);

begin

  test_runner_watchdog(runner, 1 ms);

  clk_input_gen : if input_clk_fast generate
    clk_input <= not clk_input after clk_fast_period / 2;
  else generate
    clk_input <= not clk_input after clk_slow_period / 2;
  end generate;

  clk_output_gen : if output_clk_fast generate
    clk_output <= not clk_output after clk_fast_period / 2;
  else generate
    clk_output <= not clk_output after clk_slow_period / 2;
  end generate;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;
    variable data : std_logic_vector(data_width - 1 downto 0);
    variable address : integer;
    variable buf : buffer_t;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    buf := allocate(memory, 4 * num_words);

    for idx in 0 to num_words - 1 loop
      address := 4 * idx;
      data := rnd.RandSlv(data'length);

       -- Call is non-blocking. I.e. we will build up a queue of writes.
      write_bus(net, axil_input_master, address, data);
      set_expected_word(memory, address, data);
      wait until rising_edge(clk_input);
    end loop;

    for idx in 0 to num_words - 1 loop
      address := 4 * idx;
      data := read_word(memory, address, 4);

      check_bus(net, axil_input_master, address, data);
    end loop;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axil_master_inst : entity bfm.axil_master
    generic map (
      bus_handle => axil_input_master
    )
    port map (
      clk => clk_input,

      axil_m2s => input_m2s,
      axil_s2m => input_s2m
    );


  ------------------------------------------------------------------------------
  axil_slave_inst : entity bfm.axil_slave
  generic map (
    axi_slave => axil_output_slave,
    data_width => data_width
  )
  port map (
    clk => clk_output,

    axil_m2s => output_m2s,
    axil_s2m => output_s2m
  );


  ------------------------------------------------------------------------------
  dut : entity work.axil_cdc
    generic map (
      data_width => data_width
    )
    port map (
      clk_input => clk_input,
      input_m2s => input_m2s,
      input_s2m => input_s2m,

      clk_output => clk_output,
      output_m2s => output_m2s,
      output_s2m => output_s2m
    );

end architecture;
